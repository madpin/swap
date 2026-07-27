#!/usr/bin/env python3
"""
Rota to Google Calendar Sync

This script syncs work shifts from a Google Spreadsheet to Google Calendar.
It reads the rota data, parses shift information, and updates a dedicated calendar.

Requirements:
- Google API credentials (service account)
- Google Sheets API
- Google Calendar API

By default, the script reads service-account.json from the project directory.
Set SERVICE_ACCOUNT_FILE to override that path.
"""

import argparse
import logging
import os
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
# SPREADSHEET_ID = "1KKS89Y3M9xW6lI00qXAO45zyi7Xk5Y4DBGKqSDkfOZQ"
# SPREADSHEET_ID = "1_-INofgBo-ZX_I52raEsagUrDsu0JLMbz5z-B8X0u8c"
# https://docs.google.com/spreadsheets/d/1wYRT5yVKyprkVMfRj3DS6FjqWQ3eSbOw7AXXM6YB58k/edit?usp=sharing
SPREADSHEET_ID = "1wYRT5yVKyprkVMfRj3DS6FjqWQ3eSbOw7AXXM6YB58k"
RANGE_NAME = "Sheet1!A:H"

USERS = [
    {
        "CALENDAR_NAME": "Rachel's Rota",
        "USER_NAMES": ["DrRachelKerry", "RACHEL"],
        "EMAILS_TO_SHARE": [
            "madpin@gmail.com",
            "tpinto@indeed.com",
            "rachelkerry95@gmail.com",
            "rachiel.kerry1@gmail.com",
        ],
    },
    {
        "CALENDAR_NAME": "Grace's Rota",
        "USER_NAMES": ["DrGraceHigh", "GRACE"],
        "EMAILS_TO_SHARE": [
            "madpin@gmail.com",
        ],
    },
]

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# API scopes
SHEETS_SCOPE = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
CALENDAR_SCOPE = ["https://www.googleapis.com/auth/calendar"]

DEFAULT_SERVICE_ACCOUNT_FILE = "/Users/tpinto/madpin/swap/service-account.json"
SWAP_EVENT_PROPERTY = "swapManaged"
SWAP_EVENT_PROPERTY_VALUE = "true"
SWAP_EVENT_VERSION_PROPERTY = "swapVersion"
SWAP_EVENT_VERSION = "2"
SWAP_EVENT_DATE_PROPERTY = "swapShiftDate"
SWAP_EVENT_PROPERTIES = {
    SWAP_EVENT_PROPERTY: SWAP_EVENT_PROPERTY_VALUE,
    SWAP_EVENT_VERSION_PROPERTY: SWAP_EVENT_VERSION,
}


class GoogleSpreadsheetReader:
    """Reads data from Google Spreadsheets using the Sheets API."""

    def __init__(self, service_account_file: str):
        self.service_account_file = service_account_file
        self.service = self._build_service()

    def _build_service(self):
        """Build and return a Sheets service object."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=SHEETS_SCOPE
            )
            return build("sheets", "v4", credentials=credentials)
        except Exception as e:
            logger.error(f"Failed to build Sheets service: {e}")
            raise

    def read_sheet(self, spreadsheet_id: str, range_name: str) -> List[List[str]]:
        """Read data from specified range in a Google Spreadsheet."""
        try:
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )
            return result.get("values", [])
        except HttpError as err:
            logger.error(f"Error reading from spreadsheet: {err}")
            raise


class RotaParser:
    """Parses staff rota data from a Google Spreadsheet."""

    def __init__(self, service_account_file: str, spreadsheet_id: str, range_name: str):
        self.reader = GoogleSpreadsheetReader(service_account_file)
        self.spreadsheet_id = spreadsheet_id
        self.range_name = range_name
        self.covered_dates_by_name: Dict[str, Set[str]] = {}

    def get_rota_data(self) -> List[List[str]]:
        """Retrieve rota data from Google Spreadsheet."""
        return self.reader.read_sheet(self.spreadsheet_id, self.range_name)

    def _parse_range(
        self, time_str: str, current_date: datetime
    ) -> Dict[str, datetime]:
        """Parse a time range string and return start and end datetime objects."""
        invalid_strings = {"*n/a", "/"}

        if not time_str or time_str.lower().strip() in invalid_strings:
            raise ValueError(f"Invalid time string: {time_str}")

        time_str = time_str.strip()

        def parse_time_component(time_component: str) -> Tuple[int, int]:
            """Convert various time formats to hour and minute."""
            clean_time = re.sub(r"[^\d.:]+", "", time_component)

            if "." in clean_time:
                parts = clean_time.split(".")
            elif ":" in clean_time:
                parts = clean_time.split(":")
            else:
                parts = (
                    [clean_time[:2], clean_time[2:]]
                    if len(clean_time) == 4
                    else [clean_time, "0"]
                )

            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 and parts[1] else 0

            return hour, minute

        patterns = [
            r"(\d{4})\s*-\s*(\d{4})",
            r"(\d{1,2}[:.]\d{2})\s*-\s*(\d{1,2}[:.]\d{2})",
            # Removed the problematic pattern
            # r"(?:.*?\(?)?(\d{1,2})\s*-\s*(\d{1,2})\s*(pm)?\)?",
            r"(\d{1,2})\s*-\s*(\d{1,2})\s*(pm)",  # Corrected pattern
            r"(\d{1,2})\s*-\s*(\d{1,2})",
            r"Zone\s*\d+\s*\((\d{1,2})\s*-\s*(\d{1,2})\s*(pm)\)",  # Added pattern
            r"Zone\s*\d+\s*\((\d{1,2})\s*-\s*(\d{1,2})\)",  # Added pattern zone 2
        ]

        for pattern in patterns:
            match = re.search(pattern, time_str, re.IGNORECASE)
            if match:
                groups = match.groups()
                start_str = groups[0]
                end_str = groups[1]
                # Check if 'pm' is captured; if not, default to not PM
                is_pm = (
                    len(groups) > 2 and groups[2] == "pm"
                    if len(groups) > 2
                    else "pm" in time_str.lower()
                )

                try:
                    start_hour, start_minute = parse_time_component(start_str)
                    end_hour, end_minute = parse_time_component(end_str)

                    if is_pm and end_hour < 12:
                        end_hour += 12

                    start_datetime = current_date.replace(
                        hour=start_hour, minute=start_minute, second=0, microsecond=0
                    )
                    end_datetime = current_date.replace(
                        hour=end_hour, minute=end_minute, second=0, microsecond=0
                    )

                    if end_datetime < start_datetime:
                        end_datetime += timedelta(days=1)

                    return {"start_date": start_datetime, "end_date": end_datetime}
                except ValueError:
                    continue

        raise ValueError(f"Invalid time format: {time_str}")

    def parse_rota(self) -> List[Dict]:
        """Parse rota data and return a list of shift dictionaries."""
        data = self.get_rota_data()
        logger.info(f"Retrieved {len(data)} rows from spreadsheet")
        self.covered_dates_by_name = {}
        shifts = []
        current_dates = []
        after_today = False

        def is_date_row(row: List[str]) -> bool:
            """Check if row contains dates."""
            date_count = 0
            for cell in row:
                try:
                    for date_format in [
                        "%a %d %b",
                        "%B %d",
                        "%d %B",
                        "%d/%m",
                        "%d-%m",
                        "%d-%b",
                    ]:
                        try:
                            datetime.strptime(cell.strip(), date_format)
                            date_count += 1
                            break
                        except ValueError:
                            continue
                except (AttributeError, ValueError):
                    continue
            return date_count >= 3

        # Track the column index where the first date appears
        first_date_column = None

        for row in data:
            if not row or len(row) < 3:
                continue

            if is_date_row(row):
                logger.info(f"Found date row: {row[:7]}...")  # Show first 7 elements
                current_dates = []
                first_date_column = None  # Reset for each date row

                for col_idx, date_str in enumerate(row):
                    try:
                        parsed_date = None
                        for date_format in [
                            "%a %d %b",
                            "%B %d",
                            "%d %B",
                            "%d/%m",
                            "%d-%m",
                            "%d-%b",
                        ]:
                            try:
                                parsed_date = datetime.strptime(
                                    date_str.strip(), date_format
                                )
                                break
                            except ValueError:
                                continue

                        if parsed_date:
                            # Track the first date column
                            if first_date_column is None:
                                first_date_column = col_idx
                                logger.info(
                                    f"First date found in column {first_date_column}"
                                )

                            current_date = datetime.now()
                            target_date = parsed_date.replace(year=current_date.year)

                            # Allow dates within the last 30 days or in the future
                            thirty_days_ago = current_date - timedelta(days=30)
                            if target_date >= thirty_days_ago:
                                after_today = True

                            three_months_ago = current_date - timedelta(days=90)
                            if target_date < three_months_ago:
                                target_date = parsed_date.replace(
                                    year=current_date.year + 1
                                )
                            parsed_date = target_date
                            current_dates.append(parsed_date)
                        else:
                            current_dates.append(None)
                    except (AttributeError, ValueError):
                        current_dates.append(None)
                continue

            if not after_today:
                continue

            if "Changeover" in str(row[0]) or len(row) < 3:
                continue

            # Dynamic name search based on first_date_column
            # If first date is in column N, search for name in columns 0 to N-1
            name = None
            if first_date_column is not None and first_date_column > 0:
                for col_idx in range(first_date_column):
                    if col_idx < len(row) and row[col_idx].strip():
                        candidate_name = "".join(
                            char for char in row[col_idx] if char.isalpha()
                        )
                        if candidate_name:
                            name = candidate_name
                            logger.info(f"Found name '{name}' in column {col_idx}")
                            break

            # Fallback to column 1 if no name found
            if name is None:
                if len(row) > 1 and row[1].strip():
                    name = "".join(char for char in row[1] if char.isalpha())
                else:
                    continue

            logger.info(
                f"Processing shifts for name: '{name}' from row: {row[: min(len(row), 5)]}"
            )

            covered_dates = self.covered_dates_by_name.setdefault(name.lower(), set())
            covered_dates.update(
                current_date.strftime("%Y-%m-%d")
                for current_date in current_dates
                if current_date is not None
            )

            for i, shift_data in enumerate(row):
                if i >= len(current_dates) or not current_dates[i]:
                    continue

                current_date = current_dates[i]
                shift_data = shift_data.strip()

                shift_entry = {
                    "name": name,
                    "date": current_date.strftime("%Y-%m-%d"),
                    "raw_data": shift_data,
                    "shift_type": "regular",
                    "is_working": True,
                }

                special_cases = {
                    "AL": ("annual_leave", False),
                    "OFF": ("off", False),
                    "NCD": ("non_clinical_day", False),
                    "POST NIGHTS": ("post_nights", False),
                    "PRE NIGHT OFF": ("pre_night", False),
                    "PRE NIGHT": ("pre_night", False),
                    "TR": ("training", True),
                    "*N/A": ("not_available", False),
                    "/": ("not_available", False),
                }

                upper_shift = shift_data.upper()
                if upper_shift in special_cases:
                    shift_entry["shift_type"], shift_entry["is_working"] = (
                        special_cases[upper_shift]
                    )
                    shifts.append(shift_entry)
                    continue

                try:
                    time_range = self._parse_range(shift_data, current_date)
                    shift_entry.update(
                        {
                            "start_date": time_range["start_date"].strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "end_date": time_range["end_date"].strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                        }
                    )
                    shifts.append(shift_entry)
                except ValueError:
                    continue

        return shifts


class GoogleCalendarManager:
    """Manages Google Calendar events and calendars."""

    def __init__(self, service_account_file: str, calendar_id: str = "primary"):
        self.service_account_file = service_account_file
        self.calendar_id = calendar_id
        self.service = self._build_service()

    def _build_service(self):
        """Build and return a Calendar service object."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=CALENDAR_SCOPE
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

    def create_calendar(
        self, summary: str, description: Optional[str] = None, timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """Create a new Google Calendar."""
        calendar_body = {"summary": summary, "timeZone": timezone}
        if description:
            calendar_body["description"] = description

        try:
            calendar = self.service.calendars().insert(body=calendar_body).execute()
            logger.info(f"Created calendar: {summary}")
            return calendar
        except HttpError as error:
            logger.error(f"Failed to create calendar: {error}")
            return {}

    def share_calendar(
        self, email: str, role: str = "reader", calendar_id: Optional[str] = None
    ) -> bool:
        """Share calendar with a user."""
        rule = {
            "scope": {"type": "user", "value": email},
            "role": role,
        }

        try:
            self.service.acl().insert(
                calendarId=calendar_id or self.calendar_id, body=rule
            ).execute()
            logger.info(f"Shared calendar with {email} (role: {role})")
            return True
        except HttpError as error:
            logger.error(f"Failed to share calendar: {error}")
            return False

    def list_shared_users(
        self, calendar_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List users who have access to the calendar."""
        try:
            acl = (
                self.service.acl()
                .list(calendarId=calendar_id or self.calendar_id)
                .execute()
            )
            return acl.get("items", [])
        except HttpError as error:
            logger.error(f"Failed to list shared users: {error}")
            return []

    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        timezone: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        private_properties: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a new calendar event."""
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
        if private_properties:
            event_body["extendedProperties"] = {"private": private_properties}

        try:
            created_event = (
                self.service.events()
                .insert(calendarId=self.calendar_id, body=event_body)
                .execute()
            )
            logger.info(f"Event created: {created_event.get('htmlLink')}")
            return created_event
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return None

    def get_events_date(
        self, date: datetime, timezone: str = "Europe/Dublin"
    ) -> List[Dict[str, Any]]:
        """Get events for a specific date."""
        try:
            start_datetime = datetime.combine(date, datetime.min.time())
            end_datetime = start_datetime + timedelta(days=1)
            events = []
            page_token = None

            while True:
                events_result = (
                    self.service.events()
                    .list(
                        calendarId=self.calendar_id,
                        timeMin=self._format_datetime(start_datetime, timezone),
                        timeMax=self._format_datetime(end_datetime, timezone),
                        singleEvents=True,
                        orderBy="startTime",
                        pageToken=page_token,
                    )
                    .execute()
                )
                events.extend(events_result.get("items", []))
                page_token = events_result.get("nextPageToken")
                if not page_token:
                    return events
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            raise

    def list_events(
        self,
        from_date: Optional[date] = None,
        timezone: str = "Europe/Dublin",
    ) -> List[Dict[str, Any]]:
        """List non-deleted events starting on or after the supplied date."""
        try:
            events = []
            page_token = None

            while True:
                list_parameters = {
                    "calendarId": self.calendar_id,
                    "showDeleted": False,
                    "maxResults": 2500,
                    "pageToken": page_token,
                }
                if from_date:
                    start_datetime = datetime.combine(from_date, datetime.min.time())
                    list_parameters["timeMin"] = self._format_datetime(
                        start_datetime, timezone
                    )

                events_result = self.service.events().list(**list_parameters).execute()
                events.extend(events_result.get("items", []))
                page_token = events_result.get("nextPageToken")
                if not page_token:
                    return events
        except HttpError as error:
            logger.error(f"An error occurred while listing calendar events: {error}")
            raise

    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event."""
        try:
            self.service.events().delete(
                calendarId=self.calendar_id, eventId=event_id
            ).execute()
            logger.info(f"Event deleted: {event_id}")
            return True
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return False

    def _format_datetime(self, dt: datetime, timezone: str) -> str:
        """Format a datetime for the Google Calendar API."""
        if dt.tzinfo is None:
            tz = pytz.timezone(timezone)
            dt = tz.localize(dt)
        else:
            tz = pytz.timezone(timezone)
            dt = dt.astimezone(tz)
        return dt.isoformat()


def get_service_account_file() -> str:
    """Retrieve the configured service account file path."""
    return os.environ.get("SERVICE_ACCOUNT_FILE", DEFAULT_SERVICE_ACCOUNT_FILE)


def get_sync_start_date() -> date:
    """Return today's date in the calendar's timezone."""
    return datetime.now(pytz.timezone("Europe/Dublin")).date()


def initialize_calendar(
    calendar_manager: GoogleCalendarManager, calendar_name: str
) -> None:
    """Initialize the Google Calendar, creating it if it doesn't exist."""
    calendars = calendar_manager.list_calendars()
    # Find calendar with matching name
    matching_calendars = [
        cal for cal in calendars if cal.get("summary") == calendar_name
    ]

    if matching_calendars:
        calendar_manager.calendar_id = matching_calendars[0]["id"]
        logger.info(f"Using existing calendar: {calendar_name}")
    else:
        created_calendar = calendar_manager.create_calendar(calendar_name)
        calendar_manager.calendar_id = created_calendar["id"]
        logger.info(f"Created new calendar: {calendar_name}")


def share_calendar_with_users(
    calendar_manager: GoogleCalendarManager, emails: List[str]
) -> None:
    """Share the calendar with specified users."""
    users = calendar_manager.list_shared_users()
    found_users = {email: False for email in emails}

    for user in users:
        for email in emails:
            if user.get("scope", {}).get("value") == email:
                found_users[email] = True
                logger.info(f"Calendar already shared with {email}")

    for email, found in found_users.items():
        if not found:
            calendar_manager.share_calendar(email=email, role="writer")
            logger.info(f"Shared calendar with {email}")


def is_swap_event(event: Dict[str, Any], user_names: List[str]) -> bool:
    """Return whether an event was created by this or an older S.W.A.P. version."""
    private_properties = event.get("extendedProperties", {}).get("private", {})
    if private_properties.get(SWAP_EVENT_PROPERTY) == SWAP_EVENT_PROPERTY_VALUE:
        return True

    if not user_names:
        return False

    # Older versions did not tag events, but always started descriptions this way.
    aliases = "|".join(re.escape(name) for name in user_names)
    legacy_description = re.compile(
        rf"^(?:{aliases})\s+-\s+\d{{4}}-\d{{2}}-\d{{2}}(?:\r?\n|$)",
        re.IGNORECASE,
    )
    return bool(legacy_description.match(event.get("description", "")))


def get_swap_event_date(event: Dict[str, Any], user_names: List[str]) -> Optional[str]:
    """Read the source shift date from a current or legacy S.W.A.P. event."""
    private_properties = event.get("extendedProperties", {}).get("private", {})
    event_date = private_properties.get(SWAP_EVENT_DATE_PROPERTY)
    if event_date and re.fullmatch(r"\d{4}-\d{2}-\d{2}", event_date):
        return event_date

    if not user_names:
        return None

    aliases = "|".join(re.escape(name) for name in user_names)
    legacy_description = re.compile(
        rf"^(?:{aliases})\s+-\s+(\d{{4}}-\d{{2}}-\d{{2}})(?:\r?\n|$)",
        re.IGNORECASE,
    )
    match = legacy_description.match(event.get("description", ""))
    return match.group(1) if match else None


def _delete_event_or_raise(
    calendar_manager: GoogleCalendarManager, event_id: str
) -> None:
    if not calendar_manager.delete_event(event_id):
        raise RuntimeError(f"Failed to delete calendar event {event_id}")


def delete_swap_events(
    calendar_manager: GoogleCalendarManager,
    user_names: List[str],
    from_date: Optional[date] = None,
) -> int:
    """Delete current and legacy S.W.A.P. events from the cutoff date forward."""
    cutoff_date = from_date or get_sync_start_date()
    deleted_count = 0
    for event in calendar_manager.list_events(from_date=cutoff_date):
        if not is_swap_event(event, user_names):
            continue

        event_date = get_swap_event_date(event, user_names)
        if event_date and event_date < cutoff_date.isoformat():
            continue

        logger.info(
            "Deleting S.W.A.P. event during overwrite: %s",
            event.get("summary", event.get("id")),
        )
        _delete_event_or_raise(calendar_manager, event["id"])
        deleted_count += 1

    return deleted_count


def _event_matches(event: Dict[str, Any], summary: str, description: str) -> bool:
    return event.get("summary") == summary and event.get("description") == description


def _sync_shift_event(
    calendar_manager: GoogleCalendarManager,
    shift: Dict[str, Any],
    user_names: List[str],
) -> None:
    """Create or replace the managed event for one shift."""
    shift_date = datetime.strptime(shift["date"], "%Y-%m-%d").date()
    current_events = calendar_manager.get_events_date(shift_date) or []
    managed_events = [
        event
        for event in current_events
        if is_swap_event(event, user_names)
        and get_swap_event_date(event, user_names) == shift["date"]
    ]
    description = f"{shift['name']} - {shift['date']}\n{shift['raw_data']}"

    if "start_date" in shift and "end_date" in shift:
        start_time = datetime.strptime(shift["start_date"], "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(shift["end_date"], "%Y-%m-%d %H:%M:%S")
        summary = (
            f"🏥 Work ({start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')})"
        )
    else:
        start_time = datetime.combine(shift_date, datetime.min.time())
        end_time = start_time + timedelta(days=1)
        summary = shift["shift_type"].replace("_", " ").title()

    matching_events = [
        event for event in managed_events if _event_matches(event, summary, description)
    ]
    event_to_keep = matching_events[0] if matching_events else None

    for event in managed_events:
        if event_to_keep and event["id"] == event_to_keep["id"]:
            continue
        logger.info(f"Deleting outdated event for {shift['date']}")
        _delete_event_or_raise(calendar_manager, event["id"])

    if event_to_keep:
        logger.info(f"Event already exists for {shift['date']}, skipping")
        return

    logger.info(f"Creating new event for {shift['date']}: {summary}")
    private_properties = {
        **SWAP_EVENT_PROPERTIES,
        SWAP_EVENT_DATE_PROPERTY: shift["date"],
    }
    created_event = calendar_manager.create_event(
        summary=summary,
        description=description,
        start_time=start_time,
        end_time=end_time,
        timezone="Europe/Dublin",
        private_properties=private_properties,
    )
    if not created_event:
        raise RuntimeError(f"Failed to create calendar event for {shift['date']}")


def process_shifts(
    calendar_manager: GoogleCalendarManager,
    parsed_rota: List[Dict],
    user_names: List[str],
    covered_dates: Optional[Set[str]] = None,
    from_date: Optional[date] = None,
) -> None:
    """Reconcile the user's shifts and blank rota dates with the calendar."""
    cutoff_date = (from_date or get_sync_start_date()).isoformat()
    normalized_user_names = [name.lower() for name in user_names]
    filtered_shifts = [
        shift
        for shift in parsed_rota
        if shift["name"].lower() in normalized_user_names
        and shift["date"] >= cutoff_date
    ]
    filtered_shifts.sort(key=lambda shift: shift["date"], reverse=True)

    for shift in filtered_shifts:
        _sync_shift_event(calendar_manager, shift, user_names)

    shift_dates = {shift["date"] for shift in filtered_shifts}
    future_covered_dates = {
        covered_date
        for covered_date in covered_dates or set()
        if covered_date >= cutoff_date
    }
    for empty_date in sorted(future_covered_dates - shift_dates):
        empty_shift_date = datetime.strptime(empty_date, "%Y-%m-%d").date()
        current_events = calendar_manager.get_events_date(empty_shift_date) or []
        for event in current_events:
            if (
                not is_swap_event(event, user_names)
                or get_swap_event_date(event, user_names) != empty_date
            ):
                continue
            logger.info(f"Deleting event from blank rota date {empty_date}")
            _delete_event_or_raise(calendar_manager, event["id"])


def _environment_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync work shifts from Google Sheets to Google Calendar."
    )
    parser.add_argument(
        "--overwrite-events",
        action="store_true",
        default=_environment_flag("SWAP_OVERWRITE_EVENTS"),
        help=(
            "delete all S.W.A.P.-managed and recognizable legacy events before "
            "rebuilding the calendar"
        ),
    )
    return parser.parse_args()


def main() -> None:
    """Main function to orchestrate the rota parsing and calendar management."""
    try:
        args = parse_args()
        sync_start_date = get_sync_start_date()

        # Get service account file
        service_account_file = get_service_account_file()
        logger.info(f"Using service account file: {service_account_file}")

        # Initialize parser and parse rota
        logger.info(f"Initializing rota parser for spreadsheet: {SPREADSHEET_ID}")
        parser = RotaParser(
            service_account_file=service_account_file,
            spreadsheet_id=SPREADSHEET_ID,
            range_name=RANGE_NAME,
        )

        logger.info("Parsing rota data")
        parsed_rota = parser.parse_rota()
        parsed_rota = [
            shift
            for shift in parsed_rota
            if shift["date"] >= sync_start_date.isoformat()
        ]
        logger.info(
            "Found %d shifts from %s forward",
            len(parsed_rota),
            sync_start_date.isoformat(),
        )

        for user in USERS:
            calendar_name = user["CALENDAR_NAME"]
            user_names = user["USER_NAMES"]
            emails_to_share = user["EMAILS_TO_SHARE"]

            # Normalize user names for case-insensitive comparison
            normalized_user_names = [name.lower() for name in user_names]
            user_shifts = [
                shift
                for shift in parsed_rota
                if shift["name"].lower() in normalized_user_names
            ]
            covered_dates = set().union(
                *(
                    parser.covered_dates_by_name.get(name, set())
                    for name in normalized_user_names
                )
            )
            logger.info(f"Found {len(user_shifts)} shifts for {', '.join(user_names)}")

            # Initialize calendar manager
            logger.info(f"Initializing calendar manager for {calendar_name}")
            calendar_manager = GoogleCalendarManager(
                service_account_file=service_account_file,
            )

            # Setup calendar
            initialize_calendar(calendar_manager, calendar_name)

            # Ensure calendars are shared on every run (quick check already implemented)
            share_calendar_with_users(calendar_manager, emails_to_share)

            if args.overwrite_events:
                logger.info(
                    "Overwrite enabled; deleting existing S.W.A.P. events from %s",
                    calendar_name,
                )
                deleted_count = delete_swap_events(
                    calendar_manager,
                    user_names,
                    from_date=sync_start_date,
                )
                logger.info(
                    "Deleted %d existing S.W.A.P. events from %s",
                    deleted_count,
                    calendar_name,
                )

            # Process and update shifts
            logger.info(f"Processing shifts for {', '.join(user_names)}")
            process_shifts(
                calendar_manager,
                parsed_rota,
                user_names,
                covered_dates=covered_dates,
                from_date=sync_start_date,
            )

        logger.info("Calendar sync completed successfully")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
