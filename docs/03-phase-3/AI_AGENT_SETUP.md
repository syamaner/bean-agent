# AI Agent Workflow Setup

Complete guide to set up the Coffee Roasting AI Agent with MCP tools.

---

## What This Workflow Does

The AI Agent can:
- ✅ Get roaster status (sensors, temperatures, state)
- ✅ Control roaster (start/stop, heat, fan)
- ✅ Monitor first crack detection
- ✅ Make intelligent roasting decisions
- ✅ Execute complex multi-step roasting procedures

**Architecture**:
```
Trigger → Get Auth0 Token → Store Token → AI Agent
                                            ├─ OpenAI GPT-4o
                                            ├─ Roaster Control MCP (9 tools)
                                            └─ First Crack Detection MCP (3 tools)
```

---

## Prerequisites

✅ Basic connectivity test workflow working  
✅ OpenAI API key  
✅ Aspire running with all services  

---

## Step 1: Add OpenAI Credentials

Before importing the workflow, set up your OpenAI credentials:

1. In n8n, go to **Settings** (gear icon, bottom left)
2. Click **Credentials**
3. Click **+ Add Credential**
4. Search for "OpenAI"
5. Select **OpenAI API**
6. Configure:
   - **API Key**: Your OpenAI API key
   - **Name**: `OpenAI API` (or any name you prefer)
7. Click **Save**

---

## Step 2: Import the Workflow

1. Click **+ Add workflow**
2. Menu (⋮) → **Import from File**
3. Select: `docs/03-phase-3/workflows/roasting-agent.json`
4. Click **Open**

You should see 7 nodes:
- **When chat message received** (Manual Trigger)
- **Get Auth0 Token** (HTTP Request)
- **Store Token** (Set variable)
- **AI Agent** (LangChain Agent)
- **OpenAI Chat Model** (LLM)
- **Roaster Control MCP** (MCP Tool)
- **First Crack Detection MCP** (MCP Tool)

---

## Step 3: Configure OpenAI Credentials

The OpenAI Chat Model node needs your credential:

1. Click on **OpenAI Chat Model** node
2. Under **Credentials**, click the dropdown
3. Select your **OpenAI API** credential
4. The node should now show a green checkmark

---

## Step 4: Verify MCP Tool Configuration

### Roaster Control MCP Node

Click on the node and verify:
- **SSE Endpoint**: `http://roaster-control:5002/sse`
- **Authentication**: Bearer
- **Bearer Token**: `={{ $('Store Token').item.json.auth_token }}`
- **Tools to Include**: All

### First Crack Detection MCP Node

Click on the node and verify:
- **SSE Endpoint**: `http://first-crack-detection:5001/sse`
- **Authentication**: Bearer
- **Bearer Token**: `={{ $('Store Token').item.json.auth_token }}`
- **Tools to Include**: All

---

## Step 5: Test the Agent

### Test 1: Simple Status Check

1. Click **Test workflow**
2. The default prompt is: "Get the current roaster status and tell me if the system is ready to start roasting."
3. Click **Execute workflow**
4. Wait for the agent to complete (may take 10-30 seconds)

**Expected behavior**:
- Agent calls `get_roast_status` tool
- Agent analyzes the response
- Agent provides a natural language summary

**Example output**:
```
The roaster is currently idle and ready to begin roasting. Here's the current status:

- Roaster drum: Not running
- Bean temperature: No reading (not started)
- Chamber temperature: Ambient
- Heat level: 0%
- Fan speed: 0%

To start roasting:
1. I can start the roaster drum
2. Set heat to 100% for preheating
3. Monitor temperature until chamber reaches ~180°C
4. Then you can add the beans

Would you like me to start the preheat process?
```

### Test 2: Start Roaster

1. Edit the **AI Agent** node
2. Change the **Text** prompt to:
   ```
   Start the roaster drum and begin preheating to 180°C chamber temperature.
   ```
3. Click **Test workflow** → **Execute workflow**

**Expected behavior**:
- Agent calls `start_roaster` tool
- Agent calls `set_heat` tool with level=100
- Agent calls `set_fan` tool with speed=0
- Agent reports success

### Test 3: Multi-Step Command

Prompt:
```
Check the current status, then start the roaster and set up for preheating. 
Also start the first crack detection monitoring.
```

**Expected behavior**:
- Agent calls `get_roast_status`
- Agent calls `start_roaster`
- Agent calls `set_heat` (100%)
- Agent calls `start_first_crack_detection`
- Agent provides a summary

---

## Customizing the Agent

### Modify the System Prompt

1. Click **AI Agent** node
2. Scroll to **Options** → **System Message**
3. Edit the prompt to adjust the agent's behavior

**Tips**:
- Add specific roast profiles (e.g., "light Ethiopia natural")
- Include safety rules (e.g., "never exceed 200°C")
- Add timing constraints (e.g., "total roast should be 10-12 minutes")

### Change the Model

1. Click **OpenAI Chat Model** node
2. Change **Model** to:
   - `gpt-4o-mini` (faster, cheaper)
   - `gpt-4-turbo` (more capable)
   - `gpt-4` (most capable)

### Select Specific Tools

Instead of exposing all tools, limit what the agent can do:

1. Click **Roaster Control MCP** node
2. Change **Tools to Include** to **Selected**
3. A **Tools to Include** dropdown appears
4. Select only the tools you want (e.g., just `get_roast_status`, `set_heat`, `set_fan`)

---

## Advanced Usage

### Full Roast Automation Prompt

```
Execute a complete light roast profile:

1. Start the roaster and preheat to 180°C chamber temperature
2. Start first crack detection
3. Wait for me to add beans (I'll tell you when ready)
4. Monitor temperature and rate of rise
5. When first crack is detected, reduce heat to 65% and increase fan to 45%
6. Continue until bean temperature reaches 196°C
7. Drop the beans and start cooling
8. Stop first crack detection
9. Report the complete roast summary

Provide status updates every 30 seconds during the roast.
```

**Note**: For step 3, you'll need to manually trigger the workflow again after adding beans, or use a different trigger type (like Schedule or Webhook).

### Loop for Monitoring

To create a continuous monitoring loop:

1. Add a **Wait** node after the AI Agent
2. Set wait time to 10 seconds
3. Add a **Loop Over Items** node to repeat
4. Connect back to the AI Agent

This creates a monitoring loop where the agent checks status repeatedly.

---

## Workflow Execution Modes

### Manual Mode (Current Setup)

- Click **Test workflow** each time
- Good for: Development, testing, manual control

### Production Mode

To run automatically:

1. Replace **Manual Trigger** with **Schedule Trigger**
   - Every 10 seconds
   - Or specific times (e.g., "Every day at 9 AM")

2. Or use **Webhook Trigger**
   - Trigger via HTTP POST
   - Can integrate with mobile app or web UI

---

## Monitoring Agent Behavior

### View Tool Calls

1. After execution, click on the **AI Agent** node
2. Click **Output** tab
3. Look for `toolCalls` array to see which tools were invoked

Example:
```json
{
  "output": "The roaster is now running...",
  "toolCalls": [
    {
      "tool": "start_roaster",
      "arguments": {},
      "result": {"success": true}
    },
    {
      "tool": "set_heat",
      "arguments": {"level": 100},
      "result": {"current_heat": 100}
    }
  ]
}
```

### Check MCP Server Logs

In Aspire dashboard:
1. Click on **roaster-control** service
2. View **Console** tab
3. See real-time tool invocations

---

## Troubleshooting

### Agent doesn't call tools

**Check**:
1. OpenAI credential is valid
2. MCP nodes have correct SSE endpoints
3. Bearer token is being passed correctly
4. System prompt mentions the tools

**Solution**: Make prompt more explicit:
```
Use the get_roast_status tool to check the current roaster state.
```

### Tools fail with 401 Unauthorized

**Check**:
1. Auth0 token generation succeeded
2. Token is stored in `Store Token` node
3. MCP nodes reference the token: `={{ $('Store Token').item.json.auth_token }}`

### Agent makes unsafe decisions

**Solution**: Add constraints to system prompt:
```
CRITICAL SAFETY RULES:
- NEVER set heat above 90%
- NEVER allow bean temp to exceed 200°C
- ALWAYS reduce heat after first crack
- If any safety limit is approached, immediately drop beans
```

### Agent is too slow

**Optimize**:
1. Use `gpt-4o-mini` model (faster)
2. Reduce `maxTokens` in OpenAI node (default 2000 → 1000)
3. Increase `temperature` for faster, less precise responses (0.3 → 0.5)

---

## Example Prompts to Try

### Simple Commands

```
Get the current roaster status
```

```
Start the roaster drum
```

```
Set heat to 75% and fan to 30%
```

### Complex Commands

```
Prepare the roaster for a medium roast: start the drum, 
set heat to 100%, fan to 0%, and start first crack detection.
```

```
We just detected first crack. Adjust the roaster for development phase:
reduce heat to 65% and increase fan to 45%.
```

```
The roast is complete. Drop the beans, start cooling, 
and stop first crack detection.
```

---

## Next Steps

✅ **Basic agent working** - Can call MCP tools  
→ Build full automation workflow with loop  
→ Add safety monitors and alerts  
→ Test with real roaster hardware  
→ Create roast profiles library  

---

## Quick Reference

### Available MCP Tools

**Roaster Control** (9 tools):
- `get_roast_status` - Get complete status
- `start_roaster` - Start drum motor
- `stop_roaster` - Stop drum motor
- `set_heat` - Set heat level (0-100%)
- `set_fan` - Set fan speed (0-100%)
- `drop_beans` - Open drop door
- `start_cooling` - Start cooling fan
- `stop_cooling` - Stop cooling fan
- `report_first_crack` - Report FC event

**First Crack Detection** (3 tools):
- `start_first_crack_detection` - Start monitoring
- `get_first_crack_status` - Check status
- `stop_first_crack_detection` - Stop monitoring

### Agent Types in n8n

- **Tools Agent** (Current) - Best for tool use
- **Conversational Agent** - Best for chat
- **ReAct Agent** - Best for reasoning
- **OpenAI Functions Agent** - Optimized for OpenAI

---

**Status**: Ready to roast! ☕🤖
