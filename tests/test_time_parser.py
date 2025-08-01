"""Test time parser functionality."""

import pytest
from datetime import datetime

from swap.utils.time_parser import TimeParser


class TestTimeParser:
    """Test TimeParser class."""
    
    def test_parse_range_simple(self):
        """Test parsing simple time ranges."""
        parser = TimeParser()
        current_date = datetime(2024, 1, 15)
        
        # Test basic format
        result = parser.parse_range("09:00-17:00", current_date)
        
        assert result["start_date"].hour == 9
        assert result["start_date"].minute == 0
        assert result["end_date"].hour == 17
        assert result["end_date"].minute == 0
    
    def test_parse_range_with_pm(self):
        """Test parsing time ranges with PM."""
        parser = TimeParser()
        current_date = datetime(2024, 1, 15)
        
        result = parser.parse_range("2-6 pm", current_date)
        
        assert result["start_date"].hour == 2
        assert result["end_date"].hour == 18  # 6 PM = 18:00
    
    def test_parse_range_invalid(self):
        """Test parsing invalid time ranges."""
        parser = TimeParser()
        current_date = datetime(2024, 1, 15)
        
        with pytest.raises(ValueError):
            parser.parse_range("invalid", current_date)
        
        with pytest.raises(ValueError):
            parser.parse_range("", current_date)
    
    def test_parse_date(self):
        """Test date parsing."""
        parser = TimeParser()
        
        result = parser.parse_date("Mon 15 Jan")
        assert result.day == 15
        assert result.month == 1
    
    def test_is_date_row(self):
        """Test date row detection."""
        parser = TimeParser()
        
        # Should detect date row
        date_row = ["Mon 15 Jan", "Tue 16 Jan", "Wed 17 Jan", "Thu 18 Jan"]
        assert parser.is_date_row(date_row) is True
        
        # Should not detect non-date row
        non_date_row = ["Name", "AL", "OFF", "9-5"]
        assert parser.is_date_row(non_date_row) is False
