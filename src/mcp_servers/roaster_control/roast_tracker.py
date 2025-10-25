"""Roast metrics tracker.

Tracks roast events and computes metrics:
- T0 (beans added) detection from temperature drop
- Rate of rise (RoR) from 60-second temperature buffer
- Development time tracking after first crack
- Total roast duration
"""
from datetime import datetime, UTC
from typing import Optional, Deque, Tuple
from collections import deque

from .models import SensorReading, RoastMetrics, TrackerConfig
from .utils import format_time


class RoastTracker:
    """Tracks and computes roast metrics from sensor readings."""
    
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
        # Add to temperature buffer
        self._temp_buffer.append((reading.timestamp, reading.bean_temp_c))
        
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
