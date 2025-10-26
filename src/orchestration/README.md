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
