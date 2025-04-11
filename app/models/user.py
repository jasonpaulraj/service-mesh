from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDB(UserBase):
    id: int
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# New models for service credentials
class ServiceCredentialBase(BaseModel):
    service_name: str
    token: str
    token_expires_at: datetime
    is_active: bool = True

class ServiceCredentialCreate(ServiceCredentialBase):
    user_id: int

class ServiceCredentialUpdate(BaseModel):
    service_name: Optional[str] = None
    token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None

class ServiceCredential(ServiceCredentialBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True