"""Utility functions for roaster control."""
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Tuple


def format_time(seconds: int) -> str:
    """Format seconds as MM:SS.
    
    Args:
        seconds: Total seconds
    
    Returns:
        Formatted string as MM:SS
    
    Example:
        >>> format_time(125)
        '02:05'
    """
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def get_timestamps(dt: datetime, timezone: str) -> Tuple[datetime, datetime]:
    """Get UTC and local timestamps.
    
    Args:
        dt: Datetime object (with or without timezone)
        timezone: Target timezone string (e.g. 'America/Los_Angeles')
    
    Returns:
        Tuple of (utc_time, local_time)
    """
    utc_time = dt if dt.tzinfo else dt.replace(tzinfo=ZoneInfo("UTC"))
    local_time = utc_time.astimezone(ZoneInfo(timezone))
    return utc_time, local_time