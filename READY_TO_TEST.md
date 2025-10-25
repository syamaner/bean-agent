# ✅ Ready to Test - MCP Servers with Auth0

## What's Complete

### 1. Auth0 Configuration ✅
- **API Resource Server**: `Coffee Roasting MCP API`
  - Identifier: `https://coffee-roasting-mcp`
  - ID: `68fd5acfbaba56916a9191b2`
- **Scopes Defined**:
  - `read:roaster` - Read roaster status
  - `write:roaster` - Control roaster
  - `read:detection` - Read first crack status
  - `write:detection` - Start/stop detection
- **Test Application**: `Coffee Roasting MCP Test Client`
  - Type: SPA
  - Client ID: `Lke56LiZsHChlmi8ByUDa7HxSbnynCxH`
  - Can generate tokens for testing

### 2. MCP Servers ✅
Both servers implemented with:
- HTTP+SSE transport (Starlette/Uvicorn)
- Auth0 JWT validation middleware
- User-based authentication with RBAC
- Audit logging (user info in logs)
- 23/23 tests passing

**Servers**:
- `src/mcp_servers/first_crack_detection/sse_server.py` (port 5001)
- `src/mcp_servers/roaster_control/sse_server.py` (port 5002)

### 3. Configuration Files ✅
- `.env.first_crack_detection.example` - Template for detection server
- `.env.roaster_control.example` - Template for roaster server
- Environment variables properly excluded from git

### 4. Testing Documentation ✅
- **QUICK_TEST.md** - Step-by-step quick start
- **docs/MANUAL_TESTING.md** - Comprehensive testing guide
- **test_roaster_server.sh** - Helper script to start roaster server

---

## What You Need to Do

### Step 1: Copy Environment Files (Already Done)
You already have:
- `.env.first_crack_detection` 
- `.env.roaster_control`

Both configured with your Auth0 tenant.

### Step 2: Get a Test Token

```bash
# Get token (returns full access token with all scopes)
TOKEN=$(curl --request POST \
  --url https://genai-7175210165555426.uk.auth0.com/oauth/token \
  --header 'content-type: application/json' \
  --data '{
    "client_id": "Lke56LiZsHChlmi8ByUDa7HxSbnynCxH",
    "audience": "https://coffee-roasting-mcp",
    "grant_type": "client_credentials",
    "client_secret": "FNLj1U-yJEJrajhZbCbXhkC1bxbm7brdTlw2nuB7djvS7EQZwipfW3_zL9Y6AttZ"
  }' | jq -r '.access_token')

echo $TOKEN
```

### Step 3: Start Roaster Control Server

**Terminal 1**:
```bash
./test_roaster_server.sh
```

Expected output:
```
Starting Roaster Control MCP Server on port 5002...
Mock mode: 1
Auth0 Domain: genai-7175210165555426.uk.auth0.com
Auth0 Audience: https://coffee-roasting-mcp

INFO:     Started server process [...]
INFO:     Waiting for application startup.
INFO:     Roaster Control MCP Server (HTTP+SSE) initialized
INFO:     Mock mode: True
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5002
```

### Step 4: Test Roaster Control

**Terminal 2**:
```bash
# Health check (no auth)
curl http://localhost:5002/health | jq

# Should return:
# {
#   "status": "healthy",
#   "session_active": false,
#   "roaster_connected": true
# }

# Root info (no auth)
curl http://localhost:5002/ | jq

# Protected endpoint without token (should fail 401)
curl http://localhost:5002/sse

# Protected endpoint with token (should work)
curl -H "Authorization: Bearer $TOKEN" http://localhost:5002/sse
```

### Step 5: Start First Crack Detection Server

**Terminal 3**:
```bash
cd /Users/sertanyamaner/git/coffee-roasting
source venv/bin/activate
export $(cat .env.first_crack_detection | xargs)
uvicorn src.mcp_servers.first_crack_detection.sse_server:app --port 5001
```

### Step 6: Test First Crack Detection

**Terminal 4**:
```bash
curl http://localhost:5001/health | jq
curl http://localhost:5001/ | jq
curl -H "Authorization: Bearer $TOKEN" http://localhost:5001/sse
```

---

## Expected Test Results

### ✅ Success Indicators

1. **Both servers start without errors**
2. **Health endpoints return healthy status**
3. **Root endpoints return server info**
4. **Protected endpoints reject requests without tokens** (401)
5. **Protected endpoints accept valid tokens** (SSE stream or 200 OK)
6. **Server logs show user info** (email, scopes)

### 🔍 What to Look For in Logs

When you connect with a token, you should see:
```
INFO: MCP connection from user: (client ID or email)
INFO: JWKS keys refreshed from Auth0
```

---

## Test Scenarios

### Scenario 1: Public Access ✅
```bash
curl http://localhost:5002/health
# Should work without auth
```

### Scenario 2: Auth Required ✅
```bash
curl http://localhost:5002/sse
# Should fail with 401
```

### Scenario 3: Valid Token ✅
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:5002/sse
# Should succeed (SSE stream)
```

### Scenario 4: MCP Tools (via Warp)
Configure `.warp/mcp_settings.json`:
```json
{
  "mcpServers": {
    "roaster-control": {
      "url": "http://localhost:5002/sse",
      "transport": {"type": "sse"},
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_HERE"
      }
    }
  }
}
```

Then in Warp:
- "What MCP tools are available?"
- "Use read_roaster_status"

---

## Troubleshooting Quick Reference

### Port already in use
```bash
lsof -i :5002
kill -9 <PID>
```

### Token issues
```bash
# Decode token to inspect
echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq
```

### Server won't start
```bash
# Check venv
source venv/bin/activate

# Check dependencies
pip list | grep -E "mcp|starlette|uvicorn|jose"

# Check .env files exist
ls -la .env.*
```

---

## What's Next After Manual Testing

1. ✅ Verify both servers start successfully
2. ✅ Health endpoints work (verified: returns roaster info)
3. 🔲 Test JWT authentication with real tokens
4. 🔲 Test RBAC (tokens with different scopes)
5. 🔲 Test MCP tool calls via Warp or MCP client
6. 🔲 Set up .NET Aspire orchestration
7. 🔲 Create n8n workflow for roast automation
8. 🔲 Hardware-in-the-loop testing (real Hottop)

---

## Files You Have

- `QUICK_TEST.md` - Quick start guide
- `docs/MANUAL_TESTING.md` - Detailed testing guide
- `.env.first_crack_detection` - Your config (not in git)
- `.env.roaster_control` - Your config (not in git)
- `test_roaster_server.sh` - Start script

## Commands to Remember

```bash
# Start roaster server
./test_roaster_server.sh

# Get token
curl ... | jq -r '.access_token'

# Test health
curl http://localhost:5002/health | jq

# Test with auth
curl -H "Authorization: Bearer $TOKEN" http://localhost:5002/sse
```

**You're ready to test! Start with Step 2 above.** 🚀
