from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class Calendar(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    google_calendar_id: str = Field(index=True)
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    events: list["Event"] = Relationship(back_populates="calendar")


class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    google_event_id: str = Field(index=True)
    rota_id: Optional[int] = Field(default=None, foreign_key="rota.id")
    calendar_id: int = Field(foreign_key="calendar.id")
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    calendar: Calendar = Relationship(back_populates="events")
