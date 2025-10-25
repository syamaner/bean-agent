"""Tests for roast tracker - T0 detection, RoR, development time."""
import pytest
from datetime import datetime, UTC, timedelta
import sys
sys.path.insert(0, 'src')

from src.mcp_servers.roaster_control.roast_tracker import RoastTracker
from src.mcp_servers.roaster_control.models import SensorReading, TrackerConfig


class TestT0Detection:
    """Test bean addition detection (T0)."""
    
    def setup_method(self):
        """Setup tracker with default config."""
        config = TrackerConfig(t0_detection_threshold=10.0)
        self.tracker = RoastTracker(config)
    
    def test_t0_not_detected_initially(self):
        """Test T0 is None initially."""
        assert self.tracker.get_t0() is None
    
    def test_t0_detected_on_temperature_drop(self):
        """Test T0 detected when temp drops >10°C."""
        # Preheat phase
        reading1 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=170.0,
            chamber_temp_c=180.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading1)
        assert self.tracker.get_t0() is None
        
        # Beans added - temp drops
        reading2 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=155.0,  # Dropped 15°C
            chamber_temp_c=175.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading2)
        
        # T0 should be detected
        assert self.tracker.get_t0() is not None
        assert self.tracker.get_beans_added_temp() == 170.0
    
    def test_t0_not_detected_on_small_drop(self):
        """Test T0 not detected for small temperature drops."""
        reading1 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=170.0,
            chamber_temp_c=180.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading1)
        
        reading2 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=165.0,  # Only 5°C drop
            chamber_temp_c=175.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading2)
        
        assert self.tracker.get_t0() is None
    
    def test_t0_only_detected_once(self):
        """Test T0 is only detected once."""
        # First detection
        reading1 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=170.0,
            chamber_temp_c=180.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading1)
        
        reading2 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=150.0,
            chamber_temp_c=175.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading2)
        
        t0_first = self.tracker.get_t0()
        
        # Another big drop (shouldn't change T0)
        reading3 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=130.0,  # Another big drop
            chamber_temp_c=170.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading3)
        
        assert self.tracker.get_t0() == t0_first
    
    def test_beans_added_temp_is_none_before_t0(self):
        """Test beans_added_temp is None before T0."""
        assert self.tracker.get_beans_added_temp() is None
    
    def test_beans_added_temp_captured_correctly(self):
        """Test beans_added_temp captures the pre-drop temperature."""
        # High temp
        reading1 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=175.5,
            chamber_temp_c=185.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading1)
        
        # Beans added
        reading2 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=160.0,
            chamber_temp_c=180.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading2)
        
        assert self.tracker.get_beans_added_temp() == 175.5