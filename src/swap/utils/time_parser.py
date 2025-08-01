"""Time parsing utilities extracted from original parser."""

import re
from datetime import datetime, timedelta
from typing import Dict, Tuple


class TimeParser:
    """Handles parsing of time ranges and date strings."""
    
    @staticmethod
    def parse_range(time_str: str, current_date: datetime) -> Dict[str, datetime]:
        """Parse a time range string and return start and end datetime objects."""
        invalid_strings = {"*n/a", "/", ""}
        
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
    
    @staticmethod
    def parse_date(date_str: str) -> datetime:
        """Parse various date formats."""
        date_formats = [
            "%a %d %b",
            "%B %d",
            "%d %B",
            "%d/%m",
            "%d-%m",
            "%d-%b",
        ]
        
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), date_format)
                
                # Handle year assignment logic
                current_date = datetime.now()
                target_date = parsed_date.replace(year=current_date.year)
                
                # If date is more than 3 months ago, assume next year
                three_months_ago = current_date - timedelta(days=90)
                if target_date < three_months_ago:
                    target_date = parsed_date.replace(year=current_date.year + 1)
                
                return target_date
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse date: {date_str}")
    
    @staticmethod
    def is_date_row(row: list) -> bool:
        """Check if row contains dates."""
        date_count = 0
        for cell in row:
            try:
                TimeParser.parse_date(cell)
                date_count += 1
            except (AttributeError, ValueError):
                continue
        return date_count >= 3
