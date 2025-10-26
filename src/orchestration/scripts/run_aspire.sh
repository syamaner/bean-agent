#!/bin/bash
# Run Aspire orchestration
# This starts all services (MCP servers + AI agent) via .NET Aspire

set -e

echo "🚀 Starting Coffee Roasting Orchestration via Aspire"
echo "===================================================="
echo ""

# Check if in correct directory
if [ ! -f "../aspire/CoffeeRoasting.AppHost.csproj" ]; then
    echo "❌ Error: Must be run from src/orchestration/scripts/"
    echo "   Current directory: $(pwd)"
    exit 1
fi

# Check if .NET is installed
if ! command -v dotnet &> /dev/null; then
    echo "❌ Error: .NET SDK not found"
    echo "   Install from: https://dotnet.microsoft.com/download"
    exit 1
fi

# Navigate to orchestration directory
cd ..

echo "📋 Configuration:"
echo "   Working directory: $(pwd)"
echo "   Project: aspire/CoffeeRoasting.AppHost.csproj"
echo ""

echo "▶️  Starting Aspire AppHost..."
echo ""

dotnet run --project aspire
