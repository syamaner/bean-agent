"""Shared utilities for MCP servers."""

from .otel_config import configure_opentelemetry, instrument_fastapi, get_tracer, get_meter

__all__ = [
    "configure_opentelemetry",
    "instrument_fastapi",
    "get_tracer",
    "get_meter",
]
