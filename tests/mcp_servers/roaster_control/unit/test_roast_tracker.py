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


class TestDevelopmentTime:
    """Test development time tracking (first crack to drop)."""
    
    def setup_method(self):
        """Setup tracker."""
        config = TrackerConfig()
        self.tracker = RoastTracker(config)
    
    def test_first_crack_not_reported_initially(self):
        """Test first crack is None initially."""
        assert self.tracker.get_first_crack() is None
    
    def test_report_first_crack(self):
        """Test reporting first crack (called by agent)."""
        fc_time = datetime.now(UTC)
        self.tracker.report_first_crack(fc_time, 205.5)
        
        assert self.tracker.get_first_crack() == fc_time
        assert self.tracker.get_first_crack_temp() == 205.5
    
    def test_first_crack_reported_once(self):
        """Test first crack only reported once (idempotent)."""
        fc_time1 = datetime.now(UTC)
        self.tracker.report_first_crack(fc_time1, 205.0)
        
        # Agent tries to report again (shouldn't happen, but handle it)
        fc_time2 = datetime.now(UTC) + timedelta(seconds=30)
        self.tracker.report_first_crack(fc_time2, 210.0)
        
        # Should still be first report
        assert self.tracker.get_first_crack() == fc_time1
        assert self.tracker.get_first_crack_temp() == 205.0
    
    def test_development_time_none_before_first_crack(self):
        """Test development time is None before agent reports first crack."""
        assert self.tracker.get_development_time_seconds() is None
    
    def test_development_time_calculated_after_first_crack(self):
        """Test development time calculated from first crack to current."""
        # Simulate T0
        base_time = datetime.now(UTC)
        reading1 = SensorReading(
            timestamp=base_time,
            bean_temp_c=170.0,
            chamber_temp_c=180.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading1)
        
        reading2 = SensorReading(
            timestamp=base_time + timedelta(seconds=1),
            bean_temp_c=150.0,  # T0 detected
            chamber_temp_c=175.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading2)
        
        # Agent reports first crack at T+480s (8 minutes)
        fc_time = base_time + timedelta(seconds=480)
        self.tracker.report_first_crack(fc_time, 205.0)
        
        # Current time T+540s (9 minutes)
        current_time = base_time + timedelta(seconds=540)
        current_reading = SensorReading(
            timestamp=current_time,
            bean_temp_c=210.0,
            chamber_temp_c=220.0,
            fan_speed_percent=50,
            heat_level_percent=80
        )
        self.tracker.update(current_reading)
        
        # Development time = 540 - 480 = 60 seconds
        dev_time = self.tracker.get_development_time_seconds()
        assert dev_time == 60
    
    def test_development_time_percentage(self):
        """Test development time as percentage of total roast."""
        base_time = datetime.now(UTC)
        
        # T0 at T+1s
        reading1 = SensorReading(
            timestamp=base_time,
            bean_temp_c=170.0,
            chamber_temp_c=180.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading1)
        
        reading2 = SensorReading(
            timestamp=base_time + timedelta(seconds=1),
            bean_temp_c=150.0,
            chamber_temp_c=175.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading2)
        
        # Agent reports first crack at T+480s (8 min)
        fc_time = base_time + timedelta(seconds=480)
        self.tracker.report_first_crack(fc_time, 205.0)
        
        # Current at T+600s (10 min)
        # Total roast: 600 - 1 = 599s
        # Development: 600 - 480 = 120s
        # Percentage: 120 / 599 * 100 = ~20%
        current_reading = SensorReading(
            timestamp=base_time + timedelta(seconds=600),
            bean_temp_c=215.0,
            chamber_temp_c=225.0,
            fan_speed_percent=50,
            heat_level_percent=70
        )
        self.tracker.update(current_reading)
        
        dev_pct = self.tracker.get_development_time_percent()
        assert dev_pct is not None
        assert abs(dev_pct - 20.0) < 1.0
    
    def test_development_time_none_without_t0(self):
        """Test development time percentage is None without T0."""
        # Agent reports first crack without T0 detected
        fc_time = datetime.now(UTC)
        self.tracker.report_first_crack(fc_time, 205.0)
        
        # Add a reading
        reading = SensorReading(
            timestamp=fc_time + timedelta(seconds=60),
            bean_temp_c=210.0,
            chamber_temp_c=220.0,
            fan_speed_percent=50,
            heat_level_percent=80
        )
        self.tracker.update(reading)
        
        # Percentage should be None (no T0 to calculate from)
        assert self.tracker.get_development_time_percent() is None


class TestBeanDrop:
    """Test bean drop recording and final metrics."""
    
    def setup_method(self):
        """Setup tracker."""
        config = TrackerConfig()
        self.tracker = RoastTracker(config)
    
    def test_drop_not_recorded_initially(self):
        """Test drop is None initially."""
        assert self.tracker.get_drop() is None
    
    def test_record_drop(self):
        """Test recording bean drop."""
        drop_time = datetime.now(UTC)
        self.tracker.record_drop(drop_time, 218.0)
        
        assert self.tracker.get_drop() == drop_time
        assert self.tracker.get_drop_temp() == 218.0
    
    def test_drop_recorded_once(self):
        """Test drop only recorded once (idempotent)."""
        drop_time1 = datetime.now(UTC)
        self.tracker.record_drop(drop_time1, 218.0)
        
        # Try to record again
        drop_time2 = datetime.now(UTC) + timedelta(seconds=30)
        self.tracker.record_drop(drop_time2, 220.0)
        
        # Should still be first drop
        assert self.tracker.get_drop() == drop_time1
        assert self.tracker.get_drop_temp() == 218.0
    
    def test_total_roast_duration(self):
        """Test total roast duration from T0 to drop."""
        base_time = datetime.now(UTC)
        
        # T0 at T+1s
        reading1 = SensorReading(
            timestamp=base_time,
            bean_temp_c=170.0,
            chamber_temp_c=180.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading1)
        
        reading2 = SensorReading(
            timestamp=base_time + timedelta(seconds=1),
            bean_temp_c=150.0,
            chamber_temp_c=175.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading2)
        
        # Drop at T+600s (10 minutes)
        drop_time = base_time + timedelta(seconds=600)
        self.tracker.record_drop(drop_time, 218.0)
        
        # Total duration = 600 - 1 = 599 seconds
        total = self.tracker.get_total_roast_duration()
        assert total == 599
    
    def test_total_roast_duration_none_without_t0(self):
        """Test total duration is None without T0."""
        drop_time = datetime.now(UTC)
        self.tracker.record_drop(drop_time, 218.0)
        
        assert self.tracker.get_total_roast_duration() is None
    
    def test_development_time_clamped_to_drop(self):
        """Test development time stops at drop (doesn't continue after)."""
        base_time = datetime.now(UTC)
        
        # T0
        reading1 = SensorReading(
            timestamp=base_time,
            bean_temp_c=170.0,
            chamber_temp_c=180.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading1)
        
        reading2 = SensorReading(
            timestamp=base_time + timedelta(seconds=1),
            bean_temp_c=150.0,
            chamber_temp_c=175.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading2)
        
        # First crack at T+480s
        fc_time = base_time + timedelta(seconds=480)
        self.tracker.report_first_crack(fc_time, 205.0)
        
        # Drop at T+600s
        drop_time = base_time + timedelta(seconds=600)
        self.tracker.record_drop(drop_time, 218.0)
        
        # Add reading after drop at T+700s
        reading3 = SensorReading(
            timestamp=base_time + timedelta(seconds=700),
            bean_temp_c=180.0,  # Cooling down
            chamber_temp_c=190.0,
            fan_speed_percent=100,
            heat_level_percent=0
        )
        self.tracker.update(reading3)
        
        # Development time should be 600 - 480 = 120s (clamped to drop)
        # NOT 700 - 480 = 220s
        dev_time = self.tracker.get_development_time_seconds()
        assert dev_time == 120
    
    def test_get_metrics_complete(self):
        """Test get_metrics returns complete RoastMetrics."""
        base_time = datetime.now(UTC)
        
        # T0 at T+1s
        reading1 = SensorReading(
            timestamp=base_time,
            bean_temp_c=170.0,
            chamber_temp_c=180.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading1)
        
        reading2 = SensorReading(
            timestamp=base_time + timedelta(seconds=1),
            bean_temp_c=150.0,
            chamber_temp_c=175.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading2)
        
        # First crack at T+480s (8 min)
        fc_time = base_time + timedelta(seconds=480)
        self.tracker.report_first_crack(fc_time, 205.0)
        
        # Drop at T+600s (10 min)
        drop_time = base_time + timedelta(seconds=600)
        self.tracker.record_drop(drop_time, 218.0)
        
        # Get complete metrics
        metrics = self.tracker.get_metrics()
        
        assert metrics.beans_added_temp_c == 170.0
        assert metrics.first_crack_temp_c == 205.0
        assert metrics.roast_elapsed_seconds == 599
        assert metrics.roast_elapsed_display == "09:59"
        assert metrics.development_time_seconds == 120
        assert abs(metrics.development_time_percent - 20.0) < 1.0
        assert metrics.total_roast_duration_seconds == 599
