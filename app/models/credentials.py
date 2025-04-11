"""
Credential models for the API.
"""
from datetime import datetime
from typing import Dict, Optional, Any, List

from pydantic import BaseModel, Field, validator


class ServiceCredentialBase(BaseModel):
    """Base model for service credentials."""
    service_name: str = Field(..., description="Name of the service")
    token: str = Field(..., description="JWT token for authentication")
    token_expires_at: datetime = Field(..., description="Token expiration datetime")
    is_active: bool = Field(True, description="Whether this credential is active")


class ServiceCredentialCreate(ServiceCredentialBase):
    """Model for creating service credentials."""
    user_id: int = Field(..., description="ID of the user who owns this credential")


class ServiceCredentialUpdate(BaseModel):
    """Model for updating service credentials."""
    service_name: Optional[str] = Field(None, description="Name of the service")
    token: Optional[str] = Field(None, description="JWT token for authentication")
    token_expires_at: Optional[datetime] = Field(None, description="Token expiration datetime")
    is_active: Optional[bool] = Field(None, description="Whether this credential is active")


class ServiceCredentialResponse(ServiceCredentialBase):
    """Response model for service credentials."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


class ServiceCredentialList(BaseModel):
    """Model for listing service credentials."""
    credentials: List[ServiceCredentialResponse]
    total: int