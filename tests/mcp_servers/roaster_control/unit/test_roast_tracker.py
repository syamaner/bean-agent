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


class TestRateOfRise:
    """Test Rate of Rise (RoR) calculation."""
    
    def setup_method(self):
        """Setup tracker with default config."""
        config = TrackerConfig(ror_window_size=60)
        self.tracker = RoastTracker(config)
    
    def test_ror_is_none_initially(self):
        """Test RoR is None with insufficient data."""
        assert self.tracker.get_rate_of_rise() is None
    
    def test_ror_is_none_with_one_reading(self):
        """Test RoR is None with only one reading."""
        reading = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=150.0,
            chamber_temp_c=160.0,
            fan_speed_percent=50,
            heat_level_percent=80
        )
        self.tracker.update(reading)
        assert self.tracker.get_rate_of_rise() is None
    
    def test_ror_calculated_with_two_readings(self):
        """Test RoR calculated with minimum 2 readings."""
        base_time = datetime.now(UTC)
        
        # First reading at T=0s
        reading1 = SensorReading(
            timestamp=base_time,
            bean_temp_c=150.0,
            chamber_temp_c=160.0,
            fan_speed_percent=50,
            heat_level_percent=80
        )
        self.tracker.update(reading1)
        
        # Second reading at T=60s, temp increased 10°C
        reading2 = SensorReading(
            timestamp=base_time + timedelta(seconds=60),
            bean_temp_c=160.0,
            chamber_temp_c=170.0,
            fan_speed_percent=50,
            heat_level_percent=80
        )
        self.tracker.update(reading2)
        
        # RoR should be 10°C/min
        ror = self.tracker.get_rate_of_rise()
        assert ror is not None
        assert abs(ror - 10.0) < 0.1
    
    def test_ror_with_partial_window(self):
        """Test RoR with less than 60 seconds of data."""
        base_time = datetime.now(UTC)
        
        # Two readings 30 seconds apart, 5°C rise
        reading1 = SensorReading(
            timestamp=base_time,
            bean_temp_c=150.0,
            chamber_temp_c=160.0,
            fan_speed_percent=50,
            heat_level_percent=80
        )
        self.tracker.update(reading1)
        
        reading2 = SensorReading(
            timestamp=base_time + timedelta(seconds=30),
            bean_temp_c=155.0,
            chamber_temp_c=165.0,
            fan_speed_percent=50,
            heat_level_percent=80
        )
        self.tracker.update(reading2)
        
        # RoR = (5°C / 30s) * 60s/min = 10°C/min
        ror = self.tracker.get_rate_of_rise()
        assert ror is not None
        assert abs(ror - 10.0) < 0.1
    
    def test_ror_with_full_60_second_window(self):
        """Test RoR uses oldest reading in 60-second window."""
        base_time = datetime.now(UTC)
        
        # Add readings every 10 seconds for 70 seconds
        temps = [150.0, 152.0, 154.0, 156.0, 158.0, 160.0, 162.0, 164.0]
        for i, temp in enumerate(temps):
            reading = SensorReading(
                timestamp=base_time + timedelta(seconds=i * 10),
                bean_temp_c=temp,
                chamber_temp_c=temp + 10,
                fan_speed_percent=50,
                heat_level_percent=80
            )
            self.tracker.update(reading)
        
        # Last reading is at 70s (164°C)
        # Oldest in window is at 10s (152°C) - 60 readings max
        # RoR = (164 - 152) / 60s * 60s/min = 12°C/min
        ror = self.tracker.get_rate_of_rise()
        assert ror is not None
        assert abs(ror - 12.0) < 0.5
    
    def test_ror_with_negative_rate(self):
        """Test RoR can be negative (temperature dropping)."""
        base_time = datetime.now(UTC)
        
        reading1 = SensorReading(
            timestamp=base_time,
            bean_temp_c=180.0,
            chamber_temp_c=190.0,
            fan_speed_percent=80,
            heat_level_percent=0
        )
        self.tracker.update(reading1)
        
        # Temperature dropped 10°C in 60s
        reading2 = SensorReading(
            timestamp=base_time + timedelta(seconds=60),
            bean_temp_c=170.0,
            chamber_temp_c=180.0,
            fan_speed_percent=80,
            heat_level_percent=0
        )
        self.tracker.update(reading2)
        
        ror = self.tracker.get_rate_of_rise()
        assert ror is not None
        assert abs(ror - (-10.0)) < 0.1
    
    def test_ror_with_zero_rate(self):
        """Test RoR when temperature is stable."""
        base_time = datetime.now(UTC)
        
        reading1 = SensorReading(
            timestamp=base_time,
            bean_temp_c=180.0,
            chamber_temp_c=190.0,
            fan_speed_percent=50,
            heat_level_percent=50
        )
        self.tracker.update(reading1)
        
        reading2 = SensorReading(
            timestamp=base_time + timedelta(seconds=60),
            bean_temp_c=180.0,  # Same temp
            chamber_temp_c=190.0,
            fan_speed_percent=50,
            heat_level_percent=50
        )
        self.tracker.update(reading2)
        
        ror = self.tracker.get_rate_of_rise()
        assert ror is not None
        assert abs(ror - 0.0) < 0.1
