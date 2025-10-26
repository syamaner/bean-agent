#!/bin/bash
# Fast test runner for Phase 3
# Runs only unit tests, skips slow integration tests

set -e

echo "🧪 Running Phase 3 Tests (Fast Mode)"
echo "======================================"

cd "$(dirname "$0")/.."

# Run fast tests only (unit tests, no integration/slow tests)
echo ""
echo "📦 Running fast unit tests..."
./venv/bin/pytest -c pytest-fast.ini --durations=5

echo ""
echo "✅ All Phase 3 tests passed in $(date +%s) seconds!"
echo ""
echo "💡 To run all project tests:"
echo "   ./venv/bin/pytest tests/ -v"
echo ""
echo "💡 To run integration tests (requires Auth0, slower):"
echo "   ./venv/bin/pytest tests/mcp_servers/ -v -m integration"
