"""Test configuration and fixtures."""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from swap.data.models import Base
from swap.config.settings import Settings


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield SessionLocal()
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        debug=True,
        database={"url": "sqlite:///:memory:", "echo": False},
        google={
            "service_account_file": "/test/path.json",
            "spreadsheet_id": "test-sheet-id",
            "range_name": "Sheet1!A:M",
            "timezone": "UTC",
        },
        users=[
            {
                "calendar_name": "Test Calendar",
                "user_name": "TestUser",
                "emails_to_share": ["test@example.com"],
            }
        ],
    )
