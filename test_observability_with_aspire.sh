#!/bin/bash
# Test script to verify observability works with Aspire

echo "🧪 Testing Observability with Aspire"
echo "====================================="
echo ""

# Check if Aspire is running
echo "1. Checking if Aspire dashboard is accessible..."
if curl -s http://localhost:4317 > /dev/null 2>&1; then
    echo "   ✅ Aspire OTLP endpoint is accessible at http://localhost:4317"
else
    echo "   ❌ Aspire OTLP endpoint NOT accessible"
    echo "   ⚠️  Please start your Aspire AppHost first:"
    echo "      dotnet run --project path/to/YourApp.AppHost"
    exit 1
fi

echo ""
echo "2. Setting environment variables..."
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export OTEL_SERVICE_NAME="test-mcp-server"
echo "   ✅ OTEL_EXPORTER_OTLP_ENDPOINT=$OTEL_EXPORTER_OTLP_ENDPOINT"
echo "   ✅ OTEL_SERVICE_NAME=$OTEL_SERVICE_NAME"

echo ""
echo "3. Testing observability package..."
cd /Users/sertanyamaner/git/coffee-roasting
PYTHONPATH=src ./venv/bin/python -c "
from observability import setup_logging, setup_tracing, FirstCrackMetrics, get_logger

# Initialize
setup_logging('test-service')
tracer = setup_tracing('test-service')
metrics = FirstCrackMetrics('test-service')
logger = get_logger(__name__)

# Test logging
logger.info('Test log message', extra={'test_key': 'test_value'})

# Test metrics
from datetime import datetime, timezone
metrics.record_detection(
    utc_timestamp=datetime.now(timezone.utc),
    relative_timestamp_seconds=120.0,
    audio_source='test',
    confidence=0.85
)

print('✅ Successfully sent telemetry to Aspire!')
print('')
print('Check your Aspire dashboard at: http://localhost:18888')
print('  - Logs tab: Look for \"test-service\"')
print('  - Metrics tab: Look for fc.detections.total')
print('  - Traces tab: Look for trace spans')
"

echo ""
echo "====================================="
echo "✅ Test complete!"
echo ""
echo "Next steps:"
echo "1. Open Aspire dashboard: http://localhost:18888"
echo "2. Check Logs/Metrics/Traces tabs for 'test-service'"
echo "3. Run your actual MCP servers with these env vars set"
