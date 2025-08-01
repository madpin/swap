"""Data repositories for database operations."""

import json
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import User, Shift, SyncHistory


class BaseRepository:
    """Base repository with common database operations."""
    
    def __init__(self, db: Session):
        self.db = db


class UserRepository(BaseRepository):
    """Repository for user operations."""
    
    def get_by_user_name(self, user_name: str) -> Optional[User]:
        """Get user by user_name."""
        return self.db.query(User).filter(User.user_name == user_name).first()
    
    def get_all(self) -> List[User]:
        """Get all users."""
        return self.db.query(User).all()
    
    def create(self, user_name: str, calendar_name: str, emails_to_share: List[str], calendar_id: str = None) -> User:
        """Create a new user."""
        user = User(
            user_name=user_name,
            calendar_name=calendar_name,
            calendar_id=calendar_id,
            emails_to_share=json.dumps(emails_to_share)
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_calendar_id(self, user_id: int, calendar_id: str) -> None:
        """Update user's calendar ID."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.calendar_id = calendar_id
            user.updated_at = datetime.utcnow()
            self.db.commit()
    
    def get_emails_to_share(self, user_id: int) -> List[str]:
        """Get emails to share for a user."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.emails_to_share:
            return json.loads(user.emails_to_share)
        return []


class ShiftRepository(BaseRepository):
    """Repository for shift operations."""
    
    def _calculate_shift_hash(self, shift_data: Dict[str, Any]) -> str:
        """Calculate SHA256 hash of shift data for change detection."""
        # Create a canonical representation of the shift data
        canonical_data = {
            "name": shift_data["name"],
            "date": shift_data["date"],
            "raw_data": shift_data["raw_data"],
            "shift_type": shift_data["shift_type"],
            "is_working": shift_data["is_working"],
            "start_date": shift_data.get("start_date"),
            "end_date": shift_data.get("end_date"),
        }
        
        # Convert to sorted JSON string and hash
        canonical_str = json.dumps(canonical_data, sort_keys=True)
        return hashlib.sha256(canonical_str.encode()).hexdigest()
    
    def get_by_user_and_date(self, user_id: int, date: str) -> Optional[Shift]:
        """Get shift by user and date."""
        return self.db.query(Shift).filter(
            and_(Shift.user_id == user_id, Shift.date == date)
        ).first()
    
    def get_by_user(self, user_id: int, limit: int = None) -> List[Shift]:
        """Get shifts for a user."""
        query = self.db.query(Shift).filter(Shift.user_id == user_id).order_by(Shift.date.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def get_recent_shifts(self, user_id: int, days: int = 30) -> List[Shift]:
        """Get recent shifts for a user."""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return self.db.query(Shift).filter(
            and_(Shift.user_id == user_id, Shift.date >= cutoff_date)
        ).order_by(Shift.date.desc()).all()
    
    def create_or_update(self, user_id: int, shift_data: Dict[str, Any]) -> tuple[Shift, bool]:
        """Create or update a shift. Returns (shift, is_new)."""
        data_hash = self._calculate_shift_hash(shift_data)
        
        existing_shift = self.get_by_user_and_date(user_id, shift_data["date"])
        
        if existing_shift:
            # Check if data has changed
            if existing_shift.data_hash == data_hash:
                return existing_shift, False  # No changes
            
            # Update existing shift
            existing_shift.name = shift_data["name"]
            existing_shift.raw_data = shift_data["raw_data"]
            existing_shift.shift_type = shift_data["shift_type"]
            existing_shift.is_working = shift_data["is_working"]
            existing_shift.start_date = shift_data.get("start_date")
            existing_shift.end_date = shift_data.get("end_date")
            existing_shift.data_hash = data_hash
            existing_shift.updated_at = datetime.utcnow()
            
            self.db.commit()
            return existing_shift, False
        
        else:
            # Create new shift
            shift = Shift(
                user_id=user_id,
                name=shift_data["name"],
                date=shift_data["date"],
                raw_data=shift_data["raw_data"],
                shift_type=shift_data["shift_type"],
                is_working=shift_data["is_working"],
                start_date=shift_data.get("start_date"),
                end_date=shift_data.get("end_date"),
                data_hash=data_hash
            )
            
            self.db.add(shift)
            self.db.commit()
            self.db.refresh(shift)
            return shift, True
    
    def update_calendar_event_id(self, shift_id: int, event_id: str) -> None:
        """Update shift's calendar event ID."""
        shift = self.db.query(Shift).filter(Shift.id == shift_id).first()
        if shift:
            shift.calendar_event_id = event_id
            shift.updated_at = datetime.utcnow()
            self.db.commit()
    
    def get_shifts_without_events(self, user_id: int) -> List[Shift]:
        """Get shifts that don't have calendar events."""
        return self.db.query(Shift).filter(
            and_(Shift.user_id == user_id, Shift.calendar_event_id.is_(None))
        ).all()
    
    def delete_old_shifts(self, user_id: int, before_date: str) -> int:
        """Delete shifts older than specified date."""
        deleted_count = self.db.query(Shift).filter(
            and_(Shift.user_id == user_id, Shift.date < before_date)
        ).delete()
        self.db.commit()
        return deleted_count


class SyncHistoryRepository(BaseRepository):
    """Repository for sync history operations."""
    
    def create(self, user_id: int = None, **kwargs) -> SyncHistory:
        """Create a sync history entry."""
        sync_entry = SyncHistory(
            user_id=user_id,
            total_shifts_processed=kwargs.get("total_shifts_processed", 0),
            shifts_created=kwargs.get("shifts_created", 0),
            shifts_updated=kwargs.get("shifts_updated", 0),
            shifts_deleted=kwargs.get("shifts_deleted", 0),
            events_created=kwargs.get("events_created", 0),
            events_updated=kwargs.get("events_updated", 0),
            events_deleted=kwargs.get("events_deleted", 0),
            status=kwargs.get("status", "success"),
            error_message=kwargs.get("error_message"),
        )
        
        self.db.add(sync_entry)
        self.db.commit()
        self.db.refresh(sync_entry)
        return sync_entry
    
    def get_latest(self, user_id: int = None) -> Optional[SyncHistory]:
        """Get latest sync history entry."""
        query = self.db.query(SyncHistory)
        if user_id:
            query = query.filter(SyncHistory.user_id == user_id)
        return query.order_by(SyncHistory.sync_timestamp.desc()).first()
    
    def get_recent(self, user_id: int = None, limit: int = 10) -> List[SyncHistory]:
        """Get recent sync history entries."""
        query = self.db.query(SyncHistory)
        if user_id:
            query = query.filter(SyncHistory.user_id == user_id)
        return query.order_by(SyncHistory.sync_timestamp.desc()).limit(limit).all()
