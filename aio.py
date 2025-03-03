#!/usr/bin/env python3
"""
Rota to Google Calendar Sync

This script syncs work shifts from a Google Spreadsheet to Google Calendar.
It reads the rota data, parses shift information, and updates a dedicated calendar.

Requirements:
- Google API credentials (service account)
- Google Sheets API
- Google Calendar API

Set the SERVICE_ACCOUNT_FILE environment variable to the path of your
service account credentials file before running this script.
"""

import os
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union

import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
SPREADSHEET_ID = "133dO2oU424ruQn0Gt1w-IgJMxhYw4P7HRIBWFRQkznY"
RANGE_NAME = "Sheet1!A:M"

USERS = [
    {
        "CALENDAR_NAME": "Rachel's Rota",
        "USER_NAME": "Rachel",
        "EMAILS_TO_SHARE": [
            "madpin@gmail.com",
            "tpinto@indeed.com",
            "rachelkerry95@gmail.com",
            "rachiel.kerry1@gmail.com",
        ],
    },
    {
        "CALENDAR_NAME": "Desire's Rota",
        "USER_NAME": "Desire",
        "EMAILS_TO_SHARE": [
            "madpin@gmail.com",
        ],
    }
]

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# API scopes
SHEETS_SCOPE = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
CALENDAR_SCOPE = ["https://www.googleapis.com/auth/calendar"]


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
        shifts = []
        current_dates = []
        after_today = False

        def is_date_row(row: List[str]) -> bool:
            """Check if row contains dates."""
            date_count = 0
            for cell in row:
                try:
                    for date_format in ["%a %d %b", "%B %d", "%d %B", "%d/%m", "%d-%m"]:
                        try:
                            datetime.strptime(cell.strip(), date_format)
                            date_count += 1
                            break
                        except ValueError:
                            continue
                except (AttributeError, ValueError):
                    continue
            return date_count >= 3

        for row in data:
            if not row or len(row) < 3:
                continue

            if is_date_row(row):
                current_dates = []
                for date_str in row:
                    try:
                        parsed_date = None
                        for date_format in [
                            "%a %d %b",
                            "%B %d",
                            "%d %B",
                            "%d/%m",
                            "%d-%m",
                        ]:
                            try:
                                parsed_date = datetime.strptime(
                                    date_str.strip(), date_format
                                )
                                break
                            except ValueError:
                                continue

                        if parsed_date:
                            current_date = datetime.now()
                            target_date = parsed_date.replace(year=current_date.year)
                            if target_date >= current_date:
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

            if "Changeover" in str(row[0]) or not row[1].strip() or len(row) < 3:
                continue

            name = "".join(char for char in row[1] if char.isalpha())

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

    def get_events_date(self, date: datetime) -> Optional[List[Dict[str, Any]]]:
        """Get events for a specific date."""
        try:
            start_datetime = datetime.combine(date, datetime.min.time())
            end_datetime = datetime.combine(date, datetime.max.time())

            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=start_datetime.isoformat() + "Z",
                    timeMax=end_datetime.isoformat() + "Z",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return events_result.get("items", [])
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return None

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
    """Retrieve the service account file path from environment variables."""
    service_account_file = os.environ.get("SERVICE_ACCOUNT_FILE")
    if not service_account_file:
        logger.error("Error: The SERVICE_ACCOUNT_FILE environment variable is not set.")
        exit(1)
    return service_account_file


def initialize_calendar(calendar_manager: GoogleCalendarManager, calendar_name: str) -> None:
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


def process_shifts(
    calendar_manager: GoogleCalendarManager, parsed_rota: List[Dict], user_name: str
) -> None:
    """Process and add shifts to the calendar."""
    filtered_shifts = [shift for shift in parsed_rota if shift["name"] == user_name]
    filtered_shifts.sort(key=lambda x: x["date"], reverse=True)

    # Process only the latest 100 shifts
    for shift in filtered_shifts[:100]:
        shift_date = datetime.strptime(shift["date"], "%Y-%m-%d").date()
        current_events = calendar_manager.get_events_date(shift_date) or []

        # Handle non-working days by creating an all-day event
        if not shift["is_working"]:
            summary = f"{shift['shift_type'].replace('_', ' ').title()}"
            description = f"{shift['name']} - {shift['date']}\n{shift['raw_data']}"
            start_time = datetime.combine(shift_date, datetime.min.time())
            end_time = start_time + timedelta(days=1)

            # Check if event already exists and is identical
            event_exists = False
            if current_events and len(current_events) == 1:
                existing_event = current_events[0]
                if (
                    existing_event.get("summary") == summary
                    and existing_event.get("description") == description
                ):
                    event_exists = True
                    logger.info(
                        f"All-day event already exists for {shift['date']}, skipping"
                    )

            # Remove old events if they exist and are different
            if current_events and not event_exists:
                for event in current_events:
                    logger.info(f"Deleting outdated event for {shift['date']}")
                    calendar_manager.delete_event(event["id"])

            # Create new all-day event if it doesn't exist or is different
            if not event_exists:
                logger.info(
                    f"Creating new all-day event for {shift['date']}: {summary}"
                )
                calendar_manager.create_event(
                    summary=summary,
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    timezone="Europe/Dublin",
                )
            continue

        # Only process working shifts with start and end dates
        if "start_date" not in shift or "end_date" not in shift:
            continue

        # Prepare event details
        start_time = datetime.strptime(shift["start_date"], "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(shift["end_date"], "%Y-%m-%d %H:%M:%S")
        summary = f"🏥 Hospital ({start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')})"
        description = f"{shift['name']} - {shift['date']}\n{shift['raw_data']}"

        # Check if event already exists and is identical
        event_exists = False
        if current_events and len(current_events) == 1:
            existing_event = current_events[0]
            if (
                existing_event.get("summary") == summary
                and existing_event.get("description") == description
            ):
                event_exists = True
                logger.info(f"Event already exists for {shift['date']}, skipping")

        # Remove old events if they exist and are different
        if current_events and not event_exists:
            for event in current_events:
                logger.info(f"Deleting outdated event for {shift['date']}")
                calendar_manager.delete_event(event["id"])

        # Create new event if it doesn't exist or is different
        if not event_exists:
            logger.info(f"Creating new event for {shift['date']}: {summary}")
            calendar_manager.create_event(
                summary=summary,
                description=description,
                start_time=start_time,
                end_time=end_time,
                timezone="Europe/Dublin",
            )


def main() -> None:
    """Main function to orchestrate the rota parsing and calendar management."""
    try:
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
        logger.info(f"Found {len(parsed_rota)} shifts in the rota")

        for user in USERS:
            calendar_name = user["CALENDAR_NAME"]
            user_name = user["USER_NAME"]
            emails_to_share = user["EMAILS_TO_SHARE"]

            user_shifts = [shift for shift in parsed_rota if shift["name"] == user_name]
            logger.info(f"Found {len(user_shifts)} shifts for {user_name}")

            # Initialize calendar manager
            logger.info(f"Initializing calendar manager for {calendar_name}")
            calendar_manager = GoogleCalendarManager(
                service_account_file=service_account_file,
            )

            # Setup calendar
            initialize_calendar(calendar_manager, calendar_name)
            share_calendar_with_users(calendar_manager, emails_to_share)

            # Process and update shifts
            logger.info(f"Processing shifts for {user_name}")
            process_shifts(calendar_manager, parsed_rota, user_name)

        logger.info("Calendar sync completed successfully")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
