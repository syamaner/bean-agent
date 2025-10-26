# Demo Mode Implementation Summary

## Overview

Implemented a comprehensive demo mode for both MCP servers (roaster control and first crack detection) that enables realistic visual demonstrations without requiring physical hardware or audio processing. The implementation ensures the orchestrator (n8n, agent, or LLM) is completely agnostic to whether it's running in demo or production mode.

## Key Components

### 1. Shared Scenario Configuration (`src/mcp_servers/demo_scenario.py`)

**Purpose**: Coordinates behavior between both MCP servers using a single source of truth.

**Features**:
- Predefined scenarios: `quick_roast`, `medium_roast`, `light_roast`
- Custom scenario support via environment variables
- Timeline parameters (FC trigger time, total duration)
- Temperature profile (preheat, charge drop, FC temp, end temp)
- Control response rates (heat rate factor, fan cooling factor)

**Configuration**:
```python
DEMO_MODE=true
DEMO_SCENARIO=quick_roast  # or custom env vars
```

**Scenarios**:
- **quick_roast**: 3 min total, FC at 90s (default for demos)
- **medium_roast**: 4 min total, FC at 120s (more realistic)
- **light_roast**: 3.3 min total, FC at 100s (light roast profile)

### 2. DemoRoaster Hardware (`src/mcp_servers/roaster_control/demo_roaster.py`)

**Purpose**: Realistic temperature simulation that responds to control changes.

**Features**:
- Simulates all roast phases: preheat → charge → drying → approaching FC → first crack → development → cooldown
- Dynamic response to `set_heat()` and `set_fan()` commands
- Realistic temperature curves based on phase
- Exothermic temperature rise during first crack
- Configurable via scenario parameters

**Phases**:
1. **Preheat**: Starting temperature (200°C)
2. **Charge**: Temp drop when beans added (-30°C over 3s)
3. **Drying**: Slow, steady rise (0.3°C/s base)
4. **Approaching FC**: Accelerating rise (0.5°C/s base)
5. **First Crack**: Exothermic spike (+8°C over 10s)
6. **Development**: Controlled rise to target
7. **Cooldown**: Rapid cooling (-5°C/s)

**Temperature Calculation**:
```
temp_delta = (base_rate + heat_effect - fan_effect) * dt
heat_effect = (heat% / 100) × heat_rate_factor
fan_effect = (fan% / 100) × fan_cooling_factor
```

### 3. Mock First Crack Detector (`src/mcp_servers/first_crack_detection/mock_detector.py`)

**Purpose**: Auto-triggers first crack at scenario-configured time.

**Features**:
- No audio processing in demo mode
- Monitors elapsed time since start
- Automatically triggers FC when `elapsed >= fc_trigger_time`
- Same API as real detector
- Thread-safe implementation

**Behavior**:
```python
# Initialize with scenario timing
detector = MockFirstCrackDetector(fc_trigger_time=90.0)

# Starts monitoring thread
detector.start()

# Auto-triggers at 90s
# Calls detection_callback if registered
```

### 4. Updated MCP Servers

#### Roaster Control Server (`src/mcp_servers/roaster_control/server.py`)

**Changes**:
- Added demo mode detection via `get_demo_scenario()`
- Creates `DemoRoaster` instance when demo mode enabled
- Passes scenario to hardware initialization
- Health endpoint reports `demo_mode: true`

#### FC Detection Server (`src/mcp_servers/first_crack_detection/server.py`)

**Changes**:
- Added demo mode detection via `get_demo_scenario()`
- Creates `MockFirstCrackDetector` with scenario timing
- Skips model loading in demo mode
- All tool handlers support demo mode path
- Health endpoint reports `demo_mode: true`

### 5. Docker Compose Configuration (`docker-compose.demo.yml`)

**Purpose**: Easy deployment of both MCP servers in demo mode.

**Features**:
- Two services: `roaster-control` and `first-crack-detection`
- Shared demo scenario via environment variables
- Auth0 configuration (required even in demo)
- Health checks for both services
- Network isolation

**Usage**:
```bash
docker-compose -f docker-compose.demo.yml up
```

### 6. Documentation (`DEMO_MODE.md`)

Comprehensive guide covering:
- Quick start instructions
- Scenario configurations
- Temperature simulation details
- n8n integration examples
- Troubleshooting tips
- Architecture diagram

## Key Design Decisions

### 1. Coordinated Timing via Shared Scenario

**Decision**: Both MCP servers read the same `DEMO_SCENARIO` environment variable.

**Rationale**: 
- Ensures FC detector triggers at the same time the roaster reaches FC temperature
- Prevents drift between servers
- Single source of configuration
- Easy to customize for different demo needs

### 2. Orchestrator Transparency

**Decision**: Demo mode is completely transparent to the orchestrator.

**Benefits**:
- Same API endpoints and tool schemas
- Same authentication flow
- Same response formats
- Workflows developed in demo mode work in production
- No conditional logic needed in orchestrator code

**Implementation**:
- Health endpoint includes `demo_mode` flag for debugging
- All tool responses identical to production
- Only internal implementation differs

### 3. Auth Required in Demo Mode

**Decision**: Auth0 authentication is enforced even in demo mode.

**Rationale**:
- Ensures demo deployments are secure
- Integration testing includes auth flows
- Prevents accidental exposure
- Production transition is seamless

### 4. Dynamic Control Response

**Decision**: Temperature simulation responds to heat/fan changes in real-time.

**Rationale**:
- Makes demos realistic and interactive
- Allows demonstrating control strategies
- Tests orchestrator logic for control adjustments
- Shows system responsiveness

**Implementation**:
```python
# Base rate from phase + control adjustments
temp_delta = (phase_base_rate + heat_effect - fan_effect) * dt
```

### 5. Realistic Phase Progression

**Decision**: Implement all major roast phases with characteristic behaviors.

**Rationale**:
- Demonstrates full roast lifecycle
- Tests orchestrator handling of different phases
- Showcases realistic temperature curves
- Provides educational value in demos

## Testing Scenarios

### Scenario 1: Quick Demo (3 minutes)
```bash
DEMO_SCENARIO=quick_roast
# FC at 90s, end at 180s
```
**Use case**: Quick demos, initial testing

### Scenario 2: Realistic Timing (4 minutes)
```bash
DEMO_SCENARIO=medium_roast
# FC at 120s, end at 240s
```
**Use case**: More realistic timing for detailed demos

### Scenario 3: Custom Profile
```bash
DEMO_MODE=true
DEMO_FC_TIME=105
DEMO_TOTAL_DURATION=210
DEMO_END_TEMP=205
```
**Use case**: Specific roast profiles, A/B testing

## Integration Points

### With n8n
- HTTP Request nodes with Auth0 credentials
- Poll `get_roast_status` and `get_first_crack_status`
- React to FC detection event
- Adjust controls dynamically

### With AI Agents
- Use MCP tools directly
- Same tool schemas as production
- Monitor status and make decisions
- Learn roasting strategies in safe environment

### With Dashboards
- WebSocket or polling for real-time temp
- Visualize phase transitions
- Display control settings
- Show FC detection event

## Future Enhancements

### Potential Additions
1. **Second crack simulation**: Add SC detection around 220°C
2. **Multiple bean batches**: Vary thermal properties per scenario
3. **Environmental factors**: Ambient temp, humidity effects
4. **Stalling simulation**: Model heat stalls during roast
5. **Scorching risk**: Warn if heat too high for too long
6. **Visual timeline**: Generate Artisan-style roast curves

### Performance Metrics
- Add RTF (real-time factor) reporting
- Simulation accuracy metrics
- Control latency measurements
- Memory/CPU usage tracking

### Testing Framework
- Automated scenario validation
- Regression tests for phase transitions
- Control response unit tests
- Integration test suite with both MCPs

## Deployment

### Local Development
```bash
# Set env vars
export DEMO_MODE=true
export DEMO_SCENARIO=quick_roast

# Run servers
./venv/bin/python -m src.mcp_servers.roaster_control.mcp_server
./venv/bin/python -m src.mcp_servers.first_crack_detection.server
```

### Docker Compose
```bash
# Create .env with Auth0 creds
docker-compose -f docker-compose.demo.yml up
```

### Kubernetes
- Create ConfigMap with scenario config
- Deploy as separate services
- Use service mesh for auth
- Horizontal scaling for load testing

## Verification Checklist

- [x] DemoRoaster simulates realistic temp curves
- [x] MockDetector auto-triggers at configured time
- [x] Both servers use shared scenario config
- [x] Auth0 required in demo mode
- [x] API identical to production mode
- [x] Health endpoints report demo_mode status
- [x] Temperature responds to heat/fan changes
- [x] Docker Compose configuration works
- [x] Documentation comprehensive
- [x] Orchestrator transparency maintained

## Success Criteria

✅ **Demo mode is fully functional and production-ready for:**
- Visual demonstrations to stakeholders
- n8n workflow development and testing
- AI agent integration testing
- Training and education
- Development without hardware

✅ **Key achievements:**
- Zero code changes needed in orchestrator between demo/prod
- Realistic enough for meaningful testing
- Fast enough for quick iterations (3 min roast)
- Secure with Auth0 enforcement
- Well documented with examples
