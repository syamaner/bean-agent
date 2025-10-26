#!/usr/bin/env python3
"""
First Crack Detection MCP Server - HTTP API

FastAPI-based HTTP server that wraps the First Crack Detection MCP server,
enabling REST API access for n8n workflows and orchestration platforms.

Auth0 integration with JWT validation and scope-based authorization.

Run:
    uvicorn src.mcp_servers.first_crack_detection.http_server:app --port 5001
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from src.mcp_servers.auth0_middleware import requires_scope
from src.mcp_servers.shared.auth0_middleware import validate_auth0_token
from .config import load_config
from .session_manager import DetectionSessionManager
from .models import (
    AudioConfig,
    DetectionConfig,
    ModelNotFoundError,
    MicrophoneNotAvailableError,
    FileNotFoundError as FCFileNotFoundError,
    SessionAlreadyActiveError,
    ThreadCrashError,
    InvalidAudioSourceError,
    DetectionError,
)
from .utils import setup_logging


# Global state
session_manager: DetectionSessionManager = None
config = None
logger = logging.getLogger(__name__)


# --- Request/Response Models ---

class StartDetectionRequest(BaseModel):
    audio_source_type: str = Field(
        ...,
        description="Type of audio source: 'audio_file', 'usb_microphone', or 'builtin_microphone'"
    )
    audio_file_path: Optional[str] = Field(
        None,
        description="Path to audio file (required if audio_source_type is 'audio_file')"
    )
    detection_config: Optional[dict] = Field(
        default_factory=dict,
        description="Optional detection parameters (threshold, min_pops, confirmation_window)"
    )


class HealthResponse(BaseModel):
    status: str
    model_checkpoint: str
    model_exists: bool
    device: str
    version: str
    session_active: bool
    session_id: Optional[str] = None
    session_started_at: Optional[str] = None


class APIInfoResponse(BaseModel):
    name: str
    version: str
    description: str
    auth0_required: bool
    endpoints: dict


# --- Lifespan Management ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup session manager."""
    global session_manager, config
    
    # Startup
    try:
        config = load_config()
        setup_logging(config)
        session_manager = DetectionSessionManager(config)
        logger.info(f"First Crack Detection HTTP Server initialized")
        logger.info(f"Model checkpoint: {config.model_checkpoint}")
    except Exception as e:
        logger.error(f"Failed to initialize session manager: {e}")
        raise
    
    yield
    
    # Shutdown
    if session_manager and session_manager.current_session:
        try:
            session_manager.stop_session()
            logger.info("Active detection session stopped on shutdown")
        except Exception as e:
            logger.warning(f"Error stopping session on shutdown: {e}")


# --- FastAPI App ---

app = FastAPI(
    title="First Crack Detection MCP Server",
    description="HTTP API for first crack detection with Auth0 JWT authorization",
    version="1.0.0",
    lifespan=lifespan
)


# --- Public Endpoints (no auth required) ---

@app.get("/health", response_model=HealthResponse, tags=["public"])
async def health():
    """Health check endpoint - no authentication required."""
    import torch
    from pathlib import Path
    
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
    
    return health_data


@app.api_route("/", methods=["GET", "POST"], tags=["public"])
async def root(request: Request):
    """API information (GET) and MCP tool definitions (POST) - no authentication required.
    
    This endpoint is used by n8n MCP Client to discover available tools.
    """
    if request.method == "POST":
        return {
        "tools": [
            {
                "name": "start_first_crack_detection",
                "description": "Start first crack detection monitoring with audio file, USB microphone, or built-in microphone",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "audio_source_type": {
                            "type": "string",
                            "enum": ["audio_file", "usb_microphone", "builtin_microphone"],
                            "description": "Type of audio source to use"
                        },
                        "audio_file_path": {
                            "type": "string",
                            "description": "Path to audio file (required if audio_source_type is 'audio_file')"
                        },
                        "detection_config": {
                            "type": "object",
                            "description": "Optional detection parameters",
                            "properties": {
                                "threshold": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                    "description": "Detection threshold (default: 0.5)"
                                },
                                "min_pops": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "description": "Minimum pops to confirm (default: 3)"
                                },
                                "confirmation_window": {
                                    "type": "number",
                                    "minimum": 1,
                                    "description": "Confirmation window in seconds (default: 30.0)"
                                }
                            }
                        }
                    },
                    "required": ["audio_source_type"]
                }
            },
            {
                "name": "get_first_crack_status",
                "description": "Get current first crack detection status",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "stop_first_crack_detection",
                "description": "Stop first crack detection and get session summary",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    }
    
    # GET request - return API info
    return {
        "name": "First Crack Detection MCP Server",
        "version": "1.0.0",
        "description": "HTTP API for real-time first crack detection during coffee roasting",
        "auth0_required": True,
        "endpoints": {
            "public": {
                "/health": "Health check and status",
                "/": "API information (GET) or MCP tools (POST)"
            },
            "protected": {
                "/api/detection/status": "Get current detection status (scope: read:detection)",
                "/api/detection/start": "Start detection session (scope: write:detection)",
                "/api/detection/stop": "Stop detection session (scope: write:detection)"
            }
        }
    }


# --- Protected Endpoints (Auth0 JWT required) ---

@app.get("/api/detection/status", tags=["detection"])
@requires_scope("read:detection")
async def get_status(token_payload: dict = Depends(validate_auth0_token)):
    """
    Get current first crack detection status.
    
    Requires scope: read:detection
    """
    try:
        status = session_manager.get_status()
        return {
            "status": "success",
            "result": status.model_dump()
        }
    except ThreadCrashError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": e.error_code,
                "message": str(e),
                "details": getattr(e, 'details', {})
            }
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        )


@app.post("/api/detection/start", tags=["detection"])
@requires_scope("write:detection")
async def start_detection(
    request: StartDetectionRequest,
    token_payload: dict = Depends(validate_auth0_token)
):
    """
    Start first crack detection monitoring.
    
    Requires scope: write:detection
    
    Audio sources:
    - 'audio_file': Process a pre-recorded audio file (requires audio_file_path)
    - 'usb_microphone': Use USB microphone for live detection
    - 'builtin_microphone': Use built-in microphone for live detection
    
    Detection config (optional):
    - threshold: Detection threshold 0.0-1.0 (default: 0.5)
    - min_pops: Minimum pops to confirm (default: 3)
    - confirmation_window: Confirmation window in seconds (default: 30.0)
    """
    try:
        # Parse audio config
        audio_config = AudioConfig(
            audio_source_type=request.audio_source_type,
            audio_file_path=request.audio_file_path
        )
        
        # Parse detection config (optional)
        detection_config = DetectionConfig(**request.detection_config)
        
        # Start session
        result = session_manager.start_session(audio_config)
        
        return {
            "status": "success",
            "result": result.model_dump()
        }
    except (ModelNotFoundError, FCFileNotFoundError, MicrophoneNotAvailableError,
            InvalidAudioSourceError, SessionAlreadyActiveError) as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": e.error_code,
                "message": str(e),
                "details": getattr(e, 'details', {})
            }
        )
    except Exception as e:
        logger.error(f"Error starting detection: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        )


@app.post("/api/detection/stop", tags=["detection"])
@requires_scope("write:detection")
async def stop_detection(token_payload: dict = Depends(validate_auth0_token)):
    """
    Stop first crack detection and get session summary.
    
    Requires scope: write:detection
    """
    try:
        summary = session_manager.stop_session()
        
        return {
            "status": "success",
            "result": summary.model_dump()
        }
    except Exception as e:
        logger.error(f"Error stopping detection: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        )


# --- Error Handlers ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return {
        "error": {
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "error": {
            "status_code": 500,
            "detail": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("FIRST_CRACK_DETECTION_PORT", "5001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
