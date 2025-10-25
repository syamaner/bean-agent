# HTTP API Servers for MCP Integration

This document describes the HTTP REST API servers that wrap the First Crack Detection and Roaster Control MCP servers, enabling integration with n8n workflows and other orchestration platforms.

## Overview

Both MCP servers now expose FastAPI-based HTTP REST APIs with Auth0 JWT authorization:

- **First Crack Detection HTTP Server**: Port 5001 (default)
- **Roaster Control HTTP Server**: Port 5002 (default)

These servers enable:
- RESTful access to MCP functionality
- Auth0 JWT bearer token authentication
- Scope-based authorization (read/write permissions)
- 1-second polling capability for n8n workflows
- Auto-generated OpenAPI documentation at `/docs`

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                n8n Workflow Engine                   │
│          (polls every 1 second via HTTP)            │
└────────────────────┬────────────────────────────────┘
                     │
                     │ HTTP + JWT
                     ▼
┌─────────────────────────────────────────────────────┐
│          HTTP API Servers (FastAPI)                  │
│  ┌──────────────────┐    ┌──────────────────────┐  │
│  │  First Crack     │    │  Roaster Control     │  │
│  │  Detection API   │    │  API (Port 5002)     │  │
│  │  (Port 5001)     │    │                      │  │
│  └──────────────────┘    └──────────────────────┘  │
│                                                      │
│  Auth0 Middleware: JWT validation + scope checks    │
└────────────────────┬────────────────────────────────┘
                     │
                     │ In-process calls
                     ▼
┌─────────────────────────────────────────────────────┐
│          MCP Session Managers                        │
│  ┌──────────────────┐    ┌──────────────────────┐  │
│  │  Detection       │    │  Roaster Session     │  │
│  │  Session Manager │    │  Manager             │  │
│  └──────────────────┘    └──────────────────────┘  │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
          Hardware / Model Inference
```

## Setup

### 1. Environment Variables

Both servers require Auth0 configuration. Create `.env` files in each server directory:

#### First Crack Detection `.env`
```bash
# Copy from template
cp src/mcp_servers/first_crack_detection/.env.example \
   src/mcp_servers/first_crack_detection/.env

# Edit with your values
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://coffee-roasting-api
FIRST_CRACK_DETECTION_PORT=5001
MODEL_PATH=experiments/final_model/model.pt
```

#### Roaster Control `.env`
```bash
# Copy from template
cp src/mcp_servers/roaster_control/.env.example \
   src/mcp_servers/roaster_control/.env

# Edit with your values
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://coffee-roasting-api
ROASTER_CONTROL_PORT=5002
SERIAL_PORT=/dev/tty.usbserial-12340
```

### 2. Install Dependencies

HTTP dependencies are already in `requirements.txt`:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Auth0 Configuration

Refer to `docs/03-phase-3/AUTH0_INTEGRATION.md` for complete Auth0 setup including:
- Creating the Resource Server (API)
- Defining scopes (read:detection, write:detection, read:roaster, write:roaster)
- Creating a Machine-to-Machine application for n8n
- Obtaining client credentials for token acquisition

## Running the Servers

### Development Mode (local testing)

#### First Crack Detection
```bash
# Terminal 1
source venv/bin/activate
uvicorn src.mcp_servers.first_crack_detection.http_server:app \
  --port 5001 --reload
```

#### Roaster Control
```bash
# Terminal 2
source venv/bin/activate
uvicorn src.mcp_servers.roaster_control.http_server:app \
  --port 5002 --reload
```

### Production Mode

For production deployment (Phase 3.2 with .NET Aspire):
```bash
# First Crack Detection
uvicorn src.mcp_servers.first_crack_detection.http_server:app \
  --host ******* --port 5001 --workers 1

# Roaster Control
uvicorn src.mcp_servers.roaster_control.http_server:app \
  --host ******* --port 5002 --workers 1
```

**Note**: Keep workers=1 to maintain singleton session state.

## API Endpoints

### First Crack Detection API (Port 5001)

#### Public Endpoints (no auth required)
- `GET /` - API information
- `GET /health` - Health check and server status
- `GET /docs` - Auto-generated OpenAPI documentation

#### Protected Endpoints (Auth0 JWT required)
- `GET /api/detection/status` - Get current detection status
  - **Scope**: `read:detection`
- `POST /api/detection/start` - Start detection session
  - **Scope**: `write:detection`
  - **Body**: `{ "audio_source_type": "usb_microphone", "detection_config": {...} }`
- `POST /api/detection/stop` - Stop detection session and get summary
  - **Scope**: `write:detection`

### Roaster Control API (Port 5002)

#### Public Endpoints (no auth required)
- `GET /` - API information
- `GET /health` - Health check and server status
- `GET /docs` - Auto-generated OpenAPI documentation

#### Protected Endpoints (Auth0 JWT required)
- `GET /api/roaster/status` - Get current roaster status
  - **Scope**: `read:roaster`
- `POST /api/roaster/start` - Start roasting session
  - **Scope**: `write:roaster`
- `POST /api/roaster/stop` - Stop roasting session
  - **Scope**: `write:roaster`
- `POST /api/roaster/set-heat` - Set heat level (0-100)
  - **Scope**: `write:roaster`
  - **Body**: `{ "level": 75 }`
- `POST /api/roaster/set-fan` - Set fan speed (0-100)
  - **Scope**: `write:roaster`
  - **Body**: `{ "speed": 50 }`
- `POST /api/roaster/drop-beans` - Drop beans
  - **Scope**: `write:roaster`
- `POST /api/roaster/start-cooling` - Start cooling
  - **Scope**: `write:roaster`
- `POST /api/roaster/stop-cooling` - Stop cooling
  - **Scope**: `write:roaster`
- `POST /api/roaster/report-first-crack` - Report first crack detected
  - **Scope**: `write:roaster`
  - **Body**: `{ "timestamp": "2025-01-18T10:05:30Z" }`

## Authentication Flow

### 1. Obtain Access Token

n8n or other clients must first obtain a JWT from Auth0:

```bash
curl -X POST https://YOUR_DOMAIN/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "audience": "https://coffee-roasting-api",
    "grant_type": "client_credentials"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAi...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

### 2. Use Access Token

Include the token in the `Authorization` header for all protected endpoints:

```bash
curl -X GET http://localhost:5001/api/detection/status \
  -H "Authorization: Bearer eyJ0eXAi..."
```

### 3. Token Caching

The Auth0 middleware caches JWKS keys for 1 hour to minimize Auth0 API calls. Tokens are validated on every request but key fetching is optimized.

## Error Handling

All endpoints return structured error responses:

```json
{
  "error": {
    "status_code": 400,
    "detail": {
      "code": "ROASTER_NOT_CONNECTED",
      "message": "Roaster is not connected to serial port",
      "details": {
        "serial_port": "/dev/tty.usbserial-12340"
      }
    }
  }
}
```

Common error codes:
- `401 Unauthorized` - Missing or invalid JWT token
- `403 Forbidden` - Valid token but insufficient scope
- `400 Bad Request` - Invalid request parameters or resource state
- `500 Internal Server Error` - Server-side error

## Testing

### Quick Health Check
```bash
# First Crack Detection
curl http://localhost:5001/health

# Roaster Control
curl http://localhost:5002/health
```

### Test with Authentication

1. Get token from Auth0:
```bash
export ACCESS_TOKEN=$(curl -s -X POST https://YOUR_DOMAIN/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "audience": "https://coffee-roasting-api",
    "grant_type": "client_credentials"
  }' | jq -r '.access_token')
```

2. Test detection status:
```bash
curl -X GET http://localhost:5001/api/detection/status \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

3. Test roaster status:
```bash
curl -X GET http://localhost:5002/api/roaster/status \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Interactive Testing with OpenAPI Docs

Both servers provide interactive Swagger UI documentation:
- First Crack Detection: http://localhost:5001/docs
- Roaster Control: http://localhost:5002/docs

**Note**: You'll need to click "Authorize" in Swagger UI and paste your JWT token to test protected endpoints.

## n8n Integration

### Polling Pattern (1-second interval)

n8n workflows can poll status endpoints every second:

1. **HTTP Request Node** (scheduled every 1 second):
   - Method: GET
   - URL: `http://localhost:5001/api/detection/status`
   - Authentication: Bearer Token
   - Header: `Authorization: Bearer {{$json.access_token}}`

2. **IF Node** (check for first crack):
   - Condition: `{{$json.result.first_crack_detected}} === true`
   - True branch: Trigger roaster control action
   - False branch: Continue monitoring

3. **HTTP Request Node** (trigger action):
   - Method: POST
   - URL: `http://localhost:5002/api/roaster/set-heat`
   - Body: `{ "level": 60 }`
   - Authentication: Bearer Token

### Token Management in n8n

Use n8n's **Set** node to store and refresh Auth0 tokens:
- Store token in workflow variable
- Refresh before expiry (expires_in - 60 seconds)
- Reuse across multiple HTTP request nodes

## Deployment

### Phase 3.2: .NET Aspire Orchestration

The HTTP servers will be managed by .NET Aspire in Phase 3.2:
- Aspire launches uvicorn processes for both servers
- Health checks via `/health` endpoints
- Automatic restart on failure
- Log aggregation through Aspire dashboard
- Environment variable injection

### Phase 3.3: Cloudflare Tunnels

For remote access from hosted n8n:
- Cloudflare tunnels expose local HTTP servers securely
- No public IP or port forwarding required
- Auth0 JWT provides additional authentication layer
- Scopes limit what remote workflows can do

See `docs/03-phase-3/DEPLOYMENT.md` for complete deployment architecture.

## Troubleshooting

### Auth0 401 Unauthorized
- Check `AUTH0_DOMAIN` and `AUTH0_AUDIENCE` match your Auth0 tenant
- Verify token is not expired (`exp` claim)
- Confirm token is for correct audience (`aud` claim)

### Auth0 403 Forbidden
- Check token includes required scope (`scope` claim)
- Verify scope is defined in Auth0 Resource Server
- Ensure M2M application has permission to access scope

### Connection Refused
- Verify server is running on expected port
- Check firewall rules (local development)
- Confirm port is not already in use

### Model/Hardware Not Found
- First Crack Detection: Check `MODEL_PATH` points to valid checkpoint
- Roaster Control: Verify `SERIAL_PORT` matches connected device
- Run health check endpoint to see detailed error

### JWKS Fetch Errors
- Verify internet connectivity (JWKS endpoint requires external access)
- Check `AUTH0_DOMAIN` is correct and reachable
- Review logs for specific JWKS fetch errors

## Logs

Both servers log to stdout. In development:
```bash
# First Crack Detection
uvicorn src.mcp_servers.first_crack_detection.http_server:app --port 5001 --log-level debug

# Roaster Control
uvicorn src.mcp_servers.roaster_control.http_server:app --port 5002 --log-level debug
```

In production (with Aspire), logs are aggregated in the Aspire dashboard.

## Security Best Practices

1. **Never commit `.env` files** - they contain secrets
2. **Rotate Auth0 credentials** if accidentally exposed
3. **Use principle of least privilege** - grant only required scopes
4. **Monitor token usage** - review Auth0 logs for anomalies
5. **Enable HTTPS in production** - JWT should never be sent over plain HTTP
6. **Set short token expiry** - 1-24 hours max for M2M tokens
7. **Implement rate limiting** - protect against DoS (future work)

## Next Steps

- [ ] Test both HTTP servers manually with curl
- [ ] Create n8n workflow templates for common roasting scenarios
- [ ] Implement .NET Aspire application for orchestration (Phase 3.2)
- [ ] Set up Cloudflare tunnels for remote access (Phase 3.3)
- [ ] Add Prometheus metrics endpoints (stretch goal)

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Auth0 Machine-to-Machine Flow](https://auth0.com/docs/get-started/authentication-and-authorization-flow/client-credentials-flow)
- [n8n HTTP Request Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/)
- Project Auth0 Setup: `docs/03-phase-3/AUTH0_INTEGRATION.md`
- Secrets Management: `docs/03-phase-3/SECRETS.md`
