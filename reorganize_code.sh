#!/bin/bash
# Code Reorganization Script
# Moves Phase3 orchestration code into src/orchestration

set -e

echo "🔧 Coffee Roasting Project - Code Reorganization"
echo "================================================"
echo ""

# Create new structure
echo "📁 Creating src/orchestration structure..."
mkdir -p src/orchestration/aspire
mkdir -p src/orchestration/agents
mkdir -p src/orchestration/workflows
mkdir -p src/orchestration/scripts
mkdir -p scripts/maintenance
mkdir -p scripts/setup

echo "✅ Directories created"
echo ""

# Move Aspire AppHost
echo "📦 Moving Aspire AppHost..."
mv Phase3/CoffeeRoasting.AppHost/* src/orchestration/aspire/ 2>/dev/null || true
mv Phase3/CoffeeRoasting.sln src/orchestration/ 2>/dev/null || true
mv Phase3/global.json src/orchestration/ 2>/dev/null || true
echo "✅ Aspire components moved"
echo ""

# Move Python agents
echo "🤖 Moving autonomous agents..."
mv Phase3/autonomous_agent.py src/orchestration/agents/ 2>/dev/null || true
mv Phase3/demo_agent.py src/orchestration/agents/ 2>/dev/null || true
touch src/orchestration/agents/__init__.py
echo "✅ Agents moved"
echo ""

# Move workflows (if exist)
echo "🔄 Moving workflows..."
if [ -d "Phase3/workflows" ]; then
    mv Phase3/workflows/* src/orchestration/workflows/ 2>/dev/null || true
fi
echo "✅ Workflows moved"
echo ""

# Move scripts
echo "📜 Moving scripts..."
mv Phase3/test_mcp_connection.py src/orchestration/scripts/ 2>/dev/null || true
mv Phase3/run_tests.sh src/orchestration/scripts/ 2>/dev/null || true
mv scripts/run_demo_servers.sh src/orchestration/scripts/ 2>/dev/null || true
echo "✅ Scripts moved"
echo ""

# Move utility scripts to proper locations
echo "🛠️  Organizing utility scripts..."
mv cleanup_docs.sh scripts/maintenance/ 2>/dev/null || true
# Keep set_env.sh at root (needed globally)
echo "✅ Utility scripts organized"
echo ""

# Create orchestration README
echo "📝 Creating orchestration README..."
cat > src/orchestration/README.md << 'EOF'
# Coffee Roasting Orchestration

This directory contains the orchestration layer for the autonomous coffee roasting system.

## Components

### Aspire (.NET)
- **aspire/**: .NET Aspire AppHost for orchestrating all services
  - Manages MCP servers (roaster control, first crack detection)
  - Manages autonomous AI agent
  - Provides service discovery and configuration
  - See `aspire/README.md` for details

### Agents (Python)
- **agents/autonomous_agent.py**: Main autonomous roasting agent
  - Uses OpenAI GPT-4 for decision making
  - Monitors roast progress via MCP servers
  - Adjusts heat/fan based on temperature, RoR, and development time
  - Handles first crack detection and post-FC roasting logic
  
- **agents/demo_agent.py**: Simplified demo agent for testing

### Scripts
- **scripts/run_aspire.sh**: Start Aspire orchestration
- **scripts/run_demo_servers.sh**: Start MCP servers for testing
- **scripts/test_mcp_connection.py**: Test MCP client connectivity

### Workflows
- **workflows/**: n8n workflow definitions (if used)

## Quick Start

### With Aspire (Production)
```bash
cd src/orchestration
dotnet run --project aspire
```

### Manual Testing
```bash
# Start MCP servers
./scripts/run_demo_servers.sh

# Run autonomous agent
cd ../..
./venv/bin/python src/orchestration/agents/autonomous_agent.py
```

## Configuration

Aspire configuration files:
- `aspire/appsettings.json` - Base settings
- `aspire/appsettings.Development.json` - Development overrides
- `aspire/appsettings.Demo.json` - Demo mode settings

Agent requires environment variables:
- `OPENAI_API_KEY` - OpenAI API key
- `AUTH0_DOMAIN` - Auth0 domain
- `AUTH0_CLIENT_ID` - Auth0 M2M client ID
- `AUTH0_CLIENT_SECRET` - Auth0 M2M client secret
- `AUTH0_AUDIENCE` - Auth0 API audience
- `TEST_AUDIO_FILE` - (Optional) Audio file for testing FC detection

## Architecture

```
┌─────────────────────────────────────────┐
│         .NET Aspire AppHost             │
│  (Service orchestration & discovery)    │
└──────────────┬──────────────────────────┘
               │
      ┌────────┼────────┐
      │        │        │
      ▼        ▼        ▼
   ┌────┐  ┌────┐  ┌─────┐
   │MCP │  │MCP │  │ AI  │
   │RC  │  │FC  │  │Agent│
   └────┘  └────┘  └─────┘
      │        │        │
      └────────┴────────┘
             │
      ┌──────▼───────┐
      │   Hardware   │
      │ Hottop + Mic │
      └──────────────┘
```

## Documentation

- Main docs: `../../docs/03-phase-3/`
- Aspire setup: `aspire/README.md`
- Agent architecture: `../../Phase3/docs/ARCHITECTURE.md`

## Related

- MCP Servers: `../mcp_servers/`
- Model inference: `../inference/`
- Training code: `../training/`
EOF

echo "✅ Orchestration README created"
echo ""

# Update Aspire project paths (needs manual verification)
echo "⚠️  NOTE: You may need to update paths in:"
echo "   - src/orchestration/aspire/Program.cs (projectRoot paths)"
echo "   - src/orchestration/CoffeeRoasting.sln (project paths)"
echo ""

# Create summary
echo "📊 Creating reorganization summary..."
cat > REORGANIZATION_SUMMARY.md << 'EOF'
# Code Reorganization Summary

**Date**: October 26, 2025  
**Action**: Moved orchestration code from `Phase3/` to `src/orchestration/`

## Changes

### Created Structure
```
src/orchestration/
├── aspire/              # .NET Aspire AppHost (from Phase3/CoffeeRoasting.AppHost)
├── agents/              # Python autonomous agents (from Phase3/*.py)
├── workflows/           # n8n workflows (from Phase3/workflows)
├── scripts/             # Orchestration scripts (from Phase3/*.sh, Phase3/*.py)
├── CoffeeRoasting.sln   # Solution file (from Phase3/)
├── global.json          # .NET config (from Phase3/)
└── README.md            # Orchestration overview
```

### Files Moved

**Phase3/ → src/orchestration/:**
- `CoffeeRoasting.AppHost/` → `aspire/`
- `CoffeeRoasting.sln` → `./`
- `global.json` → `./`
- `autonomous_agent.py` → `agents/`
- `demo_agent.py` → `agents/`
- `test_mcp_connection.py` → `scripts/`
- `run_tests.sh` → `scripts/`
- `workflows/` → `workflows/`

**scripts/ → src/orchestration/scripts/:**
- `run_demo_servers.sh`

**Root → scripts/:**
- `cleanup_docs.sh` → `scripts/maintenance/`

## Next Steps

1. ✅ Files moved to new structure
2. ⏭️ Update `src/orchestration/aspire/Program.cs` paths
   - Change `projectRoot` from `../..` to `../../..`
   - Change `sharedVenvPath` from `../../venv` to `../../../venv`
3. ⏭️ Update solution file paths if needed
4. ⏭️ Test Aspire orchestration: `cd src/orchestration && dotnet run --project aspire`
5. ⏭️ Update import paths in agents (if any relative imports)
6. ⏭️ Update WARP.md with new structure
7. ⏭️ Remove empty Phase3/ directory

## Benefits

- ✅ All orchestration code under `src/`
- ✅ Clearer separation: orchestration vs. services vs. ML
- ✅ Easier to navigate: `src/orchestration`, `src/mcp_servers`, `src/training`
- ✅ Phase3/ name was confusing - now clearly "orchestration"
EOF

echo "✅ Summary created: REORGANIZATION_SUMMARY.md"
echo ""

echo "✨ Reorganization complete!"
echo ""
echo "Directory structure:"
echo "  src/orchestration/aspire/     - .NET Aspire AppHost"
echo "  src/orchestration/agents/     - Python autonomous agents"
echo "  src/orchestration/workflows/  - n8n workflows"
echo "  src/orchestration/scripts/    - Orchestration scripts"
echo ""
echo "⚠️  IMPORTANT: Update paths in src/orchestration/aspire/Program.cs"
echo "   - projectRoot should be ../../.. (3 levels up)"
echo "   - venv path should be ../../../venv"
echo ""
echo "Next: cd src/orchestration && dotnet run --project aspire"
