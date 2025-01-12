from pydantic import BaseModel


class NotificationRequest(BaseModel):
    cron_expression: str
    message: str
