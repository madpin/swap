"""Google Sheets service for reading spreadsheet data."""

from typing import List
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config.logging import get_logger

logger = get_logger(__name__)


class SheetsService:
    """Service for interacting with Google Sheets API."""
    
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    
    def __init__(self, service_account_file: str):
        """Initialize the service with credentials."""
        self.service_account_file = service_account_file
        self._service = None
    
    @property
    def service(self):
        """Lazy-load the Google Sheets service."""
        if self._service is None:
            self._service = self._build_service()
        return self._service
    
    def _build_service(self):
        """Build and return a Sheets service object."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=self.SCOPES
            )
            return build("sheets", "v4", credentials=credentials)
        except Exception as e:
            logger.error(f"Failed to build Sheets service: {e}")
            raise
    
    def read_sheet(self, spreadsheet_id: str, range_name: str) -> List[List[str]]:
        """Read data from specified range in a Google Spreadsheet."""
        try:
            logger.info(f"Reading spreadsheet {spreadsheet_id}, range: {range_name}")
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )
            values = result.get("values", [])
            logger.info(f"Retrieved {len(values)} rows from spreadsheet")
            return values
        except HttpError as err:
            logger.error(f"Error reading from spreadsheet: {err}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error reading spreadsheet: {e}")
            raise
