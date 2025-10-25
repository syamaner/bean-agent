"""
Utility functions for timezone handling, formatting, and logging.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Union
import logging
import time


def get_local_timezone() -> ZoneInfo:
    """
    Get the system's local timezone.
    
    Returns:
        ZoneInfo: System local timezone
    """
    # Use datetime's astimezone() to get local timezone info
    # Then extract the timezone key properly
    import datetime as dt_module
    local_dt = dt_module.datetime.now().astimezone()
    
    # The tzinfo object has a .key attribute for ZoneInfo objects
    if hasattr(local_dt.tzinfo, 'key'):
        return ZoneInfo(local_dt.tzinfo.key)
    
    # Fallback: try common methods to get timezone
    # Use /etc/localtime symlink on Unix systems
    try:
        import os
        if os.path.exists('/etc/localtime'):
            tz_path = os.path.realpath('/etc/localtime')
            # Extract timezone from path like /usr/share/zoneinfo/America/New_York
            if 'zoneinfo/' in tz_path:
                tz_key = tz_path.split('zoneinfo/')[-1]
                return ZoneInfo(tz_key)
    except Exception:
        pass
    
    # Last resort: return UTC if we can't determine local timezone
    import datetime as dt_module
    from datetime import timezone as dt_timezone
    return ZoneInfo('UTC')


def to_local_time(dt: datetime) -> datetime:
    """
    Convert a UTC datetime to local timezone.
    
    Args:
        dt: Datetime to convert (should be UTC)
        
    Returns:
        datetime: Datetime in local timezone
    """
    local_tz = get_local_timezone()
    return dt.astimezone(local_tz)


def format_elapsed_time(seconds: Union[int, float]) -> str:
    """
    Format elapsed seconds as MM:SS.
    
    Args:
        seconds: Elapsed time in seconds
        
    Returns:
        str: Formatted time string (MM:SS)
    """
    # Convert to integer (rounds down)
    total_seconds = int(seconds)
    
    minutes = total_seconds // 60
    remaining_seconds = total_seconds % 60
    
    return f"{minutes:02d}:{remaining_seconds:02d}"


def setup_logging(config) -> None:
    """
    Configure logging based on server configuration.
    
    Args:
        config: ServerConfig instance with log_level
    """
    # Convert string log level to logging constant
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure the logger for this module/package
    logger = logging.getLogger("src.mcp_servers.first_crack_detection")
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False
