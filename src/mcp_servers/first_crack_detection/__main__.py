"""
Entry point for running the MCP server as a module.

Usage:
    python -m src.mcp_servers.first_crack_detection
"""
from .server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
