# Import and Test MCP Workflow

Step-by-step guide to import the test workflow and verify MCP connectivity.

---

## Step 1: Import the Workflow

1. Open n8n at **http://localhost:5678**

2. Click **Add workflow** (top right, + button)

3. Click the **three dots menu** (⋮) in top right

4. Select **Import from File**

5. Navigate to: `docs/03-phase-3/workflows/mcp-connection-test.json`

6. Click **Open**

7. The workflow should appear with 5 nodes:
   - Manual Trigger
   - Get Auth0 Token
   - Store Token
   - Test Roaster Status
   - Test First Crack Detection

---

## Step 2: Verify Node Configuration

### Node 1: Manual Trigger
✅ No configuration needed

### Node 2: Get Auth0 Token
Check these settings:
- **Method**: POST
- **URL**: `https://genai-7175210165555426.uk.auth0.com/oauth/token`
- **Body Parameters** (should have 4):
  - `client_id`: Jk3aF2NfkiiOIXY0eHJQxfA6jkP0Pjf7
  - `client_secret`: YOUR_AUTH0_CLIENT_SECRET
  - `audience`: https://coffee-roasting-api
  - `grant_type`: client_credentials

### Node 3: Store Token
Check assignments:
- `auth_token`: `={{ $json.access_token }}`
- `token_expires_at`: `={{ Math.floor(Date.now()/1000) + $json.expires_in }}`

### Node 4: Test Roaster Status
Check:
- **URL**: `http://roaster-control:5002/api/status`
- **Header**: Authorization = `=Bearer {{ $json.auth_token }}`

### Node 5: Test First Crack Detection
Check:
- **URL**: `http://first-crack-detection:5001/api/status`
- **Header**: Authorization = `=Bearer {{ $('Store Token').item.json.auth_token }}`

---

## Step 3: Execute the Workflow

1. Click **Test workflow** button (top right)

2. Click **Execute workflow** button

3. Watch the nodes execute (they'll turn green with checkmarks)

---

## Step 4: Verify Results

### Expected Flow:
1. ✅ **Manual Trigger** - Starts execution
2. ✅ **Get Auth0 Token** - Returns JWT token
3. ✅ **Store Token** - Extracts and stores token
4. ✅ **Test Roaster Status** - Returns roaster data
5. ✅ **Test First Crack Detection** - Returns detection data

### Check Node Outputs:

#### Get Auth0 Token Output:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

#### Store Token Output:
```json
{
  "auth_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_expires_at": 1730052297
}
```

#### Test Roaster Status Output:
```json
{
  "session_active": false,
  "roaster_running": false,
  "sensors": {
    "bean_temp_c": null,
    "chamber_temp_c": null,
    "heat_level_percent": 0,
    "fan_speed_percent": 0
  },
  "metrics": {
    "roast_elapsed_seconds": null,
    "rate_of_rise_c_per_min": null
  },
  "first_crack": {
    "detected": false,
    "timestamp_utc": null,
    "temperature_c": null
  },
  "timestamps": {
    "server_time_utc": "2025-10-26T19:45:00.000Z"
  }
}
```

#### Test First Crack Detection Output:
```json
{
  "monitoring": false,
  "first_crack_detected": false,
  "session_start_time_utc": null,
  "elapsed_time": null
}
```

---

## Troubleshooting

### ❌ Get Auth0 Token fails with 401

**Problem**: Invalid credentials

**Solution**:
1. Check Auth0 domain, client_id, and client_secret match `appsettings.Development.json`
2. Verify M2M application exists in Auth0 dashboard
3. Ensure all scopes are granted

### ❌ Test Roaster Status fails with connection error

**Problem**: Cannot reach MCP server

**Check**:
1. Aspire dashboard shows `roaster-control` is running
2. Using `http://roaster-control:5002` not `localhost:5002`
3. n8n container is on same Docker network

**Solution**:
```bash
# Check if services are running
docker ps | grep coffee-roasting

# Check n8n can reach services
docker exec -it coffee-roasting-n8n-1 ping roaster-control
```

### ❌ Test fails with 401 Unauthorized

**Problem**: Token missing scopes

**Solution**:
1. Go to Auth0 Dashboard
2. Applications → n8n M2M app → APIs tab
3. Expand "Coffee Roasting API"
4. Ensure ALL scopes are checked:
   - `read:roaster`
   - `write:roaster`
   - `read:detection`
   - `write:detection`
5. Save and regenerate token

### ❌ Node shows "Expression Error"

**Problem**: Syntax error in expression

**Common fixes**:
- Authorization header: `=Bearer {{ $json.auth_token }}` (note the `=` at start)
- Accessing previous node: `={{ $('Store Token').item.json.auth_token }}`

---

## Step 5: Save the Workflow

1. Click **Save** button (top right)
2. Name it: "MCP Connection Test"
3. Click **Save**

The workflow is now saved in your n8n instance (persisted in `.n8n/` directory).

---

## Next Steps

✅ **Basic connectivity verified** - Both MCP servers are reachable with Auth0 tokens

**Now you can**:
1. Create AI Agent workflow with LangChain MCP Tool nodes
2. Build full roasting automation workflow
3. Test with mock hardware

See [N8N_MCP_SETUP.md](./N8N_MCP_SETUP.md) for AI Agent configuration.

---

## Quick Reference

### Auth0 Token Endpoint
```
POST https://genai-7175210165555426.uk.auth0.com/oauth/token
{
  "client_id": "Jk3aF2NfkiiOIXY0eHJQxfA6jkP0Pjf7",
  "client_secret": "YOUR_AUTH0_CLIENT_SECRET",
  "audience": "https://coffee-roasting-api",
  "grant_type": "client_credentials"
}
```

### MCP Server Endpoints
- Roaster Control: `http://roaster-control:5002/api/status`
- First Crack Detection: `http://first-crack-detection:5001/api/status`

### Bearer Token Format
```
Authorization: Bearer <access_token>
```

---

**Status**: Ready for testing ✅
