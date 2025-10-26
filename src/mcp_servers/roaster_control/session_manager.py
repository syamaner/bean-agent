"""Roast session manager - thread-safe orchestration of hardware + tracker."""
import logging
import threading
import time
from datetime import datetime, UTC
from typing import Optional

logger = logging.getLogger(__name__)

from .hardware import HardwareInterface
from .roast_tracker import RoastTracker
from .models import ServerConfig, RoastStatus, SensorReading
from .utils import get_timestamps


class RoastSessionManager:
    """Manages roasting session with thread-safe operations.
    
    Orchestrates:
    - Hardware connection and control
    - Sensor polling in background thread
    - Roast metric tracking
    - Thread-safe status queries
    """
    
    def __init__(self, hardware: HardwareInterface, config: ServerConfig):
        """Initialize session manager.
        
        Args:
            hardware: Hardware interface (MockRoaster or HottopRoaster)
            config: Server configuration
        """
        self._hardware = hardware
        self._config = config
        self._tracker = RoastTracker(config.tracker)
        
        # Session state
        self._session_active = False
        self._polling_active = False
        self._polling_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Latest sensor reading (for thread-safe access)
        self._latest_reading: Optional[SensorReading] = None
    
    # ----- Session Lifecycle -----
    def start_session(self):
        """Start roasting session.
        
        - Connects to hardware
        - Starts polling thread
        - Idempotent (safe to call multiple times)
        """
        with self._lock:
            if self._session_active:
                return  # Already active
            
            # Connect hardware
            self._hardware.connect()
            
            # Start polling thread
            self._polling_active = True
            self._polling_thread = threading.Thread(
                target=self._polling_loop,
                daemon=True
            )
            self._polling_thread.start()
            
            self._session_active = True
    
    def stop_session(self):
        """Stop roasting session.
        
        - Stops polling thread
        - Disconnects hardware
        - Idempotent (safe to call when not running)
        """
        with self._lock:
            if not self._session_active:
                return  # Not active
            
            # Stop polling
            self._polling_active = False
            
            self._session_active = False
        
        # Wait for thread to finish (outside lock)
        if self._polling_thread is not None:
            self._polling_thread.join(timeout=2.0)
            self._polling_thread = None
        
        # Disconnect hardware
        self._hardware.disconnect()
    
    def is_active(self) -> bool:
        """Check if session is active."""
        with self._lock:
            return self._session_active
    
    def get_hardware_info(self) -> dict:
        """Get hardware roaster information.
        
        Returns:
            Dict with keys: 'brand', 'model', 'version'
        """
        return self._hardware.get_roaster_info()
    
    def _polling_loop(self):
        """Background thread: poll sensors and update tracker."""
        interval = self._config.tracker.polling_interval
        
        while self._polling_active:
            try:
                # Read sensors
                reading = self._hardware.read_sensors()
                
                # Update tracker and cache reading
                with self._lock:
                    self._tracker.update(reading)
                    self._latest_reading = reading
            
            except Exception as e:
                # Log error but don't crash thread
                logger.error(f"Polling error: {e}", exc_info=True)
            
            time.sleep(interval)
    
    # ----- Control Commands -----
    def set_heat(self, percent: int):
        """Set heat level."""
        with self._lock:
            self._hardware.set_heat(percent)
    
    def set_fan(self, percent: int):
        """Set fan speed."""
        with self._lock:
            self._hardware.set_fan(percent)
    
    def start_roaster(self):
        """Start roaster drum."""
        with self._lock:
            self._hardware.start_drum()
    
    def stop_roaster(self):
        """Stop roaster drum."""
        with self._lock:
            self._hardware.stop_drum()
    
    def drop_beans(self):
        """Drop beans and record in tracker."""
        with self._lock:
            self._hardware.drop_beans()
            # Record drop with current temperature
            if self._latest_reading is not None:
                self._tracker.record_drop(
                    datetime.now(UTC),
                    self._latest_reading.bean_temp_c
                )
    
    def start_cooling(self):
        """Start cooling fan."""
        with self._lock:
            self._hardware.start_cooling()
    
    def stop_cooling(self):
        """Stop cooling fan."""
        with self._lock:
            self._hardware.stop_cooling()
    
    def report_first_crack(self, when: datetime, temp_c: Optional[float] = None):
        """Report first crack event to tracker."""
        with self._lock:
            # Use current temperature if not provided
            if temp_c is None and self._latest_reading is not None:
                temp_c = self._latest_reading.bean_temp_c
            # Only report if we have a temperature
            if temp_c is not None:
                self._tracker.report_first_crack(when, temp_c)
    
    # ----- Status Queries -----
    def get_status(self) -> RoastStatus:
        """Get complete roast status.
        
        Thread-safe: can be called while polling.
        """
        with self._lock:
            # Get latest sensor reading
            sensors = self._latest_reading
            if sensors is None:
                # No readings yet - return safe defaults
                sensors = SensorReading(
                    timestamp=datetime.now(UTC),
                    bean_temp_c=0.0,
                    chamber_temp_c=0.0,
                    fan_speed_percent=0,
                    heat_level_percent=0
                )
            
            # Get metrics from tracker
            metrics = self._tracker.get_metrics()
            
            # Connection info
            connection = {
                "connected": self._hardware.is_connected(),
                "roaster_info": self._hardware.get_roaster_info()
            }
            
            # Roaster running status
            roaster_running = self._hardware.is_drum_running()
            
            # Build timestamps dict (T0, FC, drop)
            timestamps = {}
            if self._tracker.get_t0() is not None:
                utc, local = get_timestamps(self._tracker.get_t0(), self._config.timezone)
                timestamps["t0_utc"] = utc.isoformat()
                timestamps["t0_local"] = local.isoformat()
            
            if self._tracker.get_first_crack() is not None:
                utc, local = get_timestamps(self._tracker.get_first_crack(), self._config.timezone)
                timestamps["first_crack_utc"] = utc.isoformat()
                timestamps["first_crack_local"] = local.isoformat()
            
            if self._tracker.get_drop() is not None:
                utc, local = get_timestamps(self._tracker.get_drop(), self._config.timezone)
                timestamps["drop_utc"] = utc.isoformat()
                timestamps["drop_local"] = local.isoformat()
            
            return RoastStatus(
                session_active=self._session_active,
                roaster_running=roaster_running,
                timestamps=timestamps,
                sensors=sensors,
                metrics=metrics,
                connection=connection
            )