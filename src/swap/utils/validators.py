"""Data validation utilities."""

from typing import Dict, Any, List
from datetime import datetime


def validate_shift_data(shift_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize shift data."""
    required_fields = ["name", "date", "raw_data", "shift_type", "is_working"]
    
    for field in required_fields:
        if field not in shift_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate name
    if not shift_data["name"] or not isinstance(shift_data["name"], str):
        raise ValueError("Name must be a non-empty string")
    
    # Validate date format
    try:
        datetime.strptime(shift_data["date"], "%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format")
    
    # Validate shift_type
    valid_shift_types = {
        "regular", "annual_leave", "off", "non_clinical_day", 
        "post_nights", "pre_night", "training", "not_available"
    }
    if shift_data["shift_type"] not in valid_shift_types:
        raise ValueError(f"Invalid shift_type: {shift_data['shift_type']}")
    
    # Validate working shifts have time data
    if shift_data["is_working"] and shift_data["shift_type"] == "regular":
        if not shift_data.get("start_date") or not shift_data.get("end_date"):
            raise ValueError("Working shifts must have start_date and end_date")
        
        # Validate datetime format
        try:
            datetime.strptime(shift_data["start_date"], "%Y-%m-%d %H:%M:%S")
            datetime.strptime(shift_data["end_date"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError("start_date and end_date must be in 'YYYY-MM-DD HH:MM:SS' format")
    
    return shift_data


def validate_user_config(user_config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user configuration."""
    required_fields = ["calendar_name", "user_name", "emails_to_share"]
    
    for field in required_fields:
        if field not in user_config:
            raise ValueError(f"Missing required field: {field}")
    
    if not isinstance(user_config["emails_to_share"], list):
        raise ValueError("emails_to_share must be a list")
    
    if not user_config["emails_to_share"]:
        raise ValueError("emails_to_share cannot be empty")
    
    # Validate email format (basic)
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    for email in user_config["emails_to_share"]:
        if not re.match(email_pattern, email):
            raise ValueError(f"Invalid email format: {email}")
    
    return user_config
