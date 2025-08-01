"""Database models for swap application."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """User model for storing user configuration."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    user_name = Column(String(100), unique=True, nullable=False, index=True)
    calendar_name = Column(String(200), nullable=False)
    calendar_id = Column(String(200), nullable=True)
    emails_to_share = Column(Text, nullable=False)  # JSON serialized list
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    shifts = relationship("Shift", back_populates="user", cascade="all, delete-orphan")
    sync_history = relationship("SyncHistory", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(user_name='{self.user_name}', calendar_name='{self.calendar_name}')>"


class Shift(Base):
    """Shift model for storing parsed shift data."""
    
    __tablename__ = "shifts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Shift data
    name = Column(String(100), nullable=False)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD format
    raw_data = Column(String(200), nullable=False)
    shift_type = Column(String(50), nullable=False)
    is_working = Column(Boolean, nullable=False)
    
    # Time information (for working shifts)
    start_date = Column(String(19), nullable=True)  # YYYY-MM-DD HH:MM:SS format
    end_date = Column(String(19), nullable=True)    # YYYY-MM-DD HH:MM:SS format
    
    # Calendar integration
    calendar_event_id = Column(String(200), nullable=True)
    
    # Data integrity
    data_hash = Column(String(64), nullable=False, index=True)  # SHA256 hash of shift data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="shifts")
    
    def __repr__(self) -> str:
        return f"<Shift(name='{self.name}', date='{self.date}', type='{self.shift_type}')>"


class SyncHistory(Base):
    """Track synchronization history and changes."""
    
    __tablename__ = "sync_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Sync details
    sync_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    total_shifts_processed = Column(Integer, nullable=False)
    shifts_created = Column(Integer, default=0)
    shifts_updated = Column(Integer, default=0)
    shifts_deleted = Column(Integer, default=0)
    events_created = Column(Integer, default=0)
    events_updated = Column(Integer, default=0)
    events_deleted = Column(Integer, default=0)
    
    # Status and errors
    status = Column(String(20), nullable=False)  # 'success', 'error', 'partial'
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sync_history")
    
    def __repr__(self) -> str:
        return f"<SyncHistory(timestamp='{self.sync_timestamp}', status='{self.status}')>"
