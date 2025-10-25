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
from .config import load_config
from .session_manager import RoasterSessionManager
from .utils import setup_logging

# Import shared Auth0 middleware
from src.mcp_servers.shared.auth0_middleware import (
    validate_auth0_token,
    check_user_scope,
    get_user_info,
    log_user_action
)


# Global state
mcp_server = Server("roaster-control")
session_manager: RoasterSessionManager = None
config = None
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
                
                # Check scopes (user must have at least one roaster scope)
                has_read = check_user_scope(payload, "read:roaster")
                has_write = check_user_scope(payload, "write:roaster")
                
                if not (has_read or has_write):
                    user = get_user_info(payload)
                    return JSONResponse(
                        {
                            "error": "Insufficient permissions",
                            "required_scopes": ["read:roaster OR write:roaster"],
                            "your_scopes": user["scopes"],
                            "user_email": user["email"]
                        },
                        status_code=403
                    )
                
                # Store payload and user info in request state
                request.state.auth = payload
                request.state.user = get_user_info(payload)
                
                # Log connection
                logger.info(f"MCP connection from user: {request.state.user['email']}")
                
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
    from .server import (
        handle_read_status,
        handle_start_roaster,
        handle_stop_roaster,
        handle_set_heat,
        handle_set_fan,
        handle_drop_beans,
        handle_start_cooling,
        handle_stop_cooling,
        handle_report_first_crack
    )
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
                "session_active": session_manager.current_session is not None,
                "roaster_connected": session_manager.roaster is not None
            }
            
            if session_manager.current_session:
                health_data["session_id"] = session_manager.current_session.session_id
                health_data["roaster_running"] = session_manager.current_session.roaster_running
            
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
            # Map tool names to handlers
            handlers = {
                "read_roaster_status": handle_read_status,
                "start_roaster": handle_start_roaster,
                "stop_roaster": handle_stop_roaster,
                "set_heat": handle_set_heat,
                "set_fan": handle_set_fan,
                "drop_beans": handle_drop_beans,
                "start_cooling": handle_start_cooling,
                "stop_cooling": handle_stop_cooling,
                "report_first_crack": handle_report_first_crack
            }
            
            if name not in handlers:
                result = {"error": f"Unknown tool: {name}"}
            else:
                # Execute handler
                result = await handlers[name](arguments)
                
                # Log user action (audit trail)
                # Note: We don't have access to request.state here,
                # so we'll log without user info for now
                # TODO: Pass user context through MCP session
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
        "session_active": session_manager.current_session is not None,
        "roaster_connected": session_manager.roaster is not None
    })


# Lifespan
@asynccontextmanager
async def lifespan(app):
    """Initialize on startup, cleanup on shutdown."""
    global session_manager, config
    
    # Startup
    config = load_config()
    setup_logging(config)
    session_manager = RoasterSessionManager(config)
    setup_mcp_server()
    
    logger.info("Roaster Control MCP Server (HTTP+SSE) initialized")
    logger.info(f"Mock mode: {config.mock_mode}")
    
    yield
    
    # Shutdown
    if session_manager and session_manager.current_session:
        try:
            session_manager.stop_roaster()
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
