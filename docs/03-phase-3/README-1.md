# Phase 3: AI-Orchestrated Coffee Roasting 🤖☕

**Status**: ✅ Complete  
**Date**: October 26, 2025

## Overview

AI-powered coffee roasting orchestration using:
- **MCP SSE Servers** (roaster control + first crack detection)
- **Auth0 M2M Authentication** (secure API access)
- **.NET Aspire** (service orchestration)
- **Python AI Agent** (GPT-4 powered)

## Quick Start

### 1. Configure OpenAI API Key

Edit `CoffeeRoasting.AppHost/appsettings.Development.json`:
```json
{
  "Parameters": {
    "openai-api-key": "sk-your-actual-key-here"
  }
}
```

### 2. Start Everything

```bash
cd CoffeeRoasting.AppHost
dotnet run
```

This starts:
- ✅ Roaster Control MCP Server (http://localhost:5002)
- ✅ First Crack Detection MCP Server (http://localhost:5001)
- ✅ Python AI Agent (runs once, then exits)
- ✅ Aspire Dashboard (http://localhost:15055)

### 3. View Results

Check the Aspire dashboard to see the AI agent's output and roaster interactions.

## Architecture

```
┌─────────────────┐
│  Python AI      │  GPT-4 powered agent
│  Agent          │  (demo_agent.py)
└────────┬────────┘
         │ MCP SSE + Auth0
         ├───────────────────┬──────────────────
         │                   │
┌────────▼────────┐   ┌──────▼──────────┐
│ Roaster Control │   │ First Crack     │
│  MCP Server     │   │ Detection MCP   │
│  Port: 5002     │   │  Port: 5001     │
└────────┬────────┘   └────────┬────────┘
         │                     │
         └──────────┬──────────┘
                    │
           ┌────────▼────────┐
           │  .NET Aspire    │
           │  Orchestrator   │
           └─────────────────┘
```

## What the Agent Does

The Python AI agent (`demo_agent.py`) demonstrates:

1. **🔐 Authenticate** - Gets Auth0 M2M token
2. **🔌 Connect** - Establishes MCP SSE connections to both servers
3. **📊 Read Status** - Fetches current roaster status
4. **🤔 AI Analysis** - GPT-4 creates optimal roasting plan
5. **🔥 Control** - Starts roaster, sets heat and fan
6. **✅ Complete** - Shows full Phase 3 capabilities

## Alternative: Claude Desktop

For interactive AI chat with the roaster:

See: [CLAUDE_DESKTOP_SETUP.md](./CLAUDE_DESKTOP_SETUP.md)

## Files

```
Phase3/
├── CoffeeRoasting.AppHost/        # .NET Aspire orchestration
│   ├── Program.cs                  # Service configuration
│   └── appsettings.Development.json # Config (Auth0 + OpenAI)
├── demo_agent.py                   # Python AI agent script
├── CLAUDE_DESKTOP_SETUP.md         # Claude integration guide
└── README.md                       # This file
```

## MCP Servers

### Roaster Control (Port 5002)
- `read_roaster_status` - Temperature, heat, fan, timing
- `start_roaster` / `stop_roaster` - Drum control
- `set_heat` / `set_fan` - Adjust settings (0-100%)
- `drop_beans` - Drop and start cooling

### First Crack Detection (Port 5001)
- `start_first_crack_detection` - Begin audio monitoring
- `get_first_crack_status` - Check status
- `stop_first_crack_detection` - End monitoring

## Authentication

Auth0 M2M tokens (24hr expiry):
```bash
curl -s -X POST https://genai-7175210165555426.uk.auth0.com/oauth/token \
  -H 'Content-Type: application/json' \
  -d '{
    "client_id": "Jk3aF2NfkiiOIXY0eHJQxfA6jkP0Pjf7",
    "client_secret": "YOUR_AUTH0_CLIENT_SECRET",
    "audience": "https://coffee-roasting-api",
    "grant_type": "client_credentials"
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])"
```

## Troubleshooting

**Agent fails to start?**
- Set valid `OPENAI_API_KEY` in appsettings
- Check Aspire dashboard logs

**MCP connection errors?**
- Verify servers are healthy: `curl http://localhost:5002/health`
- Check Auth0 token in demo script

**Want to run agent manually?**
```bash
export OPENAI_API_KEY="your-key"
python demo_agent.py
```

## Success! 🎉

Phase 3 complete when you see in Aspire logs:
- ✅ Auth0 token acquired
- ✅ MCP servers connected
- ✅ Roaster status read
- ✅ GPT-4 roasting plan
- ✅ Roaster controlled successfully

## Next Steps

- Connect real Hottop hardware (set `ROASTER_MOCK_MODE=0`)
- Build autonomous roasting loops
- Add roast profile management
- Log and analyze roast data
