from datetime import datetime
import json
import asyncio
from swap.utils.logger import logger
from swap.models.notification import Notification
from swap.core.database import get_db
from swap.models.calendar import Calendar, UserCalendar, Event
from swap.services.google_calendar import GoogleCalendarService
from swap.services.rota_parser import RotaParser


async def send_notification(message: str = "", recipients: list[str] = None, cron_expression: str = None):
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


from swap.services.google_calendar import GoogleCalendarService
from swap.core.rota_operations import get_rota
from swap.models.calendar import UserCalendar, Event
from datetime import datetime, timedelta


async def sync_calendars():
    """
    Synchronize all active calendars with Google Calendar.
    """
    try:
        logger.info("Starting calendar sync")
        with get_db() as session:
            # Get all active calendars with their user mappings
            active_calendars = (
                session.query(Calendar)
                .filter(Calendar.is_active == True)
                .all()
            )
            
            if not active_calendars:
                logger.info("No active calendars found to sync")
                return

            # Get current rota data
            rota_data = await get_rota()
            
            # Process each calendar
            for calendar in active_calendars:
                try:
                    logger.info(f"Syncing calendar: {calendar.name} ({calendar.id})")
                    
                    # Get user mappings for this calendar
                    user_mappings = (
                        session.query(UserCalendar)
                        .filter(
                            UserCalendar.calendar_id == calendar.id,
                            UserCalendar.is_active == True
                        )
                        .all()
                    )

                    if not user_mappings:
                        logger.info(f"No user mappings found for calendar {calendar.id}")
                        continue

                    # Initialize Google Calendar service
                    calendar_service = GoogleCalendarService(
                        service_account_file="gcal_service_account.json",
                        calendar_id=calendar.google_calendar_id
                    )

                    # Process rota entries for mapped users
                    for mapping in user_mappings:
                        user_entries = [
                            entry for entry in rota_data 
                            if entry["name"] == mapping.user_name
                        ]

                        for entry in user_entries:
                            if not entry.get("is_working", False):
                                continue  # Skip non-working shifts

                            # Check if event already exists
                            existing_event = (
                                session.query(Event)
                                .filter(
                                    Event.calendar_id == calendar.id,
                                    Event.start_time == datetime.fromisoformat(entry["start_date"]),
                                    Event.end_time == datetime.fromisoformat(entry["end_date"])
                                )
                                .first()
                            )

                            if existing_event:
                                # Update existing event if needed
                                event_title = f"{entry['name']}: {entry['raw_data']}"
                                if existing_event.title != event_title:
                                    existing_event.title = event_title
                                    existing_event.updated_at = datetime.utcnow()
                                    await calendar_service.update_event(
                                        existing_event.google_event_id,
                                        summary=event_title,
                                        start_time=existing_event.start_time,
                                        end_time=existing_event.end_time
                                    )
                            else:
                                # Create new event
                                event_title = f"{entry['name']}: {entry['raw_data']}"
                                google_event = await calendar_service.create_event(
                                    summary=event_title,
                                    start_time=datetime.fromisoformat(entry["start_date"]),
                                    end_time=datetime.fromisoformat(entry["end_date"]),
                                    timezone="UTC"
                                )

                                new_event = Event(
                                    calendar_id=calendar.id,
                                    google_event_id=google_event["id"],
                                    title=event_title,
                                    start_time=datetime.fromisoformat(entry["start_date"]),
                                    end_time=datetime.fromisoformat(entry["end_date"]),
                                    google_synced=True
                                )
                                session.add(new_event)

                    # Update last synced timestamp
                    calendar.last_synced = datetime.utcnow()
                    session.commit()
                    
                except Exception as cal_error:
                    logger.error(f"Failed to sync calendar {calendar.id}: {cal_error}")
                    continue
            
            logger.info("Calendar sync completed")
            
    except Exception as e:
        logger.error(f"Calendar sync failed: {e}")
        raise
