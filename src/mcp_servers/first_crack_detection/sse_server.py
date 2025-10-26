#!/usr/bin/env python3
"""
First Crack Detection MCP Server - HTTP+SSE Transport

MCP server with HTTP+SSE transport for remote access via Warp, Claude Desktop.
Includes Auth0 JWT authentication.

Run:
    uvicorn src.mcp_servers.first_crack_detection.sse_server:app --port 5001

Configure in Warp (.warp/mcp_settings.json):
{
  "mcpServers": {
    "first-crack-detection": {
      "url": "http://localhost:5001/sse",
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
from .session_manager import DetectionSessionManager
from .utils import setup_logging

# Import shared Auth0 middleware
from src.mcp_servers.shared.auth0_middleware import (
    validate_auth0_token,
    check_scope,
    get_client_info,
    log_client_action
)

# Global state
mcp_server = Server("first-crack-detection")
session_manager: DetectionSessionManager = None
config = None
logger = logging.getLogger(__name__)


# Auth0 Middleware
class Auth0Middleware(BaseHTTPMiddleware):
    """Validate Auth0 JWT for MCP endpoints."""
    
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
                
                # Check scopes (client must have at least one detection scope)
                has_read = check_scope(payload, "read:detection")
                has_write = check_scope(payload, "write:detection")
                
                if not (has_read or has_write):
                    client = get_client_info(payload)
                    return JSONResponse(
                        {
                            "error": "Insufficient permissions",
                            "required_scopes": ["read:detection OR write:detection"],
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


# Setup MCP tools
def setup_mcp_server():
    """Register MCP tools and resources."""
    # Import server module to share globals
    from . import server as server_module
    from .server import (
        handle_start_detection,
        handle_get_status,
        handle_stop_detection
    )
    
    # Share globals with server.py handlers
    server_module.session_manager = session_manager
    server_module.config = config
    
    from mcp.types import Tool, TextContent, Resource, ReadResourceResult
    from pathlib import Path
    import json
    import torch
    
    @mcp_server.list_resources()
    async def list_resources() -> list:
        return [
            Resource(
                uri="health://status",
                name="Server Health",
                description="Health check and server status",
                mimeType="application/json"
            )
        ]
    
    @mcp_server.read_resource()
    async def read_resource(uri: str) -> ReadResourceResult:
        if uri == "health://status":
            health_data = {
                "status": "healthy",
                "model_checkpoint": config.model_checkpoint,
                "model_exists": Path(config.model_checkpoint).exists(),
                "device": "mps" if torch.backends.mps.is_available() else "cpu",
                "version": "1.0.0",
                "session_active": session_manager.current_session is not None
            }
            
            if session_manager.current_session:
                health_data["session_id"] = session_manager.current_session.session_id
                health_data["session_started_at"] = str(session_manager.current_session.started_at)
            
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
                name="start_first_crack_detection",
                description="Start first crack detection monitoring",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "audio_source_type": {
                            "type": "string",
                            "enum": ["audio_file", "usb_microphone", "builtin_microphone"]
                        },
                        "audio_file_path": {"type": "string"},
                        "detection_config": {"type": "object"}
                    },
                    "required": ["audio_source_type"]
                }
            ),
            Tool(
                name="get_first_crack_status",
                description="Get current detection status",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="stop_first_crack_detection",
                description="Stop detection and get summary",
                inputSchema={"type": "object", "properties": {}}
            )
        ]
    
    @mcp_server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            if name == "start_first_crack_detection":
                result = await handle_start_detection(arguments)
            elif name == "get_first_crack_status":
                result = await handle_get_status(arguments)
            elif name == "stop_first_crack_detection":
                result = await handle_stop_detection(arguments)
            else:
                result = {"error": f"Unknown tool: {name}"}
            
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
        "name": "First Crack Detection MCP Server",
        "version": "1.0.0",
        "transport": "sse",
        "endpoints": {
            "sse": "/sse (Auth0 JWT required)",
            "messages": "/messages (Auth0 JWT required)",
            "health": "/health (public)"
        }
    })


async def health(request: Request):
    """Health check."""
    import torch
    from pathlib import Path
    
    health_data = {
        "status": "healthy",
        "session_active": session_manager.current_session is not None,
        "model_exists": Path(config.model_checkpoint).exists(),
        "device": "mps" if torch.backends.mps.is_available() else "cpu"
    }
    
    return JSONResponse(health_data)


# Lifespan
@asynccontextmanager
async def lifespan(app):
    """Initialize on startup, cleanup on shutdown."""
    global session_manager, config
    
    # Startup - load real model and config
    config = load_config()
    setup_logging(config)
    session_manager = DetectionSessionManager(config)
    logger.info(f"Model: {config.model_checkpoint}")
    
    setup_mcp_server()
    logger.info("First Crack Detection MCP Server (HTTP+SSE) initialized")
    
    yield
    
    # Shutdown
    if session_manager and session_manager.current_session:
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
        has_read = check_scope(payload, "read:detection")
        has_write = check_scope(payload, "write:detection")
        
        if not (has_read or has_write):
            client = get_client_info(payload)
            return JSONResponse(
                {
                    "error": "Insufficient permissions",
                    "required_scopes": ["read:detection OR write:detection"],
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
    async with sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
        await mcp_server.run(
            streams[0],  # read stream  
            streams[1],  # write stream
            mcp_server.create_initialization_options()
        )
    # Return empty response to avoid NoneType error
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
    port = int(os.getenv("FIRST_CRACK_DETECTION_PORT", "5001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
