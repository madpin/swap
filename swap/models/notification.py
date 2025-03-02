from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import BaseModel


class NotificationRequest(BaseModel):
    cron_expression: str
    message: str
    channel: str = "telegram"  # Default to telegram
    recipients: list[str]


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    message: str
    channel: str = Field(default="telegram")
    recipients: str  # JSON string of recipient list
    status: str = Field(default="pending")  # pending, sent, failed
    scheduled_for: datetime
    sent_at: Optional[datetime] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
