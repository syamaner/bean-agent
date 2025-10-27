"""
Roaster Control domain-specific metrics.

Implements observability requirements from docs/observability_requirements.md
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from opentelemetry import metrics

logger = logging.getLogger(__name__)


class RoasterMetrics:
    """Metrics for roaster sensor readings and roast events."""
    
    def __init__(self):
        meter = metrics.get_meter("roaster-control")
        
        # Gauges for real-time sensor values (using UpDownCounter as closest match)
        self.bean_temperature = meter.create_observable_gauge(
            name="roaster.bean_temperature",
            description="Current bean temperature",
            unit="Cel",  # Celsius in ASCII
            callbacks=[self._get_bean_temp]
        )
        
        self.environment_temperature = meter.create_observable_gauge(
            name="roaster.environment_temperature",
            description="Current environment/chamber temperature",
            unit="Cel",  # Celsius in ASCII
            callbacks=[self._get_env_temp]
        )
        
        # Histogram for temperature readings (captures distribution over time)
        self.bean_temp_histogram = meter.create_histogram(
            name="roaster.bean_temperature.reading",
            description="Bean temperature readings",
            unit="Cel"  # Celsius in ASCII
        )
        
        self.env_temp_histogram = meter.create_histogram(
            name="roaster.environment_temperature.reading",
            description="Environment temperature readings",
            unit="Cel"  # Celsius in ASCII
        )
        
        # Gauges for control settings
        self.fan_speed_histogram = meter.create_histogram(
            name="roaster.fan_speed.setting",
            description="Fan speed setting changes",
            unit="%"
        )
        
        self.heat_level_histogram = meter.create_histogram(
            name="roaster.heat_level.setting",
            description="Heat level setting changes",
            unit="%"
        )
        
        # Histogram for rate of rise
        self.rate_of_rise = meter.create_histogram(
            name="roaster.rate_of_rise",
            description="Rate of temperature rise",
            unit="Cel/min"  # Celsius per minute in ASCII
        )
        
        # Histograms for roast phase metrics
        self.development_time = meter.create_histogram(
            name="roaster.development_time",
            description="Development time (time after first crack)",
            unit="s"
        )
        
        self.development_time_percentage = meter.create_histogram(
            name="roaster.development_time_percentage",
            description="Development time as percentage of total roast",
            unit="%"
        )
        
        # Key temperature milestones
        self.charge_temperature = meter.create_histogram(
            name="roaster.charge_temperature",
            description="Temperature when beans are charged",
            unit="Cel"  # Celsius in ASCII
        )
        
        self.first_crack_temperature = meter.create_histogram(
            name="roaster.first_crack_temperature",
            description="Temperature at first crack",
            unit="Cel"  # Celsius in ASCII
        )
        
        self.drop_temperature = meter.create_histogram(
            name="roaster.drop_temperature",
            description="Temperature when beans are dropped",
            unit="Cel"  # Celsius in ASCII
        )
        
        self.roast_duration = meter.create_histogram(
            name="roaster.roast_duration",
            description="Total roast duration",
            unit="s"
        )
        
        # Cache for observable callbacks
        self._cached_bean_temp: Optional[float] = None
        self._cached_env_temp: Optional[float] = None
    
    def _get_bean_temp(self, options):
        """Callback for observable bean temperature gauge."""
        if self._cached_bean_temp is not None:
            yield metrics.Observation(self._cached_bean_temp, {})
    
    def _get_env_temp(self, options):
        """Callback for observable environment temperature gauge."""
        if self._cached_env_temp is not None:
            yield metrics.Observation(self._cached_env_temp, {})
    
    def record_bean_temperature(self, temperature: float, timestamp: datetime):
        """Record bean temperature reading."""
        self._cached_bean_temp = temperature
        self.bean_temp_histogram.record(
            temperature,
            {"utc_timestamp": timestamp.isoformat()}
        )
    
    def record_environment_temperature(self, temperature: float, timestamp: datetime):
        """Record environment temperature reading."""
        self._cached_env_temp = temperature
        self.env_temp_histogram.record(
            temperature,
            {"utc_timestamp": timestamp.isoformat()}
        )
    
    def record_fan_speed_change(self, speed_percent: float, timestamp: datetime):
        """Record fan speed setting change."""
        self.fan_speed_histogram.record(
            speed_percent,
            {"utc_timestamp": timestamp.isoformat()}
        )
        logger.info(
            "Fan speed changed",
            extra={
                "event": "fan_speed_changed",
                "speed_percent": speed_percent,
                "utc_timestamp": timestamp.isoformat()
            }
        )
    
    def record_heat_level_change(self, level_percent: float, timestamp: datetime):
        """Record heat level setting change."""
        self.heat_level_histogram.record(
            level_percent,
            {"utc_timestamp": timestamp.isoformat()}
        )
        logger.info(
            "Heat level changed",
            extra={
                "event": "heat_level_changed",
                "level_percent": level_percent,
                "utc_timestamp": timestamp.isoformat()
            }
        )
    
    def record_rate_of_rise(self, ror_c_per_min: float, timestamp: datetime):
        """Record rate of rise."""
        self.rate_of_rise.record(
            ror_c_per_min,
            {"utc_timestamp": timestamp.isoformat()}
        )
    
    def record_development_metrics(
        self,
        development_time_sec: float,
        development_percentage: float,
        timestamp: datetime
    ):
        """Record development time metrics."""
        self.development_time.record(
            development_time_sec,
            {"utc_timestamp": timestamp.isoformat()}
        )
        self.development_time_percentage.record(
            development_percentage,
            {"utc_timestamp": timestamp.isoformat()}
        )
    
    def record_charge_temperature(self, temperature: float, timestamp: datetime):
        """Record charge temperature (when beans added)."""
        self.charge_temperature.record(
            temperature,
            {"utc_timestamp": timestamp.isoformat()}
        )
        logger.info(
            "Beans charged",
            extra={
                "event": "beans_charged",
                "temperature_c": temperature,
                "utc_timestamp": timestamp.isoformat()
            }
        )
    
    def record_first_crack_temperature(self, temperature: float, timestamp: datetime):
        """Record first crack temperature."""
        self.first_crack_temperature.record(
            temperature,
            {"utc_timestamp": timestamp.isoformat()}
        )
        logger.info(
            "First crack",
            extra={
                "event": "first_crack",
                "temperature_c": temperature,
                "utc_timestamp": timestamp.isoformat()
            }
        )
    
    def record_drop_temperature(self, temperature: float, timestamp: datetime):
        """Record drop temperature (when beans dropped)."""
        self.drop_temperature.record(
            temperature,
            {"utc_timestamp": timestamp.isoformat()}
        )
        logger.info(
            "Beans dropped",
            extra={
                "event": "beans_dropped",
                "temperature_c": temperature,
                "utc_timestamp": timestamp.isoformat()
            }
        )
    
    def record_roast_duration(self, duration_sec: float, timestamp: datetime):
        """Record total roast duration."""
        self.roast_duration.record(
            duration_sec,
            {"utc_timestamp": timestamp.isoformat()}
        )
        logger.info(
            "Roast completed",
            extra={
                "event": "roast_completed",
                "duration_sec": duration_sec,
                "utc_timestamp": timestamp.isoformat()
            }
        )
