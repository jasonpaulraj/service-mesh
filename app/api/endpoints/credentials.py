from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.credentials_service import CredentialsService
from app.models.user import User, UserCreate, UserUpdate, UserInDB
from app.models.credentials import (
    ServiceCredentialCreate,
    ServiceCredentialUpdate,
    ServiceCredentialResponse,
    ServiceCredentialList
)
from app.database.session import get_db
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

router = APIRouter()
settings = get_settings()
security = HTTPBearer()

credentials_service = CredentialsService(
    secret_key=settings.SECRET_KEY,
    token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
)

# Public endpoints


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    print(f"Received registration request for user: {user_data.username}")
    try:
        return credentials_service.create_user(db, user_data)
    except HTTPException as e:
        print(f"HTTP Exception during registration: {e}")
        raise e
    except Exception as e:
        print(f"Exception during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


class LoginCredentials(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(
    credentials: LoginCredentials,
    db: AsyncSession = Depends(get_db)
):
    user = credentials_service.authenticate_user(
        db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate login token
    token_data = credentials_service.login_token(db, user)

    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active
        },
        **token_data,
        "service_credentials": credentials_service.get_user_service_credentials(db, user.id)
    }

# Protected endpoints (require authentication via login)


class LoginData(BaseModel):
    username: str
    password: str
    service_name: str


@router.post("/token")
def login_for_access_token(
    login_data: LoginData,
    db: AsyncSession = Depends(get_db)
):
    user = credentials_service.authenticate_user(
        db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials_service.create_access_token(
        db=db,
        user=user,
        service_name=login_data.service_name
    )
    access_token = credentials_service.create_access_token(
        data={"sub": login_data.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> UserInDB:
    return credentials_service.verify_user_token(db, token.credentials)


@router.delete("/service-credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_credential(
    credential_id: int,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a service credential by ID."""
    # First check if the credential belongs to the user
    result = db.execute(
        select(ServiceCredentials)
        .where(
            ServiceCredentials.id == credential_id,
            ServiceCredentials.user_id == current_user.id
        )
    )
    credential = result.scalar_one_or_none()

    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service credential not found"
        )

    deleted = credentials_service.delete_service_credential(db, credential_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete service credential"
        )
