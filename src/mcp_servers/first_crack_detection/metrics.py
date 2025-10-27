"""
First Crack Detection domain-specific metrics.

Implements observability requirements from docs/observability_requirements.md
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from opentelemetry import metrics

logger = logging.getLogger(__name__)


class FirstCrackMetrics:
    """Metrics for first crack detection events."""
    
    def __init__(self):
        meter = metrics.get_meter("first-crack-detection")
        
        # Counter: First crack detections
        self.first_crack_detected = meter.create_counter(
            name="first_crack.detected",
            description="First crack detection events",
            unit="1"
        )
        
        # Histogram: Time from start to first crack
        self.time_to_first_crack = meter.create_histogram(
            name="first_crack.time_from_start",
            description="Elapsed time from detection start to first crack",
            unit="s"
        )
    
    def record_first_crack(
        self,
        timestamp: datetime,
        elapsed_seconds: float,
        microphone_type: str,
        temperature: Optional[float] = None
    ):
        """
        Record a first crack detection event.
        
        Args:
            timestamp: UTC timestamp when first crack was detected
            elapsed_seconds: Seconds elapsed since detection started
            microphone_type: Type of microphone (audio_file, usb_microphone, builtin_microphone)
            temperature: Bean temperature at first crack (if available)
        """
        attributes = {
            "utc_timestamp": timestamp.isoformat(),
            "microphone_type": microphone_type
        }
        
        if temperature is not None:
            attributes["temperature_c"] = str(temperature)
        
        # Increment counter
        self.first_crack_detected.add(1, attributes)
        
        # Record duration
        self.time_to_first_crack.record(elapsed_seconds, attributes)
        
        logger.info(
            "First crack detected",
            extra={
                "event": "first_crack_detected",
                "utc_timestamp": timestamp.isoformat(),
                "elapsed_seconds": elapsed_seconds,
                "microphone_type": microphone_type,
                "temperature_c": temperature
            }
        )
