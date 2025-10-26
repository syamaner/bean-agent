"""Tests for data models."""
import pytest
from datetime import datetime, UTC
from pydantic import ValidationError

from src.mcp_servers.roaster_control.models import (
    SensorReading,
    RoastMetrics,
    RoastStatus,
    HardwareConfig,
    TrackerConfig,
    ServerConfig,
)


class TestSensorReading:
    """Test SensorReading model."""
    
    def test_valid_reading(self):
        """Test valid sensor reading creation."""
        reading = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=185.5,
            chamber_temp_c=195.0,
            fan_speed_percent=70,
            heat_level_percent=60
        )
        assert reading.bean_temp_c == 185.5
        assert reading.chamber_temp_c == 195.0
        assert reading.fan_speed_percent == 70
        assert reading.heat_level_percent == 60
    
    def test_temperature_validation_too_low(self):
        """Test temperature below valid range."""
        with pytest.raises(ValidationError):
            SensorReading(
                timestamp=datetime.now(UTC),
                bean_temp_c=-100,  # Invalid
                chamber_temp_c=195.0,
                fan_speed_percent=70,
                heat_level_percent=60
            )
    
    def test_temperature_validation_too_high(self):
        """Test temperature above valid range."""
        with pytest.raises(ValidationError):
            SensorReading(
                timestamp=datetime.now(UTC),
                bean_temp_c=400,  # Invalid
                chamber_temp_c=195.0,
                fan_speed_percent=70,
                heat_level_percent=60
            )
    
    def test_percentage_validation_negative(self):
        """Test negative percentage."""
        with pytest.raises(ValidationError):
            SensorReading(
                timestamp=datetime.now(UTC),
                bean_temp_c=185.5,
                chamber_temp_c=195.0,
                fan_speed_percent=-10,  # Invalid
                heat_level_percent=60
            )
    
    def test_percentage_validation_too_high(self):
        """Test percentage above 100."""
        with pytest.raises(ValidationError):
            SensorReading(
                timestamp=datetime.now(UTC),
                bean_temp_c=185.5,
                chamber_temp_c=195.0,
                fan_speed_percent=150,  # Invalid
                heat_level_percent=60
            )


class TestRoastMetrics:
    """Test RoastMetrics model."""
    
    def test_all_none_initially(self):
        """Test metrics can be all None initially."""
        metrics = RoastMetrics()
        assert metrics.roast_elapsed_seconds is None
        assert metrics.roast_elapsed_display is None
        assert metrics.rate_of_rise_c_per_min is None
        assert metrics.beans_added_temp_c is None
        assert metrics.first_crack_temp_c is None
        assert metrics.development_time_percent is None
    
    def test_partial_metrics(self):
        """Test partial metrics (some None, some values)."""
        metrics = RoastMetrics(
            roast_elapsed_seconds=300,
            roast_elapsed_display="05:00",
            rate_of_rise_c_per_min=12.5,
            beans_added_temp_c=170.0
        )
        assert metrics.roast_elapsed_seconds == 300
        assert metrics.roast_elapsed_display == "05:00"
        assert metrics.rate_of_rise_c_per_min == 12.5
        assert metrics.beans_added_temp_c == 170.0
        assert metrics.first_crack_temp_c is None
    
    def test_complete_metrics(self):
        """Test complete roast metrics."""
        metrics = RoastMetrics(
            roast_elapsed_seconds=600,
            roast_elapsed_display="10:00",
            rate_of_rise_c_per_min=10.0,
            beans_added_temp_c=170.0,
            first_crack_temp_c=195.0,
            first_crack_time_display="08:23",
            development_time_seconds=97,
            development_time_display="01:37",
            development_time_percent=16.2,
            total_roast_duration_seconds=600
        )
        assert metrics.roast_elapsed_seconds == 600
        assert metrics.development_time_percent == 16.2
        assert metrics.total_roast_duration_seconds == 600


class TestHardwareConfig:
    """Test HardwareConfig model."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = HardwareConfig()
        assert config.port == "/dev/tty.usbserial-DN016OJ3"
        assert config.baud_rate == 115200
        assert config.timeout == 1.0
        assert config.mock_mode is False  # Default is real hardware (tests force mock via env)
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = HardwareConfig(
            port="/dev/cu.usbserial-custom",
            baud_rate=9600,
            timeout=2.0,
            mock_mode=False
        )
        assert config.port == "/dev/cu.usbserial-custom"
        assert config.baud_rate == 9600
        assert config.timeout == 2.0
        assert config.mock_mode is False


class TestTrackerConfig:
    """Test TrackerConfig model."""
    
    def test_default_values(self):
        """Test default tracker configuration."""
        config = TrackerConfig()
        assert config.t0_detection_threshold == 10.0
        assert config.polling_interval == 1.0
        assert config.ror_window_size == 60
        assert config.development_time_target_min == 15.0
        assert config.development_time_target_max == 20.0
    
    def test_custom_threshold(self):
        """Test custom T0 detection threshold."""
        config = TrackerConfig(t0_detection_threshold=15.0)
        assert config.t0_detection_threshold == 15.0
    
    def test_custom_dev_time_targets(self):
        """Test custom development time targets."""
        config = TrackerConfig(
            development_time_target_min=12.0,
            development_time_target_max=18.0
        )
        assert config.development_time_target_min == 12.0
        assert config.development_time_target_max == 18.0


class TestServerConfig:
    """Test ServerConfig model."""
    
    def test_default_values(self):
        """Test default server configuration."""
        config = ServerConfig()
        assert isinstance(config.hardware, HardwareConfig)
        assert isinstance(config.tracker, TrackerConfig)
        assert config.logging_level == "INFO"
        assert config.timezone == "America/Los_Angeles"
    
    def test_nested_config(self):
        """Test nested configuration."""
        config = ServerConfig(
            hardware=HardwareConfig(port="/dev/custom", mock_mode=False),
            tracker=TrackerConfig(t0_detection_threshold=12.0),
            logging_level="DEBUG",
            timezone="UTC"
        )
        assert config.hardware.port == "/dev/custom"
        assert config.hardware.mock_mode is False
        assert config.tracker.t0_detection_threshold == 12.0
        assert config.logging_level == "DEBUG"
        assert config.timezone == "UTC"


class TestRoastStatus:
    """Test RoastStatus model."""
    
    def test_minimal_status(self):
        """Test minimal status (not roasting)."""
        status = RoastStatus(
            session_active=False,
            roaster_running=False,
            timestamps={},
            sensors=SensorReading(
                timestamp=datetime.now(UTC),
                bean_temp_c=20.0,
                chamber_temp_c=20.0,
                fan_speed_percent=0,
                heat_level_percent=0
            ),
            metrics=RoastMetrics(),
            connection={"status": "connected"}
        )
        assert status.session_active is False
        assert status.roaster_running is False
        assert status.sensors.bean_temp_c == 20.0
    
    def test_active_roast_status(self):
        """Test status during active roast."""
        status = RoastStatus(
            session_active=True,
            roaster_running=True,
            timestamps={
                "session_start": datetime.now(UTC).isoformat(),
                "beans_added": datetime.now(UTC).isoformat()
            },
            sensors=SensorReading(
                timestamp=datetime.now(UTC),
                bean_temp_c=185.0,
                chamber_temp_c=195.0,
                fan_speed_percent=70,
                heat_level_percent=60
            ),
            metrics=RoastMetrics(
                roast_elapsed_seconds=480,
                roast_elapsed_display="08:00",
                rate_of_rise_c_per_min=12.5
            ),
            connection={"status": "connected", "port": "/dev/tty.usbserial-1420"}
        )
        assert status.session_active is True
        assert status.roaster_running is True
        assert status.metrics.roast_elapsed_seconds == 480
        assert status.connection["status"] == "connected"