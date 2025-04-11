"""
Database models for the application.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """Model for storing user information."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    token = Column(String(255), nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    
    # Relationship with ServiceCredentials
    credentials = relationship("ServiceCredentials", back_populates="user")


class ServiceCredentials(Base, TimestampMixin):
    """Model for storing service JWT bearer tokens associated with users."""
    __tablename__ = "service_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_name = Column(String(100), nullable=False)
    token = Column(String(1024), nullable=False)
    token_expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationship with User
    user = relationship("User", back_populates="credentials")