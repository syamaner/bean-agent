#!/bin/bash
# Quick test script for Roaster Control MCP Server

cd /Users/sertanyamaner/git/coffee-roasting
source venv/bin/activate

# Load environment
export $(cat .env.roaster_control | xargs)

echo "Starting Roaster Control MCP Server on port 5002..."
echo "Mock mode: $ROASTER_MOCK_MODE"
echo "Auth0 Domain: $AUTH0_DOMAIN"
echo "Auth0 Audience: $AUTH0_AUDIENCE"
echo ""

uvicorn src.mcp_servers.roaster_control.sse_server:app --port 5002 --host 0.0.0.0
