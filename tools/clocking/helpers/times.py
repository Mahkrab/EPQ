from zoneinfo import ZoneInfo
from datetime import datetime
import os

def local_tz() -> ZoneInfo: 
    """
    Returns the local timezone from the environment variable `EPQ_CLOCK_TZ`, defaults to Europe/London.
    """
    return ZoneInfo(os.environ.get("EPQ_CLOCK_TZ", "Europe/London"))

def now() -> datetime: 
    """
    Returns the `datetime` of the current timezone. 
    """
    return datetime.now(local_tz())