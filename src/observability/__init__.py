"""
Observability package for coffee roasting system.

Uses OpenTelemetry for logs, metrics, and traces.
Integrates seamlessly with .NET Aspire dashboard via OTLP.
"""

from .logging import setup_logging, get_logger
from .metrics import FirstCrackMetrics, RoasterMetrics, AgentMetrics
from .tracing import setup_tracing, trace_span, get_tracer

__all__ = [
    # Logging
    "setup_logging",
    "get_logger",
    # Metrics
    "FirstCrackMetrics",
    "RoasterMetrics",
    "AgentMetrics",
    # Tracing
    "setup_tracing",
    "trace_span",
    "get_tracer",
]
