"""
OpenTelemetry metrics for coffee roasting system.

Defines metrics classes for First Crack Detection, Roaster Control, and Agent.
All metrics are automatically exported to .NET Aspire dashboard via OTLP.
"""
import os
from datetime import datetime
from typing import Optional
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource


def _setup_meter_provider(service_name: str, otlp_endpoint: Optional[str] = None) -> metrics.Meter:
    """
    Setup OpenTelemetry meter provider.
    
    Args:
        service_name: Name of the service
        otlp_endpoint: OTLP endpoint (default: from env or http://localhost:4317)
        
    Returns:
        metrics.Meter: Configured meter instance
    """
    if otlp_endpoint is None:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    
    resource = Resource.create({"service.name": service_name})
    
    exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
    
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)
    
    return metrics.get_meter(service_name)


class FirstCrackMetrics:
    """
    Metrics for First Crack Detection MCP.
    
    Tracks:
    - First crack detection events
    - Inference performance
    - Audio stream health
    """
    
    def __init__(self, service_name: str = "first-crack-mcp", otlp_endpoint: Optional[str] = None):
        """
        Initialize First Crack metrics.
        
        Args:
            service_name: Service name for OpenTelemetry
            otlp_endpoint: OTLP endpoint URL
        """
        self.meter = _setup_meter_provider(service_name, otlp_endpoint)
        
        # Detection events
        self.fc_detection_counter = self.meter.create_counter(
            name="fc.detections.total",
            description="Total first crack detections",
            unit="1"
        )
        
        # Inference performance
        self.inference_duration = self.meter.create_histogram(
            name="fc.inference.duration",
            description="Model inference duration",
            unit="s"
        )
        
        # Current state gauges (using UpDownCounter as gauge replacement)
        self.confidence_gauge = self.meter.create_gauge(
            name="fc.confidence",
            description="Current first crack detection confidence",
            unit="1"
        )
        
        self.audio_buffer_size = self.meter.create_gauge(
            name="fc.audio_buffer.size",
            description="Current audio buffer size in samples",
            unit="samples"
        )
        
        # Session metrics
        self.session_duration = self.meter.create_histogram(
            name="fc.session.duration",
            description="Detection session duration",
            unit="s"
        )
        
        # Health metrics
        self.audio_errors = self.meter.create_counter(
            name="fc.audio.errors.total",
            description="Audio stream errors",
            unit="1"
        )
        
        self.model_load_duration = self.meter.create_histogram(
            name="fc.model.load_duration",
            description="Model load time",
            unit="s"
        )
    
    def record_detection(
        self,
        utc_timestamp: datetime,
        relative_timestamp_seconds: float,
        audio_source: str,
        confidence: float
    ):
        """Record a first crack detection event."""
        self.fc_detection_counter.add(
            1,
            attributes={
                "audio_source": audio_source,
                "utc_timestamp": utc_timestamp.isoformat(),
                "relative_timestamp": f"{int(relative_timestamp_seconds // 60):02d}:{int(relative_timestamp_seconds % 60):02d}"
            }
        )
    
    def record_inference(self, duration_seconds: float, confidence: float):
        """Record inference metrics."""
        self.inference_duration.record(duration_seconds)
        self.confidence_gauge.set(confidence)
    
    def record_audio_buffer(self, size: int):
        """Record current audio buffer size."""
        self.audio_buffer_size.set(size)
    
    def record_session_end(self, duration_seconds: float, detected: bool):
        """Record session completion."""
        self.session_duration.record(
            duration_seconds,
            attributes={"first_crack_detected": str(detected)}
        )
    
    def record_audio_error(self, error_type: str):
        """Record audio stream error."""
        self.audio_errors.add(1, attributes={"error_type": error_type})
    
    def record_model_load(self, duration_seconds: float):
        """Record model load time."""
        self.model_load_duration.record(duration_seconds)


class RoasterMetrics:
    """
    Metrics for Roaster Control MCP.
    
    Tracks:
    - Sensor readings (temperature, fan, heat)
    - Calculated metrics (RoR, development time)
    - Control commands
    - Key roast events
    """
    
    def __init__(self, service_name: str = "roaster-control-mcp", otlp_endpoint: Optional[str] = None):
        """
        Initialize Roaster Control metrics.
        
        Args:
            service_name: Service name for OpenTelemetry
            otlp_endpoint: OTLP endpoint URL
        """
        self.meter = _setup_meter_provider(service_name, otlp_endpoint)
        
        # Sensor gauges
        self.bean_temp = self.meter.create_gauge(
            name="roaster.bean_temp.celsius",
            description="Bean temperature in Celsius",
            unit="C"
        )
        
        self.chamber_temp = self.meter.create_gauge(
            name="roaster.chamber_temp.celsius",
            description="Chamber temperature in Celsius",
            unit="C"
        )
        
        self.fan_speed = self.meter.create_gauge(
            name="roaster.fan_speed.percent",
            description="Fan speed percentage",
            unit="%"
        )
        
        self.heat_level = self.meter.create_gauge(
            name="roaster.heat_level.percent",
            description="Heat level percentage",
            unit="%"
        )
        
        # Calculated metrics
        self.rate_of_rise = self.meter.create_gauge(
            name="roaster.rate_of_rise.c_per_min",
            description="Rate of temperature rise per minute",
            unit="C/min"
        )
        
        self.development_time_pct = self.meter.create_gauge(
            name="roaster.development_time.percent",
            description="Development time as percentage of total roast",
            unit="%"
        )
        
        # Key temperatures (recorded as events)
        self.charge_temp = self.meter.create_histogram(
            name="roaster.charge_temp.celsius",
            description="Temperature when beans added",
            unit="C"
        )
        
        self.fc_temp = self.meter.create_histogram(
            name="roaster.first_crack_temp.celsius",
            description="Temperature at first crack",
            unit="C"
        )
        
        self.drop_temp = self.meter.create_histogram(
            name="roaster.drop_temp.celsius",
            description="Temperature when beans dropped",
            unit="C"
        )
        
        # Duration
        self.roast_duration = self.meter.create_histogram(
            name="roaster.roast_duration.seconds",
            description="Total roast duration",
            unit="s"
        )
        
        # Control commands
        self.heat_adjustments = self.meter.create_counter(
            name="roaster.heat_adjustments.total",
            description="Number of heat adjustments",
            unit="1"
        )
        
        self.fan_adjustments = self.meter.create_counter(
            name="roaster.fan_adjustments.total",
            description="Number of fan adjustments",
            unit="1"
        )
        
        self.bean_drops = self.meter.create_counter(
            name="roaster.bean_drops.total",
            description="Number of bean drops",
            unit="1"
        )
        
        # Health
        self.sensor_errors = self.meter.create_counter(
            name="roaster.sensor_errors.total",
            description="Sensor read errors",
            unit="1"
        )
        
        self.command_errors = self.meter.create_counter(
            name="roaster.command_errors.total",
            description="Control command errors",
            unit="1"
        )
        
        self.connection_status = self.meter.create_gauge(
            name="roaster.connection.status",
            description="Connection status (0=disconnected, 1=connected)",
            unit="1"
        )
    
    def record_sensors(
        self,
        utc_timestamp: datetime,
        bean_temp_c: float,
        chamber_temp_c: float,
        fan_speed_pct: float,
        heat_level_pct: float
    ):
        """Record sensor readings."""
        attrs = {"utc_timestamp": utc_timestamp.isoformat()}
        
        self.bean_temp.set(bean_temp_c, attributes=attrs)
        self.chamber_temp.set(chamber_temp_c, attributes=attrs)
        self.fan_speed.set(fan_speed_pct, attributes=attrs)
        self.heat_level.set(heat_level_pct, attributes=attrs)
    
    def record_calculated_metrics(
        self,
        utc_timestamp: datetime,
        rate_of_rise_c_per_min: float,
        development_time_pct: float
    ):
        """Record calculated metrics."""
        attrs = {"utc_timestamp": utc_timestamp.isoformat()}
        
        self.rate_of_rise.set(rate_of_rise_c_per_min, attributes=attrs)
        self.development_time_pct.set(development_time_pct, attributes=attrs)
    
    def record_charge_temp(self, utc_timestamp: datetime, temp_c: float):
        """Record charge (beans added) temperature."""
        self.charge_temp.record(
            temp_c,
            attributes={"utc_timestamp": utc_timestamp.isoformat()}
        )
    
    def record_first_crack_temp(self, utc_timestamp: datetime, temp_c: float):
        """Record first crack temperature."""
        self.fc_temp.record(
            temp_c,
            attributes={"utc_timestamp": utc_timestamp.isoformat()}
        )
    
    def record_drop_temp(self, utc_timestamp: datetime, temp_c: float):
        """Record drop (end roast) temperature."""
        self.drop_temp.record(
            temp_c,
            attributes={"utc_timestamp": utc_timestamp.isoformat()}
        )
    
    def record_roast_duration(self, utc_timestamp: datetime, duration_seconds: float):
        """Record total roast duration."""
        self.roast_duration.record(
            duration_seconds,
            attributes={"utc_timestamp": utc_timestamp.isoformat()}
        )
    
    def record_heat_adjustment(self, utc_timestamp: datetime, new_level: float):
        """Record heat level adjustment."""
        self.heat_adjustments.add(
            1,
            attributes={
                "utc_timestamp": utc_timestamp.isoformat(),
                "new_level": str(int(new_level))
            }
        )
    
    def record_fan_adjustment(self, utc_timestamp: datetime, new_speed: float):
        """Record fan speed adjustment."""
        self.fan_adjustments.add(
            1,
            attributes={
                "utc_timestamp": utc_timestamp.isoformat(),
                "new_speed": str(int(new_speed))
            }
        )
    
    def record_bean_drop(self, utc_timestamp: datetime):
        """Record bean drop event."""
        self.bean_drops.add(
            1,
            attributes={"utc_timestamp": utc_timestamp.isoformat()}
        )
    
    def record_sensor_error(self, error_type: str):
        """Record sensor error."""
        self.sensor_errors.add(1, attributes={"error_type": error_type})
    
    def record_command_error(self, command: str, error_type: str):
        """Record control command error."""
        self.command_errors.add(
            1,
            attributes={"command": command, "error_type": error_type}
        )
    
    def set_connection_status(self, connected: bool):
        """Set connection status."""
        self.connection_status.set(1 if connected else 0)


class AgentMetrics:
    """
    Metrics for Autonomous Roasting Agent.
    
    Tracks:
    - Decision making
    - LLM usage
    - Roast outcomes
    - Safety violations
    """
    
    def __init__(self, service_name: str = "roasting-agent", otlp_endpoint: Optional[str] = None):
        """
        Initialize Agent metrics.
        
        Args:
            service_name: Service name for OpenTelemetry
            otlp_endpoint: OTLP endpoint URL
        """
        self.meter = _setup_meter_provider(service_name, otlp_endpoint)
        
        # Decision making
        self.decision_duration = self.meter.create_histogram(
            name="agent.decision.duration",
            description="LLM decision latency",
            unit="s"
        )
        
        self.decisions_total = self.meter.create_counter(
            name="agent.decisions.total",
            description="Total decisions made",
            unit="1"
        )
        
        self.safety_violations = self.meter.create_counter(
            name="agent.safety_violations.total",
            description="Safety check violations",
            unit="1"
        )
        
        # Roast outcomes
        self.roasts_completed = self.meter.create_counter(
            name="agent.roasts_completed.total",
            description="Successfully completed roasts",
            unit="1"
        )
        
        self.roasts_aborted = self.meter.create_counter(
            name="agent.roasts_aborted.total",
            description="Aborted roasts",
            unit="1"
        )
        
        self.target_achievement = self.meter.create_histogram(
            name="agent.target_achievement.ratio",
            description="Percentage of roasts hitting target profile",
            unit="%"
        )
        
        # LLM usage
        self.llm_tokens = self.meter.create_counter(
            name="agent.llm_tokens.total",
            description="Total LLM tokens consumed",
            unit="tokens"
        )
        
        self.llm_errors = self.meter.create_counter(
            name="agent.llm_errors.total",
            description="LLM API errors",
            unit="1"
        )
    
    def record_decision(self, duration_seconds: float, action: str, phase: str):
        """Record agent decision."""
        self.decision_duration.record(duration_seconds)
        self.decisions_total.add(
            1,
            attributes={"action": action, "phase": phase}
        )
    
    def record_safety_violation(self, violation_type: str, value: float):
        """Record safety violation."""
        self.safety_violations.add(
            1,
            attributes={"type": violation_type, "value": str(value)}
        )
    
    def record_roast_completed(self, profile: str, dev_time_pct: float, drop_temp: float):
        """Record successful roast completion."""
        self.roasts_completed.add(
            1,
            attributes={
                "profile": profile,
                "dev_time_pct": str(int(dev_time_pct)),
                "drop_temp": str(int(drop_temp))
            }
        )
    
    def record_roast_aborted(self, profile: str, reason: str):
        """Record aborted roast."""
        self.roasts_aborted.add(
            1,
            attributes={"profile": profile, "reason": reason}
        )
    
    def record_target_achievement(self, achievement_pct: float):
        """Record target achievement percentage."""
        self.target_achievement.record(achievement_pct)
    
    def record_llm_tokens(self, tokens: int, model: str):
        """Record LLM token usage."""
        self.llm_tokens.add(tokens, attributes={"model": model})
    
    def record_llm_error(self, error_type: str):
        """Record LLM error."""
        self.llm_errors.add(1, attributes={"error_type": error_type})
