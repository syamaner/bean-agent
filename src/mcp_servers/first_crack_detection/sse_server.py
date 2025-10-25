#!/usr/bin/env python3
"""
First Crack Detection MCP Server - HTTP+SSE Transport

MCP server with HTTP+SSE transport for remote access via Warp, Claude Desktop,
and n8n workflows. Includes Auth0 JWT authentication.

Run:
    uvicorn src.mcp_servers.first_crack_detection.sse_server:app --port 5001

Configure in Warp (mcp_settings.json):
{
  "mcpServers": {
    "first-crack-detection": {
      "url": "http://localhost:5001/sse",
      "transport": {
        "type": "sse"
      },
      "headers": {
        "Authorization": "Bearer YOUR_AUTH0_TOKEN"
      }
    }
  }
}
"""
import logging
import os
from typing import Optional

from fastapi import FastAPI, Request, Response, Depends
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from starlette.middleware.base import BaseHTTPMiddleware

from mcp.server import Server
from mcp.server.sse import SseServerTransport

# Import existing MCP server components
from .config import load_config
from .session_manager import DetectionSessionManager
from .server import register_tools as setup_mcp_tools
from .utils import setup_logging

# Import shared Auth0 middleware
from src.mcp_servers.shared.auth0_middleware import validate_auth0_token


# Global state
mcp_server = Server("first-crack-detection")
session_manager: DetectionSessionManager = None
config = None
logger = logging.getLogger(__name__)


# Auth0 Middleware for MCP
class Auth0MCPMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate Auth0 JWT tokens for MCP endpoints.
    
    Validates tokens for /sse endpoint (MCP transport).
    Public endpoints like /health are exempt.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        if request.url.path in ["/", "/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Validate Auth0 token for MCP endpoints
        if request.url.path.startswith("/sse") or request.url.path.startswith("/messages"):
            try:
                # Extract Authorization header
                auth_header = request.headers.get("Authorization")
                if not auth_header:
                    return JSONResponse(
                        status_code=401,
                        content={"error": "Missing Authorization header"}
                    )
                
                # Validate token (raises HTTPException if invalid)
                token_payload = await validate_auth0_token(auth_header.replace("Bearer ", ""))
                
                # Check for required scopes
                scopes = token_payload.get("scope", "").split()
                required_scopes = {"read:detection", "write:detection"}
                
                if not required_scopes.intersection(scopes):
                    return JSONResponse(
                        status_code=403,
                        content={
                            "error": "Insufficient permissions",
                            "required_scopes": list(required_scopes),
                            "your_scopes": scopes
                        }
                    )
                
                # Store token payload in request state
                request.state.auth_payload = token_payload
                
            except Exception as e:
                logger.error(f"Auth0 validation error: {e}")
                return JSONResponse(
                    status_code=401,
                    content={"error": f"Invalid token: {str(e)}"}
                )
        
        return await call_next(request)


# FastAPI app
app = FastAPI(
    title="First Crack Detection MCP Server",
    description="MCP server with HTTP+SSE transport and Auth0 JWT authentication",
    version="1.0.0"
)

# Add Auth0 middleware
app.add_middleware(Auth0MCPMiddleware)


@app.on_event("startup")
async def startup():
    """Initialize MCP server and session manager on startup."""
    global session_manager, config, mcp_server
    
    try:
        # Load configuration
        config = load_config()
        setup_logging(config)
        
        # Initialize session manager
        session_manager = DetectionSessionManager(config)
        
        # Register MCP tools with the server
        # Pass session_manager to tool handlers
        setup_mcp_tools(mcp_server, session_manager, config)
        
        logger.info(f"First Crack Detection MCP Server initialized")
        logger.info(f"Model checkpoint: {config.model_checkpoint}")
        logger.info(f"SSE endpoint: /sse")
        
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Clean up on shutdown."""
    if session_manager and session_manager.current_session:
        try:
            session_manager.stop_session()
            logger.info("Active detection session stopped on shutdown")
        except Exception as e:
            logger.warning(f"Error stopping session on shutdown: {e}")


# Public endpoints (no auth required)

@app.get("/", tags=["public"])
async def root():
    """API information."""
    return {
        "name": "First Crack Detection MCP Server",
        "version": "1.0.0",
        "description": "MCP server with HTTP+SSE transport for remote access",
        "transport": "sse",
        "endpoints": {
            "mcp_sse": "/sse (requires Auth0 JWT)",
            "mcp_messages": "/messages (requires Auth0 JWT)",
            "health": "/health (public)",
            "docs": "/docs (public)"
        },
        "auth": {
            "type": "Auth0 JWT",
            "required_scopes": ["read:detection", "write:detection"],
            "header": "Authorization: Bearer <token>"
        },
        "configuration": {
            "warp_example": {
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
        }
    }


@app.get("/health", tags=["public"])
async def health():
    """Health check endpoint."""
    import torch
    from pathlib import Path
    
    return {
        "status": "healthy",
        "model_checkpoint": config.model_checkpoint,
        "model_exists": Path(config.model_checkpoint).exists(),
        "device": "mps" if torch.backends.mps.is_available() else "cpu",
        "version": "1.0.0",
        "session_active": session_manager.current_session is not None,
        "session_id": session_manager.current_session.session_id if session_manager.current_session else None
    }


# MCP SSE endpoints (Auth0 protected)

@app.get("/sse", tags=["mcp"])
async def handle_sse(request: Request):
    """
    MCP Server-Sent Events endpoint.
    
    This is the main MCP transport endpoint. MCP clients connect here
    to establish an SSE connection for bidirectional JSON-RPC communication.
    
    Requires Auth0 JWT with read:detection or write:detection scope.
    """
    from mcp.server.sse import SseServerTransport
    
    # Create SSE transport
    transport = SseServerTransport("/messages")
    
    async def event_generator():
        """Generate SSE events for MCP protocol."""
        try:
            async with transport.connect_sse(
                request.scope,
                request.receive,
                None  # Send is handled by EventSourceResponse
            ) as (read_stream, write_stream):
                # Run MCP server with this transport
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options()
                )
        except Exception as e:
            logger.error(f"SSE connection error: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": str(e)
            }
    
    return EventSourceResponse(event_generator())


@app.post("/messages", tags=["mcp"])
async def handle_messages(request: Request):
    """
    MCP messages endpoint for client-to-server communication.
    
    MCP clients POST JSON-RPC messages here.
    
    Requires Auth0 JWT with read:detection or write:detection scope.
    """
    from mcp.server.sse import SseServerTransport
    
    transport = SseServerTransport("/messages")
    
    # Handle POST message
    response = await transport.handle_post_message(
        request.scope,
        request.receive,
        None
    )
    
    return Response(
        content=response.get("body", b""),
        status_code=response.get("status", 200),
        headers=dict(response.get("headers", []))
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("FIRST_CRACK_DETECTION_PORT", "5001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
