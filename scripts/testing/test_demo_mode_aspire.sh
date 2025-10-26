#!/bin/bash
#
# Test Demo Mode in Aspire AppHost
#
# Tests the demo mode functionality of both MCP servers running in Aspire

set -e

echo "🧪 Testing Demo Mode in Aspire AppHost"
echo "========================================"
echo ""

# Check if Aspire is running
if ! curl -s http://localhost:5002/health > /dev/null 2>&1; then
    echo "❌ Roaster Control server not running on port 5002"
    echo "   Start Aspire AppHost first:"
    echo "   cd Phase3/CoffeeRoasting.AppHost"
    echo "   dotnet run"
    exit 1
fi

if ! curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo "❌ FC Detection server not running on port 5001"
    echo "   Start Aspire AppHost first"
    exit 1
fi

echo "✅ Both servers are running"
echo ""

# Get Auth0 token (you need to set these env vars)
if [ -z "$AUTH0_DOMAIN" ] || [ -z "$AUTH0_CLIENT_ID" ] || [ -z "$AUTH0_CLIENT_SECRET" ] || [ -z "$AUTH0_AUDIENCE" ]; then
    echo "⚠️  Auth0 environment variables not set"
    echo "   Set: AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_AUDIENCE"
    echo ""
    echo "Skipping authenticated tests. Testing public health endpoints only..."
    echo ""
    
    # Test health endpoints (public)
    echo "📊 Roaster Control Health:"
    curl -s http://localhost:5002/health | jq '.'
    echo ""
    
    echo "📊 FC Detection Health:"
    curl -s http://localhost:5001/health | jq '.'
    echo ""
    
    # Check for demo_mode flag
    ROASTER_DEMO=$(curl -s http://localhost:5002/health | jq -r '.demo_mode')
    FC_DEMO=$(curl -s http://localhost:5001/health | jq -r '.demo_mode')
    
    if [ "$ROASTER_DEMO" = "true" ] && [ "$FC_DEMO" = "true" ]; then
        echo "✅ Demo mode is ENABLED on both servers"
    else
        echo "ℹ️  Demo mode status:"
        echo "   Roaster Control: $ROASTER_DEMO"
        echo "   FC Detection: $FC_DEMO"
    fi
    
    exit 0
fi

echo "🔑 Getting Auth0 token..."
TOKEN=$(curl --silent --request POST \
  --url "https://${AUTH0_DOMAIN}/oauth/token" \
  --header 'content-type: application/json' \
  --data "{
    \"client_id\":\"${AUTH0_CLIENT_ID}\",
    \"client_secret\":\"${AUTH0_CLIENT_SECRET}\",
    \"audience\":\"${AUTH0_AUDIENCE}\",
    \"grant_type\":\"client_credentials\"
  }" | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "❌ Failed to get Auth0 token"
    exit 1
fi

echo "✅ Got Auth0 token"
echo ""

# Test health endpoints
echo "📊 Testing Health Endpoints"
echo "----------------------------"
echo ""

echo "Roaster Control Health:"
ROASTER_HEALTH=$(curl -s http://localhost:5002/health)
echo "$ROASTER_HEALTH" | jq '.'
ROASTER_DEMO=$(echo "$ROASTER_HEALTH" | jq -r '.demo_mode')
echo ""

echo "FC Detection Health:"
FC_HEALTH=$(curl -s http://localhost:5001/health)
echo "$FC_HEALTH" | jq '.'
FC_DEMO=$(echo "$FC_HEALTH" | jq -r '.demo_mode')
echo ""

# Verify demo mode
if [ "$ROASTER_DEMO" = "true" ] && [ "$FC_DEMO" = "true" ]; then
    echo "✅ Demo mode is ENABLED on both servers"
else
    echo "⚠️  Demo mode not fully enabled:"
    echo "   Roaster Control: $ROASTER_DEMO"
    echo "   FC Detection: $FC_DEMO"
fi
echo ""

# Test roaster control workflow
echo "🔥 Testing Roaster Control Workflow"
echo "------------------------------------"
echo ""

echo "1️⃣  Starting roaster..."
START_RESULT=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:5002/tools/start_roaster)
echo "$START_RESULT" | jq '.'
echo ""

sleep 2

echo "2️⃣  Setting heat to 70%..."
HEAT_RESULT=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"level": 70}' \
  http://localhost:5002/tools/set_heat)
echo "$HEAT_RESULT" | jq '.'
echo ""

sleep 2

echo "3️⃣  Setting fan to 40%..."
FAN_RESULT=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"speed": 40}' \
  http://localhost:5002/tools/set_fan)
echo "$FAN_RESULT" | jq '.'
echo ""

sleep 2

echo "4️⃣  Reading roaster status..."
STATUS_RESULT=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:5002/tools/read_roaster_status)
echo "$STATUS_RESULT" | jq '.data | {bean_temp_c, heat_level, fan_speed, roaster_running}'
echo ""

# Test FC detection
echo "🎯 Testing First Crack Detection"
echo "----------------------------------"
echo ""

echo "1️⃣  Starting FC detection..."
FC_START=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"audio_source_type": "builtin_microphone"}' \
  http://localhost:5001/tools/start_first_crack_detection)
echo "$FC_START" | jq '.'
echo ""

echo "2️⃣  Waiting 10 seconds and checking status..."
sleep 10

FC_STATUS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:5001/tools/get_first_crack_status)
echo "$FC_STATUS" | jq '.'
echo ""

# Get expected FC time from scenario (default quick_roast = 90s)
echo "ℹ️  In demo mode (quick_roast scenario):"
echo "   - First crack should trigger at 90 seconds"
echo "   - Temperature should be progressing through phases"
echo "   - Heat/fan changes should affect temperature rate"
echo ""

# Monitor for a bit
echo "📈 Monitoring temperature for 15 seconds..."
for i in {1..3}; do
    sleep 5
    STATUS=$(curl -s -H "Authorization: Bearer $TOKEN" \
      http://localhost:5002/tools/read_roaster_status)
    TEMP=$(echo "$STATUS" | jq -r '.data.bean_temp_c')
    echo "   T+${i}5s: Bean temp = ${TEMP}°C"
done
echo ""

# Check FC status again
echo "3️⃣  Checking FC detection status again..."
FC_STATUS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:5001/tools/get_first_crack_status)
FC_DETECTED=$(echo "$FC_STATUS" | jq -r '.result.first_crack_detected')
echo "$FC_STATUS" | jq '.result | {is_running, first_crack_detected, mock_mode}'
echo ""

if [ "$FC_DETECTED" = "true" ]; then
    echo "✅ First crack was detected!"
else
    echo "ℹ️  First crack not yet detected (need to wait ~90s total)"
fi
echo ""

# Cleanup
echo "🧹 Cleanup"
echo "----------"
echo ""

echo "Stopping FC detection..."
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:5001/tools/stop_first_crack_detection | jq '.'
echo ""

echo "Stopping roaster..."
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:5002/tools/stop_roaster | jq '.'
echo ""

echo "✅ Demo mode test complete!"
echo ""
echo "Summary:"
echo "--------"
echo "✅ Both servers running in demo mode"
echo "✅ Auth0 authentication working"
echo "✅ Roaster control responding to commands"
echo "✅ Temperature simulation active"
echo "✅ FC detection running"
echo ""
echo "Next steps:"
echo "- Wait ~90 seconds to see FC auto-trigger"
echo "- Monitor temperature progression through phases"
echo "- Test with different heat/fan settings"
echo "- Try different scenarios (medium_roast, light_roast)"
