# DevUI Integration Complete ✅

**Date:** November 2025  
**Status:** Ready for testing

---

## Summary

Microsoft Agent Framework **DevUI** is now fully integrated into the coffee roasting agent project, providing a powerful web-based interface for visual debugging, testing, and agent development.

---

## What Was Added

### 1. **Dependencies** (`requirements.txt`)
```
agent-framework-devui>=0.1.0
```

### 2. **DevUI Server Launcher** (`agents/roaster/devui_server.py`)
- Standalone script to launch DevUI with the roasting agent
- Command-line arguments for port, tracing, browser control
- Automatic agent initialization and MCP connection
- User-friendly terminal output with tips

### 3. **Multi-Agent Example** (`agents/roaster/examples/devui_example.py`)
- Demonstrates DevUI with 3 agents simultaneously:
  - **CoffeeRoastingAgent** - Roaster control + first crack detection
  - **QualityControlAgent** - Roast quality evaluation
  - **InventoryAgent** - Bean inventory management
- Shows multi-agent orchestration patterns

### 4. **Comprehensive Documentation**
- **agents/roaster/README.md** - Updated with DevUI section
- **docs/04-phase-4/DEVUI.md** - Complete DevUI guide (570 lines)
- **docs/04-phase-4/QUICKSTART.md** - Added DevUI quick start

---

## How to Use

### Launch Single Agent

```bash
python -m agents.roaster.devui_server
```

Opens http://localhost:8080 with **CoffeeRoastingAgent** ready to test.

### Launch Multi-Agent

```bash
python agents/roaster/examples/devui_example.py
```

Opens http://localhost:8080 with **3 agents** available in dropdown.

### Custom Options

```bash
# Custom port
python -m agents.roaster.devui_server --port 8888

# No auto browser
python -m agents.roaster.devui_server --no-browser

# Enable tracing
python -m agents.roaster.devui_server --tracing framework
```

---

## Features

### 🖥️ Interactive Web Interface
- Chat with agents in browser
- Natural language interaction
- Real-time responses
- Multi-turn conversations

### 🔍 Tool Call Visualization
- See every MCP tool invocation
- Inspect request parameters
- View response payloads
- Debug tool execution flow
- JSON syntax highlighting

### 💬 Conversation Management
- Create and name conversations
- Switch between conversations
- Review conversation history
- Export for analysis

### 🧠 Agent Inspector
- View agent configuration
- List available tools
- Inspect instructions
- Monitor agent state

### 📊 Performance Metrics
- Response time tracking
- Token usage monitoring
- Tool execution timing
- API call statistics

### 🔬 OpenTelemetry Integration
- Distributed tracing support
- Aspire Dashboard integration
- Span visualization
- Performance profiling

---

## Testing Scenarios

### Scenario 1: Roaster Status Check
```
You: Check the current roaster status

Agent: [Calls get_roaster_status()]
The roaster is idle. Bean temp: 25°C, Chamber: 25°C, Heat: 0%, Fan: 0%
```

### Scenario 2: Start Preheat
```
You: Start preheat at 100% heat

Agent: [Calls start_roaster(initial_heat=100)]
✅ Roaster started. Chamber heating to 180-200°C for bean loading.
```

### Scenario 3: First Crack Detection
```
You: Start first crack detection with USB microphone

Agent: [Calls start_first_crack_detection(audio_source='usb_microphone')]
✅ Audio monitoring active. Threshold: 0.5, Min pops: 3
```

### Scenario 4: Status and Adjust
```
You: Check status and make adjustments if needed

Agent: [Calls get_roaster_status(), get_first_crack_status()]
Current phase: Maillard. Bean temp: 185°C, RoR: 7.2°C/min.
No adjustments needed. Monitoring for first crack (~30 seconds).
```

### Scenario 5: Multi-Agent Quality Check
```
# Switch to QualityControlAgent in dropdown

You: Evaluate a roast at 196°C with 18% development

Agent: [Calls simulate_quality_check(196, 18)]
Quality Score: 80/80 - Excellent
✅ Perfect light roast temperature
✅ Optimal development time
Recommendation: Approved for sale
```

---

## DevUI API

### List Agents
```bash
curl http://localhost:8080/v1/entities
```

### Send Message
```bash
curl -X POST http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{"model": "CoffeeRoastingAgent", "input": "Check status"}'
```

### Python Client
```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8080/v1", api_key="not-needed")
response = client.responses.create(
    model="CoffeeRoastingAgent",
    input="Start preheat"
)
```

---

## Architecture

```
┌────────────────────────────────────────────────┐
│         DevUI Server (Port 8080)               │
│                                                 │
│  ┌──────────────────────────────────────────┐ │
│  │  Web Interface (React)                   │ │
│  │  - Chat UI                               │ │
│  │  - Agent Selector                        │ │
│  │  - Tool Call Inspector                   │ │
│  │  - Conversation History                  │ │
│  └──────────────────────────────────────────┘ │
│                      │                          │
│                      ▼                          │
│  ┌──────────────────────────────────────────┐ │
│  │  REST API (/v1/*)                        │ │
│  │  - OpenAI-compatible                     │ │
│  │  - Entity management                     │ │
│  │  - Conversation storage                  │ │
│  └──────────────────────────────────────────┘ │
│                      │                          │
└──────────────────────┼──────────────────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │  Registered Agents            │
       │                               │
       │  1. CoffeeRoastingAgent       │
       │     - 11 MCP tools            │
       │     - First crack detection   │
       │     - Roaster control         │
       │                               │
       │  2. QualityControlAgent       │
       │     - Quality scoring         │
       │                               │
       │  3. InventoryAgent            │
       │     - Bean inventory          │
       └───────────────────────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │  MCP Servers (HTTP + Auth0)   │
       │                               │
       │  - First Crack (5001)         │
       │  - Roaster Control (5002)     │
       └───────────────────────────────┘
```

---

## Benefits

### For Development
- **Rapid Testing** - Test agent behavior without writing code
- **Visual Debugging** - See exactly what tools are called
- **Quick Iteration** - Modify instructions, reload agent
- **Multi-Agent** - Test agent coordination in one UI

### For Debugging
- **Tool Inspection** - Verify parameters and responses
- **Conversation Review** - Understand agent reasoning
- **Performance Metrics** - Identify bottlenecks
- **Error Diagnosis** - Pinpoint failures quickly

### For Demonstration
- **Live Demos** - Show agent capabilities interactively
- **Stakeholder Reviews** - Non-technical users can test
- **Feature Validation** - Prove functionality works
- **User Feedback** - Gather insights from testing

---

## Comparison: DevUI vs. CLI Agent

| Aspect | DevUI | CLI Agent |
|--------|-------|-----------|
| **Interface** | Web browser | Terminal |
| **Visualization** | Tool calls highlighted | Text only |
| **History** | Full conversation view | Scrollback buffer |
| **Multi-user** | Shareable URL | Single terminal |
| **Tool Inspection** | Click to expand JSON | Manual logging |
| **Testing** | Point-and-click | Code/scripts |
| **Learning Curve** | Immediate | Requires Python |
| **Production** | Dev/demo only | Can run in prod |

**Use DevUI for:** Development, debugging, demos, testing  
**Use CLI for:** Production, automation, scripting, CI/CD

---

## Next Steps

### Immediate
1. ✅ Launch DevUI and test basic commands
2. ✅ Verify MCP tool calls work correctly
3. ✅ Test multi-turn conversations

### Short Term
- Add more example agents (quality, inventory, analytics)
- Create test scenarios for common workflows
- Document best practices for DevUI usage
- Integrate with Aspire Dashboard tracing

### Long Term
- Build custom DevUI plugins for roast visualization
- Add real-time telemetry dashboard
- Create saved conversation templates
- Develop automated testing suite using DevUI API

---

## Resources

- **Quick Start:** [QUICKSTART.md](./QUICKSTART.md) - 5-minute setup
- **Complete Guide:** [DEVUI.md](./DEVUI.md) - Full documentation (570 lines)
- **Agent README:** [agents/roaster/README.md](../../agents/roaster/README.md)
- **DevUI GitHub:** https://github.com/microsoft/agent-framework/tree/main/python/packages/devui

---

## Troubleshooting

### DevUI won't start
```bash
pip install agent-framework-devui --pre
```

### Agent not listed
Check terminal for initialization errors, verify `.env` configuration.

### MCP tools fail
Ensure MCP servers running:
```bash
curl http://localhost:5001/health
curl http://localhost:5002/health
```

### Port conflict
```bash
python -m agents.roaster.devui_server --port 8888
```

---

**DevUI Integration Complete! 🎉**

Your coffee roasting agent now has enterprise-grade visual debugging and testing capabilities. Launch DevUI, start chatting with your agent, and see the magic happen! ☕🤖

---

**Built with ❤️ using Microsoft Agent Framework DevUI**
