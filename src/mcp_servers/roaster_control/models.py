"""Data models for roaster control."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class SensorReading(BaseModel):
    """Raw sensor data from hardware."""
    timestamp: datetime
    bean_temp_c: float = Field(..., ge=-50, le=300)
    chamber_temp_c: float = Field(..., ge=-50, le=300)
    fan_speed_percent: int = Field(..., ge=0, le=100)
    heat_level_percent: int = Field(..., ge=0, le=100)


class RoastMetrics(BaseModel):
    """Computed roast metrics."""
    roast_elapsed_seconds: Optional[int] = None
    roast_elapsed_display: Optional[str] = None
    rate_of_rise_c_per_min: Optional[float] = None
    beans_added_temp_c: Optional[float] = None
    first_crack_temp_c: Optional[float] = None
    first_crack_time_display: Optional[str] = None
    development_time_seconds: Optional[int] = None
    development_time_display: Optional[str] = None
    development_time_percent: Optional[float] = None
    total_roast_duration_seconds: Optional[int] = None


class HardwareConfig(BaseModel):
    """Hardware configuration."""
    port: str = "/dev/tty.usbserial-1420"
    baud_rate: int = Field(115200, gt=0, le=921600)  # Valid baud rate range
    timeout: float = Field(1.0, gt=0, le=60.0)  # Reasonable timeout range
    mock_mode: bool = True  # Default to mock for safety
    
    @field_validator('baud_rate')
    @classmethod
    def validate_baud_rate(cls, v: int) -> int:
        """Validate baud rate is a standard value."""
        valid_rates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
        if v not in valid_rates:
            raise ValueError(
                f"Baud rate must be one of {valid_rates}, got {v}"
            )
        return v


class TrackerConfig(BaseModel):
    """Roast tracker configuration."""
    t0_detection_threshold: float = Field(10.0, gt=0, le=100.0)  # °C drop to detect beans added
    polling_interval: float = Field(1.0, gt=0.1, le=10.0)  # seconds
    ror_window_size: int = Field(60, ge=10, le=300)  # seconds for rate of rise calculation
    development_time_target_min: float = Field(15.0, ge=0, le=100.0)  # %
    development_time_target_max: float = Field(20.0, ge=0, le=100.0)  # %
    
    @field_validator('development_time_target_max')
    @classmethod
    def validate_dev_time_range(cls, v: float, info) -> float:
        """Validate max is greater than min."""
        if 'development_time_target_min' in info.data:
            min_val = info.data['development_time_target_min']
            if v < min_val:
                raise ValueError(
                    f"development_time_target_max ({v}) must be >= "
                    f"development_time_target_min ({min_val})"
                )
        return v


class ServerConfig(BaseModel):
    """Complete server configuration."""
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    tracker: TrackerConfig = Field(default_factory=TrackerConfig)
    logging_level: str = "INFO"
    timezone: str = "America/Los_Angeles"
    
    @field_validator('logging_level')
    @classmethod
    def validate_logging_level(cls, v: str) -> str:
        """Validate logging level is valid."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"logging_level must be one of {valid_levels}, got {v}"
            )
        return v_upper
    
    def validate(self) -> None:
        """Perform complex cross-field validation.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate timezone string
        try:
            from zoneinfo import ZoneInfo
            ZoneInfo(self.timezone)
        except Exception as e:
            raise ValueError(f"Invalid timezone '{self.timezone}': {e}")
        
        # Validate hardware + tracker compatibility
        if self.tracker.polling_interval > 5.0 and not self.hardware.mock_mode:
            raise ValueError(
                f"Polling interval ({self.tracker.polling_interval}s) too high "
                f"for real hardware (max 5.0s recommended)"
            )


class RoastStatus(BaseModel):
    """Complete roast status response."""
    session_active: bool
    roaster_running: bool
    timestamps: dict  # All event timestamps (UTC + local)
    sensors: SensorReading
    metrics: RoastMetrics
    connection: dict  # Connection status info