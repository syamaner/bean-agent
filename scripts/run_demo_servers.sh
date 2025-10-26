#!/bin/bash
#
# Run both MCP servers in demo mode for testing
#

set -e

echo "🚀 Starting MCP servers in DEMO MODE"
echo "======================================"
echo ""

# Set demo mode environment variables
export DEMO_MODE=true
export DEMO_SCENARIO=quick_roast

# Auth0 configuration (should be set from set_env.sh)
# Verify required env vars are set
if [ -z "$AUTH0_DOMAIN" ] || [ -z "$AUTH0_CLIENT_ID" ] || [ -z "$AUTH0_CLIENT_SECRET" ]; then
    echo "❌ Error: Auth0 environment variables not set"
    echo "   Please run: source ./set_env.sh"
    exit 1
fi

export AUTH0_AUDIENCE="${AUTH0_AUDIENCE:-https://coffee-roasting-api}"

# Kill any existing servers on these ports
echo "🧹 Cleaning up existing servers..."
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
lsof -ti:5002 | xargs kill -9 2>/dev/null || true
sleep 1

echo "✅ Ports cleared"
echo ""

# Start roaster control server
echo "🔥 Starting Roaster Control Server (port 5002)..."
./venv/bin/python -m uvicorn src.mcp_servers.roaster_control.sse_server:app \
  --host 0.0.0.0 \
  --port 5002 \
  --log-level info &

ROASTER_PID=$!
echo "   PID: $ROASTER_PID"
sleep 2

# Start FC detection server  
echo "🎯 Starting First Crack Detection Server (port 5001)..."
./venv/bin/python -m uvicorn src.mcp_servers.first_crack_detection.sse_server:app \
  --host 0.0.0.0 \
  --port 5001 \
  --log-level info &

FC_PID=$!
echo "   PID: $FC_PID"
sleep 2

echo ""
echo "✅ Both servers started!"
echo ""
echo "📊 Server URLs:"
echo "   Roaster Control:      http://localhost:5002"
echo "   First Crack Detection: http://localhost:5001"
echo ""
echo "🧪 Test with:"
echo "   ./scripts/testing/test_demo_mode_aspire.sh"
echo ""
echo "🛑 Stop with:"
echo "   kill $ROASTER_PID $FC_PID"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping servers...'; kill $ROASTER_PID $FC_PID 2>/dev/null; exit 0" INT TERM

echo "Press Ctrl+C to stop servers..."
wait
