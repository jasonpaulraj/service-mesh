"""
Database session management.
"""
import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

logger = logging.getLogger(__name__)

# Get database URL from settings
settings = get_settings()

# Modify the engine creation to use the correct connector
engine = create_engine(
    settings.DATABASE_URL.replace('mysql+mysqlconnector', 'mysql+pymysql'),
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args=settings.DATABASE_CONNECT_ARGS,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """
    Get database session.
    
    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()