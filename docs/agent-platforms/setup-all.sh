#!/bin/bash
# Quick Setup Script for All Agent Platforms
# Coffee Roasting Project - Agent Orchestration

set -e

echo "🚀 Coffee Roasting - Agent Platform Setup"
echo "=========================================="
echo ""

# Navigate to Aspire directory
cd "$(dirname "$0")/../../src/orchestration/aspire" || exit 1

echo "📍 Working directory: $(pwd)"
echo ""

# Check if user secrets are already set
echo "🔐 Checking user secrets..."
if dotnet user-secrets list | grep -q "langflow-password"; then
    echo "✅ LangFlow password already set"
else
    echo "⚠️  LangFlow password not set"
    read -rsp "Enter password for LangFlow (admin user): " LANGFLOW_PASS
    echo ""
    dotnet user-secrets set "Parameters:langflow-password" "$LANGFLOW_PASS"
    echo "✅ LangFlow password set"
fi

if dotnet user-secrets list | grep -q "flowise-password"; then
    echo "✅ Flowise password already set"
else
    echo "⚠️  Flowise password not set"
    read -rsp "Enter password for Flowise (admin user): " FLOWISE_PASS
    echo ""
    dotnet user-secrets set "Parameters:flowise-password" "$FLOWISE_PASS"
    echo "✅ Flowise password set"
fi

if dotnet user-secrets list | grep -q "n8n-api-key"; then
    echo "✅ n8n API key already set"
else
    echo "⚠️  n8n API key not set"
    N8N_KEY=$(openssl rand -base64 32)
    dotnet user-secrets set "Parameters:n8n-api-key" "$N8N_KEY"
    echo "✅ n8n API key set (auto-generated)"
fi

echo ""
echo "✅ All secrets configured!"
echo ""
echo "📦 Starting Aspire..."
echo "   Dashboard will be at: http://localhost:15000"
echo ""
echo "🎯 Agent Platforms:"
echo "   LangFlow: http://localhost:7860 (⭐ Recommended)"
echo "   Flowise:  http://localhost:3000"
echo "   n8n:      http://localhost:5678"
echo ""
echo "📚 Next steps:"
echo "   1. Run 'dotnet run' from src/orchestration/aspire"
echo "   2. Open your chosen platform"
echo "   3. Follow docs/agent-platforms/<platform>/docs/SETUP.md"
echo ""
echo "💡 Quick links:"
echo "   - Main README: docs/agent-platforms/README.md"
echo "   - Comparison: docs/03-phase-3/agent-platform-comparison.md"
echo ""
echo "🎉 Setup complete! Happy roasting!"
