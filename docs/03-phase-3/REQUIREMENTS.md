# Phase 3: Intelligent Roasting Agent - Requirements

**Status**: 📋 Planning  
**Prerequisites**: Phase 1 ✅ + Phase 2 ✅  
**Updated**: October 25, 2025

---

## Overview

Phase 3 builds an intelligent agent that orchestrates coffee roasting using the two MCP servers from Phase 2. The agent makes real-time decisions based on sensor data and first crack detection to execute roasting profiles.

---

## Architecture

### Part 1: Agent Development & Local Testing

```
┌─────────────────────────────────────────────────────────┐
│              .NET Aspire Host                           │
│  ┌───────────────────────────────────────────────────┐  │
│  │         n8n Workflow (Container)                   │  │
│  │  • Workflow orchestration                          │  │
│  │  • LLM decision nodes (OpenAI/Anthropic)          │  │
│  │  • HTTP polling (1s intervals)                     │  │
│  │  • Roast profile execution                         │  │
│  └─────────────┬─────────────┬────────────────────────┘  │
│                │             │                            │
│  ┌─────────────▼────────┐  ┌─▼────────────────────────┐  │
│  │ First Crack MCP      │  │ Roaster Control MCP      │  │
│  │ (Python Project)     │  │ (Python Project)         │  │
│  │ • HTTP API           │  │ • HTTP API               │  │
│  │ • Auth0 validation   │  │ • Auth0 validation       │  │
│  │ • Polling endpoints  │  │ • Polling endpoints      │  │
│  └──────────────────────┘  └──────────┬───────────────┘  │
└─────────────────────────────────────────┼──────────────┘
                                          │ USB Serial
                                   ┌──────▼───────┐
                                   │ Hottop       │
                                   │ KN-8828B-2K+ │
                                   └──────────────┘
```

### Part 2: Production Deployment

```
┌─────────────────────────────────────────────────────────┐
│              Cloud / Hosted                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │         n8n Cloud Instance                        │   │
│  │  • Workflow agent                                 │   │
│  │  • LLM integration                                │   │
│  └───────────┬──────────────────────────────────────┘   │
└─────────────┼────────────────────────────────────────┘
              │ HTTPS + JWT
              │
┌─────────────▼────────────────────────────────────────┐
│         Cloudflare Tunnel                             │
│  • Secure tunnel to home network                      │
│  • Auth0 JWT validation                               │
│  • TLS termination                                    │
└─────────────┬────────────────────────────────────────┘
              │
┌─────────────▼────────────────────────────────────────┐
│         Home Network                                  │
│  ┌──────────────────────────────────────────────┐    │
│  │  MCP Servers (Python on Mac/RPi)             │    │
│  │  • First Crack Detection                      │    │
│  │  • Roaster Control                            │    │
│  │  • HTTP APIs with Auth0                       │    │
│  │  • Cloudflare tunnel client                   │    │
│  └─────────────┬────────────────────────────────┘    │
│                │ USB                                   │
│         ┌──────▼───────┐                              │
│         │ Hottop       │                              │
│         │ KN-8828B-2K+ │                              │
│         └──────────────┘                              │
└───────────────────────────────────────────────────────┘
```

---

## Part 1: Agent Development (Local)

### 1.1 MCP Server HTTP APIs

#### Upgrade MCP Servers from stdio to HTTP

**First Crack Detection MCP**:
```
POST /api/detect/start
  Body: {
    "audio_source_type": "usb_microphone",
    "detection_config": {...}
  }
  Auth: Bearer <Auth0 JWT>
  Scopes: roast:admin

GET /api/detect/status
  Auth: Bearer <Auth0 JWT>
  Scopes: roast:observer OR roast:admin
  Returns: {
    "monitoring": true/false,
    "first_crack_detected": true/false,
    "timestamp_utc": "ISO 8601",
    "timestamp_local": "ISO 8601",
    "elapsed_time": "MM:SS",
    ...
  }

POST /api/detect/stop
  Auth: Bearer <Auth0 JWT>
  Scopes: roast:admin
```

**Roaster Control MCP**:
```
POST /api/roaster/start
POST /api/roaster/stop
POST /api/roaster/set-heat
  Body: {"percent": 50}
POST /api/roaster/set-fan
  Body: {"percent": 30}
POST /api/roaster/drop-beans
POST /api/roaster/start-cooling
POST /api/roaster/stop-cooling
POST /api/roaster/report-first-crack
  Body: {"timestamp": "...", "temperature": 200.5}

GET /api/roaster/status
  Returns: {
    "session_active": true,
    "roaster_running": true,
    "sensors": {...},
    "metrics": {
      "roast_elapsed_seconds": 420,
      "rate_of_rise_c_per_min": 5.2,
      "beans_added_temp_c": 170.0,
      "first_crack_temp_c": 196.5,
      "development_time_percent": 18.5,
      ...
    },
    "timestamps": {...}
  }
```

**Auth0 Configuration**:

See detailed configuration in [Auth0 Setup](#auth0-setup) section below.

- Two roles: `roast:admin` and `roast:observer`
- Scope-based authorization on every endpoint
- JWT validation using Auth0 public keys
- Token introspection for claims validation

**Polling Strategy**:
- Agent polls both status endpoints every 1 second
- Simpler than SSE, works well for n8n workflows
- Acceptable latency for roasting (not millisecond-critical)

### 1.2 .NET Aspire Orchestration

**Aspire AppHost**:
- Orchestrate n8n container
- Orchestrate both Python MCP servers as projects
- Service discovery and configuration
- Centralized logging and monitoring
- Development environment setup

**Python Project Integration**:
```csharp
// AppHost/Program.cs
var builder = DistributedApplication.CreateBuilder(args);

// MCP Servers as Python projects
var firstCrack = builder.AddPythonProject(
    "first-crack-mcp",
    "../../../src/mcp_servers/first_crack_detection",
    "server.py"
)
.WithEnvironment("AUTH0_DOMAIN", "your-domain.auth0.com")
.WithEnvironment("AUTH0_AUDIENCE", "https://coffee-roasting-api")
.WithHttpEndpoint(port: 5001);

var roasterControl = builder.AddPythonProject(
    "roaster-control-mcp",
    "../../../src/mcp_servers/roaster_control",
    "server.py"
)
.WithEnvironment("AUTH0_DOMAIN", "your-domain.auth0.com")
.WithEnvironment("AUTH0_AUDIENCE", "https://coffee-roasting-api")
.WithEnvironment("ROASTER_MOCK_MODE", "0")
.WithHttpEndpoint(port: 5002);

// n8n container
var n8n = builder.AddContainer("n8n", "n8nio/n8n")
    .WithEnvironment("N8N_HOST", "localhost")
    .WithEnvironment("N8N_PORT", "5678")
    .WithHttpEndpoint(port: 5678);

// Reference MCP servers in n8n
n8n.WithReference(firstCrack);
n8n.WithReference(roasterControl);

builder.Build().Run();
```

### 1.3 n8n Workflow Agent

**Workflow Structure**:
1. **Preheat Phase**
   - Start roaster drum
   - Ramp up heat to target (e.g., 180°C chamber)
   - Poll status every 1s
   - Monitor temperature rise

2. **Beans Added Detection**
   - Watch for temperature drop (T0 detection)
   - Start first crack monitoring
   - Begin roast timer

3. **Roasting Phase**
   - Monitor rate of rise (RoR)
   - Adjust heat/fan based on profile
   - LLM decision nodes for adjustments
   - Poll both APIs every 1s

4. **First Crack Response**
   - Detect FC from audio MCP
   - Report FC to roaster MCP
   - Calculate development time

5. **Development Phase**
   - Monitor development time %
   - Target: 15-20% development time
   - LLM decides when to drop

6. **Drop & Cooling**
   - Execute bean drop
   - Start cooling
   - Log roast data

**LLM Decision Nodes**:
- Use OpenAI/Anthropic for decision making
- Provide context: current temps, RoR, profile targets
- Agent suggests: heat adjustments, when to drop beans
- Safety limits enforced (max temp, max RoR)

**Roast Profiles**:
- Light roast: Drop at 200-205°C, 18-20% dev time
- Medium roast: Drop at 210-215°C, 15-18% dev time
- Dark roast: Drop at 220-225°C, 12-15% dev time

---

## Auth0 Setup

### References

- [Auth0 MCP Introduction](https://auth0.com/blog/an-introduction-to-mcp-and-authorization/)
- [Auth0 MCP Server Guide](https://auth0.com/docs/get-started/auth0-mcp-server)
- [Auth0 APIs Documentation](https://auth0.com/docs/get-started/apis)
- [Auth0 RBAC Guide](https://auth0.com/docs/manage-users/access-control/rbac)

### Tenant Configuration

#### 1. Create Auth0 API

```
Name: Coffee Roasting API
Identifier: https://coffee-roasting-api
Signing Algorithm: RS256
Allow Offline Access: No
```

#### 2. Define Scopes

**Admin Scopes (roast:admin role)**:
- `read:roaster` - Read roaster status and sensors
- `write:roaster` - Control roaster (heat, fan, drum, drop)
- `read:detection` - Read first crack detection status
- `write:detection` - Start/stop first crack detection

**Observer Scopes (roast:observer role)**:
- `read:roaster` - Read roaster status and sensors
- `read:detection` - Read first crack detection status

#### 3. Create Roles

**Roast Admin Role**:
```json
{
  "name": "Roast Admin",
  "description": "Full control of roaster and detection",
  "permissions": [
    "read:roaster",
    "write:roaster",
    "read:detection",
    "write:detection"
  ]
}
```

**Roast Observer Role**:
```json
{
  "name": "Roast Observer",
  "description": "Read-only access to status",
  "permissions": [
    "read:roaster",
    "read:detection"
  ]
}
```

#### 4. Create Machine-to-Machine Application

For n8n agent:
```
Name: n8n Roasting Agent
Type: Machine-to-Machine
Authorized API: Coffee Roasting API
Grant Type: client_credentials
Scopes: All admin scopes
```

### Scope-to-Endpoint Mapping

#### First Crack Detection MCP

| Endpoint | Method | Required Scope | Role |
|----------|--------|----------------|------|
| `/api/detect/start` | POST | `write:detection` | Admin |
| `/api/detect/stop` | POST | `write:detection` | Admin |
| `/api/detect/status` | GET | `read:detection` | Admin, Observer |

#### Roaster Control MCP

| Endpoint | Method | Required Scope | Role |
|----------|--------|----------------|------|
| `/api/roaster/start` | POST | `write:roaster` | Admin |
| `/api/roaster/stop` | POST | `write:roaster` | Admin |
| `/api/roaster/set-heat` | POST | `write:roaster` | Admin |
| `/api/roaster/set-fan` | POST | `write:roaster` | Admin |
| `/api/roaster/drop-beans` | POST | `write:roaster` | Admin |
| `/api/roaster/start-cooling` | POST | `write:roaster` | Admin |
| `/api/roaster/stop-cooling` | POST | `write:roaster` | Admin |
| `/api/roaster/report-first-crack` | POST | `write:roaster` | Admin |
| `/api/roaster/status` | GET | `read:roaster` | Admin, Observer |

### JWT Validation Implementation

#### Token Validation Flow

```python
from jose import jwt, JWTError
import requests
from functools import wraps
from flask import request, jsonify

# Configuration
AUTH0_DOMAIN = os.environ["AUTH0_DOMAIN"]  # e.g., "your-tenant.auth0.com"
AUTH0_AUDIENCE = os.environ["AUTH0_AUDIENCE"]  # e.g., "https://coffee-roasting-api"
ALGORITHMS = ["RS256"]

# Cache for JWKS (refresh periodically)
_jwks_cache = None
_jwks_cache_time = None
JWKS_CACHE_DURATION = 3600  # 1 hour

def get_jwks():
    """Fetch Auth0 public keys for JWT verification."""
    global _jwks_cache, _jwks_cache_time
    
    now = time.time()
    if _jwks_cache and (_jwks_cache_time + JWKS_CACHE_DURATION > now):
        return _jwks_cache
    
    url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    response = requests.get(url)
    response.raise_for_status()
    
    _jwks_cache = response.json()
    _jwks_cache_time = now
    return _jwks_cache

def get_token_from_header():
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]

def verify_token(token):
    """Verify JWT token and return claims.
    
    Raises:
        JWTError: If token is invalid
    """
    jwks = get_jwks()
    
    # Get the key ID from token header
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = None
    
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
            break
    
    if not rsa_key:
        raise JWTError("Unable to find appropriate key")
    
    # Verify and decode token
    payload = jwt.decode(
        token,
        rsa_key,
        algorithms=ALGORITHMS,
        audience=AUTH0_AUDIENCE,
        issuer=f"https://{AUTH0_DOMAIN}/"
    )
    
    return payload

def requires_scope(required_scope):
    """Decorator to enforce scope-based authorization.
    
    Usage:
        @app.route("/api/roaster/start", methods=["POST"])
        @requires_scope("write:roaster")
        def start_roaster():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract token
            token = get_token_from_header()
            if not token:
                return jsonify({"error": "Missing authorization token"}), 401
            
            # Verify token
            try:
                payload = verify_token(token)
            except JWTError as e:
                return jsonify({"error": f"Invalid token: {str(e)}"}), 401
            
            # Check scope
            token_scopes = payload.get("scope", "").split()
            if required_scope not in token_scopes:
                return jsonify({
                    "error": "Insufficient permissions",
                    "required_scope": required_scope
                }), 403
            
            # Store user info in request context (optional)
            request.user_id = payload.get("sub")
            request.scopes = token_scopes
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
```

#### Usage Example

```python
from flask import Flask, jsonify
from auth import requires_scope

app = Flask(__name__)

@app.route("/api/roaster/start", methods=["POST"])
@requires_scope("write:roaster")
def start_roaster():
    """Start roaster drum (requires admin role)."""
    # Token already validated by decorator
    session_manager.start_roaster()
    return jsonify({"success": True})

@app.route("/api/roaster/status", methods=["GET"])
@requires_scope("read:roaster")
def get_status():
    """Get roaster status (admin or observer)."""
    status = session_manager.get_status()
    return jsonify(status.dict())
```

### Token Acquisition (n8n)

#### Get Access Token from Auth0

```http
POST https://your-tenant.auth0.com/oauth/token
Content-Type: application/json

{
  "client_id": "<n8n-app-client-id>",
  "client_secret": "<n8n-app-client-secret>",
  "audience": "https://coffee-roasting-api",
  "grant_type": "client_credentials"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

#### n8n HTTP Request Node Configuration

```json
{
  "method": "POST",
  "url": "http://localhost:5002/api/roaster/start",
  "authentication": "genericCredentialType",
  "genericAuthType": "httpHeaderAuth",
  "headers": {
    "Authorization": "Bearer {{$credentials.auth0Token}}"
  }
}
```

### Testing Auth0 Integration

#### Test Token Validity

```bash
# Get token
export TOKEN=$(curl -s -X POST https://your-tenant.auth0.com/oauth/token \
  -H 'Content-Type: application/json' \
  -d '{
    "client_id": "<client-id>",
    "client_secret": "<client-secret>",
    "audience": "https://coffee-roasting-api",
    "grant_type": "client_credentials"
  }' | jq -r .access_token)

# Test authenticated endpoint
curl -X GET http://localhost:5002/api/roaster/status \
  -H "Authorization: Bearer $TOKEN"

# Test unauthorized endpoint (should get 403)
curl -X POST http://localhost:5002/api/roaster/start \
  -H "Authorization: Bearer $TOKEN_WITHOUT_WRITE_SCOPE"
```

#### Verify Token Claims

Decode JWT at [jwt.io](https://jwt.io) to verify:
- `iss`: `https://your-tenant.auth0.com/`
- `aud`: `https://coffee-roasting-api`
- `scope`: Contains required scopes (e.g., `read:roaster write:roaster`)
- `exp`: Expiration timestamp (future)

---

## Part 2: Production Deployment

### 2.1 Home Network Setup

**Hardware**:
- Mac or Raspberry Pi running MCP servers
- Hottop roaster connected via USB
- USB microphone for first crack detection

**MCP Servers**:
- Both servers run as systemd services (or launchd on Mac)
- HTTP APIs on localhost ports
- Cloudflare tunnel client installed

### 2.2 Cloudflare Tunnel

**Setup**:
```bash
# Install tunnel
brew install cloudflared

# Authenticate
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create coffee-roasting

# Configure tunnel
# ~/.cloudflared/config.yml
tunnel: <tunnel-id>
credentials-file: /path/to/credentials.json

ingress:
  - hostname: first-crack.yourdomain.com
    service: http://localhost:5001
  - hostname: roaster.yourdomain.com
    service: http://localhost:5002
  - service: http_status:404
```

**DNS Configuration**:
- CNAME records pointing to tunnel
- TLS handled by Cloudflare
- Auth0 JWT validation at edge (optional) or in app

### 2.3 n8n Cloud Integration

**Setup**:
- Use hosted n8n instance (n8n.cloud)
- Configure HTTP request nodes to hit tunnel URLs
- Store Auth0 credentials in n8n credentials store
- Import workflow from Part 1 (tested locally)

**Authentication**:
- n8n uses Auth0 machine-to-machine credentials
- JWT obtained from Auth0 token endpoint
- Include in Authorization header for all requests

---

## Stretch Goals

### 3.1 Custom Python Agent (Anthropic SDK)

Alternative to n8n workflow:

```python
# Using Anthropic's Agent SDK
from anthropic import Anthropic

client = Anthropic(api_key="...")

# Agent with tool use
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    tools=[
        {
            "name": "get_roaster_status",
            "description": "Get current roaster sensors and metrics",
            ...
        },
        {
            "name": "set_heat",
            "description": "Adjust roaster heat level",
            ...
        },
        # ... all MCP tools
    ],
    messages=[...]
)
```

Benefits:
- More programmatic control
- Better for custom logic and algorithms
- Can run as standalone service

### 3.2 .NET Agent

Alternative using .NET with Semantic Kernel or LangChain.NET:

```csharp
// Using Semantic Kernel
var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("gpt-4", apiKey)
    .Build();

// Register MCP tools as plugins
kernel.ImportPluginFromObject(new RoasterControlPlugin(httpClient));
kernel.ImportPluginFromObject(new FirstCrackPlugin(httpClient));

// Agent loop
await kernel.InvokePromptAsync(
    "You are a coffee roasting expert. Monitor the roaster..."
);
```

Benefits:
- Native .NET integration with Aspire
- Strong typing and tooling
- Can leverage .NET ecosystem

---

## Testing Strategy

### Part 1 Testing (Local)
1. **Unit tests** for HTTP endpoints
2. **Integration tests** with mock roaster
3. **End-to-end test** with n8n workflow and mock roaster
4. **Manual test** with real Hottop hardware

### Part 2 Testing (Production)
1. **Tunnel connectivity** tests
2. **Auth0 JWT** validation tests
3. **Latency tests** (cloud → home network)
4. **Failover scenarios** (network loss, server restart)

---

## Success Metrics

### Part 1
✅ MCP servers expose HTTP APIs with Auth0  
✅ .NET Aspire orchestrates all services  
✅ n8n workflow executes full roast cycle  
✅ Agent makes autonomous decisions via LLM  
✅ Roast completes successfully with real hardware  

### Part 2
✅ MCP servers accessible via Cloudflare tunnel  
✅ n8n Cloud can control home roaster remotely  
✅ Auth0 authentication working end-to-end  
✅ Acceptable latency (<2s round-trip)  
✅ Stable 24/7 operation  

---

## Timeline

**Part 1**: 2-3 weeks
- Week 1: HTTP APIs + Auth0 integration
- Week 2: Aspire orchestration + n8n workflow
- Week 3: Testing + refinement

**Part 2**: 1 week
- Cloudflare tunnel setup
- n8n Cloud configuration
- Production validation

**Stretch Goals**: As time permits
- Python agent: 1 week
- .NET agent: 1 week

---

## Dependencies

### New Dependencies
- `fastapi` or `flask` - HTTP server for MCP
- `uvicorn` - ASGI server
- `python-jose` - JWT validation
- `requests` - HTTP client for Auth0

### .NET Dependencies
- Aspire workload
- Aspire.Hosting.Python package
- Aspire.Hosting.NodeJs package (for n8n)

### Infrastructure
- Auth0 account (free tier sufficient)
- Cloudflare account (free tier sufficient)
- n8n Cloud account (or self-hosted)

---

## Open Questions

1. **Polling interval**: 1 second OK, or should we support configurable intervals?
2. **Auth0 setup**: Use existing tenant or create new one?
3. **n8n hosting**: Cloud vs self-hosted preference?
4. **Raspberry Pi**: Use RPi for deployment, or stick with Mac?
5. **Backup agent**: Should we implement both Python and .NET agents, or choose one?

---

**Phase 3 Status**: Ready to start after Phase 2 completion ✅
