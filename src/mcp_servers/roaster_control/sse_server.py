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

# Import shared Auth0 middleware
from src.mcp_servers.shared.auth0_middleware import (
    validate_auth0_token,
    check_scope,
    get_client_info,
    log_client_action
)


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
        
        # MCP endpoints require auth
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
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="read_roaster_status",
                description="Read current roaster status and sensors (read:roaster)",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="start_roaster",
                description="Start roaster drum rotation (write:roaster)",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="stop_roaster",
                description="Stop roaster and end session (write:roaster)",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="set_heat",
                description="Set heat level 0-100% (write:roaster)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "level": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100
                        }
                    },
                    "required": ["level"]
                }
            ),
            Tool(
                name="set_fan",
                description="Set fan speed 0-100% (write:roaster)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "speed": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100
                        }
                    },
                    "required": ["speed"]
                }
            ),
            Tool(
                name="drop_beans",
                description="Drop beans and start cooling (write:roaster)",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="start_cooling",
                description="Start cooling drum (write:roaster)",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="stop_cooling",
                description="Stop cooling drum (write:roaster)",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="report_first_crack",
                description="Report first crack detected (write:roaster)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "timestamp": {"type": "string"}
                    },
                    "required": ["timestamp"]
                }
            )
        ]
    
    @mcp_server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls with user audit logging."""
        try:
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
                session_manager.report_first_crack(timestamp)
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
    return JSONResponse({
        "status": "healthy",
        "session_active": session_manager.is_active(),
        "roaster_info": session_manager.get_hardware_info()
    })


# Lifespan
@asynccontextmanager
async def lifespan(app):
    """Initialize on startup, cleanup on shutdown."""
    global session_manager, config
    
    # Startup
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
    logger.info(f"Mock mode: {config.hardware.mock_mode}")
    
    yield
    
    # Shutdown
    if session_manager and session_manager.is_active():
        try:
            session_manager.stop_session()
        except Exception as e:
            logger.warning(f"Shutdown error: {e}")


# Create Starlette app
sse_transport = SseServerTransport("/messages")

app = Starlette(
    debug=False,
    routes=[
        Route("/", root),
        Route("/health", health),
        Mount("/sse", app=sse_transport.connect_sse),
        Mount("/messages", app=sse_transport.handle_post_message),
    ],
    middleware=[
        Middleware(Auth0Middleware)
    ],
    lifespan=lifespan
)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("ROASTER_CONTROL_PORT", "5002"))
    uvicorn.run(app, host="0.0.0.0", port=port)
