from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional

import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import asyncio
import functools
from google.auth.transport.requests import Request as GoogleRequest


class GoogleCalendarError(Exception):
    """Base class for Google Calendar related exceptions."""

    pass


class AuthenticationError(GoogleCalendarError):
    """Raised when authentication with Google Calendar API fails."""

    pass


class CalendarNotFoundError(GoogleCalendarError):
    """Raised when the specified calendar is not found."""

    pass


class EventCreationError(GoogleCalendarError):
    """Raised when an event cannot be created."""

    pass


class EventUpdateError(GoogleCalendarError):
    """Raised when an event cannot be updated."""

    pass


class EventDeletionError(GoogleCalendarError):
    """Raised when an event cannot be deleted."""

    pass


class EventNotFoundError(GoogleCalendarError):
    """Raised when a specific event is not found."""

    pass


class CalendarSharingError(GoogleCalendarError):
    """Raised when sharing a calendar fails."""

    pass


class CalendarAccessError(GoogleCalendarError):
    """Raised when there's an error managing calendar access."""

    pass


class CalendarCreationError(GoogleCalendarError):
    """Raised when creating a new calendar fails."""

    pass


class CalendarDeletionError(GoogleCalendarError):
    """Raised when deleting a calendar fails."""

    pass


# Constants
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_SHARING_BASE_URL = (
    "https://calendar.google.com/calendar/u/0/r/settings/calendar"
)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def to_thread(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))


class GoogleCalendarService:
    """
    An asynchronous service to manage Google Calendar events with comprehensive
    timezone support and enhanced error handling.
    """

    def __init__(
        self,
        service_account_file: str,
        calendar_id: str = "primary",
    ) -> None:
        """
        Initializes the calendar service.

        Args:
            service_account_file: Path to the service account credentials file.
            calendar_id: Default calendar ID to use for operations (default: "primary").
        """
        self.service_account_file = service_account_file
        self.calendar_id = calendar_id
        self.service = self._authenticate()

    def _authenticate(self) -> Any:
        """
        Authenticates with Google Calendar API using Service Account.

        Returns:
            The Google Calendar API service.

        Raises:
            FileNotFoundError: If service account file is missing.
            AuthenticationError: If authentication fails.
        """
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=SCOPES
            )
            return build("calendar", "v3", credentials=creds, static_discovery=False)
        except FileNotFoundError:
            logger.error(f"Service account file not found: {self.service_account_file}")
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError("Failed to authenticate with Google Calendar API")

    async def _execute_request(self, request):
        """
        Executes an API request asynchronously using asyncio.to_thread.

        Args:
            request: The API request to execute.

        Returns:
            The API response.

        Raises:
            GoogleCalendarError: If the API request fails.
        """
        try:
            # Use asyncio.to_thread to run the blocking API call in a separate thread
            return await to_thread(request.execute)
        except HttpError as error:
            logger.error(f"An HTTP error occurred: {error}")
            if error.resp.status == 403:
                raise CalendarAccessError(
                    "Insufficient permissions to access the calendar."
                )
            elif error.resp.status == 404:
                raise CalendarNotFoundError(
                    "The specified calendar or event was not found."
                )
            else:
                raise GoogleCalendarError(f"An HTTP error occurred: {error}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise GoogleCalendarError(f"An unexpected error occurred: {e}")

    async def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        timezone: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        calendar_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Creates a new calendar event asynchronously.

        Args:
            summary: Event title.
            start_time: Event start datetime.
            end_time: Event end datetime.
            timezone: Timezone for the event.
            description: Optional event description.
            location: Optional event location.
            attendees: Optional list of attendee email addresses.
            calendar_id: Optional calendar ID (uses default if not provided).

        Returns:
            Dict containing the created event details or None if creation failed.

        Raises:
            ValueError: If timezone is invalid or end time is before start time.
            EventCreationError: If the event creation fails.
        """
        self._validate_event_parameters(timezone, start_time, end_time)

        event_body = self._build_event_body(
            summary, start_time, end_time, timezone, description, location, attendees
        )

        request = self.service.events().insert(
            calendarId=calendar_id or self.calendar_id, body=event_body
        )
        try:
            created_event = await self._execute_request(request)
            logger.info(f"Event created: {created_event.get('htmlLink')}")
            return created_event
        except Exception as error:
            logger.error(f"An error occurred: {error}")
            raise EventCreationError("Failed to create event")

    async def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        timezone: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        calendar_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Updates an existing calendar event asynchronously.

        Args:
            event_id: The ID of the event to update.
            summary: Optional new event title.
            start_time: Optional new start datetime.
            end_time: Optional new end datetime.
            timezone: Optional new timezone.
            description: Optional new description.
            location: Optional new location.
            attendees: Optional new list of attendee email addresses.
            calendar_id: Optional calendar ID (uses default if not provided).

        Returns:
            Dict containing the updated event details or None if update failed.

        Raises:
            ValueError: If event ID is empty, timezone is invalid, or end time is before start time.
            EventNotFoundError: If the event to update is not found.
            EventUpdateError: If the event update fails.
        """
        if not event_id:
            raise ValueError("Event ID cannot be empty")

        cal_id = calendar_id or self.calendar_id

        # Fetch current event details
        try:
            event_request = self.service.events().get(
                calendarId=cal_id, eventId=event_id
            )
            event = await self._execute_request(event_request)
        except HttpError as error:
            if error.resp.status == 404:
                raise EventNotFoundError(f"Event with ID '{event_id}' not found.")
            else:
                logger.error(f"Error retrieving event: {error}")
                raise EventUpdateError("Failed to retrieve event details for update")

        if timezone:
            self._validate_timezone(timezone)

        if start_time and end_time:
            self._validate_time_range(start_time, end_time)

        # Update fields that have changed
        update_needed = self._update_event_fields(
            event,
            summary,
            start_time,
            end_time,
            timezone,
            description,
            location,
            attendees,
        )

        if not update_needed:
            logger.info("No changes detected, skipping update.")
            return event

        # Perform the update
        try:
            update_request = self.service.events().update(
                calendarId=cal_id, eventId=event_id, body=event
            )
            updated_event = await self._execute_request(update_request)
            logger.info(f"Event updated: {updated_event.get('htmlLink')}")
            return updated_event
        except Exception as error:
            logger.error(f"An error occurred during event update: {error}")
            raise EventUpdateError("Failed to update event")

    async def delete_event(
        self, event_id: str, calendar_id: Optional[str] = None
    ) -> bool:
        """
        Deletes a calendar event asynchronously.

        Args:
            event_id: The ID of the event to delete.
            calendar_id: Optional calendar ID (uses default if not provided).

        Returns:
            True if deletion was successful, False otherwise.

        Raises:
            ValueError: If event ID is empty.
            EventDeletionError: If the event deletion fails.
        """
        if not event_id:
            raise ValueError("Event ID cannot be empty")

        request = self.service.events().delete(
            calendarId=calendar_id or self.calendar_id, eventId=event_id
        )
        try:
            await self._execute_request(request)
            logger.info(f"Event deleted: {event_id}")
            return True
        except Exception as error:
            logger.error(f"An error occurred: {error}")
            raise EventDeletionError("Failed to delete event")

    async def get_events_limit(
        self, max_results: int = 10, calendar_id: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves events from the calendar asynchronously.

        Args:
            max_results: Maximum number of events to retrieve.
            calendar_id: Optional calendar ID (uses default if not provided).

        Returns:
            List of event dictionaries or None if there was an error.

        Raises:
            GoogleCalendarError: If there's an error retrieving events.
        """
        try:
            request = self.service.events().list(
                calendarId=calendar_id or self.calendar_id,
                timeMin=datetime.utcnow().isoformat() + "Z",
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            events_result = await self._execute_request(request)
            return events_result.get("items", [])
        except Exception as error:
            logger.error(f"An error occurred: {error}")
            raise GoogleCalendarError("Failed to retrieve events")

    async def get_events_date(
        self, date: datetime, calendar_id: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves events from the calendar for a specific date asynchronously.

        Args:
            date: The date to retrieve events for.
            calendar_id: Optional calendar ID (uses default if not provided).

        Returns:
            List of event dictionaries or None if there was an error.

        Raises:
            GoogleCalendarError: If there's an error retrieving events.
        """
        try:
            start_datetime = datetime.combine(date, datetime.min.time())
            end_datetime = datetime.combine(date, datetime.max.time())

            request = self.service.events().list(
                calendarId=calendar_id or self.calendar_id,
                timeMin=start_datetime.isoformat() + "Z",
                timeMax=end_datetime.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime",
            )
            events_result = await self._execute_request(request)
            return events_result.get("items", [])
        except Exception as error:
            logger.error(f"An error occurred: {error}")
            raise GoogleCalendarError("Failed to retrieve events")

    async def share_calendar(
        self, email: str, calendar_id: Optional[str] = None, role: str = "reader"
    ) -> bool:
        """
        Shares the calendar with a user asynchronously.

        Args:
            email: Email address of the user to share with.
            calendar_id: Optional calendar ID (uses default if not provided).
            role: Access role to grant (default: "reader").

        Returns:
            True if sharing was successful, False otherwise.

        Raises:
            CalendarSharingError: If calendar sharing fails.
        """
        rule = {
            "scope": {"type": "user", "value": email},
            "role": role,
        }

        request = self.service.acl().insert(
            calendarId=calendar_id or self.calendar_id, body=rule
        )
        try:
            await self._execute_request(request)
            logger.info(f"Successfully shared calendar with {email} (role: {role})")
            return True
        except Exception as error:
            logger.error(f"Failed to share calendar: {error}")
            raise CalendarSharingError("Failed to share calendar")

    async def list_shared_users(
        self, calendar_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lists all users who have access to the calendar asynchronously.

        Args:
            calendar_id: Optional calendar ID (uses default if not provided).

        Returns:
            List of access control rules.

        Raises:
            CalendarAccessError: If listing shared users fails.
        """
        request = self.service.acl().list(calendarId=calendar_id or self.calendar_id)
        try:
            acl = await self._execute_request(request)
            return acl.get("items", [])
        except Exception as error:
            logger.error(f"Failed to list shared users: {error}")
            raise CalendarAccessError("Failed to list shared users")

    async def remove_calendar_access(
        self, email: str, calendar_id: Optional[str] = None
    ) -> bool:
        """
        Removes calendar access for a specific user asynchronously.

        Args:
            email: The email address of the user to remove access for.
            calendar_id: Optional calendar ID (uses default if not provided).

        Returns:
            True if removal was successful, False otherwise.

        Raises:
            CalendarAccessError: If removing calendar access fails.
        """
        rule_id = f"user:{email}"
        request = self.service.acl().delete(
            calendarId=calendar_id or self.calendar_id, ruleId=rule_id
        )
        try:
            await self._execute_request(request)
            logger.info(f"Successfully removed calendar access for {email}")
            return True
        except Exception as error:
            logger.error(f"Failed to remove calendar access: {error}")
            raise CalendarAccessError("Failed to remove calendar access")

    async def create_calendar(
        self, summary: str, description: Optional[str] = None, timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Creates a new Google Calendar asynchronously.

        Args:
            summary: Calendar name.
            description: Optional calendar description.
            timezone: Calendar timezone (default: UTC).

        Returns:
            Created calendar object.

        Raises:
            CalendarCreationError: If calendar creation fails.
        """
        calendar_body = {"summary": summary, "timeZone": timezone}
        if description:
            calendar_body["description"] = description

        request = self.service.calendars().insert(body=calendar_body)
        try:
            calendar = await self._execute_request(request)
            logger.info(f"Created calendar: {summary}")
            logger.info(f"Calendar ID: {calendar['id']}")
            if not self.calendar_id:
                self.calendar_id = calendar["id"]
            return calendar
        except Exception as error:
            logger.error(f"Failed to create calendar: {error}")
            raise CalendarCreationError("Failed to create calendar")

    async def delete_calendar(self, calendar_id: Optional[str] = None) -> bool:
        """
        Deletes a Google Calendar asynchronously.

        Args:
            calendar_id: Optional ID of calendar to delete.
                         If not provided, uses the instance's calendar_id.

        Returns:
            True if deletion was successful, False otherwise.

        Raises:
            CalendarDeletionError: If calendar deletion fails.
        """
        cal_id = calendar_id or self.calendar_id
        if not cal_id:
            logger.warning("No calendar ID provided")
            return False

        request = self.service.calendars().delete(calendarId=cal_id)
        try:
            await self._execute_request(request)
            logger.info(f"Successfully deleted calendar: {cal_id}")
            if cal_id == self.calendar_id:
                self.calendar_id = None
            return True
        except Exception as error:
            logger.error(f"Failed to delete calendar: {error}")
            raise CalendarDeletionError("Failed to delete calendar")

    async def list_calendars(self) -> List[Dict[str, Any]]:
        """
        Lists all calendars available to the service account asynchronously.

        Returns:
            List of calendar objects.

        Raises:
            GoogleCalendarError: If listing calendars fails.
        """
        request = self.service.calendarList().list()
        try:
            calendar_list = await self._execute_request(request)
            calendars = calendar_list.get("items", [])
            if not calendars:
                logger.info("No calendars found")
            else:
                logger.info("\nAvailable Calendars:")
                for calendar in calendars:
                    logger.info(f"- {calendar['summary']} (ID: {calendar['id']})")
            return calendars
        except Exception as error:
            logger.error(f"Failed to list calendars: {error}")
            raise GoogleCalendarError("Failed to list calendars")

    async def get_calendar_details(
        self, calendar_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gets detailed information about a specific calendar asynchronously.

        Args:
            calendar_id: Optional ID of calendar to get details for.
                         If not provided, uses the instance's calendar_id.

        Returns:
            Calendar details object.

        Raises:
            GoogleCalendarError: If fetching calendar details fails.
        """
        cal_id = calendar_id or self.calendar_id
        if not cal_id:
            logger.warning("No calendar ID provided")
            return {}

        request = self.service.calendars().get(calendarId=cal_id)
        try:
            return await self._execute_request(request)
        except Exception as error:
            logger.error(f"Failed to get calendar details: {error}")
            raise GoogleCalendarError("Failed to get calendar details")

    def _build_event_body(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        timezone: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Helper method to build the event body for API requests, including timezone information.

        Args:
            summary: Event title.
            start_time: Event start datetime (timezone-aware or naive).
            end_time: Event end datetime (timezone-aware or naive).
            timezone: Timezone for the event (e.g., 'America/New_York').
            description: Optional event description.
            location: Optional event location.
            attendees: Optional list of attendee email addresses.

        Returns:
            Dict containing the formatted event body for API request.
        """
        event_body = {
            "summary": summary,
            "start": {
                "dateTime": self._format_datetime(start_time, timezone),
                "timeZone": timezone,
            },
            "end": {
                "dateTime": self._format_datetime(end_time, timezone),
                "timeZone": timezone,
            },
        }
        if description is not None:
            event_body["description"] = description
        if location:
            event_body["location"] = location
        if attendees:
            event_body["attendees"] = [{"email": attendee} for attendee in attendees]

        return event_body

    def _format_datetime(self, dt: datetime, timezone: str) -> str:
        """
        Formats a datetime object into a string representation for the Google Calendar API,
        handling timezone conversions if necessary.

        Args:
            dt: The datetime object.
            timezone: The target timezone.

        Returns:
            A string representation of the datetime in ISO 8601 format with timezone offset.
        """
        if dt.tzinfo is None:
            tz = pytz.timezone(timezone)
            dt = tz.localize(dt)
        else:
            tz = pytz.timezone(timezone)
            dt = dt.astimezone(tz)

        return dt.isoformat()

    def _validate_timezone(self, timezone_str: str) -> None:
        """
        Validates a timezone string using the pytz library.

        Args:
            timezone_str: The timezone string to validate.

        Raises:
            ValueError: If the timezone is invalid.
        """
        try:
            pytz.timezone(timezone_str)
        except pytz.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {timezone_str}")

    def _validate_time_range(self, start_time: datetime, end_time: datetime) -> None:
        """
        Validates that the end time is not before the start time.

        Args:
            start_time: The start datetime.
            end_time: The end datetime.

        Raises:
            ValueError: If end time is before start time.
        """
        if end_time < start_time:
            raise ValueError("End time cannot be before start time")

    def _validate_event_parameters(
        self, timezone: str, start_time: datetime, end_time: datetime
    ) -> None:
        """
        Validates event parameters.

        Args:
            timezone: The timezone string.
            start_time: The start datetime.
            end_time: The end datetime.

        Raises:
            ValueError: If timezone is invalid or end time is before start time.
        """
        self._validate_timezone(timezone)
        self._validate_time_range(start_time, end_time)

    def _update_event_fields(
        self,
        event: Dict[str, Any],
        summary: Optional[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        timezone: Optional[str],
        description: Optional[str],
        location: Optional[str],
        attendees: Optional[List[str]],
    ) -> bool:
        """
        Updates the event dictionary with new values for specified fields.

        Args:
            event: The event dictionary to update.
            summary: Optional new event title.
            start_time: Optional new start datetime.
            end_time: Optional new end datetime.
            timezone: Optional new timezone.
            description: Optional new description.
            location: Optional new location.
            attendees: Optional new list of attendee email addresses.

        Returns:
            True if any fields were updated, False otherwise.
        """
        update_needed = False
        if summary is not None and event.get("summary") != summary:
            event["summary"] = summary
            update_needed = True
        if start_time is not None and self._format_datetime(
            start_time, timezone or event["start"].get("timeZone")
        ) != event["start"].get("dateTime"):
            event["start"] = {
                "dateTime": self._format_datetime(
                    start_time, timezone or event["start"].get("timeZone")
                ),
                "timeZone": timezone or event["start"].get("timeZone"),
            }
            update_needed = True
        if end_time is not None and self._format_datetime(
            end_time, timezone or event["end"].get("timeZone")
        ) != event["end"].get("dateTime"):
            event["end"] = {
                "dateTime": self._format_datetime(
                    end_time, timezone or event["end"].get("timeZone")
                ),
                "timeZone": timezone or event["end"].get("timeZone"),
            }
            update_needed = True
        if description is not None and event.get("description") != description:
            event["description"] = description
            update_needed = True
        if location is not None and event.get("location") != location:
            event["location"] = location
            update_needed = True
        if attendees is not None:
            current_attendees = {
                a["email"] for a in event.get("attendees", []) if "email" in a
            }
            new_attendees = set(attendees)
            if current_attendees != new_attendees:
                event["attendees"] = [{"email": attendee} for attendee in attendees]
                update_needed = True

        return update_needed
