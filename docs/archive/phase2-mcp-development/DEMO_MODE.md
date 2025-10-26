# Demo Mode for MCP Servers

This document explains how to run the coffee roaster MCP servers in **demo mode** for visual demonstrations, testing with n8n, or integration showcases without requiring physical hardware or audio processing.

## Overview

Demo mode provides:
- **Realistic temperature simulation** that progresses through all roast phases
- **Automatic first crack detection** at configured times
- **Dynamic response** to heat/fan control changes
- **Coordinated behavior** between both MCP servers using shared scenarios
- **Full Auth0 authentication** (required even in demo mode)
- **Identical API** to production mode - orchestrators can't tell the difference

## Quick Start

### 1. Set Up Environment

Create a `.env` file with Auth0 credentials:

```bash
# Auth0 configuration (required)
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://your-api-audience
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret

# Demo mode
DEMO_MODE=true
DEMO_SCENARIO=quick_roast
```

### 2. Run with Docker Compose

```bash
docker-compose -f docker-compose.demo.yml up
```

This starts both MCP servers:
- **Roaster Control**: http://localhost:8001
- **First Crack Detection**: http://localhost:8002

### 3. Test the APIs

Get an Auth0 token and test:

```bash
# Get token
TOKEN=$(curl --request POST \
  --url "https://${AUTH0_DOMAIN}/oauth/token" \
  --header 'content-type: application/json' \
  --data '{
    "client_id":"'"${AUTH0_CLIENT_ID}"'",
    "client_secret":"'"${AUTH0_CLIENT_SECRET}"'",
    "audience":"'"${AUTH0_AUDIENCE}"'",
    "grant_type":"client_credentials"
  }' | jq -r '.access_token')

# Check health
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/health

# Start roaster
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8001/tools/start_roaster

# Set heat and fan
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"percent": 70}' \
  http://localhost:8001/tools/set_heat

# Get status (watch temperature rise)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/tools/get_roast_status

# Start FC detection
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8002/tools/start_first_crack_detection

# Check FC status (will auto-detect at configured time)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8002/tools/get_first_crack_status
```

## Scenarios

Three predefined scenarios are available:

### Quick Roast (default)
- **Duration**: 3 minutes total
- **First crack**: 90 seconds
- **End temp**: 210°C
- **Best for**: Quick demos and testing

```bash
DEMO_SCENARIO=quick_roast
```

### Medium Roast
- **Duration**: 4 minutes
- **First crack**: 2 minutes
- **End temp**: 215°C
- **Best for**: More realistic timing

```bash
DEMO_SCENARIO=medium_roast
```

### Light Roast
- **Duration**: 3.3 minutes
- **First crack**: 100 seconds
- **End temp**: 205°C
- **Best for**: Light roast profiles

```bash
DEMO_SCENARIO=light_roast
```

## Custom Scenarios

Override individual parameters:

```bash
DEMO_MODE=true
DEMO_FC_TIME=120              # FC at 2 minutes
DEMO_TOTAL_DURATION=240       # 4 minute total
DEMO_PREHEAT_TEMP=200         # Starting temp
DEMO_CHARGE_DROP=30           # Temp drop on charge
DEMO_FC_TEMP=196              # FC temperature
DEMO_FC_RISE=8                # FC exothermic rise
DEMO_END_TEMP=210             # Target end temp
DEMO_HEAT_RATE=0.3            # Heat response factor
DEMO_FAN_COOLING=0.15         # Fan cooling factor
```

## Temperature Simulation

The DemoRoaster simulates realistic roast phases:

1. **Preheat** (200°C): Initial state
2. **Charge** (drops 30°C): Beans added, temp drops
3. **Drying** (slow rise): Moisture evaporation
4. **Approaching FC** (faster rise): Building energy
5. **First Crack** (exothermic +8°C): Beans crack, temp spikes
6. **Development** (controlled): Develop flavor to target
7. **Cooldown** (rapid drop): After bean drop

### Dynamic Control Response

The simulation responds to control changes:

- **Heat %**: Higher heat → faster temp rise
  - Formula: `base_rate + (heat% × 0.3°C/sec)`
- **Fan %**: Higher fan → cooling effect
  - Formula: `base_rate - (fan% × 0.15°C/sec)`
- **Cooling mode**: Rapid cooling at -5°C/sec

### Example Timeline (quick_roast)

| Time | Phase | Temp | Event |
|------|-------|------|-------|
| 0s | Charge | 200°C → 170°C | Beans added, temp drops |
| 10s | Drying | 175°C | Slow rise begins |
| 50s | Approaching FC | 190°C | Accelerating |
| 90s | **First Crack** | 196°C → 204°C | **FC detected**, exothermic rise |
| 120s | Development | 207°C | Approaching target |
| 180s | End | 210°C | Drop beans |

## Integration with n8n

### Workflow Example

1. **Start Roast**
   - Call `start_roaster` on roaster MCP
   - Set initial heat/fan (e.g., 70%/30%)
   - Call `start_first_crack_detection` on FC MCP

2. **Monitor Loop** (every 5 seconds)
   - Call `get_roast_status` → track temperature
   - Call `get_first_crack_status` → check for FC

3. **On First Crack Detected**
   - Call `report_first_crack` on roaster MCP
   - Adjust heat/fan for development phase
   - Continue monitoring

4. **End Roast**
   - Call `drop_beans` → cooling phase
   - Call `stop_first_crack_detection`
   - Save roast data

### n8n Node Configuration

For HTTP Request nodes:

```json
{
  "method": "POST",
  "url": "http://localhost:8001/tools/{{ $node[\"Tool Name\"].json[\"tool\"] }}",
  "authentication": "genericCredentialType",
  "genericAuthType": "oAuth2Api",
  "sendHeaders": true,
  "headerParameters": {
    "parameters": [
      {
        "name": "Content-Type",
        "value": "application/json"
      }
    ]
  }
}
```

## Orchestrator Transparency

The orchestrator (n8n, agent, or LLM) **cannot tell** it's in demo mode:
- Same API endpoints and tool schemas
- Same response formats
- Same authentication requirements
- Same timing (just compressed)

This means:
- ✅ Develop workflows in demo mode
- ✅ Test integration flows
- ✅ Demo to stakeholders
- ✅ Switch to production without code changes

## Troubleshooting

### Servers not starting

Check Auth0 configuration:
```bash
docker-compose -f docker-compose.demo.yml logs
```

### FC not detecting

Verify scenario timing:
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8002/health
# Check "demo_mode": true and FC trigger time
```

### Temperature not changing

Ensure drum is started:
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/tools/start_roaster
```

## Architecture

```
┌─────────────────────────────────────────┐
│         Agent / n8n / LLM               │
│         (orchestrator)                  │
└────────────┬───────────────┬────────────┘
             │               │
             │ Tools         │ Tools
             │ (with Auth)   │ (with Auth)
             ▼               ▼
    ┌────────────────┐  ┌────────────────┐
    │  Roaster MCP   │  │   FC MCP       │
    │  (Port 8001)   │  │  (Port 8002)   │
    └────────┬───────┘  └────────┬───────┘
             │                   │
             │ Scenario          │ Scenario
             │ (env vars)        │ (env vars)
             ▼                   ▼
    ┌────────────────┐  ┌────────────────┐
    │  DemoRoaster   │  │  MockDetector  │
    │  (temp sim)    │  │  (auto-trigger)│
    └────────────────┘  └────────────────┘
```

Both servers read the same `DEMO_SCENARIO` config, ensuring coordinated behavior.

## Security Note

**Auth0 authentication is ALWAYS required**, even in demo mode. This ensures:
- Demo deployments remain secure
- Integration testing includes auth flows
- Production transition is seamless

Never disable auth, even for demos.

## Next Steps

- Set up n8n workflow using demo mode
- Test with different scenarios
- Create visual dashboards tracking temp/status
- Build automated roast profiles
- Switch to production hardware when ready
