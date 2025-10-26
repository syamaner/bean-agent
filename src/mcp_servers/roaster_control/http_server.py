"""HTTP API server for Roaster Control MCP.

This module provides HTTP/REST endpoints for the roaster control functionality,
while maintaining backward compatibility with the stdio MCP transport.

Run with:
    uvicorn src.mcp_servers.roaster_control.http_server:app --host 0.0.0.0 --port 5002
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .session_manager import RoastSessionManager
from .hardware import MockRoaster, HottopRoaster
from .models import ServerConfig, HardwareConfig
from ..auth0_middleware import requires_scope


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# Request/Response Models
# ============================================

class SetControlRequest(BaseModel):
    """Request model for heat/fan control."""
    percent: int = Field(..., ge=0, le=100, description="Percentage (0-100 in 10% increments)")


class FirstCrackReportRequest(BaseModel):
    """Request model for reporting first crack."""
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp when FC occurred")
    temperature: float = Field(..., description="Bean temperature in °C at first crack")


# ============================================
# Global State
# ============================================

_session_manager: RoastSessionManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app.
    
    Initializes session manager on startup and cleans up on shutdown.
    """
    global _session_manager
    
    # Startup
    logger.info("Starting Roaster Control HTTP Server")
    
    # Configuration
    mock_mode = os.environ.get("ROASTER_MOCK_MODE", "1") == "1"
    port = os.environ.get("ROASTER_PORT", "/dev/tty.usbserial-DN016OJ3")
    
    config = ServerConfig(
        hardware=HardwareConfig(
            mock_mode=mock_mode,
            port=port,
            baud_rate=115200
        ),
        logging_level="INFO"
    )
    
    # Create hardware interface
    if config.hardware.mock_mode:
        logger.info("Using MockRoaster (simulated hardware)")
        hardware = MockRoaster()
    else:
        logger.info(f"Using HottopRoaster on port {port}")
        hardware = HottopRoaster(port=config.hardware.port)
    
    # Create session manager
    _session_manager = RoastSessionManager(hardware, config)
    
    # Start session
    _session_manager.start_session()
    logger.info("Session started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Roaster Control HTTP Server")
    if _session_manager and _session_manager.is_active():
        _session_manager.stop_session()
        logger.info("Session stopped")


# ============================================
# FastAPI App
# ============================================

app = FastAPI(
    title="Roaster Control MCP",
    description="HTTP API for controlling Hottop KN-8828B-2K+ coffee roaster",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================
# Health / Public Endpoints
# ============================================

@app.get("/health")
async def health():
    """Health check endpoint (no auth required)."""
    return {
        "status": "healthy",
        "service": "roaster-control-mcp",
        "session_active": _session_manager.is_active() if _session_manager else False
    }


@app.api_route("/", methods=["GET", "POST"])
async def root(request: Request):
    """Root endpoint (no auth required).
    
    GET: Returns API info
    POST: Returns MCP tool definitions for n8n
    """
    if request.method == "POST":
        return {
        "tools": [
            {
                "name": "get_roast_status",
                "description": "Get complete roast status including sensors, metrics, and timestamps",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "start_roaster",
                "description": "Start roaster drum motor",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "stop_roaster",
                "description": "Stop roaster drum motor",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "set_heat",
                "description": "Set roaster heat level (0-100% in 10% increments)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "percent": {
                            "type": "integer",
                            "description": "Heat level percentage (0-100 in 10% increments)",
                            "minimum": 0,
                            "maximum": 100
                        }
                    },
                    "required": ["percent"]
                }
            },
            {
                "name": "set_fan",
                "description": "Set roaster fan speed (0-100% in 10% increments)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "percent": {
                            "type": "integer",
                            "description": "Fan speed percentage (0-100 in 10% increments)",
                            "minimum": 0,
                            "maximum": 100
                        }
                    },
                    "required": ["percent"]
                }
            },
            {
                "name": "drop_beans",
                "description": "Open bean drop door and start cooling",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "start_cooling",
                "description": "Start cooling fan motor",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "stop_cooling",
                "description": "Stop cooling fan motor",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "report_first_crack",
                "description": "Report first crack detection (called by agent after FC MCP detects)",
                "input_schema": {
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
            }
            }
        ]
    }
    
    # GET request - return API info
    return {
        "service": "roaster-control-mcp",
        "version": "1.0.0",
        "docs": "/docs"
    }


# ============================================
# Protected Endpoints - Read (Observer Role)
# ============================================

@app.get("/api/roaster/status")
@requires_scope("read:roaster")
async def get_status(request: Request):
    """Get complete roast status.
    
    Requires: read:roaster scope (Admin or Observer)
    """
    if not _session_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session manager not initialized"
        )
    
    roast_status = _session_manager.get_status()
    return JSONResponse(content=roast_status.dict())


# ============================================
# Protected Endpoints - Write (Admin Role)
# ============================================

@app.post("/api/roaster/start")
@requires_scope("write:roaster")
async def start_roaster(request: Request):
    """Start roaster drum motor.
    
    Requires: write:roaster scope (Admin only)
    """
    if not _session_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session manager not initialized"
        )
    
    _session_manager.start_roaster()
    return {"success": True, "message": "Roaster drum started"}


@app.post("/api/roaster/stop")
@requires_scope("write:roaster")
async def stop_roaster(request: Request):
    """Stop roaster drum motor.
    
    Requires: write:roaster scope (Admin only)
    """
    if not _session_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session manager not initialized"
        )
    
    _session_manager.stop_roaster()
    return {"success": True, "message": "Roaster drum stopped"}


@app.post("/api/roaster/set-heat")
@requires_scope("write:roaster")
async def set_heat(request: Request, body: SetControlRequest):
    """Set heat level.
    
    Requires: write:roaster scope (Admin only)
    """
    if not _session_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session manager not initialized"
        )
    
    # Validate 10% increments
    if body.percent % 10 != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Heat level must be in 10% increments (0, 10, 20, ..., 100)"
        )
    
    _session_manager.set_heat(body.percent)
    return {"success": True, "message": f"Heat set to {body.percent}%"}


@app.post("/api/roaster/set-fan")
@requires_scope("write:roaster")
async def set_fan(request: Request, body: SetControlRequest):
    """Set fan speed.
    
    Requires: write:roaster scope (Admin only)
    """
    if not _session_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session manager not initialized"
        )
    
    # Validate 10% increments
    if body.percent % 10 != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fan speed must be in 10% increments (0, 10, 20, ..., 100)"
        )
    
    _session_manager.set_fan(body.percent)
    return {"success": True, "message": f"Fan set to {body.percent}%"}


@app.post("/api/roaster/drop-beans")
@requires_scope("write:roaster")
async def drop_beans(request: Request):
    """Drop beans and start cooling.
    
    Requires: write:roaster scope (Admin only)
    """
    if not _session_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session manager not initialized"
        )
    
    _session_manager.drop_beans()
    return {"success": True, "message": "Beans dropped, cooling started"}


@app.post("/api/roaster/start-cooling")
@requires_scope("write:roaster")
async def start_cooling(request: Request):
    """Start cooling fan.
    
    Requires: write:roaster scope (Admin only)
    """
    if not _session_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session manager not initialized"
        )
    
    _session_manager.start_cooling()
    return {"success": True, "message": "Cooling started"}


@app.post("/api/roaster/stop-cooling")
@requires_scope("write:roaster")
async def stop_cooling(request: Request):
    """Stop cooling fan.
    
    Requires: write:roaster scope (Admin only)
    """
    if not _session_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session manager not initialized"
        )
    
    _session_manager.stop_cooling()
    return {"success": True, "message": "Cooling stopped"}


@app.post("/api/roaster/report-first-crack")
@requires_scope("write:roaster")
async def report_first_crack(request: Request, body: FirstCrackReportRequest):
    """Report first crack detection from FC MCP server.
    
    Requires: write:roaster scope (Admin only)
    """
    if not _session_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session manager not initialized"
        )
    
    # Parse timestamp
    from datetime import datetime
    try:
        fc_time = datetime.fromisoformat(body.timestamp.replace('Z', '+00:00'))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timestamp format: {str(e)}"
        )
    
    _session_manager.report_first_crack(fc_time, body.temperature)
    return {"success": True, "message": "First crack recorded"}


# ============================================
# Error Handlers
# ============================================

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# ============================================
# Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    host = os.environ.get("HTTP_HOST", "0.0.0.0")
    port = int(os.environ.get("HTTP_PORT", "5002"))
    debug = os.environ.get("HTTP_DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting HTTP server on {host}:{port}")
    uvicorn.run(
        "src.mcp_servers.roaster_control.http_server:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
