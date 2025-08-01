"""Google Calendar service for managing calendars and events."""

from typing import List, Dict, Any, Optional
from datetime import datetime

import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config.logging import get_logger

logger = get_logger(__name__)


class CalendarService:
    """Service for interacting with Google Calendar API."""
    
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    
    def __init__(self, service_account_file: str, timezone: str = "UTC"):
        """Initialize the service with credentials."""
        self.service_account_file = service_account_file
        self.timezone = timezone
        self._service = None
        self.calendar_id = "primary"
    
    @property
    def service(self):
        """Lazy-load the Google Calendar service."""
        if self._service is None:
            self._service = self._build_service()
        return self._service
    
    def _build_service(self):
        """Build and return a Calendar service object."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=self.SCOPES
            )
            return build("calendar", "v3", credentials=credentials)
        except Exception as e:
            logger.error(f"Failed to build Calendar service: {e}")
            raise
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """List all available calendars."""
        try:
            calendar_list = self.service.calendarList().list().execute()
            return calendar_list.get("items", [])
        except HttpError as error:
            logger.error(f"Failed to list calendars: {error}")
            return []
    
    def find_calendar_by_name(self, calendar_name: str) -> Optional[Dict[str, Any]]:
        """Find calendar by name."""
        calendars = self.list_calendars()
        for calendar in calendars:
            if calendar.get("summary") == calendar_name:
                return calendar
        return None
    
    def create_calendar(
        self, summary: str, description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new Google Calendar."""
        calendar_body = {
            "summary": summary,
            "timeZone": self.timezone
        }
        if description:
            calendar_body["description"] = description
        
        try:
            calendar = self.service.calendars().insert(body=calendar_body).execute()
            logger.info(f"Created calendar: {summary} (ID: {calendar['id']})")
            return calendar
        except HttpError as error:
            logger.error(f"Failed to create calendar: {error}")
            raise
    
    def get_or_create_calendar(self, calendar_name: str) -> str:
        """Get existing calendar ID or create new calendar. Returns calendar ID."""
        existing_calendar = self.find_calendar_by_name(calendar_name)
        
        if existing_calendar:
            calendar_id = existing_calendar["id"]
            logger.info(f"Using existing calendar: {calendar_name} (ID: {calendar_id})")
            return calendar_id
        else:
            created_calendar = self.create_calendar(calendar_name)
            calendar_id = created_calendar["id"]
            logger.info(f"Created new calendar: {calendar_name} (ID: {calendar_id})")
            return calendar_id
    
    def share_calendar(
        self, calendar_id: str, email: str, role: str = "reader"
    ) -> bool:
        """Share calendar with a user."""
        rule = {
            "scope": {"type": "user", "value": email},
            "role": role,
        }
        
        try:
            self.service.acl().insert(calendarId=calendar_id, body=rule).execute()
            logger.info(f"Shared calendar {calendar_id} with {email} (role: {role})")
            return True
        except HttpError as error:
            logger.error(f"Failed to share calendar with {email}: {error}")
            return False
    
    def get_shared_users(self, calendar_id: str) -> List[Dict[str, Any]]:
        """Get list of users who have access to the calendar."""
        try:
            acl = self.service.acl().list(calendarId=calendar_id).execute()
            return acl.get("items", [])
        except HttpError as error:
            logger.error(f"Failed to list shared users: {error}")
            return []
    
    def ensure_calendar_shared(self, calendar_id: str, emails: List[str]) -> None:
        """Ensure calendar is shared with all specified emails."""
        shared_users = self.get_shared_users(calendar_id)
        shared_emails = {
            user.get("scope", {}).get("value")
            for user in shared_users
            if user.get("scope", {}).get("type") == "user"
        }
        
        for email in emails:
            if email not in shared_emails:
                self.share_calendar(calendar_id, email, role="writer")
            else:
                logger.debug(f"Calendar already shared with {email}")
    
    def create_event(
        self,
        calendar_id: str,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Optional[str]:
        """Create a new calendar event. Returns event ID."""
        event_body = {
            "summary": summary,
            "start": {
                "dateTime": self._format_datetime(start_time),
                "timeZone": self.timezone,
            },
            "end": {
                "dateTime": self._format_datetime(end_time),
                "timeZone": self.timezone,
            },
        }
        
        if description is not None:
            event_body["description"] = description
        if location:
            event_body["location"] = location
        
        try:
            created_event = (
                self.service.events()
                .insert(calendarId=calendar_id, body=event_body)
                .execute()
            )
            event_id = created_event["id"]
            logger.info(f"Event created: {summary} (ID: {event_id})")
            return event_id
        except HttpError as error:
            logger.error(f"Failed to create event: {error}")
            return None
    
    def get_events_for_date(self, calendar_id: str, date: datetime) -> List[Dict[str, Any]]:
        """Get events for a specific date."""
        try:
            # Convert date to timezone-aware datetime range
            tz = pytz.timezone(self.timezone)
            start_datetime = tz.localize(datetime.combine(date.date(), datetime.min.time()))
            end_datetime = tz.localize(datetime.combine(date.date(), datetime.max.time()))
            
            events_result = (
                self.service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=start_datetime.isoformat(),
                    timeMax=end_datetime.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return events_result.get("items", [])
        except HttpError as error:
            logger.error(f"Failed to get events for date {date}: {error}")
            return []
    
    def delete_event(self, calendar_id: str, event_id: str) -> bool:
        """Delete a calendar event."""
        try:
            self.service.events().delete(
                calendarId=calendar_id, eventId=event_id
            ).execute()
            logger.info(f"Event deleted: {event_id}")
            return True
        except HttpError as error:
            logger.error(f"Failed to delete event {event_id}: {error}")
            return False
    
    def update_event(
        self,
        calendar_id: str,
        event_id: str,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> bool:
        """Update an existing calendar event."""
        event_body = {
            "summary": summary,
            "start": {
                "dateTime": self._format_datetime(start_time),
                "timeZone": self.timezone,
            },
            "end": {
                "dateTime": self._format_datetime(end_time),
                "timeZone": self.timezone,
            },
        }
        
        if description is not None:
            event_body["description"] = description
        if location:
            event_body["location"] = location
        
        try:
            self.service.events().update(
                calendarId=calendar_id, eventId=event_id, body=event_body
            ).execute()
            logger.info(f"Event updated: {event_id}")
            return True
        except HttpError as error:
            logger.error(f"Failed to update event {event_id}: {error}")
            return False
    
    def _format_datetime(self, dt: datetime) -> str:
        """Format a datetime for the Google Calendar API."""
        if dt.tzinfo is None:
            tz = pytz.timezone(self.timezone)
            dt = tz.localize(dt)
        else:
            tz = pytz.timezone(self.timezone)
            dt = dt.astimezone(tz)
        return dt.isoformat()
