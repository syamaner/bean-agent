# Quick Start: MS Agent Framework Coffee Roasting Agent

Get the Agent Framework roasting agent running in 5 minutes.

## Prerequisites

- ✅ Python 3.11 venv activated
- ✅ MCP servers built and tested (Phase 2)
- ✅ OpenAI API key
- ✅ Auth0 M2M application configured

## Step 1: Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

This adds:
- `agent-framework-core`
- `agent-framework-openai`
- `openai`

## Step 2: Configure Environment

Create `.env` file:

```bash
cd agents/roaster
cp .env.example .env
```

Edit `.env` with your credentials:

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

## Step 3: Start MCP Servers

**Terminal 1 - First Crack Detection:**
```bash
python -m src.mcp_servers.first_crack_detection
```

**Terminal 2 - Roaster Control:**
```bash
python -m src.mcp_servers.roaster_control
```

Wait for both servers to show:
```
✅ Server ready on http://localhost:5001
✅ Server ready on http://localhost:5002
```

## Step 4: Run the Agent

**Terminal 3 - Agent:**
```bash
python -m agents.roaster.agent
```

You should see:
```
🔥 Coffee Roasting Agent - MS Agent Framework
============================================================

✅ Agent initialized with MCP tools:
   - First Crack Detection: http://localhost:5001
   - Roaster Control: http://localhost:5002

Example commands:
  - Start the preheat cycle
  - Check current roaster status
  - Start first crack detection
  ...

🤖 You: 
```

## Step 5: Test the Agent

Try these commands:

### Check roaster status
```
🤖 You: Check the current roaster status
```

Expected response:
```
🤖 Agent: [Calls get_roaster_status()]

The roaster is currently idle. Status:
- Bean temp: 25°C (room temperature)
- Chamber temp: 25°C
- Heat: 0%, Fan: 0%
- No active roast session
```

### Start preheat
```
🤖 You: Start the preheat cycle at 100% heat
```

Expected response:
```
🤖 Agent: [Calls start_roaster(initial_heat=100)]

✅ Roaster started at 100% heat
The roaster is now preheating. Target chamber temperature is 180-200°C.
I'll monitor and let you know when ready for beans.
```

### Start first crack detection
```
🤖 You: Start first crack detection using USB microphone
```

Expected response:
```
🤖 Agent: [Calls start_first_crack_detection(audio_source='usb_microphone')]

✅ First crack detection started
Audio monitoring active via USB microphone.
Threshold: 0.5, Min pops: 3, Confirmation window: 30s
```

### Check status and adjust
```
🤖 You: Check status and make any needed adjustments
```

The agent will:
1. Call `get_roaster_status()`
2. Call `get_first_crack_status()`
3. Analyze current phase and metrics
4. Make decision (adjust heat/fan or continue monitoring)
5. Explain reasoning

## Step 6: Autonomous Loop (Optional)

For fully autonomous roasting, create a script:

**`autonomous_roast.py`:**
```python
import asyncio
import time
from agents.roaster import create_roasting_agent

async def main():
    agent = create_roasting_agent()
    
    # Start preheat and detection
    await agent.run("Start preheat at 100% heat and begin first crack detection")
    
    # Autonomous loop
    roasting = True
    while roasting:
        response = await agent.run(
            "Check roaster and first crack status. Make any needed adjustments. "
            "Tell me if roast is complete or if I need to add beans."
        )
        
        print(f"\n[{time.strftime('%H:%M:%S')}] {response}\n")
        
        # Check for completion
        if "roast complete" in response.lower() or "beans dropped" in response.lower():
            roasting = False
        
        # Add beans manually when prompted
        if "ready for beans" in response.lower():
            input("\n⏸️  Add beans now, then press Enter to continue...")
        
        await asyncio.sleep(10)  # Check every 10 seconds
    
    print("\n✅ Roast complete!")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python autonomous_roast.py
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'agent_framework'"

**Fix:**
```bash
pip install agent-framework-core agent-framework-openai
```

### "401 Unauthorized" from MCP servers

**Fix:**
1. Verify `.env` has correct Auth0 credentials
2. Test token manually:
```bash
curl -X POST "https://YOUR_DOMAIN.auth0.com/oauth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "audience": "YOUR_AUDIENCE",
    "grant_type": "client_credentials"
  }'
```

### "Connection refused" errors

**Fix:**
1. Ensure MCP servers are running:
```bash
curl http://localhost:5001/health
curl http://localhost:5002/health
```
2. Check firewall isn't blocking ports 5001/5002

### Agent doesn't call tools

**Fix:**
1. Verify using function-calling model (gpt-4o, not gpt-3.5)
2. Check tool signatures have proper type annotations
3. Make instructions more explicit: "Use the get_roaster_status tool to check..."

## Step 7: Use DevUI for Visual Debugging (Optional)

Launch the web-based debugging interface:

```bash
python -m agents.roaster.devui_server
```

This will:
- Start DevUI server on http://localhost:8080
- Automatically open your browser
- Provide interactive chat interface
- Visualize tool calls
- Show conversation history

**Try it:**
1. Select "CoffeeRoastingAgent" from dropdown
2. Chat: "Check roaster status"
3. Watch tool calls execute in real-time
4. Click tool calls to inspect request/response

**Multi-Agent Example:**
```bash
python agents/roaster/examples/devui_example.py
```

Launches 3 agents:
- CoffeeRoastingAgent (roaster control)
- QualityControlAgent (quality evaluation)
- InventoryAgent (bean inventory)

**See:** [DevUI Guide](./DEVUI.md) for complete documentation.

---

## What's Next?

✅ **You're ready!** The agent can now:
- Control the roaster (heat, fan, start/stop)
- Monitor first crack detection
- Make autonomous roasting decisions
- Follow professional roasting profiles
- Debug visually with DevUI

### Recommended next steps:

1. ✅ **Test with DevUI** - Visual debugging and testing
2. **Test with mock hardware** - Verify logic before real roaster
3. **Create custom profiles** - Light, medium, dark roast configurations
4. **Add observability** - Integrate with OpenTelemetry

### Learn more:

- [Complete README](../../agents/roaster/README.md) - Full documentation
- [Phase 4 Overview](./README.md) - Architecture and design decisions
- [Project WARP.md](../../WARP.md) - Development guidelines

---

**Happy roasting! ☕🤖**
