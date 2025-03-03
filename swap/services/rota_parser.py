import os.path
from pprint import pprint
from typing import Dict, List, Optional, Union
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from swap.utils.logger import logger
import pytest

"""
Note:
    Description:
        This script reads and parses staff rota data from a Google Sheet. It supports authentication via service accounts and provides functionalities to extract shift information, including start and end times, for each staff member.

    Features:
        - Authenticates with Google Sheets API using a service account.
        - Reads data from a specified Google Sheet and range.
        - Parses rota data to extract shift details, handling various time formats and special cases (e.g., 'AL', 'OFF', 'NCD').
        - Converts parsed time ranges into datetime objects.
        - Structures the parsed data into a list of dictionaries, each representing a shift.

    Required Environment Variables:
        - SERVICE_ACCOUNT_FILE: Path to the service account credentials JSON file.

    Required Packages:
        - google-auth
        - google-auth-oauthlib
        - google-api-python-client
        - pytest (for testing)

    Usage:
        - Set the SERVICE_ACCOUNT_FILE environment variable to the path of your service account credentials file.
        - Run the script directly to execute the main function, which reads and prints the parsed rota data.
        - Alternatively, import the `RotaParser` class into other Python scripts to use its functionalities.

    Author:
        tpinto
"""

# Constants for authentication
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# # Logger setup
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
# )
# logger = logging.getLogger(__name__)


class GoogleSpreadsheetReader:
    """
    Reads data from Google Spreadsheets using the Sheets API.

    Supports both OAuth 2.0 and Service Account authentication.
    Provides methods to authenticate, read data from a specific range, and handle API errors.
    """

    def __init__(
        self,
        oauth_token_file: Optional[str] = "token.json",
        oauth_client_secrets_file: Optional[str] = None,
        service_account_file: Optional[str] = None,
    ):
        """
        Initializes the SpreadsheetReader with authentication credentials.

        Args:
            oauth_token_file: Path to the OAuth token file.
            oauth_client_secrets_file: Path to the OAuth client secrets file.
            service_account_file: Path to the service account credentials file.

        Raises:
            ValueError: If neither OAuth nor Service Account credentials are provided.
        """
        self.oauth_token_file = oauth_token_file
        self.oauth_client_secrets_file = oauth_client_secrets_file
        self.service_account_file = service_account_file
        self.credentials: Optional[Union[Credentials, ServiceAccountCredentials]] = None
        self.service = None

        if not any([oauth_token_file, service_account_file]):
            raise ValueError(
                "Either OAuth or Service Account credentials must be provided."
            )
        self.authenticate()

    def authenticate(self):
        """
        Authenticates the user using either OAuth 2.0 or Service Account credentials.

        Prioritizes Service Account if both types are provided.
        """
        if self.service_account_file:
            self._authenticate_service_account()
        elif self.oauth_token_file and self.oauth_client_secrets_file:
            self._authenticate_oauth()
        else:
            raise ValueError("Invalid credentials provided for authentication.")

        self.service = build("sheets", "v4", credentials=self.credentials)
        logger.info("Successfully authenticated and built service object.")

    def _authenticate_service_account(self):
        """Authenticates using a Service Account."""
        try:
            self.credentials = ServiceAccountCredentials.from_service_account_file(
                self.service_account_file, scopes=SCOPES
            )
            logger.info("Service Account authentication successful.")
        except Exception as e:
            logger.error(f"Service Account authentication failed: {e}")
            raise

    def _authenticate_oauth(self):
        """Authenticates using OAuth 2.0.

        Loads existing token if available, otherwise initiates a new flow.
        """
        credentials = None
        if os.path.exists(self.oauth_token_file):
            credentials = Credentials.from_authorized_user_file(
                self.oauth_token_file, SCOPES
            )
            logger.info("Loaded existing OAuth token.")

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                logger.info("OAuth token expired. Attempting to refresh.")
                credentials.refresh(Request())
            else:
                logger.info("No valid OAuth token found. Initiating new flow.")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.oauth_client_secrets_file, SCOPES
                )
                credentials = flow.run_local_server(port=0)

            with open(self.oauth_token_file, "w") as token:
                token.write(credentials.to_json())
            logger.info("New OAuth token saved.")

        self.credentials = credentials

    def read_sheet(self, spreadsheet_id: str, range_name: str) -> List[List[str]]:
        """
        Reads data from a specified range in a Google Spreadsheet.

        Args:
            spreadsheet_id: The ID of the spreadsheet.
            range_name: The A1 notation of the range to read.

        Returns:
            A list of lists representing the rows and columns of the specified range.
            Returns an empty list if no data is found.

        Raises:
            HttpError: If there is an error with the Google Sheets API request.
            Exception: If authentication has not been performed.
        """
        if not self.service:
            logger.error(
                "Authentication has not been performed. Call authenticate() first."
            )
            raise Exception("Authentication required before reading data.")
        try:
            sheet = self.service.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )
            values = result.get("values", [])
            logger.info(
                f"Successfully read data from spreadsheet {spreadsheet_id}, range {range_name}"
            )
            return values
        except HttpError as err:
            logger.error(f"Error reading from spreadsheet: {err}")
            raise


class RotaParser(GoogleSpreadsheetReader):
    """
    Parses staff rota data from a Google Spreadsheet.

    Inherits from GoogleSpreadsheetReader for authentication and data retrieval.
    Adds functionality to parse the rota data into a structured format.
    """

    def __init__(self, service_account_file: str, spreadsheet_id: str, range_name: str):
        """
        Initializes the RotaParser with the path to the service account file.

        Args:
            service_account_file: Path to the service account credentials file.
        """
        super().__init__(service_account_file=service_account_file)
        self.spreadsheet_id = spreadsheet_id
        self.range_name = range_name
        self.rota_data = self.get_rota_data()

    def get_rota_data(self) -> List[List[str]]:
        """
        Retrieves the rota data from the Google Spreadsheet.

        Returns:
            The rota data as a list of lists.
        """
        return self.read_sheet(
            spreadsheet_id=self.spreadsheet_id, range_name=self.range_name
        )

    def _parse_range(
        self, time_str: str, current_date: datetime
    ) -> Dict[str, datetime]:
        """
        Parses a time range string and returns start and end datetime objects.

        Args:
            time_str: String representing time range in various formats.
            current_date: Base date to combine with the parsed times.

        Returns:
            Dict containing 'start_date' and 'end_date' datetime objects.

        Raises:
            ValueError: If the time string is invalid or cannot be parsed.
        """
        invalid_strings = {
            "*n/a",
            "/",
        }

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
            r"(?:.*?\(?)?(\d{1,2})\s*-\s*(\d{1,2})\s*(pm)?\)?",
        ]

        for pattern in patterns:
            match = re.search(pattern, time_str, re.IGNORECASE)
            if match:
                groups = match.groups()
                start_str = groups[0]
                end_str = groups[1]
                is_pm = (
                    groups[2]
                    if len(groups) > 2 and groups[2] == "pm"
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
        """
        Parses the rota data and returns a list of shift dictionaries.

        Returns:
            List of dictionaries containing shift information.
        Example:
            [{
                "name": "Rachel",
                "date": "2025-07-10",
                "raw_data": "/",
                "shift_type": "not_available",
                "is_working": false
            },
            {
                "name": "Rachel",
                "date": "2025-07-11",
                "raw_data": "/",
                "shift_type": "not_available",
                "is_working": false
            },
            {
                "name": "Nicholas",
                "date": "2025-07-08",
                "raw_data": "0800-1700",
                "shift_type": "regular",
                "is_working": true,
                "start_date": "2025-07-08 08:00:00",
                "end_date": "2025-07-08 17:00:00"
            }]
        """
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

        for row in self.rota_data:
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
                logger.debug(
                    f"Current dates: {[d.strftime('%Y-%m-%d') if isinstance(d, datetime) else str(d) for d in current_dates]}"
                )
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
                if name == "Rachel":
                    logger.debug(
                        f"Current date: {current_date.strftime('%Y-%m-%d')} shift data: {shift_data}, i: {i}"
                    )

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


def test_parse_range():
    """Test cases for the _parse_range method."""
    parser = RotaParser(
        service_account_file=os.environ.get("SERVICE_ACCOUNT_FILE"),
        spreadsheet_id="your_spreadsheet_id",
        range_name="your_range_name",
    )
    now = datetime.now()

    valid_test_cases = [
        (
            "1600-0000",
            now,
            {
                "start_date": now.replace(hour=16, minute=0, second=0, microsecond=0),
                "end_date": now.replace(hour=0, minute=0, second=0, microsecond=0)
                + timedelta(days=1),
            },
        ),
        (
            "0800-1700",
            now,
            {
                "start_date": now.replace(hour=8, minute=0, second=0, microsecond=0),
                "end_date": now.replace(hour=17, minute=0, second=0, microsecond=0),
            },
        ),
        (
            "2200-0830",
            now,
            {
                "start_date": now.replace(hour=22, minute=0, second=0, microsecond=0),
                "end_date": now.replace(hour=8, minute=30, second=0, microsecond=0)
                + timedelta(days=1),
            },
        ),
        (
            "1200-2000",
            now,
            {
                "start_date": now.replace(hour=12, minute=0, second=0, microsecond=0),
                "end_date": now.replace(hour=20, minute=0, second=0, microsecond=0),
            },
        ),
        (
            "8-6pm",
            now,
            {
                "start_date": now.replace(hour=8, minute=0, second=0, microsecond=0),
                "end_date": now.replace(hour=18, minute=0, second=0, microsecond=0),
            },
        ),
        (
            "Zone 2 (8-6pm)",
            now,
            {
                "start_date": now.replace(hour=8, minute=0, second=0, microsecond=0),
                "end_date": now.replace(hour=18, minute=0, second=0, microsecond=0),
            },
        ),
        (
            "Zone 2 (10-7pm)",
            now,
            {
                "start_date": now.replace(hour=10, minute=0, second=0, microsecond=0),
                "end_date": now.replace(hour=19, minute=0, second=0, microsecond=0),
            },
        ),
        (
            "22.00 - 08.30",
            now,
            {
                "start_date": now.replace(hour=22, minute=0, second=0, microsecond=0),
                "end_date": now.replace(hour=8, minute=30, second=0, microsecond=0)
                + timedelta(days=1),
            },
        ),
        (
            "16:00-00:00",
            now,
            {
                "start_date": now.replace(hour=16, minute=0, second=0, microsecond=0),
                "end_date": now.replace(hour=0, minute=0, second=0, microsecond=0)
                + timedelta(days=1),
            },
        ),
    ]

    invalid_test_cases = [
        ("", now),
        ("off", now),
        ("ncd", now),
        ("al", now),
        ("post nights", now),
        ("pre night off", now),
        ("*n/a", now),
        ("/", now),
        ("some invalid string", now),
    ]

    for time_str, current_date, expected in valid_test_cases:
        result = parser._parse_range(time_str, current_date)
        assert (
            result == expected
        ), f"Failed for '{time_str}': expected {expected}, got {result}"

    for time_str, current_date in invalid_test_cases:
        with pytest.raises(ValueError):
            parser._parse_range(time_str, current_date)


if __name__ == "__main__":
    service_account_file = os.environ.get("SERVICE_ACCOUNT_FILE")
    # spreadsheet_id = "1AGJHWnPGumB-QbmrW97E1cvF_cJvUEJeZ57RZoVe77E" # Dev
    spreadsheet_id = "1MqJwH59lHhE6q0kmFNkQZzpteRLTQBlX2vKhEhVltHQ"
    range_name = "Combined Rota!A:M"

    if not service_account_file:
        logger.error("Error: The SERVICE_ACCOUNT_FILE environment variable is not set.")
        exit(1)

    parser = RotaParser(
        service_account_file=service_account_file,
        spreadsheet_id=spreadsheet_id,
        range_name=range_name,
    )
    parsed_rota = parser.parse_rota()
    pprint(
        sorted(
            [shift for shift in parsed_rota if shift["name"] == "Rachel"],
            key=lambda x: x["date"],
        )
    )
