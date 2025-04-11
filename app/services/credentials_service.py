from datetime import datetime, timedelta
from typing import Optional, List
from jose import jwt, JWTError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from passlib.context import CryptContext
from app.models.user import User, UserInDB, UserCreate, UserUpdate
from app.models.credentials import ServiceCredentialCreate, ServiceCredentialResponse, ServiceCredentialUpdate
from app.database.models import ServiceCredentials, User as DBUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CredentialsService:
    def __init__(self, secret_key: str, algorithm: str = "HS256", token_expire_minutes: int = 30):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expire_minutes = token_expire_minutes

    def get_user(self, db: AsyncSession, username: str) -> Optional[UserInDB]:
        result = db.execute(select(DBUser).where(DBUser.username == username))
        user = result.scalars().first()
        if user:
            return UserInDB.from_orm(user)
        return None

    def create_user(self, db: AsyncSession, user_data: UserCreate) -> dict:
        # Check if user exists
        result = db.execute(select(DBUser).where(
            DBUser.username == user_data.username))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username already registered"
            )

        # Create new user
        current_time = datetime.utcnow()
        hashed_password = self.get_password_hash(user_data.password)
        db_user = DBUser(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
            created_at=current_time,
            updated_at=current_time
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        user_data = {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "is_active": db_user.is_active,
            "created_at": db_user.created_at,
            "updated_at": db_user.updated_at
        }

        # Generate login token
        token_data = self.login_token(db, UserInDB.from_orm(db_user))

        return {
            **user_data,
            **token_data
        }

    def get_password_hash(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def authenticate_user(self, db: AsyncSession, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password."""
        user = self.get_user(db, username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return User.from_orm(user)

    def login_token(self, db: AsyncSession, user: UserInDB, expires_delta: Optional[timedelta] = None) -> dict:
        # Create token with expiration
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)

        to_encode = {
            "sub": user.username,
            "exp": expire
        }
        token = jwt.encode(to_encode, self.secret_key,
                           algorithm=self.algorithm)

        # Update user table with login token
        db.execute(
            update(DBUser)
            .where(DBUser.id == user.id)
            .values(
                token=token,
                token_expires_at=expire,
                updated_at=datetime.utcnow()
            )
        )
        db.commit()

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_at": expire
        }

    def create_access_token(self, db: AsyncSession, user: UserInDB, service_name: str, expires_delta: Optional[timedelta] = None) -> dict:
        # Create token with expiration
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)

        to_encode = {
            "sub": user.username,
            "exp": expire
        }
        token = jwt.encode(to_encode, self.secret_key,
                           algorithm=self.algorithm)

        # Create or update service credential
        result = db.execute(
            select(ServiceCredentials)
            .where(
                ServiceCredentials.user_id == user.id,
                ServiceCredentials.service_name == service_name
            )
        )
        existing_cred = result.scalars().first()

        if existing_cred:
            db.execute(
                update(ServiceCredentials)
                .where(ServiceCredentials.id == existing_cred.id)
                .values(
                    token=token,
                    token_expires_at=expire,
                    is_active=True
                )
            )
        else:
            service_cred = ServiceCredentials(
                user_id=user.id,
                service_name=service_name,
                token=token,
                token_expires_at=expire,
                is_active=True
            )
            db.add(service_cred)

        db.commit()

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_at": expire,
            "service_name": service_name
        }

    def verify_token(self, db: AsyncSession, token: str) -> dict:
        try:
            # First decode the token to check its basic validity
            payload = jwt.decode(token, self.secret_key,
                                 algorithms=[self.algorithm])
            if not payload:
                raise HTTPException(status_code=401, detail="Invalid token")

            # Check if token exists in service_credentials and is not expired
            result = db.execute(
                select(ServiceCredentials)
                .where(
                    ServiceCredentials.token == token,
                    ServiceCredentials.token_expires_at > datetime.utcnow(),
                    ServiceCredentials.is_active == True
                )
            )
            service_cred = result.scalars().first()

            if not service_cred:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token not found or expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"})

    def get_user_service_credentials(self, db: AsyncSession, user_id: int) -> list:
        result = db.execute(
            select(ServiceCredentials)
            .where(
                ServiceCredentials.user_id == user_id,
                ServiceCredentials.is_active == True
            )
        )
        credentials = result.scalars().all()
        return [
            {
                "service_name": cred.service_name,
                "api_token": cred.token,
                "expires_at": cred.token_expires_at,
                "is_active": cred.is_active
            }
            for cred in credentials
        ]

    def delete_service_credential(self, db: AsyncSession, credential_id: int) -> bool:
        """Delete a service credential by its ID."""
        result = db.execute(
            delete(ServiceCredentials)
            .where(ServiceCredentials.id == credential_id)
            .returning(ServiceCredentials.id)
        )
        deleted = result.scalar_one_or_none()
        db.commit()
        return bool(deleted)

    def verify_user_token(self, db: AsyncSession, token: str) -> UserInDB:
        """Verify user token and check expiration."""
        try:
            # First decode the token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username = payload.get("sub")
            if not username:
                raise HTTPException(status_code=401, detail="Invalid token")

            # Check if token exists in user table and is not expired
            result = db.execute(
                select(DBUser)
                .where(
                    DBUser.username == username,
                    DBUser.token == token,
                    DBUser.token_expires_at > datetime.utcnow()
                )
            )
            user = result.scalars().first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired. Please login again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return UserInDB.from_orm(user)

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired. Please login again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"})
