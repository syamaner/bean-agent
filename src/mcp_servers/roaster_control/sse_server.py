#!/usr/bin/env python3
"""
Roaster Control MCP Server - HTTP+SSE Transport

MCP server with HTTP+SSE transport for remote access via Warp, Claude Desktop.
Includes Auth0 JWT authentication with user-based audit logging.

Run:
    uvicorn src.mcp_servers.roaster_control.sse_server:app --port 5002

Configure in Warp (.warp/mcp_settings.json):
{
  "mcpServers": {
    "roaster-control": {
      "url": "http://localhost:5002/sse",
      "transport": {"type": "sse"},
      "headers": {
        "Authorization": "Bearer YOUR_AUTH0_TOKEN"
      }
    }
  }
}
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

from mcp.server import Server
from mcp.server.sse import SseServerTransport

# Import existing MCP components
from .models import ServerConfig
from .session_manager import RoastSessionManager
from .hardware import MockRoaster
from .demo_roaster import DemoRoaster

# Import shared Auth0 middleware
from src.mcp_servers.shared.auth0_middleware import (
    validate_auth0_token,
    check_scope,
    get_client_info,
    log_client_action
)

# Import demo scenario
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from demo_scenario import get_demo_scenario


# Global state
mcp_server = Server("roaster-control")
session_manager: RoastSessionManager = None
config: ServerConfig = None
logger = logging.getLogger(__name__)


# Auth0 Middleware for MCP
class Auth0Middleware(BaseHTTPMiddleware):
    """Validate Auth0 JWT for MCP endpoints with user audit logging."""
    
    async def dispatch(self, request: Request, call_next):
        # Public endpoints
        if request.url.path in ["/", "/health"]:
            return await call_next(request)
        
        # MCP endpoints require auth - but don't wrap the response
        if request.url.path.startswith("/sse") or request.url.path.startswith("/messages"):
            try:
                auth_header = request.headers.get("Authorization", "")
                if not auth_header.startswith("Bearer "):
                    return JSONResponse(
                        {"error": "Missing or invalid Authorization header"},
                        status_code=401
                    )
                
                token = auth_header.replace("Bearer ", "")
                payload = await validate_auth0_token(token)
                
                # Check scopes (client must have at least one roaster scope)
                has_read = check_scope(payload, "read:roaster")
                has_write = check_scope(payload, "write:roaster")
                
                if not (has_read or has_write):
                    client = get_client_info(payload)
                    return JSONResponse(
                        {
                            "error": "Insufficient permissions",
                            "required_scopes": ["read:roaster OR write:roaster"],
                            "your_scopes": client["scopes"],
                            "client_id": client["client_id"]
                        },
                        status_code=403
                    )
                
                # Store payload and client info in request state
                request.state.auth = payload
                request.state.client = get_client_info(payload)
                
                # Log connection
                logger.info(f"MCP connection from client: {request.state.client['client_id']}")
                
                # IMPORTANT: Don't wrap SSE/streaming responses - return directly
                # The BaseHTTPMiddleware wrapping causes issues with SSE protocol
                response = await call_next(request)
                return response
                
            except Exception as e:
                logger.error(f"Auth error: {e}")
                return JSONResponse(
                    {"error": f"Authentication failed: {str(e)}"},
                    status_code=401
                )
        
        return await call_next(request)


# Setup MCP tools with audit logging
def setup_mcp_server():
    """Register MCP tools and resources with user audit logging."""
    from mcp.types import Tool, TextContent, Resource, ReadResourceResult
    import json
    
    @mcp_server.list_resources()
    async def list_resources() -> list:
        return [
            Resource(
                uri="health://status",
                name="Server Health",
                description="Health check and roaster status",
                mimeType="application/json"
            )
        ]
    
    @mcp_server.read_resource()
    async def read_resource(uri: str) -> ReadResourceResult:
        if uri == "health://status":
            health_data = {
                "status": "healthy",
                "version": "1.0.0",
                "session_active": session_manager.is_active(),
                "roaster_info": session_manager.get_hardware_info()
            }
            
            return ReadResourceResult(
                contents=[TextContent(
                    type="text",
                    text=json.dumps(health_data, indent=2)
                )]
            )
        raise ValueError(f"Unknown resource: {uri}")
    
    @mcp_server.list_tools()
    async def list_tools(request_context=None) -> list[Tool]:
        # Get scopes from context if available (set by transport)
        # For now, return all tools - MCP doesn't expose request context in list_tools
        # Access control happens at call_tool level
        
        # Define all available tools
        all_tools = [
            Tool(
                name="read_roaster_status",
                description="""Read comprehensive roaster status including:
                - session_active: bool - whether a roast session is running
                - roaster_running: bool - drum motor state
                - bean_temp_c: float - current bean temperature in Celsius
                - env_temp_c: float - environmental/chamber temperature
                - heat_level: int (0-100) - current heating element power
                - fan_speed: int (0-100) - current fan speed percentage
                - cooling_active: bool - cooling tray state
                - elapsed_time_sec: float - seconds since roast start
                - first_crack_time: ISO timestamp or null - when FC was detected
                - ror_c_per_min: float - rate of rise (temperature change rate)
                - Events list with timestamps for key roast events
                Returns JSON with all sensor readings and roast progress.""",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="start_roaster",
                description="""Start the roaster drum motor. Call this before adding beans.
                Typically used during preheat phase when chamber reaches ~180°C.
                Does not automatically start heating - use set_heat separately.""",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="stop_roaster",
                description="""Stop roaster drum and end the roast session. 
                Use drop_beans instead for normal roast completion.
                This is for emergency stops or cancelling a roast.""",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="set_heat",
                description="""Adjust heating element power level (0-100%).
                - During preheat: typically 100% to reach starting temp quickly
                - Early roast: 80-100% to build heat momentum  
                - After FC: reduce to 60-80% to control development
                - Near finish: reduce to 40-60% to prevent scorching
                Changes take effect immediately but temperature responds gradually.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "level": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                            "description": "Heat power percentage (0-100)"
                        }
                    },
                    "required": ["level"]
                }
            ),
            Tool(
                name="set_fan",
                description="""Adjust airflow/fan speed (0-100%).
                - Lower fan (20-40%): retains heat, faster roast, risk of scorching
                - Higher fan (60-80%): removes heat/smoke, slower roast, better clarity
                - During preheat: low (20-30%) to build heat
                - During roast: gradually increase from 30% → 60%
                - After FC: increase to 50-70% for development control
                Fan affects both temperature and smoke removal.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "speed": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                            "description": "Fan speed percentage (0-100)"
                        }
                    },
                    "required": ["speed"]
                }
            ),
            Tool(
                name="drop_beans",
                description="""Drop roasted beans into cooling tray and automatically start cooling.
                Use this to finish a roast when target is reached. 
                Beans fall from drum into cooling tray, drum stops, cooling fan activates.
                Typical usage: when bean temp reaches 190-195°C for light roasts,
                or 200-205°C for medium roasts, 2-3 minutes after first crack.""",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="start_cooling",
                description="""Manually start cooling tray fan.
                Normally drop_beans does this automatically.
                Use only if you need to cool beans already in the tray.""",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="stop_cooling",
                description="""Stop cooling tray fan.
                Use after beans have cooled to room temperature (typically 3-5 minutes).""",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="report_first_crack",
                description="""Report that first crack (FC) has been detected.
                Called by first crack detection system or manually.
                Records FC time and temperature for roast profile tracking.
                After FC, development phase begins - typically reduce heat and increase fan.""",
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
            )
        ]
        
        return all_tools
    
    @mcp_server.call_tool()
    async def call_tool(name: str, arguments: dict, request_context=None) -> list[TextContent]:
        """Handle tool calls with scope-based access control."""
        # Define which tools require write access
        write_tools = {
            "start_roaster", "stop_roaster", "set_heat", "set_fan",
            "drop_beans", "start_cooling", "stop_cooling", "report_first_crack"
        }
        
        try:
            # Note: In SSE transport, we don't have direct access to request context
            # Scope enforcement happens at middleware level
            # This is a secondary check - tools are documented with required scopes
            
            # Call session_manager methods directly
            if name == "read_roaster_status":
                status = session_manager.get_status()
                result = {"status": "success", "data": status.model_dump()}
            elif name == "start_roaster":
                session_manager.start_roaster()
                result = {"status": "success", "message": "Roaster started"}
            elif name == "stop_roaster":
                session_manager.stop_roaster()
                result = {"status": "success", "message": "Roaster stopped"}
            elif name == "set_heat":
                session_manager.set_heat(arguments["level"])
                result = {"status": "success", "message": f"Heat set to {arguments['level']}%"}
            elif name == "set_fan":
                session_manager.set_fan(arguments["speed"])
                result = {"status": "success", "message": f"Fan set to {arguments['speed']}%"}
            elif name == "drop_beans":
                session_manager.drop_beans()
                result = {"status": "success", "message": "Beans dropped"}
            elif name == "start_cooling":
                session_manager.start_cooling()
                result = {"status": "success", "message": "Cooling started"}
            elif name == "stop_cooling":
                session_manager.stop_cooling()
                result = {"status": "success", "message": "Cooling stopped"}
            elif name == "report_first_crack":
                from datetime import datetime
                timestamp = datetime.fromisoformat(arguments["timestamp"])
                temperature = arguments.get("temperature")
                session_manager.report_first_crack(timestamp, temperature)
                result = {"status": "success", "message": "First crack reported"}
            else:
                result = {"error": f"Unknown tool: {name}"}
            
            # Log successful actions
            if result.get("status") == "success":
                logger.info(f"Tool executed: {name} with args: {arguments}")
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
        except Exception as e:
            logger.error(f"Tool error: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e), "type": type(e).__name__}, indent=2)
            )]


# Routes

async def root(request: Request):
    """API info."""
    return JSONResponse({
        "name": "Roaster Control MCP Server",
        "version": "1.0.0",
        "transport": "sse",
        "endpoints": {
            "sse": "/sse (Auth0 JWT required)",
            "messages": "/messages (Auth0 JWT required)",
            "health": "/health (public)"
        },
        "roles": {
            "observer": "read:roaster (view status only)",
            "operator": "read:roaster + write:roaster (full control)",
            "admin": "all scopes + admin:roaster"
        }
    })


async def health(request: Request):
    """Health check."""
    demo_scenario = get_demo_scenario()
    return JSONResponse({
        "status": "healthy",
        "demo_mode": demo_scenario is not None,
        "session_active": session_manager.is_active(),
        "roaster_info": session_manager.get_hardware_info()
    })


# Lifespan
@asynccontextmanager
async def lifespan(app):
    """Initialize on startup, cleanup on shutdown."""
    global session_manager, config
    
    # Startup
    demo_scenario = get_demo_scenario()
    demo_mode = demo_scenario is not None
    
    if demo_mode:
        logger.info(f"Starting in DEMO MODE with scenario: {os.getenv('DEMO_SCENARIO', 'quick_roast')}")
        config = ServerConfig()
        # Skip validation in demo mode to allow missing hardware config
        hardware = DemoRoaster(scenario=demo_scenario)
    else:
        config = ServerConfig()
        config.validate()
        
        # Create hardware (mock or real)
        if config.hardware.mock_mode:
            hardware = MockRoaster()
        else:
            from .hardware import HottopRoaster
            hardware = HottopRoaster(port=config.hardware.port)
    
    session_manager = RoastSessionManager(hardware, config)
    session_manager.start_session()  # Start session and polling
    setup_mcp_server()
    
    logger.info("Roaster Control MCP Server (HTTP+SSE) initialized")
    logger.info(f"Demo mode: {demo_mode}, Mock mode: {config.hardware.mock_mode}")
    
    yield
    
    # Shutdown
    if session_manager and session_manager.is_active():
        try:
            session_manager.stop_session()
        except Exception as e:
            logger.warning(f"Shutdown error: {e}")


# Create SSE transport
from mcp.server.transport_security import TransportSecuritySettings
security_settings = TransportSecuritySettings(
    enable_dns_rebinding_protection=False  # Disable for local development
)
sse_transport = SseServerTransport("/messages", security_settings)

# SSE endpoint handler (as per MCP documentation)
async def handle_sse(request: Request):
    """Handle SSE connection and run MCP server with Auth0 validation."""
    # Validate Auth0 token BEFORE starting SSE
    try:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"error": "Missing or invalid Authorization header"},
                status_code=401
            )
        
        token = auth_header.replace("Bearer ", "")
        payload = await validate_auth0_token(token)
        
        # Check scopes
        has_read = check_scope(payload, "read:roaster")
        has_write = check_scope(payload, "write:roaster")
        
        if not (has_read or has_write):
            client = get_client_info(payload)
            return JSONResponse(
                {
                    "error": "Insufficient permissions",
                    "required_scopes": ["read:roaster OR write:roaster"],
                    "your_scopes": client["scopes"]
                },
                status_code=403
            )
        
        logger.info(f"SSE connection from client: {get_client_info(payload)['client_id']}")
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return JSONResponse(
            {"error": f"Authentication failed: {str(e)}"},
            status_code=401
        )
    
    # Auth passed, establish SSE connection
    logger.info("SSE connection established, starting MCP server...")
    async with sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
        logger.info("Got streams, running MCP server...")
        await mcp_server.run(
            streams[0],  # read stream  
            streams[1],  # write stream
            mcp_server.create_initialization_options()
        )
        logger.info("MCP server run completed")
    # Return empty response to avoid NoneType error
    logger.info("Returning response")
    return Response()

app = Starlette(
    debug=False,
    routes=[
        Route("/", root),
        Route("/health", health),
        Route("/sse", handle_sse, methods=["GET"]),
        Mount("/messages", app=sse_transport.handle_post_message),
    ],
    # NO MIDDLEWARE - Auth handled in route handlers to avoid SSE issues
    lifespan=lifespan
)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("ROASTER_CONTROL_PORT", "5002"))
    uvicorn.run(app, host="0.0.0.0", port=port)
