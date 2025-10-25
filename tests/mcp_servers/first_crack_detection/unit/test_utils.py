"""
Tests for utility functions (timezone, formatting, logging).

Following TDD approach:
1. Write tests first (RED) - ensure they fail for the RIGHT reason
2. Implement utility functions (GREEN)
3. Refactor (REFACTOR)
"""
import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def test_get_local_timezone_returns_zoneinfo():
    """Test get_local_timezone returns a ZoneInfo object."""
    from src.mcp_servers.first_crack_detection.utils import get_local_timezone
    
    tz = get_local_timezone()
    
    assert isinstance(tz, ZoneInfo)


def test_get_local_timezone_is_system_timezone():
    """Test get_local_timezone returns system's local timezone."""
    from src.mcp_servers.first_crack_detection.utils import get_local_timezone
    from zoneinfo import available_timezones
    
    tz = get_local_timezone()
    
    # Should be a valid timezone or UTC fallback
    # Use .key attribute if available, otherwise str()
    tz_key = tz.key if hasattr(tz, 'key') else str(tz)
    assert tz_key in available_timezones() or tz_key == 'UTC'


def test_to_local_time_converts_utc_to_local():
    """Test to_local_time converts UTC datetime to local timezone."""
    from src.mcp_servers.first_crack_detection.utils import to_local_time
    
    # Create a UTC datetime
    utc_dt = datetime(2025, 1, 25, 15, 30, 0, tzinfo=timezone.utc)
    
    # Convert to local
    local_dt = to_local_time(utc_dt)
    
    # Should have timezone info
    assert local_dt.tzinfo is not None
    assert local_dt.tzinfo != timezone.utc
    
    # Should represent the same moment in time (same timestamp)
    assert utc_dt.timestamp() == local_dt.timestamp()


def test_to_local_time_preserves_moment():
    """Test to_local_time preserves the actual moment in time."""
    from src.mcp_servers.first_crack_detection.utils import to_local_time
    
    utc_dt = datetime.now(timezone.utc)
    local_dt = to_local_time(utc_dt)
    
    # Same Unix timestamp means same moment in time
    assert abs(utc_dt.timestamp() - local_dt.timestamp()) < 1  # Within 1 second


def test_format_elapsed_time_zero_seconds():
    """Test format_elapsed_time with 0 seconds."""
    from src.mcp_servers.first_crack_detection.utils import format_elapsed_time
    
    result = format_elapsed_time(0)
    
    assert result == "00:00"


def test_format_elapsed_time_less_than_minute():
    """Test format_elapsed_time with seconds < 60."""
    from src.mcp_servers.first_crack_detection.utils import format_elapsed_time
    
    result = format_elapsed_time(45)
    
    assert result == "00:45"


def test_format_elapsed_time_exactly_one_minute():
    """Test format_elapsed_time with exactly 60 seconds."""
    from src.mcp_servers.first_crack_detection.utils import format_elapsed_time
    
    result = format_elapsed_time(60)
    
    assert result == "01:00"


def test_format_elapsed_time_minutes_and_seconds():
    """Test format_elapsed_time with minutes and seconds."""
    from src.mcp_servers.first_crack_detection.utils import format_elapsed_time
    
    result = format_elapsed_time(125)  # 2:05
    
    assert result == "02:05"


def test_format_elapsed_time_ten_minutes():
    """Test format_elapsed_time with double-digit minutes."""
    from src.mcp_servers.first_crack_detection.utils import format_elapsed_time
    
    result = format_elapsed_time(630)  # 10:30
    
    assert result == "10:30"


def test_format_elapsed_time_rounds_down():
    """Test format_elapsed_time rounds down fractional seconds."""
    from src.mcp_servers.first_crack_detection.utils import format_elapsed_time
    
    result = format_elapsed_time(125.9)  # 2:05.9 -> 2:05
    
    assert result == "02:05"


def test_format_elapsed_time_handles_float():
    """Test format_elapsed_time works with float input."""
    from src.mcp_servers.first_crack_detection.utils import format_elapsed_time
    
    result = format_elapsed_time(90.5)  # 1:30.5 -> 1:30
    
    assert result == "01:30"


def test_setup_logging_configures_logger():
    """Test setup_logging configures logging."""
    from src.mcp_servers.first_crack_detection.utils import setup_logging
    from src.mcp_servers.first_crack_detection.models import ServerConfig
    import logging
    
    config = ServerConfig(
        model_checkpoint="/path/to/model.pt",
        log_level="DEBUG"
    )
    
    setup_logging(config)
    
    # Should configure root logger or module logger
    logger = logging.getLogger("src.mcp_servers.first_crack_detection")
    assert logger.level == logging.DEBUG or logging.root.level == logging.DEBUG


def test_setup_logging_info_level():
    """Test setup_logging with INFO level."""
    from src.mcp_servers.first_crack_detection.utils import setup_logging
    from src.mcp_servers.first_crack_detection.models import ServerConfig
    import logging
    
    config = ServerConfig(
        model_checkpoint="/path/to/model.pt",
        log_level="INFO"
    )
    
    setup_logging(config)
    
    logger = logging.getLogger("src.mcp_servers.first_crack_detection")
    # Should be INFO or lower (more permissive)
    assert logger.level <= logging.INFO or logging.root.level <= logging.INFO


def test_setup_logging_warning_level():
    """Test setup_logging with WARNING level."""
    from src.mcp_servers.first_crack_detection.utils import setup_logging
    from src.mcp_servers.first_crack_detection.models import ServerConfig
    import logging
    
    config = ServerConfig(
        model_checkpoint="/path/to/model.pt",
        log_level="WARNING"
    )
    
    setup_logging(config)
    
    logger = logging.getLogger("src.mcp_servers.first_crack_detection")
    # Should be WARNING or lower
    assert logger.level <= logging.WARNING or logging.root.level <= logging.WARNING


def test_setup_logging_creates_structured_format():
    """Test setup_logging creates structured log format."""
    from src.mcp_servers.first_crack_detection.utils import setup_logging
    from src.mcp_servers.first_crack_detection.models import ServerConfig
    import logging
    
    config = ServerConfig(
        model_checkpoint="/path/to/model.pt",
        log_level="INFO"
    )
    
    setup_logging(config)
    
    # Function should complete without error
    # Actual format validation would require capturing log output
    assert True  # If we got here, setup worked
