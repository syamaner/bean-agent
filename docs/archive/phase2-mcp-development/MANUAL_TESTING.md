# Manual Testing Guide for MCP Servers

## Prerequisites

### 1. Auth0 Configuration ✅

**API Resource Server**: `https://coffee-roasting-mcp`  
**API ID**: `68fd5acfbaba56916a9191b2`

**Scopes**:
- `read:roaster` - Read roaster status and sensors
- `write:roaster` - Control roaster (start, stop, set heat/fan, drop beans)
- `read:detection` - Read first crack detection status
- `write:detection` - Start/stop first crack detection

**Test Application**: Coffee Roasting MCP Test Client  
**Client ID**: `Lke56LiZsHChlmi8ByUDa7HxSbnynCxH`  
**Type**: SPA (Single Page Application)

### 2. Get Test Tokens

You can get test tokens using one of these methods:

#### Option A: Auth0 Dashboard (Quick Test Token)
1. Go to: https://manage.auth0.com/dashboard/us/genai-7175210165555426/apis/68fd5acfbaba56916a9191b2/test
2. Select all scopes
3. Copy the access token

#### Option B: Using Auth0 CLI
```bash
auth0 test token -a https://coffee-roasting-mcp -s "read:roaster write:roaster read:detection write:detection"
```

#### Option C: OAuth 2.0 Password Grant (for testing)
```bash
curl --request POST \
  --url https://genai-7175210165555426.uk.auth0.com/oauth/token \
  --header 'content-type: application/json' \
  --data '{
    "client_id": "Lke56LiZsHChlmi8ByUDa7HxSbnynCxH",
    "audience": "https://coffee-roasting-mcp",
    "grant_type": "client_credentials",
    "client_secret": "FNLj1U-yJEJrajhZbCbXhkC1bxbm7brdTlw2nuB7djvS7EQZwipfW3_zL9Y6AttZ"
  }'
```

**Save the token**:
```bash
export TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ii4uLiJ9..."
```

---

## Testing First Crack Detection MCP Server

### 1. Start Server

```bash
cd /Users/sertanyamaner/git/coffee-roasting
source venv/bin/activate

# Load environment variables
export $(cat .env.first_crack_detection | xargs)

# Start server
uvicorn src.mcp_servers.first_crack_detection.sse_server:app --port 5001
```

### 2. Test Public Endpoints

```bash
# Health check (no auth required)
curl http://localhost:5001/health

# Root endpoint (no auth required)
curl http://localhost:5001/
```

Expected response:
```json
{
  "name": "First Crack Detection MCP Server",
  "version": "1.0.0",
  "transport": "sse",
  "endpoints": {
    "sse": "/sse (Auth0 JWT required)",
    "messages": "/messages (Auth0 JWT required)",
    "health": "/health (public)"
  }
}
```

### 3. Test Protected Endpoints (Requires Auth)

#### Without Token (Should Fail - 401)
```bash
curl http://localhost:5001/sse
```

#### With Token (Should Succeed)
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:5001/sse
```

### 4. Test MCP Tools (via SSE)

For SSE testing, you'll need an MCP client or use the Warp MCP configuration.

**Warp Configuration** (`.warp/mcp_settings.json`):
```json
{
  "mcpServers": {
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

---

## Testing Roaster Control MCP Server

### 1. Start Server

```bash
# In a new terminal
cd /Users/sertanyamaner/git/coffee-roasting
source venv/bin/activate

# Load environment variables
export $(cat .env.roaster_control | xargs)

# Start server (mock mode)
uvicorn src.mcp_servers.roaster_control.sse_server:app --port 5002
```

### 2. Test Public Endpoints

```bash
# Health check
curl http://localhost:5002/health

# Root endpoint (shows RBAC info)
curl http://localhost:5002/
```

### 3. Test RBAC Scenarios

#### Observer Role (read:roaster only)

**Get a token with only read:roaster scope**:
```bash
# Use Auth0 test token page, select only "read:roaster"
export OBSERVER_TOKEN="..."
```

**Test read access (Should Succeed)**:
```bash
curl -H "Authorization: Bearer $OBSERVER_TOKEN" http://localhost:5002/sse
```

#### Operator Role (read:roaster + write:roaster)

**Get a token with both scopes**:
```bash
# Use Auth0 test token page, select "read:roaster" and "write:roaster"
export OPERATOR_TOKEN="..."
```

**Test full access (Should Succeed)**:
```bash
curl -H "Authorization: Bearer $OPERATOR_TOKEN" http://localhost:5002/sse
```

#### No Scopes (Should Fail - 403)
```bash
# Use Auth0 test token page, select NO scopes or wrong scopes
export NO_SCOPE_TOKEN="..."

curl -H "Authorization: Bearer $NO_SCOPE_TOKEN" http://localhost:5002/sse
```

Expected error:
```json
{
  "error": "Insufficient permissions",
  "required_scopes": ["read:roaster OR write:roaster"],
  "your_scopes": [],
  "user_email": "user@example.com"
}
```

---

## Testing with Warp MCP Client

### Configuration for Both Servers

Create `.warp/mcp_settings.json`:
```json
{
  "mcpServers": {
    "first-crack-detection": {
      "url": "http://localhost:5001/sse",
      "transport": {"type": "sse"},
      "headers": {
        "Authorization": "Bearer YOUR_FULL_ACCESS_TOKEN"
      }
    },
    "roaster-control": {
      "url": "http://localhost:5002/sse",
      "transport": {"type": "sse"},
      "headers": {
        "Authorization": "Bearer YOUR_FULL_ACCESS_TOKEN"
      }
    }
  }
}
```

### Test MCP Tools in Warp

1. **List available tools**:
   ```
   Ask Warp: "What MCP tools are available?"
   ```

2. **Test First Crack Detection**:
   ```
   Ask Warp: "Use the start_first_crack_detection tool with audio_file source"
   ```

3. **Test Roaster Control**:
   ```
   Ask Warp: "Use the read_roaster_status tool"
   Ask Warp: "Use the set_heat tool to set heat to 50%"
   ```

---

## Expected Test Results

### ✅ Success Scenarios

1. **Public endpoints work without auth**
2. **Protected endpoints reject requests without tokens** (401)
3. **Protected endpoints reject tokens without required scopes** (403)
4. **Observer tokens can access /sse but can't control** (RBAC)
5. **Operator tokens can fully control roaster**
6. **MCP tools execute and return proper responses**
7. **User info logged in server logs**

### ❌ Failure Scenarios to Test

1. Invalid token → 401 Authentication failed
2. Expired token → 401 Token has expired
3. Wrong audience → 401 Invalid token claims
4. Missing scopes → 403 Insufficient permissions
5. Malformed Authorization header → 401 Missing or invalid header

---

## Troubleshooting

### Server Won't Start
- Check virtual environment is activated
- Check .env file exists and is loaded
- Check port not already in use: `lsof -i :5001`

### 401 Unauthorized
- Verify token is valid and not expired
- Check AUTH0_DOMAIN and AUTH0_AUDIENCE match
- Verify Authorization header: `Bearer <token>`

### 403 Forbidden
- Check token has required scopes
- Verify scopes in JWT: `jwt decode $TOKEN`
- Check server logs for scope mismatch details

### JWKS Fetch Errors
- Verify AUTH0_DOMAIN is correct
- Check internet connectivity
- Auth0 domain should NOT have `https://` prefix in .env

---

## Next Steps After Manual Testing

1. ✅ Confirm both servers start successfully
2. ✅ Verify Auth0 JWT validation works
3. ✅ Test RBAC (Observer vs Operator)
4. ✅ Confirm MCP tools execute properly
5. 🔲 Set up .NET Aspire orchestration
6. 🔲 Create n8n workflow
7. 🔲 End-to-end integration test
