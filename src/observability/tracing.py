"""
OpenTelemetry distributed tracing for coffee roasting system.

Provides context propagation and span instrumentation across
MCP servers, agent, and internal components.
"""
import os
from contextlib import contextmanager
from typing import Optional, Dict, Any
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.flask import FlaskInstrumentor


def setup_tracing(
    service_name: str,
    otlp_endpoint: Optional[str] = None,
    auto_instrument: bool = True
) -> trace.Tracer:
    """
    Configure OpenTelemetry tracing for a service.
    
    Args:
        service_name: Name of the service (e.g., "first-crack-mcp")
        otlp_endpoint: OTLP endpoint URL (default: from env or http://localhost:4317)
        auto_instrument: Auto-instrument HTTP libraries (default: True)
        
    Returns:
        trace.Tracer: Configured tracer instance
        
    Environment Variables:
        OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint
        OTEL_TRACES_EXPORTER: Set to "otlp" to enable
    """
    # Determine endpoint
    if otlp_endpoint is None:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    
    # Create resource with service name
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
    })
    
    # Create TracerProvider
    provider = TracerProvider(resource=resource)
    
    # Add OTLP exporter
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Set global tracer provider
    trace.set_tracer_provider(provider)
    
    # Auto-instrument HTTP libraries
    if auto_instrument:
        try:
            RequestsInstrumentor().instrument()
            print(f"Auto-instrumented: requests library")
        except Exception as e:
            print(f"Warning: Could not instrument requests: {e}")
        
        try:
            FlaskInstrumentor().instrument()
            print(f"Auto-instrumented: Flask")
        except Exception as e:
            print(f"Warning: Could not instrument Flask: {e}")
    
    print(f"OpenTelemetry tracing configured for {service_name} → {otlp_endpoint}")
    
    return trace.get_tracer(service_name)


def get_tracer(name: str) -> trace.Tracer:
    """
    Get a tracer instance.
    
    Args:
        name: Tracer name (typically service or module name)
        
    Returns:
        trace.Tracer: Tracer instance
    """
    return trace.get_tracer(name)


@contextmanager
def trace_span(
    tracer: trace.Tracer,
    span_name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL
):
    """
    Context manager for creating a trace span.
    
    Args:
        tracer: Tracer instance
        span_name: Name of the span
        attributes: Optional span attributes
        kind: Span kind (INTERNAL, CLIENT, SERVER, etc.)
        
    Yields:
        trace.Span: Active span
        
    Example:
        tracer = get_tracer(__name__)
        with trace_span(tracer, "inference", {"model": "ast"}):
            # ... do work ...
            pass
    """
    with tracer.start_as_current_span(span_name, kind=kind) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span


def add_span_event(span: trace.Span, name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Add an event to the current span.
    
    Args:
        span: Span to add event to
        name: Event name
        attributes: Optional event attributes
        
    Example:
        span.add_event("first_crack_detected", {"confidence": 0.87})
    """
    if attributes:
        span.add_event(name, attributes=attributes)
    else:
        span.add_event(name)


def record_exception(span: trace.Span, exception: Exception):
    """
    Record an exception in the current span.
    
    Args:
        span: Span to record exception in
        exception: Exception to record
    """
    span.record_exception(exception)
    span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))
