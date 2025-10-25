"""Data models for roaster control."""
from pydantic import BaseModel, Field
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
    baud_rate: int = 115200
    timeout: float = 1.0
    mock_mode: bool = True  # Default to mock for safety


class TrackerConfig(BaseModel):
    """Roast tracker configuration."""
    t0_detection_threshold: float = 10.0  # °C drop to detect beans added
    polling_interval: float = 1.0  # seconds
    ror_window_size: int = 60  # seconds for rate of rise calculation
    development_time_target_min: float = 15.0  # %
    development_time_target_max: float = 20.0  # %


class ServerConfig(BaseModel):
    """Complete server configuration."""
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    tracker: TrackerConfig = Field(default_factory=TrackerConfig)
    logging_level: str = "INFO"
    timezone: str = "America/Los_Angeles"


class RoastStatus(BaseModel):
    """Complete roast status response."""
    session_active: bool
    roaster_running: bool
    timestamps: dict  # All event timestamps (UTC + local)
    sensors: SensorReading
    metrics: RoastMetrics
    connection: dict  # Connection status info