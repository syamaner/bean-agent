# Quick Start: n8n with MCP Servers

Get up and running with n8n and MCP servers in 5 minutes.

---

## Prerequisites

✅ Docker installed and running  
✅ .NET 9.0 SDK installed  
✅ Auth0 credentials configured in `appsettings.Development.json`  
✅ OpenAI API key (for AI Agent workflows)

---

## Step 1: Start All Services

```bash
cd src/orchestration/aspire
dotnet run
```

This starts:
- **Roaster Control MCP** on http://localhost:5002
- **First Crack Detection MCP** on http://localhost:5001
- **n8n** on http://localhost:5678
- **AI Agent** (Python autonomous agent)
- **Aspire Dashboard** on http://localhost:15000 (or similar)

Wait for all services to show "Running" in the Aspire dashboard.

---

## Step 2: Access n8n

Open browser to: **http://localhost:5678**

### First-Time Setup

1. **Create Owner Account**
   - Email: your-email@example.com
   - Password: (choose secure password)
   - First name / Last name

2. **Skip Usage Survey** (optional)

3. **Skip Tutorial** (or follow if new to n8n)

---

## Step 3: Verify MCP Connectivity

### Test Workflow: "MCP Connection Test"

1. Click **+ Add workflow**
2. Add nodes in this order:

#### Node 1: Manual Trigger
- Just click to add, no configuration needed

#### Node 2: HTTP Request (Get Auth0 Token)
- **Method**: POST
- **URL**: `https://genai-7175210165555426.uk.auth0.com/oauth/token`
- **Body**: JSON
  ```json
  {
    "client_id": "Jk3aF2NfkiiOIXY0eHJQxfA6jkP0Pjf7",
    "client_secret": "05agLnSUZceYK2Yl9bYGGnV_zuy7EAJ9ZWnMuOpCHEIOx2v8xZ7XNAmsQW020m2k",
    "audience": "https://coffee-roasting-api",
    "grant_type": "client_credentials"
  }
  ```
- **Options** → **Response** → **Response Format**: JSON

#### Node 3: Set Variable (Store Token)
- **Name**: `auth_token`
- **Value**: `={{$json.access_token}}`

#### Node 4: HTTP Request (Test Roaster Status)
- **Method**: GET
- **URL**: `http://roaster-control:5002/api/status`
- **Authentication**: Generic Credential Type
  - Select **Header Auth**
  - Name: `Authorization`
  - Value: `Bearer {{$('Set Variable').item.json.auth_token}}`

#### Node 5: Display Result
- Add **Code** node (optional) or just view output

### Run the Workflow

1. Click **Test workflow** button (top right)
2. Click **Execute workflow**
3. Check each node for green checkmarks
4. View Node 4 output - should show roaster status JSON

**Expected output**:
```json
{
  "session_active": false,
  "roaster_running": false,
  "sensors": {...},
  "metrics": {...}
}
```

---

## Step 4: Create First AI Agent Workflow

### Workflow: "Coffee Roaster Agent"

1. **Add AI Agent Node**
   - Type: Tools Agent
   - Model: OpenAI (configure with your API key)
   
2. **Add LangChain MCP Tool (Roaster)**
   - SSE Endpoint: `http://roaster-control:5002/sse`
   - Authentication: Bearer
   - Token: Use the auth_token from previous step
   - Tools: All

3. **Add LangChain MCP Tool (First Crack)**
   - SSE Endpoint: `http://first-crack-detection:5001/sse`
   - Authentication: Bearer
   - Token: Use the auth_token from previous step
   - Tools: All

4. **Configure System Prompt**:
   ```
   You are a coffee roasting expert controlling a Hottop KN-8828B-2K+ roaster.
   
   Available tools:
   - Roaster Control: start_roaster, set_heat, set_fan, drop_beans, get_roast_status
   - First Crack Detection: start_first_crack_detection, get_first_crack_status
   
   When asked to perform actions, use the appropriate tools.
   Always check status before making changes.
   ```

5. **Test with Simple Prompt**:
   ```
   Get the current roaster status and tell me if it's ready to start roasting.
   ```

---

## Step 5: Monitor in Aspire Dashboard

Open the Aspire dashboard (URL shown in terminal when running `dotnet run`).

### What to Monitor

1. **Services Tab**: All services should be green (Running)
2. **Console Logs**: View real-time logs from each service
3. **Traces**: See HTTP requests between services
4. **Metrics**: Monitor resource usage

### Useful Views

- **n8n logs**: See workflow executions
- **roaster-control logs**: See MCP tool invocations
- **first-crack-detection logs**: See detection activity

---

## Common Issues

### n8n container won't start

**Error**: Volume mount permission denied

**Solution**:
```bash
chmod -R 777 .n8n
```

### Cannot connect to MCP servers from n8n

**Error**: Connection refused or timeout

**Check**:
1. Services are running (Aspire dashboard)
2. Using correct URLs: `http://roaster-control:5002` NOT `localhost:5002`
3. Network: All containers on same Docker network

### Auth0 401 Unauthorized

**Check**:
1. Token is valid (not expired)
2. Scopes are correct in Auth0 M2M app
3. Auth0 domain matches in both places

---

## Environment Variables in n8n

These are available in n8n workflows via `{{$env.VAR_NAME}}`:

- `ROASTER_CONTROL_SSE`: MCP server endpoint
- `FIRST_CRACK_SSE`: Detection server endpoint
- `AUTH0_DOMAIN`: Auth0 tenant
- `AUTH0_AUDIENCE`: API audience
- `AUTH0_CLIENT_ID`: M2M client ID
- `AUTH0_CLIENT_SECRET`: M2M client secret

---

## Next Steps

✅ Verified n8n connects to MCP servers  
→ Create full roasting workflow with AI Agent  
→ Test with mock hardware  
→ Document workflow templates  
→ Test with real hardware

---

## Quick Commands

```bash
# Start everything
cd src/orchestration/aspire && dotnet run

# View n8n logs only
docker logs coffee-roasting-n8n-1 -f

# Stop all services
# (Ctrl+C in the terminal running Aspire)

# Clean n8n data (reset)
rm -rf .n8n/*

# Rebuild if needed
cd src/orchestration/aspire && dotnet clean && dotnet run
```

---

**Ready to build workflows!** 🚀

See [N8N_MCP_SETUP.md](./N8N_MCP_SETUP.md) for detailed workflow examples.
