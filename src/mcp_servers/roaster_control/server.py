"""MCP server for roaster control."""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from mcp.server import Server
from mcp.types import Tool, TextContent, Resource

from .session_manager import RoastSessionManager
from .hardware import MockRoaster
from .models import ServerConfig
from .exceptions import RoasterError

# Add parent directories to path for observability
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import observability
try:
    from observability import (
        setup_logging as setup_otel_logging,
        setup_tracing,
        RoasterMetrics,
        get_logger as get_otel_logger,
        trace_span,
        get_tracer
    )
    OBSERVABILITY_ENABLED = True
except ImportError:
    print("Warning: Observability package not available", file=sys.stderr)
    OBSERVABILITY_ENABLED = False

# Global state
_session_manager: Optional[RoastSessionManager] = None
_config: Optional[ServerConfig] = None

# Observability instances
if OBSERVABILITY_ENABLED:
    otel_logger = None
    tracer = None
    metrics = None

# Create MCP server
server = Server("roaster-control")


def init_server(config: Optional[ServerConfig] = None) -> None:
    """Initialize server with configuration.
    
    Args:
        config: Server configuration (uses defaults if None)
    
    Raises:
        ValueError: If configuration is invalid
    """
    global _session_manager, _config, otel_logger, tracer, metrics
    
    # Initialize observability
    if OBSERVABILITY_ENABLED:
        try:
            setup_otel_logging("roaster-control-mcp")
            tracer = setup_tracing("roaster-control-mcp")
            metrics = RoasterMetrics("roaster-control-mcp")
            otel_logger = get_otel_logger(__name__)
            otel_logger.info("Observability initialized")
        except Exception as e:
            print(f"Failed to initialize observability: {e}", file=sys.stderr)
    
    if config is None:
        config = ServerConfig()
    
    # Simple mock flag for testing
    use_mock = os.getenv("USE_MOCK_HARDWARE", "false").lower() == "true"
    
    if use_mock:
        # Override config to reflect mock mode
        config.hardware.mock_mode = True
        hardware = MockRoaster()
        if OBSERVABILITY_ENABLED and otel_logger:
            otel_logger.info("Using mock roaster hardware")
    else:
        config.validate()
        from .hardware import HottopRoaster
        hardware = HottopRoaster(port=config.hardware.port)
        if OBSERVABILITY_ENABLED and otel_logger:
            otel_logger.info("Using real Hottop hardware", extra={"port": config.hardware.port})
    
    _config = config
    _session_manager = RoastSessionManager(hardware, _config)
    
    if OBSERVABILITY_ENABLED and otel_logger:
        otel_logger.info("Roaster session manager initialized")


# ----- Tool Implementations -----

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="set_heat",
            description="Set roaster heat level (0-100% in 10% increments)",
            inputSchema={
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "Heat level percentage (0-100 in 10% increments)",
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["level"]
            }
        ),
        Tool(
            name="set_fan",
            description="Set roaster fan speed (0-100% in 10% increments)",
            inputSchema={
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "integer",
                        "description": "Fan speed percentage (0-100 in 10% increments)",
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["speed"]
            }
        ),
        Tool(
            name="start_roaster",
            description="Start roaster drum motor",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="stop_roaster",
            description="Stop roaster drum motor",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="drop_beans",
            description="Open bean drop door and start cooling",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="start_cooling",
            description="Start cooling fan motor",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="stop_cooling",
            description="Stop cooling fan motor",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="report_first_crack",
            description="Report first crack detection (called by agent after FC MCP detects)",
            inputSchema={
                "type": "object",
                "properties": {
                    "timestamp": {
                        "type": "string",
                        "description": "ISO 8601 UTC timestamp when first crack occurred"
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Bean temperature in °C at first crack"
                    }
                },
                "required": ["timestamp", "temperature"]
            }
        ),
        Tool(
            name="get_roast_status",
            description="Get complete roast status including sensors, metrics, and timestamps",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if _session_manager is None:
        return [TextContent(
            type="text",
            text="Error: Server not initialized. Call init_server() first."
        )]
    
    try:
        if name == "set_heat":
            level = arguments["level"]
            
            if OBSERVABILITY_ENABLED and otel_logger:
                otel_logger.info("Setting heat level", extra={"level": level})
            
            if OBSERVABILITY_ENABLED and tracer:
                with trace_span(tracer, "set_heat", {"level": level}):
                    _session_manager.set_heat(level)
            else:
                _session_manager.set_heat(level)
            
            # Record metric
            if OBSERVABILITY_ENABLED and metrics:
                metrics.record_heat_adjustment(datetime.now(datetime.UTC), level)
            
            return [TextContent(
                type="text",
                text=f"Heat set to {level}%"
            )]
        
        elif name == "set_fan":
            speed = arguments["speed"]
            
            if OBSERVABILITY_ENABLED and otel_logger:
                otel_logger.info("Setting fan speed", extra={"speed": speed})
            
            if OBSERVABILITY_ENABLED and tracer:
                with trace_span(tracer, "set_fan", {"speed": speed}):
                    _session_manager.set_fan(speed)
            else:
                _session_manager.set_fan(speed)
            
            # Record metric
            if OBSERVABILITY_ENABLED and metrics:
                metrics.record_fan_adjustment(datetime.now(datetime.UTC), speed)
            
            return [TextContent(
                type="text",
                text=f"Fan set to {speed}%"
            )]
        
        elif name == "start_roaster":
            _session_manager.start_roaster()
            return [TextContent(
                type="text",
                text="Roaster drum started"
            )]
        
        elif name == "stop_roaster":
            _session_manager.stop_roaster()
            return [TextContent(
                type="text",
                text="Roaster drum stopped"
            )]
        
        elif name == "drop_beans":
            _session_manager.drop_beans()
            return [TextContent(
                type="text",
                text="Beans dropped, cooling started"
            )]
        
        elif name == "start_cooling":
            _session_manager.start_cooling()
            return [TextContent(
                type="text",
                text="Cooling fan started"
            )]
        
        elif name == "stop_cooling":
            _session_manager.stop_cooling()
            return [TextContent(
                type="text",
                text="Cooling fan stopped"
            )]
        
        elif name == "report_first_crack":
            timestamp_str = arguments["timestamp"]
            temperature = arguments["temperature"]
            
            # Validate temperature range (typical first crack range)
            if not (150.0 <= temperature <= 250.0):
                return [TextContent(
                    type="text",
                    text=f"Error: First crack temperature must be between 150°C and 250°C, got {temperature}°C"
                )]
            
            # Parse ISO timestamp and ensure UTC
            try:
                from datetime import UTC
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                # Convert to UTC if not already
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=UTC)
                elif timestamp.tzinfo != UTC:
                    timestamp = timestamp.astimezone(UTC)
            except ValueError as e:
                return [TextContent(
                    type="text",
                    text=f"Error: Invalid timestamp format '{timestamp_str}': {e}"
                )]
            
            _session_manager.report_first_crack(timestamp, temperature)
            return [TextContent(
                type="text",
                text=f"First crack reported at {timestamp_str}, {temperature}°C"
            )]
        
        elif name == "get_roast_status":
            if OBSERVABILITY_ENABLED and tracer:
                with trace_span(tracer, "get_roast_status"):
                    status = _session_manager.get_status()
            else:
                status = _session_manager.get_status()
            
            # Record sensor metrics
            if OBSERVABILITY_ENABLED and metrics and status.sensors:
                from datetime import timezone
                metrics.record_sensors(
                    utc_timestamp=datetime.now(timezone.utc),
                    bean_temp_c=status.sensors.bean_temp,
                    chamber_temp_c=status.sensors.chamber_temp,
                    fan_speed_pct=float(status.sensors.fan_speed),
                    heat_level_pct=float(status.sensors.heat_level)
                )
                
                # Record calculated metrics if available
                if status.metrics:
                    metrics.record_calculated_metrics(
                        utc_timestamp=datetime.now(timezone.utc),
                        rate_of_rise_c_per_min=status.metrics.rate_of_rise_c_per_min,
                        development_time_pct=status.metrics.development_time_percent
                    )
            
            # Convert to dict for JSON serialization
            import json
            # Use mode='json' to serialize datetime objects as ISO strings
            status_dict = status.model_dump(mode='json')
            
            return [TextContent(
                type="text",
                text=json.dumps(status_dict, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except RoasterError as e:
        return [TextContent(
            type="text",
            text=f"Error: {str(e)} (code: {e.error_code})"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


# ----- Resources -----

@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="health://status",
            name="Server Health",
            mimeType="application/json",
            description="Health check and server status"
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content."""
    if uri == "health://status":
        import json
        import os
        
        use_mock = os.getenv("USE_MOCK_HARDWARE", "false").lower() == "true"
        hardware_mode = "mock" if use_mock else "real"
        
        health_data = {
            "status": "healthy",
            "version": "1.0.0",
            "hardware_mode": hardware_mode,
            "session_active": _session_manager.is_active() if _session_manager else False,
            "roaster_info": _session_manager.get_hardware_info() if _session_manager else None
        }
        
        return json.dumps(health_data, indent=2)
    
    raise ValueError(f"Unknown resource: {uri}")
