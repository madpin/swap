# swap/models/rota.py
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class Rota(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    date: datetime
    start_time: datetime
    end_time: datetime
    shift_type: str
    is_working: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = Field(default=False)

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.updated_at = datetime.utcnow()

    class Config:
        from_attributes = True
