"""Tests for RoastSessionManager - thread-safe session orchestration."""
import pytest
import time
from datetime import datetime, UTC
import sys
sys.path.insert(0, 'src')

from src.mcp_servers.roaster_control.session_manager import RoastSessionManager
from src.mcp_servers.roaster_control.hardware import MockRoaster
from src.mcp_servers.roaster_control.models import ServerConfig


class TestSessionLifecycle:
    """Test session start/stop lifecycle."""
    
    def setup_method(self):
        """Setup session manager with mock hardware."""
        config = ServerConfig()
        hardware = MockRoaster()
        self.manager = RoastSessionManager(hardware, config)
    
    def test_session_not_active_initially(self):
        """Test session is not active on init."""
        assert not self.manager.is_active()
    
    def test_start_session(self):
        """Test starting a session."""
        self.manager.start_session()
        assert self.manager.is_active()
    
    def test_start_session_connects_hardware(self):
        """Test start_session connects to hardware."""
        self.manager.start_session()
        # Hardware should be connected
        assert self.manager._hardware.is_connected()
    
    def test_start_session_starts_polling(self):
        """Test start_session starts polling thread."""
        self.manager.start_session()
        
        # Wait a bit for polling to happen
        time.sleep(0.5)
        
        # Tracker should have received sensor readings
        # (can check by seeing if buffer has data)
        assert self.manager._tracker._temp_buffer
    
    def test_start_session_idempotent(self):
        """Test start_session is idempotent."""
        self.manager.start_session()
        first_start = self.manager.is_active()
        
        # Start again
        self.manager.start_session()
        second_start = self.manager.is_active()
        
        assert first_start == second_start
        # Should not create multiple threads
        assert self.manager._polling_thread is not None
    
    def test_stop_session(self):
        """Test stopping a session."""
        self.manager.start_session()
        self.manager.stop_session()
        
        assert not self.manager.is_active()
    
    def test_stop_session_stops_polling(self):
        """Test stop_session stops polling thread."""
        self.manager.start_session()
        time.sleep(0.2)
        
        self.manager.stop_session()
        
        # Thread should be stopped
        assert not self.manager._polling_active
    
    def test_stop_session_idempotent(self):
        """Test stop_session is idempotent (safe when not running)."""
        # Stop without starting - should not error
        self.manager.stop_session()
        assert not self.manager.is_active()
    
    def test_session_survives_multiple_start_stop_cycles(self):
        """Test can start/stop multiple times."""
        # Cycle 1
        self.manager.start_session()
        assert self.manager.is_active()
        self.manager.stop_session()
        assert not self.manager.is_active()
        
        # Cycle 2
        self.manager.start_session()
        assert self.manager.is_active()
        self.manager.stop_session()
        assert not self.manager.is_active()


class TestControlCommands:
    """Test hardware control command execution."""
    
    def setup_method(self):
        """Setup session manager."""
        config = ServerConfig()
        hardware = MockRoaster()
        self.manager = RoastSessionManager(hardware, config)
        self.manager.start_session()
        time.sleep(0.1)  # Let polling start
    
    def teardown_method(self):
        """Clean up session."""
        self.manager.stop_session()
    
    def test_set_heat(self):
        """Test setting heat level."""
        self.manager.set_heat(80)
        
        # Should be reflected in hardware
        assert self.manager._hardware._heat == 80
    
    def test_set_heat_validates_range(self):
        """Test heat validation."""
        from src.mcp_servers.roaster_control.exceptions import InvalidCommandError
        
        with pytest.raises(InvalidCommandError):
            self.manager.set_heat(150)  # Out of range
    
    def test_set_heat_validates_increments(self):
        """Test heat must be in 10% increments."""
        from src.mcp_servers.roaster_control.exceptions import InvalidCommandError
        
        with pytest.raises(InvalidCommandError):
            self.manager.set_heat(75)  # Not 10% increment
    
    def test_set_fan(self):
        """Test setting fan speed."""
        self.manager.set_fan(60)
        assert self.manager._hardware._fan == 60
    
    def test_start_roaster(self):
        """Test starting roaster drum."""
        self.manager.start_roaster()
        assert self.manager._hardware._drum_running
    
    def test_stop_roaster(self):
        """Test stopping roaster drum."""
        self.manager.start_roaster()
        self.manager.stop_roaster()
        assert not self.manager._hardware._drum_running
    
    def test_drop_beans(self):
        """Test dropping beans."""
        self.manager.drop_beans()
        
        # Should record drop in tracker
        assert self.manager._tracker.get_drop() is not None
    
    def test_start_cooling(self):
        """Test starting cooling fan."""
        self.manager.start_cooling()
        assert self.manager._hardware._cooling
    
    def test_stop_cooling(self):
        """Test stopping cooling fan."""
        self.manager.start_cooling()
        self.manager.stop_cooling()
        assert not self.manager._hardware._cooling


class TestStatusQueries:
    """Test status query operations."""
    
    def setup_method(self):
        """Setup session manager."""
        config = ServerConfig()
        hardware = MockRoaster()
        self.manager = RoastSessionManager(hardware, config)
        self.manager.start_session()
        time.sleep(1.5)  # Let polling accumulate readings for RoR
    
    def teardown_method(self):
        """Clean up session."""
        self.manager.stop_session()
    
    def test_get_status_returns_roast_status(self):
        """Test get_status returns RoastStatus model."""
        from src.mcp_servers.roaster_control.models import RoastStatus
        
        status = self.manager.get_status()
        assert isinstance(status, RoastStatus)
    
    def test_get_status_includes_session_active(self):
        """Test status includes session_active flag."""
        status = self.manager.get_status()
        assert status.session_active is True
    
    def test_get_status_includes_sensors(self):
        """Test status includes current sensor readings."""
        status = self.manager.get_status()
        
        assert status.sensors is not None
        assert hasattr(status.sensors, 'bean_temp_c')
        assert hasattr(status.sensors, 'chamber_temp_c')
    
    def test_get_status_includes_metrics(self):
        """Test status includes computed metrics."""
        status = self.manager.get_status()
        
        assert status.metrics is not None
        # RoR should be available after some readings
        assert status.metrics.rate_of_rise_c_per_min is not None
    
    def test_get_status_is_thread_safe(self):
        """Test get_status can be called while polling."""
        # Call get_status multiple times rapidly
        statuses = []
        for _ in range(5):
            status = self.manager.get_status()
            statuses.append(status)
            time.sleep(0.05)
        
        # All should succeed
        assert len(statuses) == 5
        # All should have valid data
        for status in statuses:
            assert status.sensors is not None
    
    def test_report_first_crack(self):
        """Test reporting first crack updates tracker."""
        fc_time = datetime.now(UTC)
        self.manager.report_first_crack(fc_time, 205.0)
        
        status = self.manager.get_status()
        assert status.metrics.first_crack_temp_c == 205.0