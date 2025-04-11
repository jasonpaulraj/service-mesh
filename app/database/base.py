"""
Base module for database models.
"""
from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models."""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class TimestampMixin:
    """Mixin to add created_at and updated_at columns to models."""

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )