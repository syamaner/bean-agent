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
from .demo_roaster import DemoRoaster
from .models import ServerConfig
from .exceptions import RoasterError

# Import demo scenario from shared location
sys.path.insert(0, str(Path(__file__).parent.parent))
from demo_scenario import get_demo_scenario

# Global state
_session_manager: Optional[RoastSessionManager] = None
_config: Optional[ServerConfig] = None
_demo_mode: bool = False
_demo_scenario = None

# Create MCP server
server = Server("roaster-control")


def init_server(config: Optional[ServerConfig] = None) -> None:
    """Initialize server with configuration.
    
    Args:
        config: Server configuration (uses defaults if None)
    
    Raises:
        ValueError: If configuration is invalid
    """
    global _session_manager, _config, _demo_mode, _demo_scenario
    
    # Check for demo mode from shared scenario
    _demo_scenario = get_demo_scenario()
    _demo_mode = _demo_scenario is not None
    
    if config is None:
        config = ServerConfig()
    
    # Validate configuration (skip some checks in demo mode)
    if not _demo_mode:
        config.validate()
    
    _config = config
    
    # Create hardware (demo/mock/real based on config and scenario)
    if _demo_mode:
        hardware = DemoRoaster(scenario=_demo_scenario)
    elif _config.hardware.mock_mode:
        hardware = MockRoaster()
    else:
        from .hardware import HottopRoaster
        hardware = HottopRoaster(port=_config.hardware.port)
    
    _session_manager = RoastSessionManager(hardware, _config)


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
            _session_manager.set_heat(level)
            return [TextContent(
                type="text",
                text=f"Heat set to {level}%"
            )]
        
        elif name == "set_fan":
            speed = arguments["speed"]
            _session_manager.set_fan(speed)
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
            status = _session_manager.get_status()
            
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
        
        hardware_mode = "demo" if _demo_mode else ("mock" if _config.hardware.mock_mode else "real")
        
        health_data = {
            "status": "healthy",
            "version": "1.0.0",
            "hardware_mode": hardware_mode,
            "demo_mode": _demo_mode,
            "session_active": _session_manager.is_active() if _session_manager else False,
            "roaster_info": _session_manager.get_hardware_info() if _session_manager else None
        }
        
        return json.dumps(health_data, indent=2)
    
    raise ValueError(f"Unknown resource: {uri}")
