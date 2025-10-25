"""Roast metrics tracker.

Tracks roast events and computes metrics:
- T0 (beans added) detection from temperature drop
- Rate of rise (RoR) from 60-second temperature buffer
- Development time tracking after first crack
- Total roast duration
"""
import logging
from datetime import datetime, UTC
from typing import Optional, Deque, Tuple
from collections import deque

logger = logging.getLogger(__name__)

from .models import SensorReading, RoastMetrics, TrackerConfig
from .utils import format_time


class RoastTracker:
    """Tracks and computes roast metrics from sensor readings.
    
    Public interface expected by SessionManager/Server:
    - update(SensorReading)
    - get_t0(), get_beans_added_temp()
    - report_first_crack(datetime, temp_c)
    - get_first_crack(), get_first_crack_temp()
    - get_development_time_seconds(), get_development_time_percent()
    - get_rate_of_rise()
    - record_drop(datetime, temp_c)
    - get_drop(), get_drop_temp()
    - get_total_roast_duration()
    - get_metrics() -> RoastMetrics
    """
    
    def __init__(self, config: TrackerConfig):
        """Initialize roast tracker.
        
        Args:
            config: Tracker configuration
        """
        self._config = config
        
        # Timestamps
        self._t0: Optional[datetime] = None  # Beans added time
        self._first_crack: Optional[datetime] = None
        self._drop: Optional[datetime] = None
        self._last_timestamp: Optional[datetime] = None
        
        # Temperature buffer for RoR (stores (timestamp, temp) tuples)
        self._temp_buffer: Deque[Tuple[datetime, float]] = deque(
            maxlen=config.ror_window_size
        )
        
        # Captured values
        self._beans_added_temp: Optional[float] = None
        self._first_crack_temp: Optional[float] = None
        self._drop_temp: Optional[float] = None
    
    def update(self, reading: SensorReading):
        """Process new sensor reading.
        
        Args:
            reading: Current sensor reading
        """
        # Safety checks (log warnings for attended operation)
        if reading.bean_temp_c > 250.0:
            logger.warning(
                f"⚠️  OVERHEAT WARNING: Bean temperature at {reading.bean_temp_c:.1f}°C "
                f"(safe limit: 250°C)"
            )
        
        if reading.chamber_temp_c > 300.0:
            logger.warning(
                f"⚠️  OVERHEAT WARNING: Chamber temperature at {reading.chamber_temp_c:.1f}°C "
                f"(safe limit: 300°C)"
            )
        
        # Add to temperature buffer
        self._temp_buffer.append((reading.timestamp, reading.bean_temp_c))
        self._last_timestamp = reading.timestamp
        
        # Check for stall (negative RoR after T0 for extended period)
        if self._t0 is not None and len(self._temp_buffer) >= 30:
            ror = self.get_rate_of_rise()
            if ror is not None and ror < -2.0:  # Temperature dropping
                logger.warning(
                    f"⚠️  STALL WARNING: Rate of rise is {ror:.1f}°C/min (negative)"
                )
        
        # Auto-detect T0 if not set
        if self._t0 is None:
            self._detect_beans_added(reading)
    
    def _detect_beans_added(self, reading: SensorReading):
        """Detect sudden temperature drop indicating beans added.
        
        Args:
            reading: Current sensor reading
        """
        if len(self._temp_buffer) < 2:
            return
        
        prev_timestamp, prev_temp = self._temp_buffer[-2]
        curr_temp = reading.bean_temp_c
        
        drop = prev_temp - curr_temp
        
        if drop > self._config.t0_detection_threshold:
            self._t0 = reading.timestamp
            self._beans_added_temp = prev_temp
    
    def get_t0(self) -> Optional[datetime]:
        """Get T0 (beans added time).
        
        Returns:
            Timestamp when beans were added, or None if not detected
        """
        return self._t0
    
    def get_beans_added_temp(self) -> Optional[float]:
        """Get temperature when beans were added.
        
        Returns:
            Temperature in °C when beans were added, or None if not detected
        """
        return self._beans_added_temp
    
    def get_rate_of_rise(self) -> Optional[float]:
        """Calculate rate of rise (RoR) from temperature buffer.
        
        RoR is the temperature change per minute, calculated from the
        oldest and newest readings in the buffer.
        
        Returns:
            Rate of rise in °C/min, or None if insufficient data
        """
        if len(self._temp_buffer) < 2:
            return None
        
        # Get oldest and newest readings
        oldest_timestamp, oldest_temp = self._temp_buffer[0]
        newest_timestamp, newest_temp = self._temp_buffer[-1]
        
        # Calculate time difference in seconds
        time_delta = (newest_timestamp - oldest_timestamp).total_seconds()
        
        if time_delta == 0:
            return None
        
        # Calculate temperature change
        temp_delta = newest_temp - oldest_temp
        
        # Convert to °C per minute
        ror = (temp_delta / time_delta) * 60.0
        
        return round(ror, 1)
    
    # ----- First crack reporting & development time -----
    def report_first_crack(self, when: datetime, temp_c: float):
        """Record first crack event as reported by agent.
        
        This is idempotent: only the first report is stored.
        """
        if self._first_crack is None:
            self._first_crack = when
            self._first_crack_temp = temp_c
    
    def get_first_crack(self) -> Optional[datetime]:
        """Return first crack timestamp if reported."""
        return self._first_crack
    
    def get_first_crack_temp(self) -> Optional[float]:
        """Return temperature at first crack if reported."""
        return self._first_crack_temp
    
    def get_development_time_seconds(self) -> Optional[int]:
        """Return development time (seconds) since first crack.
        
        Requires that first crack is reported and at least one reading
        after that (to provide current time). If drop is recorded in the
        future, this will clamp to drop time.
        """
        if self._first_crack is None or self._last_timestamp is None:
            return None
        end_time = self._drop if self._drop is not None else self._last_timestamp
        if end_time < self._first_crack:
            return 0
        return int((end_time - self._first_crack).total_seconds())
    
    def get_development_time_percent(self) -> Optional[float]:
        """Return development time as percentage of total roast time.
        
        Total roast time is measured from T0 to current (or drop) time.
        Returns None if T0 is not detected or there is no current time.
        """
        if self._t0 is None or self._first_crack is None:
            return None
        
        # Use drop time if recorded, otherwise current time
        end_time = self._drop if self._drop is not None else self._last_timestamp
        if end_time is None:
            return None
        
        total_secs = int((end_time - self._t0).total_seconds())
        if total_secs <= 0:
            return None
        dev_secs = self.get_development_time_seconds()
        if dev_secs is None:
            return None
        return round((dev_secs / total_secs) * 100.0, 1)
    
    # ----- Bean drop recording -----
    def record_drop(self, when: datetime, temp_c: float):
        """Record bean drop event.
        
        This is idempotent: only the first drop is recorded.
        """
        if self._drop is None:
            self._drop = when
            self._drop_temp = temp_c
    
    def get_drop(self) -> Optional[datetime]:
        """Return drop timestamp if recorded."""
        return self._drop
    
    def get_drop_temp(self) -> Optional[float]:
        """Return temperature at drop if recorded."""
        return self._drop_temp
    
    def get_total_roast_duration(self) -> Optional[int]:
        """Return total roast duration (T0 to drop) in seconds.
        
        Returns None if T0 or drop not recorded.
        """
        if self._t0 is None or self._drop is None:
            return None
        return int((self._drop - self._t0).total_seconds())
    
    # ----- Complete metrics -----
    def get_metrics(self) -> RoastMetrics:
        """Return complete roast metrics as RoastMetrics model.
        
        This is the main interface for SessionManager to get all metrics.
        """
        # Calculate roast elapsed time
        roast_elapsed_secs = None
        roast_elapsed_display = None
        if self._t0 is not None:
            end_time = self._drop if self._drop is not None else self._last_timestamp
            if end_time is not None:
                roast_elapsed_secs = int((end_time - self._t0).total_seconds())
                roast_elapsed_display = format_time(roast_elapsed_secs)
        
        # Calculate first crack display time
        fc_time_display = None
        if self._first_crack is not None and self._t0 is not None:
            fc_elapsed = int((self._first_crack - self._t0).total_seconds())
            fc_time_display = format_time(fc_elapsed)
        
        # Calculate development time display
        dev_time_display = None
        dev_time_secs = self.get_development_time_seconds()
        if dev_time_secs is not None:
            dev_time_display = format_time(dev_time_secs)
        
        return RoastMetrics(
            roast_elapsed_seconds=roast_elapsed_secs,
            roast_elapsed_display=roast_elapsed_display,
            rate_of_rise_c_per_min=self.get_rate_of_rise(),
            beans_added_temp_c=self._beans_added_temp,
            first_crack_temp_c=self._first_crack_temp,
            first_crack_time_display=fc_time_display,
            development_time_seconds=dev_time_secs,
            development_time_display=dev_time_display,
            development_time_percent=self.get_development_time_percent(),
            total_roast_duration_seconds=self.get_total_roast_duration()
        )
