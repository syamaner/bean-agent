# Quick Manual Test Guide

## ✅ Setup Complete

- **Auth0 API**: `https://coffee-roasting-mcp` (ID: `68fd5acfbaba56916a9191b2`)
- **Test Client**: `Lke56LiZsHChlmi8ByUDa7HxSbnynCxH`
- **Scopes**: `read:roaster`, `write:roaster`, `read:detection`, `write:detection`
- **Environment files**: `.env.roaster_control`, `.env.first_crack_detection`

---

## Step 1: Get a Test Token

```bash
# Get full access token (all scopes)
curl --request POST \
  --url https://genai-7175210165555426.uk.auth0.com/oauth/token \
  --header 'content-type: application/json' \
  --data '{
    "client_id": "Lke56LiZsHChlmi8ByUDa7HxSbnynCxH",
    "audience": "https://coffee-roasting-mcp",
    "grant_type": "client_credentials",
    "client_secret": "FNLj1U-yJEJrajhZbCbXhkC1bxbm7brdTlw2nuB7djvS7EQZwipfW3_zL9Y6AttZ"
  }' | jq -r '.access_token'
```

**Save it**:
```bash
export TOKEN="paste_your_token_here"
```

---

## Step 2: Start Roaster Control Server

**Terminal 1**:
```bash
./test_roaster_server.sh
```

Or manually:
```bash
cd /Users/sertanyamaner/git/coffee-roasting
source venv/bin/activate
export $(cat .env.roaster_control | xargs)
uvicorn src.mcp_servers.roaster_control.sse_server:app --port 5002
```

---

## Step 3: Test Roaster Control (Terminal 2)

### Test Public Endpoints (No Auth)

```bash
# Health check
curl http://localhost:5002/health | jq

# Root info
curl http://localhost:5002/ | jq
```

### Test Protected Endpoints (With Auth)

```bash
# Without token (should fail with 401)
curl -i http://localhost:5002/sse

# With token (should succeed or show SSE stream)
curl -i -H "Authorization: Bearer $TOKEN" http://localhost:5002/sse
```

---

## Step 4: Start First Crack Detection Server

**Terminal 3**:
```bash
cd /Users/sertanyamaner/git/coffee-roasting
source venv/bin/activate
export $(cat .env.first_crack_detection | xargs)
uvicorn src.mcp_servers.first_crack_detection.sse_server:app --port 5001
```

---

## Step 5: Test First Crack Detection (Terminal 4)

```bash
# Health check
curl http://localhost:5001/health | jq

# Root info
curl http://localhost:5001/ | jq

# Protected endpoint
curl -i -H "Authorization: Bearer $TOKEN" http://localhost:5001/sse
```

---

## Step 6: Test with Warp MCP (Optional)

Create `.warp/mcp_settings.json`:
```json
{
  "mcpServers": {
    "roaster-control": {
      "url": "http://localhost:5002/sse",
      "transport": {"type": "sse"},
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_HERE"
      }
    },
    "first-crack-detection": {
      "url": "http://localhost:5001/sse",
      "transport": {"type": "sse"},
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_HERE"
      }
    }
  }
}
```

Then ask Warp:
- "What MCP tools are available?"
- "Use read_roaster_status"
- "Use get_first_crack_status"

---

## Expected Results

### ✅ Roaster Control Health
```json
{
  "status": "healthy",
  "session_active": false,
  "roaster_connected": true
}
```

### ✅ First Crack Health
```json
{
  "status": "healthy",
  "model_exists": true,
  "device": "mps",
  "session_active": false
}
```

### ✅ Root Endpoints
Both should return server info with endpoints and RBAC details.

### ❌ 401 Without Token
```
Missing or invalid Authorization header
```

### ✅ SSE Connection
With valid token, you should see SSE stream headers or MCP handshake.

---

## Troubleshooting

### "Address already in use"
```bash
# Find process using port 5002
lsof -i :5002

# Kill it
kill -9 <PID>
```

### "ModuleNotFoundError"
```bash
# Make sure venv is activated
source venv/bin/activate

# Verify packages
pip list | grep -E "mcp|starlette|uvicorn"
```

### "JWKS fetch failed"
- Check internet connection
- Verify AUTH0_DOMAIN in .env (no `https://` prefix)
- Check Auth0 domain is correct: `genai-7175210165555426.uk.auth0.com`

### Token doesn't work
```bash
# Decode token to check
echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq

# Check audience and scopes
```

---

## Next Steps

1. ✅ Both servers start successfully
2. ✅ Public endpoints work
3. ✅ Protected endpoints require auth
4. ✅ JWT validation works
5. 🔲 Test MCP tool calls (need MCP client or Warp)
6. 🔲 Test RBAC with different scope tokens
7. 🔲 Verify user audit logging in server logs

For detailed testing guide, see: `docs/MANUAL_TESTING.md`
