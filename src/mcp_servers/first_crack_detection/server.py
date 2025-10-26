#!/usr/bin/env python3
"""
First Crack Detection MCP Server

Exposes first crack detection functionality as MCP tools for
integration with n8n workflows and AI agents.

Transport: stdio (JSON-RPC over stdin/stdout)
"""
import asyncio
import logging
import os
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource, ReadResourceResult

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
from .mock_detector import MockFirstCrackDetector

# Import demo scenario from shared location
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from demo_scenario import get_demo_scenario


# Global state
server = Server("first-crack-detection")
session_manager: DetectionSessionManager = None
config = None
logger = logging.getLogger(__name__)
demo_mode = False
mock_detector: MockFirstCrackDetector = None
demo_scenario = None


def register_tools():
    """Register all MCP tools and resources."""
    
    # Health resource
    @server.list_resources()
    async def list_resources() -> list:
        """List available resources."""
        return [
            Resource(
                uri="health://status",
                name="Server Health",
                description="Health check and server status",
                mimeType="application/json"
            )
        ]
    
    @server.read_resource()
    async def read_resource(uri: str) -> ReadResourceResult:
        """Read resource content."""
        if uri == "health://status":
            import json
            import torch
            
            health_data = {
                "status": "healthy",
                "model_checkpoint": config.model_checkpoint if not demo_mode else "demo_mode",
                "model_exists": Path(config.model_checkpoint).exists() if not demo_mode else True,
                "device": "mps" if torch.backends.mps.is_available() else "cpu",
                "version": "1.0.0",
                "demo_mode": demo_mode,
                "session_active": (session_manager.current_session is not None) if not demo_mode else (mock_detector.is_running if mock_detector else False)
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
        else:
            raise ValueError(f"Unknown resource: {uri}")
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="start_first_crack_detection",
                description="Start first crack detection monitoring with audio file, USB microphone, or built-in microphone",
                inputSchema={
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
                            "properties": {
                                "threshold": {
                                    "type": "number",
                                    "minimum": 0.0,
                                    "maximum": 1.0,
                                    "description": "Detection threshold (default: 0.5)"
                                },
                                "min_pops": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "description": "Minimum pops to confirm (default: 3)"
                                },
                                "confirmation_window": {
                                    "type": "number",
                                    "minimum": 1.0,
                                    "description": "Confirmation window in seconds (default: 30.0)"
                                }
                            },
                            "description": "Optional detection parameters"
                        }
                    },
                    "required": ["audio_source_type"]
                }
            ),
            Tool(
                name="get_first_crack_status",
                description="Get current first crack detection status",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="stop_first_crack_detection",
                description="Stop first crack detection and get session summary",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls."""
        try:
            if name == "start_first_crack_detection":
                result = await handle_start_detection(arguments)
            elif name == "get_first_crack_status":
                result = await handle_get_status(arguments)
            elif name == "stop_first_crack_detection":
                result = await handle_stop_detection(arguments)
            else:
                result = {"error": f"Unknown tool: {name}"}
            
            import json
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
        except Exception as e:
            logger.error(f"Tool call error: {e}", exc_info=True)
            import json
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "type": type(e).__name__
                }, indent=2)
            )]


async def handle_start_detection(arguments: dict) -> dict:
    """Handle start_first_crack_detection tool call."""
    try:
        if demo_mode:
            # Demo mode: use mock detector
            if mock_detector.is_running:
                return {
                    "status": "error",
                    "error": {
                        "code": "SESSION_ALREADY_ACTIVE",
                        "message": "Detection already running in demo mode"
                    }
                }
            
            mock_detector.start()
            
            return {
                "status": "success",
                "result": {
                    "session_id": "demo_session",
                    "started_at": str(mock_detector.first_crack_time) if mock_detector.first_crack_time else None,
                    "audio_source": "demo_mode",
                    "demo_mode": True
                }
            }
        
        # Real mode: use session manager
        # Parse audio config
        audio_config = AudioConfig(
            audio_source_type=arguments["audio_source_type"],
            audio_file_path=arguments.get("audio_file_path")
        )
        
        # Parse detection config (optional)
        detection_config_data = arguments.get("detection_config", {})
        detection_config = DetectionConfig(**detection_config_data)
        
        # Start session
        result = session_manager.start_session(audio_config)
        
        return {
            "status": "success",
            "result": result.model_dump()
        }
    except (ModelNotFoundError, FCFileNotFoundError, MicrophoneNotAvailableError, 
            InvalidAudioSourceError) as e:
        return {
            "status": "error",
            "error": {
                "code": e.error_code,
                "message": str(e),
                "details": getattr(e, 'details', {})
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in start_detection: {e}", exc_info=True)
        return {
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e),
                "details": {}
            }
        }


async def handle_get_status(arguments: dict) -> dict:
    """Handle get_first_crack_status tool call."""
    try:
        if demo_mode:
            # Demo mode: return mock detector status
            status = mock_detector.get_status()
            return {
                "status": "success",
                "result": status
            }
        
        # Real mode
        status = session_manager.get_status()
        
        return {
            "status": "success",
            "result": status.model_dump()
        }
    except ThreadCrashError as e:
        return {
            "status": "error",
            "error": {
                "code": e.error_code,
                "message": str(e),
                "details": getattr(e, 'details', {})
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_status: {e}", exc_info=True)
        return {
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e),
                "details": {}
            }
        }


async def handle_stop_detection(arguments: dict) -> dict:
    """Handle stop_first_crack_detection tool call."""
    try:
        if demo_mode:
            # Demo mode: stop mock detector
            summary = mock_detector.stop()
            return {
                "status": "success",
                "result": summary
            }
        
        # Real mode
        summary = session_manager.stop_session()
        
        return {
            "status": "success",
            "result": summary.model_dump()
        }
    except Exception as e:
        logger.error(f"Unexpected error in stop_detection: {e}", exc_info=True)
        return {
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e),
                "details": {}
            }
        }


async def main():
    """
    Run the MCP server with stdio transport.
    """
    global session_manager, config, demo_mode, mock_detector, demo_scenario
    
    # Debug: Check environment
    import os
    logger.info(f"DEMO_MODE env var: {os.getenv('DEMO_MODE', 'NOT SET')}")
    
    # Check for demo mode from shared scenario
    demo_scenario = get_demo_scenario()
    demo_mode = demo_scenario is not None
    logger.info(f"Demo mode active: {demo_mode}, scenario: {demo_scenario}")
    
    if demo_mode:
        logger.info(f"Starting in DEMO MODE - FC at {demo_scenario.fc_trigger_time}s")
        mock_detector = MockFirstCrackDetector(fc_trigger_time=demo_scenario.fc_trigger_time)
        config = type('Config', (), {'model_checkpoint': 'demo_mode'})()
    else:
        # Load configuration
        try:
            config = load_config()
            setup_logging(config)
            logger.info(f"Loaded configuration: {config.model_checkpoint}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
        
        # Initialize session manager
        try:
            session_manager = DetectionSessionManager(config)
            logger.info("DetectionSessionManager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize session manager: {e}")
            raise
    
    # Register tools
    register_tools()
    logger.info("MCP Server initialized with tools, waiting for connections...")
    
    # Run server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
