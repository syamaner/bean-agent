"""
OpenTelemetry configuration for Python MCP servers.

Automatically configures OTLP export to Aspire Dashboard using environment variables:
- OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (e.g., http://localhost:19065)
- OTEL_EXPORTER_OTLP_PROTOCOL: Protocol (grpc or http/protobuf)
- OTEL_EXPORTER_OTLP_HEADERS: Auth headers (e.g., x-otlp-api-key=...)
- OTEL_SERVICE_NAME: Service name for telemetry
- OTEL_RESOURCE_ATTRIBUTES: Additional resource attributes

These are automatically injected by Aspire AppHost.
"""
import logging
import os
from typing import Optional

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

# Auto-instrumentation for FastAPI/Starlette
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

logger = logging.getLogger(__name__)


def configure_opentelemetry(service_name: Optional[str] = None) -> None:
    """
    Configure OpenTelemetry with OTLP exporters for Aspire Dashboard.
    
    Args:
        service_name: Override service name (defaults to OTEL_SERVICE_NAME env var)
    
    Environment Variables (auto-injected by Aspire):
        OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint URL
        OTEL_EXPORTER_OTLP_PROTOCOL: Protocol (grpc/http/protobuf)
        OTEL_EXPORTER_OTLP_HEADERS: Auth headers
        OTEL_SERVICE_NAME: Service name
        OTEL_RESOURCE_ATTRIBUTES: Resource attributes (key=value,key=value)
    """
    # Check if OTLP endpoint is configured
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otlp_endpoint:
        logger.warning("OTEL_EXPORTER_OTLP_ENDPOINT not set - telemetry disabled")
        return
    
    # Get service name from env or parameter
    service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "unknown-service")
    
    # Parse resource attributes from env
    resource_attrs = {SERVICE_NAME: service_name}
    if resource_attrs_str := os.getenv("OTEL_RESOURCE_ATTRIBUTES"):
        for pair in resource_attrs_str.split(","):
            if "=" in pair:
                key, value = pair.split("=", 1)
                resource_attrs[key.strip()] = value.strip()
    
    resource = Resource(attributes=resource_attrs)
    
    # Configure Tracing
    try:
        tracer_provider = TracerProvider(resource=resource)
        
        # Create OTLP span exporter (reads endpoint/headers from env)
        otlp_span_exporter = OTLPSpanExporter()
        
        # Add batch processor
        span_processor = BatchSpanProcessor(otlp_span_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)
        
        logger.info(f"OpenTelemetry tracing configured: {service_name} -> {otlp_endpoint}")
    except Exception as e:
        logger.error(f"Failed to configure OpenTelemetry tracing: {e}")
    
    # Configure Metrics
    try:
        # Create OTLP metric exporter (reads endpoint/headers from env)
        otlp_metric_exporter = OTLPMetricExporter()
        
        # Periodic export every 10 seconds (faster for dev, matches Aspire defaults)
        metric_export_interval_ms = int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "10000"))
        metric_reader = PeriodicExportingMetricReader(
            otlp_metric_exporter,
            export_interval_millis=metric_export_interval_ms
        )
        
        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader]
        )
        
        # Set global meter provider
        metrics.set_meter_provider(meter_provider)
        
        logger.info(f"OpenTelemetry metrics configured: {service_name} -> {otlp_endpoint}")
    except Exception as e:
        logger.error(f"Failed to configure OpenTelemetry metrics: {e}")
    
    # Configure Logging
    try:
        # Create OTLP log exporter (reads endpoint/headers from env)
        otlp_log_exporter = OTLPLogExporter()
        
        # Create logger provider
        logger_provider = LoggerProvider(resource=resource)
        
        # Add batch processor
        log_export_interval_ms = int(os.getenv("OTEL_BLRP_SCHEDULE_DELAY", "1000"))
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(otlp_log_exporter)
        )
        
        # Attach OTLP handler to root logger
        handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
        logging.getLogger().addHandler(handler)
        
        logger.info(f"OpenTelemetry logging configured: {service_name} -> {otlp_endpoint}")
    except Exception as e:
        logger.error(f"Failed to configure OpenTelemetry logging: {e}")


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer for the given name."""
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    """Get a meter for the given name."""
    return metrics.get_meter(name)


class MCPMetrics:
    """Helper class for collecting MCP-specific metrics."""
    
    def __init__(self, service_name: str):
        self.meter = get_meter(f"{service_name}.mcp")
        
        # Counter: total tool calls
        self.tool_calls = self.meter.create_counter(
            name="mcp.tool.calls",
            description="Total number of MCP tool calls",
            unit="1"
        )
        
        # Counter: tool call errors
        self.tool_errors = self.meter.create_counter(
            name="mcp.tool.errors",
            description="Number of MCP tool call errors",
            unit="1"
        )
        
        # Histogram: tool call duration
        self.tool_duration = self.meter.create_histogram(
            name="mcp.tool.duration",
            description="Duration of MCP tool calls",
            unit="ms"
        )
        
        # UpDownCounter: active sessions (for stateful servers)
        self.active_sessions = self.meter.create_up_down_counter(
            name="mcp.sessions.active",
            description="Number of active MCP sessions",
            unit="1"
        )
    
    def record_tool_call(self, tool_name: str, duration_ms: float, success: bool = True, **attributes):
        """Record a tool call with metrics."""
        attrs = {"tool.name": tool_name, "success": str(success), **attributes}
        
        self.tool_calls.add(1, attrs)
        self.tool_duration.record(duration_ms, attrs)
        
        if not success:
            self.tool_errors.add(1, {"tool.name": tool_name, **attributes})


def instrument_fastapi(app) -> None:
    """Auto-instrument FastAPI/Starlette app for HTTP tracing."""
    if FASTAPI_AVAILABLE:
        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI/Starlette auto-instrumentation enabled")
        except Exception as e:
            logger.error(f"Failed to instrument FastAPI: {e}")
    else:
        logger.warning("FastAPI instrumentation not available")
