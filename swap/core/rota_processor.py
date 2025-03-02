from swap.services.rota_parser import RotaParser
from swap.config import settings
from swap.core.database import Session, engine
from sqlmodel import select
from swap.models.rota import Rota
from swap.models.calendar import Calendar, Event
from datetime import datetime
from swap.utils.logger import logger
from swap.services.google_calendar import GoogleCalendarService
from swap.services.calendar_manager import CalendarManager
from typing import Optional


async def ingest_rota_record(
    rota_entry: dict,
    service_account_file: str,
    google_calendar_id: Optional[str] = None,
):
    """
    Ingests a rota record, creates or updates a calendar, and manages its events.
    """
    with Session(engine) as session:
        calendar = check_and_create_calendar(session, rota_entry, google_calendar_id)
        google_calendar_service = await prepare_google_calendar(
            session, calendar, service_account_file
        )
        await process_calendar_event(
            session, rota_entry, calendar, google_calendar_service
        )


async def check_and_create_calendar(
    session: Session, rota_entry: dict, calendar_manager: Optional['CalendarManager'] = None
) -> Calendar:
    """
    Checks if a calendar exists for the rota entry's name, creates one if it doesn't.
    Uses CalendarManager to handle Google Calendar creation and permissions.
    """
    calendar = session.exec(
        select(Calendar).where(Calendar.key == rota_entry["name"])
    ).first()
    
    if not calendar and calendar_manager:
        # Extract owner email from rota entry or use default
        owner_email = rota_entry.get("email", rota_entry.get("name", "default") + "@example.com")
        
        # Create calendar using manager
        calendar = await calendar_manager.get_or_create_calendar(
            name=rota_entry["name"],
            owner_email=owner_email
        )
        
    elif not calendar:
        # Fallback if no calendar manager provided
        calendar = Calendar(
            name=rota_entry["name"],
            key=rota_entry["name"],
            main_email=rota_entry.get("email"),
        )
        session.add(calendar)
        session.commit()
        session.refresh(calendar)
        
    return calendar


async def prepare_google_calendar(
    session: Session, calendar: Calendar, calendar_manager: 'CalendarManager'
) -> GoogleCalendarService:
    """
    Prepares the Google Calendar service for a given calendar.
    Uses CalendarManager to handle calendar creation and permissions.
    """
    if not calendar.google_calendar_id:
        # Create calendar in Google Calendar
        gcal = await calendar_manager.google_calendar.create_calendar(calendar.name)
        calendar.google_calendar_id = gcal["id"]
        
        # Set up permissions
        if calendar.main_email:
            await calendar_manager.google_calendar.share_calendar(
                email=calendar.main_email,
                calendar_id=gcal["id"],
                role="owner"
            )
            
        # Handle additional users if any
        if calendar.extra_emails:
            extra_emails = calendar.extra_emails.split(',')
            for email in extra_emails:
                await calendar_manager.google_calendar.share_calendar(
                    email=email.strip(),
                    calendar_id=gcal["id"],
                    role="writer"
                )
        
        session.add(calendar)
        session.commit()
        session.refresh(calendar)
    
    return GoogleCalendarService(
        service_account_file=calendar_manager.service_account_file,
        calendar_id=calendar.google_calendar_id,
    )


async def process_calendar_event(
    session: Session,
    rota_entry: dict,
    calendar: Calendar,
    google_calendar_service: GoogleCalendarService,
):
    """
    Processes the calendar event based on the rota entry.
    """
    event = session.exec(select(Event).where(Event.rota_id == rota_entry["id"])).first()
    if not event:
        event = create_event_from_rota(rota_entry, calendar.id)
        session.add(event)
    else:
        update_event_if_needed(event, rota_entry)

    session.commit()
    session.refresh(event)
    await sync_event_with_google(session, event, google_calendar_service)


def create_event_from_rota(rota_entry: dict, calendar_id: int) -> Event:
    """
    Creates a new event based on the rota entry.
    """
    start_time = rota_entry["start_time"]
    end_time = rota_entry["end_time"]
    return Event(
        rota_id=rota_entry["id"],
        calendar_id=calendar_id,
        title=rota_entry["shift_type"],
        description=f"Shift for {rota_entry['name']}",
        start_time=start_time,
        end_time=end_time,
        google_synced=False,
    )


def update_event_if_needed(event: Event, rota_entry: dict):
    """
    Updates the event if necessary.
    """
    fields_to_check = ["start_time", "end_time", "shift_type"]
    event_changed = False

    for field in fields_to_check:
        if rota_entry[field] != getattr(event, field):
            setattr(event, field, rota_entry[field])
            event_changed = True
    if event_changed:
        event.title = rota_entry["shift_type"]
        event.google_synced = False


async def sync_event_with_google(
    session: Session, event: Event, google_calendar_service: GoogleCalendarService
):
    """
    Synchronizes the event with Google Calendar.
    """
    if not event.google_synced:
        try:
            if event.google_event_id:
                await google_calendar_service.update_event(
                    event_id=event.google_event_id,
                    summary=event.title,
                    start_time=event.start_time,
                    end_time=event.end_time,
                    description=event.description,
                    timezone="UTC",
                )
            else:
                gcal_event = await google_calendar_service.create_event(
                    summary=event.title,
                    start_time=event.start_time,
                    end_time=event.end_time,
                    description=event.description,
                    timezone="UTC",
                )
                event.google_event_id = gcal_event["id"]

            event.google_synced = True
            session.add(event)
            session.commit()
        except Exception as e:
            logger.error(f"Error syncing event with Google Calendar: {e}")
