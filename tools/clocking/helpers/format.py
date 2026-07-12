from datetime import datetime
from pathlib import Path

def format_week_id(value: datetime) -> str:
    """
    # Returns the ISO 8601 format of the current week.
    """
    year, week, day = value.isocalendar()
    return f"{year}-W{week:02d}"