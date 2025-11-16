# Phase 4: Microsoft Agent Framework Integration

**Status:** ✅ IMPLEMENTATION COMPLETE  
**Date:** November 2025

---

## Overview

Phase 4 adds Microsoft Agent Framework support to the coffee roasting project, providing an alternative agent implementation alongside the existing custom Python agent (n8n-based). This creates a more structured, type-safe approach to building autonomous roasting agents with built-in tooling for development and debugging.

## Why Agent Framework?

The Microsoft Agent Framework brings enterprise-grade capabilities:

1. **Type-Safe Tool Definitions** - Pydantic models with automatic OpenAI function schema generation
2. **Built-in LLM Integration** - Native OpenAI client with function calling support
3. **DevUI for Debugging** - Visual interface for monitoring agent state and interactions
4. **Multi-Agent Orchestration** - Framework for coordinating multiple specialized agents
5. **Production-Ready Patterns** - Best practices for agent lifecycle, error handling, and testing

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         Microsoft Agent Framework (Python)                   │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  ChatAgent (OpenAI GPT-4o)                            │  │
│  │                                                        │  │
│  │  Instructions: Professional roasting expertise        │  │
│  │  Tools: 11 MCP-backed functions                       │  │
│  │  Client: OpenAIChatClient                             │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  FirstCrackTools │  │ RoasterControl   │                 │
│  │                  │  │ Tools            │                 │
│  │  - start_detection│  │ - get_status    │                 │
│  │  - get_status    │  │ - start_roaster  │                 │
│  │  - stop_detection│  │ - set_heat       │                 │
│  │                  │  │ - set_fan        │                 │
│  │                  │  │ - drop_beans     │                 │
│  │                  │  │ - stop_roaster   │                 │
│  └──────────────────┘  └──────────────────┘                 │
│           │                      │                            │
└───────────┼──────────────────────┼────────────────────────────┘
            │                      │
            │   HTTP + Auth0 JWT   │
            ▼                      ▼
  ┌──────────────────┐    ┌──────────────────┐
  │ First Crack MCP  │    │ Roaster Control  │
  │ (Port 5001)      │    │ MCP (Port 5002)  │
  │                  │    │                  │
  │ - Audio ML Model │    │ - Hottop USB     │
  │ - Pop detection  │    │ - pyhottop lib   │
  │ - Confirmation   │    │ - Mock/Real HW   │
  └──────────────────┘    └──────────────────┘
```

## What's New

### Agent Implementation (`agents/roaster/`)

```
agents/roaster/
├── __init__.py          # Package exports
├── agent.py             # ChatAgent with roasting expertise
├── config.py            # Configuration models (Pydantic)
├── mcp_tools.py         # MCP server tool wrappers
├── auth.py              # Auth0 M2M token management
├── README.md            # Complete documentation
└── .env.example         # Environment template
```

### Key Features

1. **11 MCP Tools** - Full coverage of both MCP servers:
   - First crack: `start_detection`, `get_status`, `stop_detection`
   - Roaster: `get_status`, `start_roaster`, `set_heat`, `set_fan`, `drop_beans`, `stop_roaster`, `start_cooling`, `stop_cooling`

2. **Expert Instructions** - 100+ lines of roasting knowledge embedded in agent prompt:
   - Phase-based decision making (preheat → drying → Maillard → first crack → development)
   - Safety rules and limits
   - RoR (Rate of Rise) monitoring logic
   - Professional roasting best practices

3. **Type-Safe Configuration** - Pydantic models for:
   - Agent settings (OpenAI, MCP URLs, Auth0)
   - Roast profile parameters (target FC time, development %, drop temp)
   - Safety limits (max temp, RoR thresholds)

4. **Automatic Auth0 Integration** - Token caching and refresh:
   - M2M authentication flow
   - 1-hour token lifetime with auto-refresh
   - Secure credential management

## Comparison: Agent Framework vs. n8n Agent

| Aspect | MS Agent Framework | n8n Custom Agent |
|--------|-------------------|------------------|
| **Implementation** | Python ChatAgent | n8n workflow + GPT-4 |
| **Tools** | Type-safe functions | HTTP request nodes |
| **Configuration** | Pydantic models | n8n credentials |
| **Debugging** | DevUI + logs | n8n execution viewer |
| **Deployment** | Python process | n8n container |
| **Learning Curve** | Framework patterns | Workflow design |
| **Multi-agent** | Native support | Manual coordination |
| **Best For** | Complex workflows, multiple agents | Visual design, existing n8n setup |

**Both are valid!** Choose based on your needs:
- **Agent Framework:** Building multiple specialized agents, type safety, Python-native development
- **n8n:** Visual workflow design, existing n8n infrastructure, non-programmers

## Quick Start

### 1. Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

New packages:
- `agent-framework-core>=0.1.0`
- `agent-framework-openai>=0.1.0`
- `openai>=1.0.0`

### 2. Configure Environment

Copy and edit `.env`:

```bash
cp agents/roaster/.env.example agents/roaster/.env
# Edit with your credentials
```

Required:
- `OPENAI_API_KEY` - Your OpenAI API key
- `AUTH0_*` - Auth0 M2M credentials for MCP servers

### 3. Start MCP Servers

```bash
# Terminal 1
python -m src.mcp_servers.first_crack_detection

# Terminal 2
python -m src.mcp_servers.roaster_control
```

Or use .NET Aspire if configured.

### 4. Run the Agent

**Interactive mode:**
```bash
python -m agents.roaster.agent
```

**Programmatic:**
```python
from agents.roaster import create_roasting_agent

agent = create_roasting_agent()
response = await agent.run("Start the preheat cycle")
```

See [agents/roaster/README.md](../../agents/roaster/README.md) for complete usage guide.

## Example Agent Interaction

```
🔥 Coffee Roasting Agent - MS Agent Framework
============================================================

✅ Agent initialized with MCP tools:
   - First Crack Detection: http://localhost:5001
   - Roaster Control: http://localhost:5002

🤖 You: Start the preheat cycle and begin first crack detection

🔄 Agent thinking...

🤖 Agent: I'll start the roaster and audio monitoring now.

[Calls: start_roaster(initial_heat=100)]
✅ Roaster started at 100% heat

[Calls: start_first_crack_detection(audio_source='usb_microphone')]
✅ First crack detection active on USB microphone

The roaster is preheating. Target chamber temp is 180-200°C. 
I'll monitor every 10 seconds and let you know when ready for beans.

---

🤖 You: Check status and adjust as needed

🔄 Agent thinking...

[Calls: get_roaster_status()]
[Calls: get_first_crack_status()]

🤖 Agent: Current status at 8:45:
- Bean temp: 185°C
- Chamber temp: 192°C
- RoR: 7.2°C/min
- Heat: 85%, Fan: 30%
- First crack: Not detected yet

We're in the Maillard phase with good RoR. Approaching first crack zone.
Maintaining current settings and monitoring closely. Expected FC in ~30 seconds.
```

## Use Cases

### 1. Standalone Agent

Run as independent Python process:
```python
agent = create_roasting_agent()

while roasting:
    response = await agent.run(
        "Check status and make adjustments if needed"
    )
    await asyncio.sleep(10)
```

### 2. Multi-Agent Orchestration

Coordinate multiple specialized agents:
```python
roast_agent = create_roasting_agent()
quality_agent = create_quality_control_agent()
inventory_agent = create_inventory_agent()

# Roast agent controls hardware
roast_response = await roast_agent.run("Execute roast")

# Quality agent evaluates results
quality_response = await quality_agent.run(
    f"Evaluate this roast: {roast_response}"
)

# Inventory agent updates stock
inventory_response = await inventory_agent.run(
    f"Record roast completion: {quality_response}"
)
```

### 3. DevUI Integration

Debug agent visually:
```bash
pip install agent-framework-devui
python -m agent_framework.devui --agent agents.roaster:agent
```

Open http://localhost:8000 to see:
- Real-time agent state
- Tool call history
- LLM conversation
- Performance metrics

## Testing

Unit tests for tools:
```python
def test_first_crack_status():
    config = MCPServerConfig(url="http://localhost:5001", ...)
    tools = FirstCrackTools(config)
    status = tools.get_status()
    assert "detection_active" in status
```

Integration tests:
```bash
pytest tests/agents/ -v
```

## Next Steps

### Immediate
1. ✅ Test agent with mock hardware
2. ✅ Verify all MCP tools work correctly
3. ✅ Create roast profiles (light/medium/dark)

### Short Term
- Add observability (OpenTelemetry integration)
- Build custom tools (roast logging, bean inventory)
- Create agent test suite

### Long Term
- Multi-agent orchestration (roaster + quality + inventory)
- Production deployment patterns
- Real-time roast analytics dashboard

## Resources

- [Agent Implementation README](../../agents/roaster/README.md) - Complete usage guide
- [MS Agent Framework GitHub](https://github.com/microsoft/agent-framework) - Official docs
- [Phase 3 Architecture](../03-phase-3/ARCHITECTURE.md) - Original custom agent
- [Project README](../../README.md) - Overall project overview

## Contributing

This is an experimental addition to explore alternative agent architectures. Both the Agent Framework and custom n8n approaches are maintained. Choose the one that best fits your workflow.

---

**Phase 4 Complete ✅** - Agent Framework integration ready for testing

Built with ☕ and 🤖
