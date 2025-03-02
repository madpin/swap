from datetime import datetime
import json
import asyncio
from swap.utils.logger import logger
from swap.models.notification import Notification
from swap.core.database import get_db
from swap.models.calendar import Calendar
from swap.services.google_calendar import GoogleCalendarService


async def send_notification(message: str = "", recipients: list[str] = None):
    """
    Send a notification to specified recipients.
    
    Args:
        message: The message to send
        recipients: List of recipient identifiers (e.g., Telegram chat IDs)
    """
    try:
        with get_db() as session:
            notification = Notification(
                message=message,
                recipients=json.dumps(recipients or []),
                scheduled_for=datetime.utcnow(),
            )
            session.add(notification)
            session.commit()  # Commit immediately to get the ID
            
            try:
                # TODO: Implement actual sending logic here using Telegram API
                # For now, just log it
                logger.info(f"Notification {notification.id} sent: {message} to {recipients}")
                
                notification.status = "sent"
                notification.sent_at = datetime.utcnow()
                
            except Exception as send_error:
                logger.error(f"Failed to send notification {notification.id}: {send_error}")
                notification.status = "failed"
                notification.error = str(send_error)
                raise
            
            finally:
                session.commit()
            
    except Exception as e:
        logger.error(f"Notification processing error: {e}")
        raise


async def sync_calendars():
    """
    Synchronize all active calendars with Google Calendar.
    """
    try:
        logger.info("Starting calendar sync")
        with get_db() as session:
            # Get all active calendars
            active_calendars = session.query(Calendar).filter(Calendar.is_active == True).all()
            
            if not active_calendars:
                logger.info("No active calendars found to sync")
                return
            
            # Process each calendar
            for calendar in active_calendars:
                try:
                    logger.info(f"Syncing calendar: {calendar.name} ({calendar.id})")
                    
                    # TODO: Initialize GoogleCalendarService with proper credentials
                    # calendar_service = GoogleCalendarService(
                    #     service_account_file="path/to/credentials.json",
                    #     calendar_id=calendar.google_calendar_id
                    # )
                    
                    # TODO: Implement sync logic using calendar_service
                    # For now, just update the last_synced timestamp
                    calendar.last_synced = datetime.utcnow()
                    session.commit()
                    
                except Exception as cal_error:
                    logger.error(f"Failed to sync calendar {calendar.id}: {cal_error}")
                    continue
            
            logger.info("Calendar sync completed")
            
    except Exception as e:
        logger.error(f"Calendar sync failed: {e}")
        raise
