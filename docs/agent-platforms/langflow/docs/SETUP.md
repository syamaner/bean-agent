# LangFlow Setup Guide

## Overview

LangFlow is a Python-based visual builder for AI agents with native MCP support and dynamic authentication. This guide helps you set up the autonomous coffee roasting agent in LangFlow.

## Prerequisites

✅ Aspire already configured (Program.cs updated)
✅ MCP servers running (Roaster Control + First Crack Detection)
✅ Auth0 credentials configured

## Step 1: Set Password in User Secrets

```bash
cd src/orchestration/aspire
dotnet user-secrets set "Parameters:langflow-password" "your-secure-password"
```

## Step 2: Start Aspire

```bash
dotnet run
```

LangFlow will be available at: **http://localhost:7860**

## Step 3: First Login

1. Navigate to http://localhost:7860
2. Login with:
   - Username: `admin`
   - Password: (the one you set in user secrets)

## Step 4: Create Autonomous Roasting Flow

### 4.1 Create New Flow

1. Click **"New Flow"**
2. Name it: `Autonomous Coffee Roast`
3. Select: **Agent** template

### 4.2 Add Auth0 Token Fetch

1. Add **HTTP Request** component
2. Configure:
   - **Name**: `Get Auth0 Token`
   - **Method**: `POST`
   - **URL**: `https://{env:AUTH0_DOMAIN}/oauth/token`
   - **Body Type**: `JSON`
   - **Body**:
     ```json
     {
       "client_id": "{env:AUTH0_CLIENT_ID}",
       "client_secret": "{env:AUTH0_CLIENT_SECRET}",
       "audience": "{env:AUTH0_AUDIENCE}",
       "grant_type": "client_credentials"
     }
     ```

### 4.3 Store Token in Variables

1. Add **Set Variables** component
2. Connect from **Get Auth0 Token**
3. Configure:
   - **Variable Name**: `auth_token`
   - **Value**: `{Get Auth0 Token.access_token}`
   - **Scope**: `Flow`

### 4.4 Add MCP Tools

#### Roaster Control MCP

1. Add **MCP Tools** component
2. Configure:
   - **Name**: `Roaster Control`
   - **Transport**: `SSE`
   - **URL**: `{env:ROASTER_CONTROL_SSE}`
   - **Headers**:
     ```json
     {
       "Authorization": "Bearer {$vars.auth_token}"
     }
     ```

#### First Crack Detection MCP

1. Add **MCP Tools** component
2. Configure:
   - **Name**: `First Crack Detection`
   - **Transport**: `SSE`
   - **URL**: `{env:FIRST_CRACK_SSE}`
   - **Headers**:
     ```json
     {
       "Authorization": "Bearer {$vars.auth_token}"
     }
     ```

### 4.5 Configure Agent

1. Add **Agent** component
2. Configure:
   - **Model**: `gpt-4o` (OpenAI)
   - **API Key**: From credentials
   - **Tools**: Select both MCP tools
   - **System Prompt**:
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
     5. When dev time 15-20% and temp 192-195°C: call drop_beans
     ```

### 4.6 Add Loop Mechanism

1. Add **Loop** component
2. Configure:
   - **Loop Back To**: Agent node
   - **Max Iterations**: `180` (30 minutes at 10s intervals)
   - **Condition**: `{$flow.state.phase} != 'complete'`
   - **Delay**: `10` seconds

### 4.7 Add Chat Output

1. Add **Chat Output** component
2. Connect from Agent
3. This displays the agent's decisions and actions

## Step 5: Save and Test

1. Click **Save**
2. Click **Run** (play button)
3. Type: `Start the roast`
4. Watch the agent work!

## Flow Structure

```
[Get Auth0 Token] 
    → [Set Variables: auth_token]
    → [MCP Tools: Roaster + FC Detection]
    → [Agent]
    → [Loop (every 10s, max 180 iterations)]
    → [Chat Output]
```

## Key Features

✅ **Dynamic Auth**: Token fetched fresh each run and stored in `$vars`
✅ **MCP Integration**: Both tools use `{$vars.auth_token}` for auth
✅ **Agent Loops**: Built-in loop with 10s delay
✅ **State Management**: `$flow.state` tracks roast phase
✅ **Environment Variables**: All sensitive data from Aspire

## Accessing Environment Variables in LangFlow

LangFlow automatically has access to all environment variables passed from Aspire:
- `{env:AUTH0_DOMAIN}`
- `{env:AUTH0_CLIENT_ID}`
- `{env:AUTH0_CLIENT_SECRET}`
- `{env:AUTH0_AUDIENCE}`
- `{env:ROASTER_CONTROL_SSE}`
- `{env:FIRST_CRACK_SSE}`

## Accessing Flow Variables

Once set, variables are accessible as:
- `{$vars.auth_token}`
- `{$flow.state.phase}`
- `{$flow.sessionId}`

## Troubleshooting

### Token not working
- Check that `Set Variables` component ran successfully
- Verify `{$vars.auth_token}` is populated in debug mode
- Ensure MCP tools reference `{$vars.auth_token}` in headers

### MCP tools not connecting
- Verify MCP servers are running in Aspire dashboard
- Check URL: `http://host.docker.internal:5002/sse` (use host.docker.internal, not localhost)
- Ensure Bearer token format: `Bearer {$vars.auth_token}`

### Loop not stopping
- Verify Loop condition references correct state variable
- Check that agent updates `$flow.state.phase` to 'complete'
- Set reasonable max iterations (180 = 30 min)

### Agent not using tools
- Ensure tools are connected to Agent component
- Verify system prompt clearly instructs tool usage
- Check model supports function calling (gpt-4o does)

## Export/Import Flow

**Export**:
1. Click **⋮** menu
2. Select **Export**
3. Save JSON to `docs/agent-platforms/langflow/workflows/`

**Import**:
1. Click **Import**
2. Select JSON file
3. Update any environment-specific settings

## Next Steps

- See `WORKFLOW.md` for detailed flow design
- See `TROUBLESHOOTING.md` for common issues
- Compare with `../flowise/docs/` and `../n8n/docs/` for alternatives
