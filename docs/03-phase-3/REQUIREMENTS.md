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
- Two roles: `roast:admin` and `roast:observer`
- Admin: Full access to all tools
- Observer: Read-only access to status endpoints
- JWT validation on every request
- Token introspection with Auth0 Management API

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
