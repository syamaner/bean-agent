#!/usr/bin/env python3
"""Entry point for roaster control MCP server."""
import asyncio
import sys

from .mcp_server import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)