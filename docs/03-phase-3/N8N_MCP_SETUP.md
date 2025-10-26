# n8n MCP Client Setup

Guide for using n8n's native MCP client support to connect to coffee roasting MCP servers.

**Status**: 🟡 IN PROGRESS  
**Last Updated**: 2025-10-26

---

## Overview

n8n supports MCP (Model Context Protocol) servers natively via the **LangChain MCP Tool** node. This allows AI agents in n8n workflows to directly invoke tools from our MCP servers without HTTP polling.

**Documentation**: [n8n MCP Client Tool](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolmcp/)

---

## Architecture

```
┌────────────────────────────────────────────┐
│          n8n Workflow                       │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │  AI Agent (OpenAI/Anthropic)         │ │
│  │                                       │ │
│  │  Connected Tools:                    │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │ LangChain MCP Tool              │ │ │
│  │  │ → Roaster Control MCP           │ │ │
│  │  │   (SSE: roaster-control:5002)   │ │ │
│  │  └─────────────────────────────────┘ │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │ LangChain MCP Tool              │ │ │
│  │  │ → First Crack Detection MCP     │ │ │
│  │  │   (SSE: first-crack-detection:5001)││ │
│  │  └─────────────────────────────────┘ │ │
│  └──────────────────────────────────────┘ │
└────────────────────────────────────────────┘
           │                    │
           │ SSE + Auth0        │ SSE + Auth0
           ▼                    ▼
   ┌───────────────┐    ┌───────────────────┐
   │ Roaster       │    │ First Crack       │
   │ Control MCP   │    │ Detection MCP     │
   └───────────────┘    └───────────────────┘
```

---

## Prerequisites

✅ **Aspire running** with all services:
- Roaster Control MCP (port 5002)
- First Crack Detection MCP (port 5001)
- n8n container (port 5678)

✅ **Auth0 configured** with M2M application and credentials

---

## Setup Steps

### 1. Start Aspire Orchestration

```bash
cd src/orchestration/aspire
dotnet run
```

This will start:
- Roaster Control MCP on http://localhost:5002
- First Crack Detection MCP on http://localhost:5001
- n8n on http://localhost:5678

### 2. Access n8n

Open browser to: http://localhost:5678

First time setup:
1. Create admin account
2. Set email and password
3. Skip surveys (optional)

### 3. Configure Auth0 Credentials

Before creating workflows, set up Auth0 credentials in n8n:

1. Go to **Settings** → **Credentials** → **New**
2. Search for "HTTP Header Auth" (for Bearer tokens)
3. Name: `Coffee Roasting Auth0`
4. Configuration:
   - **Name**: `Authorization`
   - **Value**: `Bearer {{$env.AUTH0_TOKEN}}`

We'll obtain the token dynamically in the workflow.

### 4. Create Auth0 Token Node

Create a reusable credential workflow:

**Node 1: HTTP Request - Get Auth0 Token**
- **Method**: POST
- **URL**: `https://{{$env.AUTH0_DOMAIN}}/oauth/token`
- **Body**: JSON
  ```json
  {
    "client_id": "{{$env.AUTH0_CLIENT_ID}}",
    "client_secret": "{{$env.AUTH0_CLIENT_SECRET}}",
    "audience": "{{$env.AUTH0_AUDIENCE}}",
    "grant_type": "client_credentials"
  }
  ```
- **Output**: Store `access_token` in workflow variable

---

## Creating the Roasting Workflow

### Workflow Structure

```
┌─────────────────────────────────────────────┐
│ 1. Manual Trigger / Schedule Trigger       │
└──────────────┬──────────────────────────────┘
               ▼
┌─────────────────────────────────────────────┐
│ 2. Get Auth0 Token                          │
│    → Store in $auth_token variable          │
└──────────────┬──────────────────────────────┘
               ▼
┌─────────────────────────────────────────────┐
│ 3. AI Agent (OpenAI GPT-4)                  │
│                                             │
│    Tools:                                   │
│    • LangChain MCP Tool (Roaster)          │
│    • LangChain MCP Tool (First Crack)      │
│                                             │
│    System Prompt:                           │
│    "You are a coffee roasting expert..."    │
│                                             │
│    User Prompt:                             │
│    "Execute a light roast profile..."       │
└──────────────┬──────────────────────────────┘
               ▼
┌─────────────────────────────────────────────┐
│ 4. Loop: Monitor & Adjust                   │
│    (Agent autonomously calls MCP tools)     │
└─────────────────────────────────────────────┘
```

### Node Configuration Details

#### Node: AI Agent

1. Add **AI Agent** node
2. Configure:
   - **Agent Type**: Tools Agent (recommended) or ReAct Agent
   - **Model**: OpenAI GPT-4 (requires API key)
   - **System Message**:
     ```
     You are an expert coffee roasting assistant for a Hottop KN-8828B-2K+ roaster.
     
     You have access to two MCP servers:
     1. Roaster Control - control hardware (heat, fan, drum, beans)
     2. First Crack Detection - monitor for first crack event
     
     Your goal is to execute a roasting profile safely and achieve the target outcome.
     
     Key principles:
     - Always check roaster status before making adjustments
     - Monitor first crack detection continuously
     - After first crack, enter development phase (15-20% of total time)
     - Drop beans at target temperature (light: 195-200°C, medium: 205-210°C)
     - Respect safety limits (max temp 205°C, max RoR 10°C/min)
     
     Available phases:
     1. Preheat: Heat 100%, Fan 0%, target 180°C
     2. Charge: User adds beans (temp drops ~100°C)
     3. Drying: Gradual heat reduction, monitor RoR
     4. Maillard: Maintain RoR 5-8°C/min
     5. First Crack: Usually 160-180°C
     6. Development: 15-20% of total time, reduce heat/increase fan
     7. Drop: Open drop door, start cooling
     ```

#### Node: LangChain MCP Tool (Roaster Control)

1. Add **LangChain MCP Tool** node inside AI Agent
2. Configure:
   - **SSE Endpoint**: `http://roaster-control:5002/sse`
   - **Authentication**: Bearer
   - **Token**: `{{$auth_token}}`
   - **Tools to Include**: All (or select specific tools)

Available tools:
- `start_roaster` - Start drum motor
- `stop_roaster` - Stop drum motor
- `set_heat` - Set heat level (0-100%, 10% increments)
- `set_fan` - Set fan speed (0-100%, 10% increments)
- `drop_beans` - Open drop door and start cooling
- `start_cooling` - Start cooling fan
- `stop_cooling` - Stop cooling fan
- `report_first_crack` - Report first crack detection
- `get_roast_status` - Get complete roast status

#### Node: LangChain MCP Tool (First Crack Detection)

1. Add **LangChain MCP Tool** node inside AI Agent
2. Configure:
   - **SSE Endpoint**: `http://first-crack-detection:5001/sse`
   - **Authentication**: Bearer
   - **Token**: `{{$auth_token}}`
   - **Tools to Include**: All

Available tools:
- `start_first_crack_detection` - Start monitoring
- `get_first_crack_status` - Check detection status
- `stop_first_crack_detection` - Stop monitoring

---

## Example Workflow: Simple Roast

### Step-by-Step

1. **Trigger**: Manual trigger or schedule
2. **Get Token**: HTTP Request to Auth0
3. **AI Agent**: Configure with both MCP tools
4. **Prompt**: 
   ```
   Execute a light roast profile with the following steps:
   
   1. Start the roaster and set heat to 100%, fan to 0%
   2. Start first crack detection monitoring
   3. Wait for user to add beans (temperature will drop)
   4. Monitor temperature and rate of rise
   5. When first crack is detected, note the time
   6. Enter development phase: reduce heat to 60%, increase fan to 50%
   7. When bean temperature reaches 195°C, drop the beans
   8. Start cooling
   9. Stop first crack detection
   10. Report completion
   
   Provide updates every 30 seconds during the roast.
   ```

### Expected Agent Behavior

The AI agent will autonomously:
1. Call `start_roaster` tool
2. Call `set_heat` with level=100
3. Call `set_fan` with speed=0
4. Call `start_first_crack_detection`
5. Periodically call `get_roast_status` to monitor
6. Detect bean charge from temperature drop
7. Monitor until `get_first_crack_status` returns detected=true
8. Call `set_heat` with level=60
9. Call `set_fan` with speed=50
10. Monitor until bean temp >= 195°C
11. Call `drop_beans`
12. Call `start_cooling`
13. Call `stop_first_crack_detection`
14. Report completion

---

## Authentication Flow

```
┌──────────┐
│ n8n      │
│ Workflow │
└────┬─────┘
     │
     │ 1. POST /oauth/token
     ▼
┌──────────────┐
│ Auth0        │
│ Token Server │
└────┬─────────┘
     │
     │ 2. access_token (JWT)
     ▼
┌──────────┐
│ n8n      │
│ (store)  │
└────┬─────┘
     │
     │ 3. SSE connection + Bearer token
     ▼
┌──────────────┐
│ MCP Server   │
│ (validates)  │
└──────────────┘
```

### Token Caching

The Auth0 token is valid for 24 hours. To optimize:

1. Store token in workflow static data
2. Check expiration before each run
3. Refresh only when needed

**Function node for token management**:
```javascript
const now = Date.now() / 1000;
const cachedToken = $workflow.staticData.auth_token;
const expiresAt = $workflow.staticData.token_expires_at || 0;

if (!cachedToken || now >= expiresAt) {
  // Need new token
  return { needsToken: true };
} else {
  // Use cached token
  return { 
    needsToken: false,
    token: cachedToken
  };
}
```

---

## Testing

### 1. Test MCP Connectivity

Create a simple workflow:
1. Get Auth0 token
2. AI Agent with just one MCP tool
3. Simple prompt: "Get the current roaster status"
4. Verify the agent can call `get_roast_status`

### 2. Test Tool Invocation

Prompt: "Start the roaster, set heat to 50%, and fan to 30%"

Expected:
- Agent calls `start_roaster`
- Agent calls `set_heat` with level=50
- Agent calls `set_fan` with speed=30

### 3. Test Full Roast (Mock Hardware)

1. Ensure `USE_MOCK_HARDWARE=true` in Aspire
2. Run the full roast workflow
3. Monitor Aspire logs for MCP server activity
4. Verify agent makes logical decisions

---

## Monitoring & Debugging

### Aspire Dashboard

The Aspire dashboard (usually http://localhost:15000) shows:
- Service health
- Logs from all containers
- Request traces

### n8n Execution Logs

In n8n:
1. Click on workflow execution
2. View each node's input/output
3. Check for MCP tool invocations
4. Verify responses

### MCP Server Logs

Watch logs in Aspire or directly:
```bash
# Roaster control logs
docker logs coffee-roasting-roaster-control-1 -f

# First crack detection logs  
docker logs coffee-roasting-first-crack-detection-1 -f
```

---

## Troubleshooting

### Error: "Cannot connect to SSE endpoint"

**Check**:
1. MCP servers are running (check Aspire dashboard)
2. SSE endpoint URLs are correct
3. Network connectivity between n8n container and MCP containers

**Solution**: Use Docker network names (`roaster-control`, `first-crack-detection`) not `localhost`

### Error: "401 Unauthorized"

**Check**:
1. Auth0 token is valid
2. Token includes required scopes (`read:roaster`, `write:roaster`, etc.)
3. MCP server Auth0 configuration matches n8n credentials

**Solution**: Verify Auth0 M2M application has all scopes granted

### Error: "Tool not found"

**Check**:
1. MCP server exposes the tool (check health endpoint)
2. Tool name is spelled correctly
3. LangChain MCP Tool node includes the tool

**Solution**: Set "Tools to Include" to "All" in MCP tool node

### Agent doesn't call tools

**Check**:
1. System prompt clearly describes when to use tools
2. Tools are properly connected to AI Agent
3. OpenAI API key is valid

**Solution**: Improve prompt clarity, provide examples

---

## Advanced Configuration

### Custom Tool Selection

Instead of exposing all tools, select specific ones:

**LangChain MCP Tool node**:
- **Tools to Include**: Selected
- **Select Tools**:
  - `get_roast_status`
  - `set_heat`
  - `set_fan`
  - `drop_beans`

### Multiple Workflows

Create separate workflows for:
1. **Preheat workflow** - Just heat up roaster
2. **Roast workflow** - Main autonomous roasting
3. **Emergency stop workflow** - Manual override

### Workflow Templates

Save successful workflows as templates:
1. Go to **Workflows**
2. Click workflow menu → **Share**
3. Export as JSON
4. Store in `docs/03-phase-3/workflows/`

---

## Next Steps

1. ✅ Add n8n to Aspire (done)
2. 🟡 Create basic connectivity test workflow
3. ⚪ Build full roasting workflow with AI Agent
4. ⚪ Test with mock hardware
5. ⚪ Document lessons learned
6. ⚪ Create reusable workflow templates

---

## References

- [n8n MCP Client Documentation](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolmcp/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [n8n AI Agents Guide](https://docs.n8n.io/advanced-ai/)
- [Auth0 Machine-to-Machine Flow](https://auth0.com/docs/get-started/authentication-and-authorization-flow/client-credentials-flow)

---

**Status**: Ready for testing  
**Last Updated**: 2025-10-26
