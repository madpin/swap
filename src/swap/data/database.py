"""Database connection and session management."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from ..config import get_settings
from .models import Base

# Global engine and session factory
_engine = None
_SessionLocal = None


def get_engine():
    """Get SQLAlchemy engine (singleton)."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database.url,
            echo=settings.database.echo,
            # SQLite specific settings
            connect_args={"check_same_thread": False} if "sqlite" in settings.database.url else {}
        )
    return _engine


def get_session_factory():
    """Get SQLAlchemy session factory (singleton)."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine()
        )
    return _SessionLocal


def get_database() -> Generator[Session, None, None]:
    """Get database session (dependency injection)."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database() -> None:
    """Initialize database, creating all tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
