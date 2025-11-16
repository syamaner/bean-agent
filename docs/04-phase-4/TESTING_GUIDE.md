# Testing Guide: MS Agent Framework Integration

Complete testing workflow to validate the Python Agent Framework + DevUI implementation and compare it with existing solutions.

---

## Testing Objectives

1. ✅ Verify Agent Framework installation
2. ✅ Test standalone agent (CLI mode)
3. ✅ Test DevUI interface
4. ✅ Test Aspire integration
5. ✅ Compare with n8n agent
6. ✅ Document pros/cons of each approach

---

## Prerequisites

### 1. Environment Setup

```bash
cd ~/git/coffee-roasting
source venv/bin/activate

# Verify Python version
python --version  # Should be 3.11.x
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt

# Verify Agent Framework packages
pip list | grep agent-framework
```

Expected output:
```
agent-framework-core        0.1.0
agent-framework-devui       0.1.0
agent-framework-openai      0.1.0
```

### 3. Configure Environment

```bash
# Check if .env exists in agents/roaster/
ls -la agents/roaster/.env

# If not, create from template
cp agents/roaster/.env.example agents/roaster/.env
```

Edit `agents/roaster/.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

FIRST_CRACK_MCP_URL=http://localhost:5001
ROASTER_CONTROL_MCP_URL=http://localhost:5002

AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_API_AUDIENCE=https://your-api-audience
AUTH0_CLIENT_ID=your-m2m-client-id
AUTH0_CLIENT_SECRET=your-m2m-client-secret
```

---

## Test 1: MCP Servers (Baseline)

**Purpose:** Ensure MCP servers are working before testing agent

### Terminal 1: Start Roaster Control

```bash
cd ~/git/coffee-roasting
source venv/bin/activate
python -m src.mcp_servers.roaster_control.sse_server
```

Expected output:
```
🚀 Roaster Control MCP Server
Port: 5002
Mock mode: True
✅ Server ready on http://localhost:5002
```

### Terminal 2: Start First Crack Detection

```bash
cd ~/git/coffee-roasting
source venv/bin/activate
python -m src.mcp_servers.first_crack_detection.sse_server
```

Expected output:
```
🎤 First Crack Detection MCP Server
Port: 5001
✅ Server ready on http://localhost:5001
```

### Verify Health

```bash
# Check both servers
curl http://localhost:5001/health
curl http://localhost:5002/health
```

Expected: `{"status":"healthy"}` from both

**✅ Pass Criteria:** Both servers running without errors

---

## Test 2: Standalone Agent (CLI Mode)

**Purpose:** Test agent without DevUI

### Terminal 3: Run Agent

```bash
cd ~/git/coffee-roasting
source venv/bin/activate
python -m agents.roaster.agent
```

Expected output:
```
🔥 Coffee Roasting Agent - MS Agent Framework
============================================================

✅ Agent initialized with MCP tools:
   - First Crack Detection: http://localhost:5001
   - Roaster Control: http://localhost:5002

Example commands:
  - Start the preheat cycle
  - Check current roaster status
  ...

🤖 You: 
```

### Test Commands

**Test 1: Status Check**
```
You: Check the current roaster status
```

Expected behavior:
- Agent calls `get_roaster_status()`
- Returns current temperature, heat, fan readings
- Response in natural language

**Test 2: Start Preheat**
```
You: Start the preheat cycle at 100% heat
```

Expected behavior:
- Agent calls `start_roaster(initial_heat=100)`
- Confirms roaster started
- Mentions target temperature

**Test 3: First Crack Detection**
```
You: Start first crack detection using audio file mode
```

Expected behavior:
- Agent calls `start_first_crack_detection()`
- Confirms audio monitoring active
- Shows detection parameters

**Test 4: Complex Request**
```
You: Check status, and if everything is ready, start preheat and detection
```

Expected behavior:
- Agent calls multiple tools sequentially
- Makes decision based on status
- Takes appropriate actions

### Exit Test

```
You: quit
```

**✅ Pass Criteria:**
- All commands execute successfully
- Tool calls visible in output
- Natural language responses
- No errors or crashes

---

## Test 3: DevUI Standalone

**Purpose:** Test web interface for agent

### Start DevUI

```bash
cd ~/git/coffee-roasting
source venv/bin/activate
python -m agents.roaster.devui_server
```

Expected output:
```
🔥 Coffee Roasting Agent - DevUI Server
============================================================

🤖 Initializing agent...
✅ Agent initialized: CoffeeRoastingAgent
   - First Crack MCP: http://localhost:5001
   - Roaster Control MCP: http://localhost:5002
   - Tools: 11 MCP tools registered

🚀 Starting DevUI server on http://localhost:8080
```

Browser should auto-open to: **http://localhost:8080**

### UI Tests

**Test 1: Agent Selection**
- Verify "CoffeeRoastingAgent" appears in dropdown
- Select it

**Test 2: Simple Status Check**
```
Message: Check the roaster status
```

Expected:
- Message appears in chat
- Agent response with tool call highlighted
- Click tool call to see JSON payload
- Response shows temperature data

**Test 3: Tool Call Inspection**
- Click on `get_roaster_status` tool call
- Verify JSON request/response visible
- Check syntax highlighting works

**Test 4: Multi-Turn Conversation**
```
Message 1: Check the roaster status
Message 2: What was the temperature?
Message 3: Start preheat at 100%
```

Expected:
- Conversation maintains context
- Agent references previous responses
- Tool calls accumulate in history

**Test 5: Conversation Management**
- Create new conversation
- Switch between conversations
- Verify each maintains separate context

**✅ Pass Criteria:**
- UI loads without errors
- Agent responds to messages
- Tool calls visible and inspectable
- Conversations work correctly

---

## Test 4: Aspire Integration

**Purpose:** Test all services running together

### Start Aspire

```bash
cd ~/git/coffee-roasting/src/orchestration/aspire
dotnet run
```

Expected output:
```
Building...
info: Aspire.Hosting[0]
      Distributed application starting...
info: Aspire.Hosting[0]
      Application host directory is: .../src/orchestration/aspire
...
Dashboard URL: http://localhost:18888
```

### Verify Services

Open browser to: **http://localhost:18888**

Check services:
- ✅ **roaster-control** - Running (port 5002)
- ✅ **first-crack-detection** - Running (port 5001)
- ✅ **devui** - Running (port 8080)
- ✅ **n8n** - Running (port 5678)

### Test DevUI via Aspire

Navigate to: **http://localhost:8080**

Run same tests as Test 3 above.

### Check Aspire Logs

In Aspire Dashboard:
1. Click "devui" service
2. View logs
3. Send message in DevUI
4. Verify logs show:
   - Request received
   - Tool calls made
   - Responses sent

### Check Traces (Optional)

If OpenTelemetry enabled:
1. Click "Traces" in Aspire
2. Find devui traces
3. Verify spans for:
   - HTTP requests
   - OpenAI calls
   - MCP tool invocations

**✅ Pass Criteria:**
- All 4 services running
- DevUI accessible via Aspire
- Logs visible in dashboard
- No errors in any service

---

## Test 5: Comparison with n8n Agent

**Purpose:** Compare Agent Framework with existing n8n solution

### n8n Agent Test

With Aspire still running, open: **http://localhost:5678**

1. Open your autonomous roasting workflow
2. Execute workflow with test message
3. Observe agent behavior

### Side-by-Side Comparison

| Test Scenario | MS Agent Framework | n8n Agent |
|--------------|-------------------|-----------|
| **Setup Time** | ___ minutes | ___ minutes |
| **Response Speed** | ___ seconds | ___ seconds |
| **Tool Call Visibility** | Click to inspect JSON | Check execution logs |
| **Debugging Experience** | DevUI + logs | n8n execution view |
| **Iteration Speed** | Code changes + reload | Visual workflow edit |
| **Multi-turn Context** | Built-in conversation | Manual state management |
| **Cost per Request** | OpenAI API only | OpenAI API only |

Fill in timing data during tests.

---

## Test 6: Error Handling

**Purpose:** Verify graceful failure modes

### Test Invalid Commands

```
You: Make the roaster fly to the moon
```

Expected:
- Agent responds it cannot do that
- No tool calls attempted
- Polite explanation

### Test MCP Server Failure

1. Stop roaster-control server (Ctrl+C in Terminal 1)
2. In DevUI: "Check roaster status"

Expected:
- Error message visible
- Agent explains server unavailable
- Doesn't crash

3. Restart roaster-control server
4. Retry command

Expected:
- Works again after server restart

### Test Auth0 Failure

1. Set invalid AUTH0_CLIENT_ID in .env
2. Restart agent
3. Try any command

Expected:
- 401 Unauthorized error
- Clear error message
- Doesn't crash

**✅ Pass Criteria:**
- Graceful error messages
- No crashes
- Recovery after fixes

---

## Test 7: Performance Benchmarks

**Purpose:** Measure response times

### Simple Status Check

```bash
time curl -X POST http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{"model": "CoffeeRoastingAgent", "input": "Check status"}'
```

Record time: _____ seconds

### With Tool Calls

```bash
time curl -X POST http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{"model": "CoffeeRoastingAgent", "input": "Start preheat at 100%"}'
```

Record time: _____ seconds

### Complex Multi-Tool Request

```bash
time curl -X POST http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{"model": "CoffeeRoastingAgent", "input": "Check roaster and first crack status, then adjust if needed"}'
```

Record time: _____ seconds

**Target Benchmarks:**
- Status check: < 2 seconds
- Single tool call: < 3 seconds
- Multi-tool: < 5 seconds

---

## Pros & Cons Analysis

### MS Agent Framework + DevUI

**Pros:**
- ✅ Type-safe tool definitions (Pydantic)
- ✅ Visual debugging (DevUI)
- ✅ Built-in conversation management
- ✅ Easy function calling
- ✅ OpenAI SDK integration
- ✅ Good for Python developers
- ✅ Programmatic and UI testing
- ✅ Hot reload with DevUI
- ✅ Multi-agent ready

**Cons:**
- ❌ New framework (less mature than alternatives)
- ❌ Python-only (for now)
- ❌ Requires code changes to modify agent
- ❌ DevUI is development-focused (not production)
- ❌ Learning curve for framework concepts
- ❌ Limited documentation (early stage)

### n8n Agent (Existing)

**Pros:**
- ✅ Visual workflow editor
- ✅ No code changes needed
- ✅ Non-programmers can modify
- ✅ Mature platform
- ✅ Built-in scheduling
- ✅ Webhook support
- ✅ Many integrations
- ✅ Production-ready

**Cons:**
- ❌ JavaScript/JSON only
- ❌ Manual conversation state
- ❌ Harder to debug agent logic
- ❌ Workflow can get complex
- ❌ Version control (JSON files)
- ❌ No type safety
- ❌ Slower iteration (UI clicks)

### Custom Python Agent (Option)

**Pros:**
- ✅ Full control
- ✅ No framework constraints
- ✅ Simple to understand
- ✅ Easy debugging
- ✅ Custom orchestration

**Cons:**
- ❌ Build everything yourself
- ❌ No DevUI out of the box
- ❌ More boilerplate code
- ❌ Reinvent patterns

---

## Recommendations

### Use MS Agent Framework When:
- 🎯 Building multiple agents
- 🎯 Python team
- 🎯 Need type safety
- 🎯 Want visual debugging
- 🎯 Rapid agent iteration

### Use n8n When:
- 🎯 Non-technical users need to modify
- 🎯 Visual workflows preferred
- 🎯 Need scheduling/webhooks
- 🎯 Existing n8n infrastructure
- 🎯 Production workflows

### Use Custom Python When:
- 🎯 Specific requirements
- 🎯 No framework overhead
- 🎯 Full control needed
- 🎯 Simple agent logic

---

## Test Results Template

### Environment
- Date: _____________
- Python Version: _____________
- Agent Framework Version: _____________

### Test Results

| Test | Status | Time | Notes |
|------|--------|------|-------|
| MCP Servers | ☐ Pass ☐ Fail | | |
| Standalone Agent | ☐ Pass ☐ Fail | | |
| DevUI Standalone | ☐ Pass ☐ Fail | | |
| Aspire Integration | ☐ Pass ☐ Fail | | |
| n8n Comparison | ☐ Pass ☐ Fail | | |
| Error Handling | ☐ Pass ☐ Fail | | |
| Performance | ☐ Pass ☐ Fail | | |

### Performance Metrics

- Status check: _____ seconds
- Single tool: _____ seconds
- Multi-tool: _____ seconds

### Issues Found

1. _______________________________
2. _______________________________
3. _______________________________

### Recommendations

_________________________________________
_________________________________________
_________________________________________

---

## Next Steps

After completing tests:

1. ✅ Document which approach works best for your use case
2. ✅ Decide: Agent Framework, n8n, or both?
3. ⏭️ If Agent Framework: Consider C# version (see CSHARP_AGENT_ROADMAP.md)
4. ⏭️ If n8n: Continue with existing workflows
5. ⏭️ If both: Use Agent Framework for dev, n8n for production

---

**Ready to test!** Follow each section in order and document your findings. 🚀☕
