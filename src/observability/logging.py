"""
OpenTelemetry-based structured logging.

Configures Python logging to emit structured logs via OpenTelemetry LogEmitter.
Logs are automatically exported to .NET Aspire dashboard via OTLP.
"""
import logging
import os
from typing import Optional
from opentelemetry import _logs
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource


def setup_logging(
    service_name: str,
    otlp_endpoint: Optional[str] = None,
    log_level: str = "INFO"
) -> None:
    """
    Configure OpenTelemetry logging for a service.
    
    Args:
        service_name: Name of the service (e.g., "first-crack-mcp")
        otlp_endpoint: OTLP endpoint URL (default: from env or http://localhost:4317)
        log_level: Python log level (default: INFO)
    
    Environment Variables:
        OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint
        OTEL_LOGS_EXPORTER: Set to "otlp" to enable
        LOG_LEVEL: Override log level
    """
    # Determine endpoint
    if otlp_endpoint is None:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    
    # Determine log level
    log_level = os.getenv("LOG_LEVEL", log_level).upper()
    
    # Create resource with service name
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
    })
    
    # Create LoggerProvider
    logger_provider = LoggerProvider(resource=resource)
    
    # Add OTLP exporter
    otlp_exporter = OTLPLogExporter(endpoint=otlp_endpoint, insecure=True)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_exporter))
    
    # Set global logger provider
    _logs.set_logger_provider(logger_provider)
    
    # Configure Python logging to use OpenTelemetry
    handler = LoggingHandler(logger_provider=logger_provider)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),  # Console output
            handler  # OpenTelemetry handler
        ]
    )
    
    logging.info(
        f"OpenTelemetry logging configured",
        extra={
            "service_name": service_name,
            "otlp_endpoint": otlp_endpoint,
            "log_level": log_level
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Logger instance that emits to OpenTelemetry
        
    Example:
        logger = get_logger(__name__)
        logger.info("First crack detected", extra={"confidence": 0.87})
    """
    return logging.getLogger(name)
