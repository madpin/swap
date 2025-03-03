from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class Calendar(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    google_calendar_id: str = Field(index=True)
    name: str
    key: str = Field(index=True, unique=True)
    main_email: Optional[str] = Field(default=None, index=True)
    extra_emails: Optional[str] = None
    description: Optional[str] = None
    timezone: str = Field(default="UTC")
    is_active: bool = Field(default=True, index=True)
    last_synced: Optional[datetime] = Field(default=None)
    sync_token: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    events: list["Event"] = Relationship(back_populates="calendar")


class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    google_event_id: str = Field(index=True)
    google_synced: bool = Field(default=False)
    rota_id: Optional[int] = Field(default=None, foreign_key="rota.id")
    calendar_id: int = Field(foreign_key="calendar.id")
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    status: str = Field(default="confirmed")  # confirmed, tentative, cancelled
    sequence: int = Field(default=0)  # For tracking updates
    recurring_event_id: Optional[str] = Field(default=None)
    recurrence: Optional[str] = Field(default=None)
    attendees: Optional[str] = Field(default=None)  # JSON string of attendees
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_synced: Optional[datetime] = Field(default=None)
    calendar: Calendar = Relationship(back_populates="events")


class UserCalendar(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_name: str = Field(index=True)  # Name from the rota spreadsheet
    calendar_id: int = Field(foreign_key="calendar.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    calendar: Calendar = Relationship(back_populates="users")

# Add the back-reference to Calendar
Calendar.users: List["UserCalendar"] = Relationship(back_populates="calendar")
