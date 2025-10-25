#!/usr/bin/env python3
"""MCP server entry point for roaster control.

This script starts the MCP server that can be connected to by Warp or other MCP clients.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server.stdio import stdio_server
from src.mcp_servers.roaster_control import init_server, ServerConfig, HardwareConfig
from src.mcp_servers.roaster_control.server import server

# Configure logging to file (not stderr - MCP uses stdio)
import os
log_dir = os.path.expanduser("~/Library/Logs/roaster-control")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "mcp-server.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for MCP server."""
    import os
    
    logger.info("Starting Roaster Control MCP Server...")
    
    # Configuration - controlled via ROASTER_MOCK_MODE environment variable
    # Set ROASTER_MOCK_MODE=1 for mock hardware, otherwise uses real Hottop
    mock_mode = os.environ.get("ROASTER_MOCK_MODE", "0") == "1"
    port = os.environ.get("ROASTER_PORT", "/dev/tty.usbserial-DN016OJ3")
    
    config = ServerConfig(
        hardware=HardwareConfig(
            mock_mode=mock_mode,
            port=port,
            baud_rate=115200
        ),
        logging_level="INFO"
    )
    
    # Initialize server
    try:
        init_server(config)
        logger.info(f"Server initialized (mock_mode={config.hardware.mock_mode})")
        
        # Start session
        from src.mcp_servers.roaster_control.server import _session_manager
        _session_manager.start_session()
        logger.info("Session started successfully")
        
        # Run MCP server
        logger.info("Running MCP server on stdio...")
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise
    finally:
        # Clean shutdown
        from src.mcp_servers.roaster_control.server import _session_manager
        if _session_manager and _session_manager.is_active():
            _session_manager.stop_session()
            logger.info("Session stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
