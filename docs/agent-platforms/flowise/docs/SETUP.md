# Flowise Setup Guide

## Overview

Flowise is a TypeScript-based visual builder for AI agents with polished UI and good MCP support. This guide helps you set up the autonomous coffee roasting agent in Flowise.

## Prerequisites

✅ Aspire already configured (Program.cs updated)
✅ MCP servers running (Roaster Control + First Crack Detection)
✅ Auth0 credentials configured

## Step 1: Set Password in User Secrets

```bash
cd src/orchestration/aspire
dotnet user-secrets set "Parameters:flowise-password" "your-secure-password"
```

## Step 2: Start Aspire

```bash
dotnet run
```

Flowise will be available at: **http://localhost:3000**

## Step 3: First Login

1. Navigate to http://localhost:3000
2. Login with:
   - Username: `admin`
   - Password: (the one you set in user secrets)

## Step 4: Create Autonomous Roasting Chatflow

### 4.1 Create New Chatflow

1. Click **"Add New"** → **"AgentFlow"**
2. Name it: `Autonomous Coffee Roast`

### 4.2 Add HTTP Node for Auth0 Token

1. Add **HTTP** node
2. Configure:
   - **Request Method**: `POST`
   - **Target URL**: `https://{{ $env.AUTH0_DOMAIN }}/oauth/token`
   - **Request Body Type**: `JSON`
   - **Request Body**:
     ```json
     {
       "client_id": "{{ $env.AUTH0_CLIENT_ID }}",
       "client_secret": "{{ $env.AUTH0_CLIENT_SECRET }}",
       "audience": "{{ $env.AUTH0_AUDIENCE }}",
       "grant_type": "client_credentials"
     }
     ```

### 4.3 Store Token in Flow State

1. Add **Custom Function** node
2. Connect from HTTP node
3. Code:
   ```javascript
   function storeToken($httpResponse, $flow) {
     // Parse the response
     const response = JSON.parse($httpResponse);
     
     // Store token in flow state
     $flow.state.auth_token = response.access_token;
     
     // Return confirmation
     return `Token stored: ${response.access_token.substring(0, 20)}...`;
   }
   ```

### 4.4 Add MCP Custom Tools

#### Roaster Control MCP

1. Add **MCP Custom Tool** node
2. Configure:
   - **Name**: `Roaster Control`
   - **MCP Config**:
     ```json
     {
       "command": "npx",
       "args": ["-y", "mcp-proxy", "{{ $env.ROASTER_CONTROL_SSE }}"],
       "headers": {
         "Authorization": "Bearer {{ $flow.state.auth_token }}"
       }
     }
     ```

#### First Crack Detection MCP

1. Add **MCP Custom Tool** node
2. Configure:
   - **Name**: `First Crack Detection`
   - **MCP Config**:
     ```json
     {
       "command": "npx",
       "args": ["-y", "mcp-proxy", "{{ $env.FIRST_CRACK_SSE }}"],
       "headers": {
         "Authorization": "Bearer {{ $flow.state.auth_token }}"
       }
     }
     ```

### 4.5 Configure Agent

1. Add **Agent** node (Tool Agent)
2. Connect:
   - **LLM**: ChatOpenAI (gpt-4o)
   - **Tools**: Both MCP tools
3. **System Message**:
   ```
   You are an expert coffee roasting assistant controlling a Hottop KN-8828B-2K+ drum roaster.
   
   ROAST PHASES:
   - Preheat: 3-5 min to 180-200°C (heat 100%, fan 0%)
   - Development: After first crack, reduce heat and increase fan
   - Drop: When dev time is 15-20% and temp 192-195°C
   
   TOOLS:
   - get_roast_status: Get temps, heat, fan
   - start_roaster: Start drum motor
   - set_heat: 0-100% (10% increments)
   - set_fan: 0-100% (10% increments)
   - start_first_crack_detection: Start FC monitoring
   - get_first_crack_status: Check if FC detected
   - drop_beans: Finish roast
   
   WORKFLOW:
   1. Call get_roast_status FIRST
   2. If not running: call start_roaster
   3. Around 8-10 min: call start_first_crack_detection
   4. After FC: reduce heat, increase fan
   5. When dev time is 15-20% and temp 192-195°C: call drop_beans
   
   Update $flow.state.phase to 'complete' when roast is done.
   ```

### 4.6 Add Loop/Iteration

1. Add **Iteration** node
2. Configure:
   - **Array Input**: Create array of 180 items (for 30 min at 10s intervals)
   - **Delay**: 10000ms between iterations
3. Or use **Condition Agent** node to check `$flow.state.phase != 'complete'`

## Step 5: Save and Test

1. Click **Save**
2. Click **Chat** icon
3. Type: `Start the roast`
4. Watch the agent work!

## Flow Structure

```
[HTTP: Get Token] 
    → [Custom Function: Store Token]
    → [MCP Tools: Roaster + FC]
    → [Agent]
    → [Iteration/Condition Loop]
```

## Key Features

✅ **Dynamic Auth**: Token stored in `$flow.state.auth_token`
✅ **MCP Integration**: Tools use `{{ $flow.state.auth_token }}`
✅ **Agent Loops**: Iteration or Condition nodes
✅ **JavaScript Custom Functions**: Full control over logic
✅ **Environment Variables**: Access via `$env`

## Accessing Environment Variables

Flowise has access to Aspire environment variables:
- `{{ $env.AUTH0_DOMAIN }}`
- `{{ $env.AUTH0_CLIENT_ID }}`
- `{{ $env.AUTH0_CLIENT_SECRET }}`
- `{{ $env.AUTH0_AUDIENCE }}`
- `{{ $env.ROASTER_CONTROL_SSE }}`
- `{{ $env.FIRST_CRACK_SSE }}`

## Accessing Flow Context

- `$flow.state.auth_token` - stored auth token
- `$flow.state.phase` - roast phase
- `$flow.sessionId` - session identifier
- `$vars.variableName` - global variables

## Troubleshooting

### Token not accessible in MCP tools
- Verify Custom Function stored token: `$flow.state.auth_token = ...`
- Check MCP config uses `{{ $flow.state.auth_token }}`
- Use double curly braces for template syntax

### MCP tools not connecting
- Ensure `npx -y mcp-proxy` is available
- Verify URL uses `host.docker.internal` not `localhost`
- Check Bearer format: `Bearer {{ $flow.state.auth_token }}`

### Loop not working
- Use Iteration node for fixed iterations
- Use Condition Agent for dynamic loop based on state
- Set appropriate delay between iterations

## Export/Import

**Export**:
1. Click **⋮** → **Export Chatflow**
2. Save JSON to `docs/agent-platforms/flowise/workflows/`

**Import**:
1. Click **Import**
2. Select JSON file

## Next Steps

- See `WORKFLOW.md` for detailed design
- Compare with `../langflow/` (recommended) and `../n8n/`
