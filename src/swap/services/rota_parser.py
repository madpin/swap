"""Rota parsing service for processing shift data from spreadsheets."""

from typing import List, Dict, Any
from datetime import datetime, timedelta

from .sheets_service import SheetsService
from ..utils.time_parser import TimeParser
from ..utils.validators import validate_shift_data
from ..config.logging import get_logger

logger = get_logger(__name__)


class RotaParser:
    """Service for parsing staff rota data from Google Spreadsheets."""
    
    # Special shift type mappings
    SPECIAL_CASES = {
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
    
    def __init__(self, sheets_service: SheetsService):
        """Initialize with a sheets service."""
        self.sheets_service = sheets_service
        self.time_parser = TimeParser()
    
    def parse_rota(
        self, spreadsheet_id: str, range_name: str, include_past_days: int = 30
    ) -> List[Dict[str, Any]]:
        """Parse rota data and return a list of shift dictionaries."""
        data = self.sheets_service.read_sheet(spreadsheet_id, range_name)
        logger.info(f"Retrieved {len(data)} rows from spreadsheet")
        
        shifts = []
        current_dates = []
        after_cutoff = False
        cutoff_date = datetime.now() - timedelta(days=include_past_days)
        
        for row in data:
            if not row or len(row) < 3:
                continue
            
            # Check if this is a date row
            if self.time_parser.is_date_row(row):
                logger.debug(f"Found date row: {row[:7]}...")
                current_dates = self._parse_date_row(row)
                
                # Check if we have any dates after cutoff
                for date in current_dates:
                    if date and date >= cutoff_date:
                        after_cutoff = True
                        break
                continue
            
            # Skip rows before we find recent dates
            if not after_cutoff:
                continue
            
            # Skip changeover rows or empty name rows
            if self._should_skip_row(row):
                continue
            
            # Extract name and process shifts for this person
            name = self._extract_name(row[1])
            if not name:
                continue
            
            logger.debug(f"Processing shifts for: '{name}'")
            
            # Process each shift in the row
            for i, shift_data in enumerate(row):
                if i >= len(current_dates) or not current_dates[i]:
                    continue
                
                try:
                    shift = self._parse_shift(name, current_dates[i], shift_data)
                    if shift:
                        validate_shift_data(shift)
                        shifts.append(shift)
                except (ValueError, Exception) as e:
                    logger.warning(f"Failed to parse shift for {name} on {current_dates[i]}: {e}")
                    continue
        
        logger.info(f"Parsed {len(shifts)} valid shifts from rota")
        return shifts
    
    def _parse_date_row(self, row: List[str]) -> List[datetime]:
        """Parse a row containing dates."""
        dates = []
        for cell in row:
            try:
                parsed_date = self.time_parser.parse_date(cell)
                dates.append(parsed_date)
            except (AttributeError, ValueError):
                dates.append(None)
        return dates
    
    def _should_skip_row(self, row: List[str]) -> bool:
        """Check if row should be skipped."""
        if "Changeover" in str(row[0]):
            return True
        if not row[1].strip() or len(row) < 3:
            return True
        return False
    
    def _extract_name(self, name_cell: str) -> str:
        """Extract clean name from cell."""
        return "".join(char for char in name_cell if char.isalpha())
    
    def _parse_shift(self, name: str, date: datetime, shift_data: str) -> Dict[str, Any]:
        """Parse a single shift entry."""
        shift_data = shift_data.strip()
        
        if not shift_data:
            return None
        
        shift_entry = {
            "name": name,
            "date": date.strftime("%Y-%m-%d"),
            "raw_data": shift_data,
            "shift_type": "regular",
            "is_working": True,
        }
        
        # Check for special cases first
        upper_shift = shift_data.upper()
        if upper_shift in self.SPECIAL_CASES:
            shift_type, is_working = self.SPECIAL_CASES[upper_shift]
            shift_entry["shift_type"] = shift_type
            shift_entry["is_working"] = is_working
            return shift_entry
        
        # Try to parse time range for working shifts
        try:
            time_range = self.time_parser.parse_range(shift_data, date)
            shift_entry.update({
                "start_date": time_range["start_date"].strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": time_range["end_date"].strftime("%Y-%m-%d %H:%M:%S"),
            })
            return shift_entry
        except ValueError:
            # If we can't parse time but it's not a special case,
            # treat as a working day without specific times (like training)
            if shift_entry["is_working"]:
                shift_entry["shift_type"] = "training"  # Or other appropriate type
            return shift_entry
