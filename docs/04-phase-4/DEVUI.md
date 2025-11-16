# DevUI Guide: Visual Debugging for Coffee Roasting Agent

Complete guide to using Microsoft Agent Framework DevUI with your coffee roasting agents.

---

## What is DevUI?

DevUI is a **web-based development interface** for Microsoft Agent Framework that provides:

### 🖥️ Interactive Chat Interface
- Test agents directly in your browser
- Natural language interaction
- Real-time responses
- Multi-turn conversations with context

### 🔍 Tool Call Visualization
- See which MCP tools are invoked
- View request parameters
- Inspect response data
- Debug tool execution flow

### 💬 Conversation Management
- Create and manage conversation threads
- Review conversation history
- Export conversations for analysis
- Switch between multiple agents

### 🧠 Agent State Inspection
- View agent configuration
- Inspect available tools
- Monitor agent status
- Debug agent instructions

### 📊 Performance Metrics
- Response time tracking
- Token usage monitoring
- Tool execution timing
- API call statistics

### 🔬 OpenTelemetry Integration
- Distributed tracing
- Span visualization
- Performance profiling
- Integration with Aspire Dashboard

---

## Installation

DevUI is already included in your `requirements.txt`:

```bash
pip install agent-framework-devui --pre
```

Or manually:
```bash
pip install -r requirements.txt
```

---

## Quick Start

### 1. Launch DevUI Server

**Easiest method** (uses built-in launcher):

```bash
python -m agents.roaster.devui_server
```

This will:
- Initialize the coffee roasting agent
- Start DevUI server on http://localhost:8080
- Automatically open your browser
- Connect to MCP servers (first crack + roaster control)

**Output:**
```
🔥 Coffee Roasting Agent - DevUI Server
============================================================

🤖 Initializing agent...
✅ Agent initialized: CoffeeRoastingAgent
   - First Crack MCP: http://localhost:5001
   - Roaster Control MCP: http://localhost:5002
   - OpenAI Model: gpt-4o
   - Tools: 11 MCP tools registered

============================================================

🚀 Starting DevUI server on http://localhost:8080

📖 DevUI Features:
   - Interactive chat interface
   - Tool call visualization
   - Conversation history
   - Agent state inspection

💡 Tips:
   - Try: 'Check roaster status'
   - Try: 'Start preheat at 100% heat'
   - Try: 'Start first crack detection'
   - Try: 'Check status and adjust as needed'

⌨️  Press Ctrl+C to stop the server
============================================================
```

### 2. Open DevUI in Browser

Navigate to: **http://localhost:8080**

You'll see:
- Agent selector dropdown (choose "CoffeeRoastingAgent")
- Chat input field
- Conversation history panel
- Tool call inspector

### 3. Start Testing

**Example conversation:**

```
You: Check the current roaster status

Agent: [Calls get_roaster_status()]

The roaster is currently idle:
- Bean temperature: 25°C (room temp)
- Chamber temperature: 25°C
- Heat level: 0%
- Fan speed: 0%
- Status: idle
- No active roast session

---

You: Start the preheat cycle at 100% heat

Agent: [Calls start_roaster(initial_heat=100)]

✅ Roaster started successfully
- Heat set to 100%
- Fan at 0% (preheat mode)
- Target chamber temp: 180-200°C

The roaster is now preheating. I'll monitor the temperature
and let you know when it's ready for beans.

---

You: Start first crack detection using USB microphone

Agent: [Calls start_first_crack_detection(
    audio_source='usb_microphone',
    threshold=0.5,
    min_pops=3
)]

✅ First crack detection started
- Audio source: USB microphone
- Detection threshold: 0.5
- Minimum pops to confirm: 3
- Confirmation window: 30 seconds

Monitoring for first crack events...
```

---

## Advanced Usage

### Custom Port

```bash
python -m agents.roaster.devui_server --port 8888
```

Then access: http://localhost:8888

### Disable Auto Browser Open

```bash
python -m agents.roaster.devui_server --no-browser
```

Manually navigate to the URL shown in the terminal.

### Enable OpenTelemetry Tracing

```bash
# Set OTLP endpoint first
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Start with tracing
python -m agents.roaster.devui_server --tracing framework
```

Traces will be sent to your OTLP collector (Jaeger, Aspire, etc.).

---

## Multi-Agent DevUI

Launch DevUI with **multiple agents** for comprehensive testing:

```bash
python agents/roaster/examples/devui_example.py
```

This creates and serves 3 agents:

### 1. **CoffeeRoastingAgent**
- Controls Hottop roaster hardware
- Manages first crack detection
- 11 MCP-backed tools

### 2. **QualityControlAgent**
- Evaluates roast quality
- Scores based on temperature and development
- Approves/rejects batches

### 3. **InventoryAgent**
- Tracks coffee bean inventory
- Monitors stock levels
- Alerts for reorder points

**Try these prompts:**

**For Roasting Agent:**
- "Check the roaster status and tell me if we're ready to add beans"
- "Start preheat at 100% heat and begin first crack detection"
- "Adjust heat to 65% and fan to 50%"

**For Quality Control Agent:**
- "Evaluate a roast that finished at 196°C with 18% development time"
- "What quality score would a 203°C roast with 14% development get?"

**For Inventory Agent:**
- "Check inventory levels for Ethiopian Natural beans"
- "Do we need to reorder any beans?"

---

## DevUI API

DevUI exposes an **OpenAI-compatible REST API** for programmatic access.

### Base URL

```
http://localhost:8080/v1
```

### Endpoints

#### `GET /v1/entities`

List all available agents:

```bash
curl http://localhost:8080/v1/entities
```

Response:
```json
[
  {
    "id": "CoffeeRoastingAgent_abc123",
    "name": "CoffeeRoastingAgent",
    "type": "agent",
    "is_active": true
  }
]
```

#### `POST /v1/responses`

Send a message to an agent:

```bash
curl -X POST http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "CoffeeRoastingAgent",
    "input": "Check the roaster status"
  }'
```

#### `POST /v1/conversations`

Create a conversation for multi-turn interactions:

```bash
curl -X POST http://localhost:8080/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "agent_id": "CoffeeRoastingAgent"
    }
  }'
```

Returns:
```json
{
  "id": "conv_abc123",
  "created_at": "2025-11-01T20:00:00Z"
}
```

Use `conversation` field in subsequent requests:

```bash
curl -X POST http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "CoffeeRoastingAgent",
    "input": "What was the last reading?",
    "conversation": "conv_abc123"
  }'
```

#### `POST /v1/entities/{id}/reload`

Hot reload agent (development mode):

```bash
curl -X POST http://localhost:8080/v1/entities/CoffeeRoastingAgent_abc123/reload
```

Useful for:
- Testing code changes without restarting server
- Rapid iteration on agent instructions
- Tool definition updates

---

## Using DevUI API with Python

### OpenAI SDK

```python
from openai import OpenAI

# Connect to DevUI
client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="not-needed"  # API key not required for local DevUI
)

# Single request
response = client.responses.create(
    model="CoffeeRoastingAgent",
    input="Start the preheat cycle"
)

print(response.output[0].content[0].text)

# Multi-turn conversation
conversation = client.conversations.create(
    metadata={"agent_id": "CoffeeRoastingAgent"}
)

response1 = client.responses.create(
    model="CoffeeRoastingAgent",
    input="Check roaster status",
    conversation=conversation.id
)

response2 = client.responses.create(
    model="CoffeeRoastingAgent",
    input="Start preheat at 100%",
    conversation=conversation.id  # Continues the same conversation
)
```

### Requests Library

```python
import requests

base_url = "http://localhost:8080/v1"

# Get available agents
entities = requests.get(f"{base_url}/entities").json()
print("Available agents:", [e["name"] for e in entities])

# Send message
response = requests.post(
    f"{base_url}/responses",
    json={
        "model": "CoffeeRoastingAgent",
        "input": "Check the roaster status"
    }
).json()

print(response["output"][0]["content"][0]["text"])
```

---

## Integration with Aspire Dashboard

If you're using .NET Aspire for orchestration, integrate DevUI traces:

### 1. Configure OpenTelemetry

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=coffee-roasting-agent
```

### 2. Start Aspire Dashboard

```bash
# From your Aspire project
dotnet run --project AppHost
```

### 3. Launch DevUI with Tracing

```bash
python -m agents.roaster.devui_server --tracing framework
```

### 4. View Traces

Navigate to Aspire Dashboard (usually http://localhost:18888) and see:
- Agent request spans
- MCP tool call spans
- HTTP request timing
- Error traces

---

## Tips & Best Practices

### 🎯 Testing Workflows

**Test individual tools first:**
```
1. "Get roaster status" (verify MCP connection)
2. "Start first crack detection" (verify audio setup)
3. "Set heat to 75%" (verify control commands)
```

**Then test complete workflows:**
```
"Start preheat, begin first crack detection, and 
monitor status every 10 seconds until ready for beans"
```

### 🔍 Debugging

**Use tool call inspector to:**
- Verify correct parameters are passed
- Check MCP server responses
- Identify errors in tool execution
- Validate JSON payloads

**Check conversation history to:**
- Review agent decision-making
- Identify instruction misunderstandings
- Optimize prompts

### 🚀 Performance Optimization

**Monitor response times:**
- Agent response < 2s (ideal)
- Tool calls < 500ms (MCP HTTP)
- Overall conversation < 5s

**If slow:**
- Use `gpt-4o-mini` instead of `gpt-4o`
- Reduce `maxTokens` in agent config
- Cache Auth0 tokens (already implemented)
- Optimize tool implementations

### 🧪 Testing Scenarios

**Create test scenarios in DevUI:**

1. **Preheat Scenario**
   - Start roaster → Monitor temp → Confirm ready

2. **Full Roast Scenario**
   - Preheat → Add beans → Monitor RoR → Detect FC → Adjust controls → Drop beans

3. **Emergency Stop Scenario**
   - Start roast → Simulate overtemp → Verify safety shutdown

4. **Quality Control Workflow** (multi-agent)
   - Complete roast → Evaluate quality → Check inventory → Log results

---

## Troubleshooting

### DevUI Won't Start

**Error:** `ModuleNotFoundError: No module named 'agent_framework.devui'`

**Fix:**
```bash
pip install agent-framework-devui --pre
```

### Agent Not Showing in UI

**Issue:** Dropdown is empty or agent not listed

**Fix:**
1. Check terminal output for initialization errors
2. Verify agent was created successfully
3. Ensure no Python import errors
4. Restart DevUI server

### MCP Tools Not Working

**Issue:** Tool calls fail in DevUI

**Fix:**
1. Verify MCP servers are running:
   ```bash
   curl http://localhost:5001/health
   curl http://localhost:5002/health
   ```

2. Check Auth0 credentials in `.env`

3. Test MCP servers directly before using DevUI

### Port Already in Use

**Error:** `Address already in use: 8080`

**Fix:**
```bash
# Use different port
python -m agents.roaster.devui_server --port 8888

# Or kill process using port 8080
lsof -ti:8080 | xargs kill
```

### Browser Doesn't Open

**Issue:** Server starts but browser doesn't launch

**Fix:**
- Use `--no-browser` flag and open manually
- Check default browser settings
- Verify URL in terminal output and navigate manually

---

## Resources

- [DevUI GitHub](https://github.com/microsoft/agent-framework/tree/main/python/packages/devui)
- [Agent Framework Docs](https://github.com/microsoft/agent-framework)
- [Project README](../../agents/roaster/README.md)
- [Phase 4 Overview](./README.md)

---

**DevUI makes agent development visual, interactive, and fun! 🚀☕**
