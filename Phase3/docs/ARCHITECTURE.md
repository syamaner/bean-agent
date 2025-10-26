# Phase 3: Intelligent Roasting Agent Architecture

**Last Updated**: 2025-10-26

---

## Overview

Phase 3 builds an autonomous coffee roasting agent that uses:
- **MCP Servers**: Python processes providing roaster control and first crack detection
- **n8n**: Workflow orchestration and polling loop
- **OpenAI GPT-4**: LLM-based decision making
- **Mock Hardware**: Safe testing before real roaster

**Decision**: Skip .NET Aspire initially for faster iteration. Add later for production deployment.

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                      n8n Workflow (Orchestrator)              │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Loop: Every 1 second                                   │ │
│  │                                                          │ │
│  │  1. Poll Roaster Status (HTTP)                          │ │
│  │     └─> GET /api/roaster/status                         │ │
│  │                                                          │ │
│  │  2. Poll First Crack Detection (HTTP)                   │ │
│  │     └─> GET /api/detection/status                       │ │
│  │                                                          │ │
│  │  3. Calculate Metrics                                   │ │
│  │     - Rate of Rise (RoR): ΔTemp / 60s                   │ │
│  │     - Development Time: Time since first crack          │ │
│  │     - Development %: (dev_time / total_time) * 100      │ │
│  │                                                          │ │
│  │  4. Safety Checks                                       │ │
│  │     - Bean temp < 205°C? (hard stop)                    │ │
│  │     - RoR < 10°C/min? (stall detection)                 │ │
│  │     - Data fresh < 4s? (watchdog)                       │ │
│  │                                                          │ │
│  │  5. OpenAI Decision (if needed)                         │ │
│  │     └─> Send context → Get action                       │ │
│  │                                                          │ │
│  │  6. Execute Control Action (if any)                     │ │
│  │     └─> POST /api/roaster/set-heat                      │ │
│  │     └─> POST /api/roaster/set-fan                       │ │
│  │                                                          │ │
│  │  7. Log Results                                         │ │
│  │     └─> Store metrics, decisions, actions               │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
          │                                  │
          ▼                                  ▼
┌─────────────────────┐        ┌─────────────────────────┐
│  Roaster Control    │        │  First Crack Detection  │
│  MCP Server         │        │  MCP Server             │
│                     │        │                         │
│  Port: 5002         │        │  Port: 5001             │
│  Auth: Auth0 M2M    │        │  Auth: Auth0 M2M        │
│                     │        │                         │
│  Tools:             │        │  Tools:                 │
│  - read_status      │        │  - get_status           │
│  - start_roaster    │        │  - start_detection      │
│  - stop_roaster     │        │  - stop_detection       │
│  - set_heat         │        │                         │
│  - set_fan          │        │  Audio Sources:         │
│  - drop_beans       │        │  - USB microphone       │
│  - start_cooling    │        │  - Built-in mic         │
│  - stop_cooling     │        │  - Audio file (test)    │
└─────────┬───────────┘        └───────────┬─────────────┘
          │                                │
          ▼                                ▼
┌─────────────────────┐        ┌─────────────────────────┐
│  MockRoaster        │        │  FirstCrackDetector     │
│  (Phase 3.1)        │        │  (Audio ML Model)       │
│                     │        │                         │
│  Simulates:         │        │  AST Model:             │
│  - Temperature      │        │  - 10s windows          │
│  - Heat/fan control │        │  - Pop confirmation     │
│  - Realistic curves │        │  - Confidence threshold │
└─────────────────────┘        └─────────────────────────┘
          │                                
          ▼                                
┌─────────────────────┐                    
│  HottopRoaster      │                    
│  (Phase 3.2)        │                    
│                     │                    
│  Real Hardware:     │                    
│  - Serial/USB conn  │                    
│  - pyhottop library │                    
│  - Live sensors     │                    
└─────────────────────┘                    
```

---

## Component Details

### n8n Workflow

**Nodes:**
1. **Interval Trigger** - Every 1 second
2. **HTTP Request: Get Roaster Status** - Poll MCP server
3. **HTTP Request: Get First Crack Status** - Poll MCP server
4. **Function: Calculate Metrics** - JavaScript code node
5. **IF: Safety Checks** - Temperature, RoR, watchdog
6. **IF: Decision Needed?** - Phase change, FC detected, etc.
7. **HTTP Request: OpenAI** - LLM decision making
8. **Switch: Action Type** - Route based on decision
9. **HTTP Request: Set Heat** - Execute control
10. **HTTP Request: Set Fan** - Execute control
11. **HTTP Request: Drop Beans** - End roast
12. **Log: Store Results** - Write to file/DB

**State Management:**
- Store previous readings in workflow variables
- Track roast start time, FC time
- Maintain control history

### OpenAI Integration

**Model**: GPT-4 (or GPT-4-turbo for faster responses)

**Prompt Structure**:
```
You are an expert coffee roaster assistant. Based on current roast data, 
recommend control adjustments.

Current State:
- Bean Temperature: 185°C
- Chamber Temperature: 190°C
- Rate of Rise: 7.2°C/min
- Time since start: 8:45
- First Crack: Not detected yet
- Heat: 75%
- Fan: 45%

Roast Profile:
- Target: Light roast (drop at 195°C)
- Target development: 18% (2:30 after FC)
- First crack expected: 9-10 minutes

Safety Limits:
- Max temp: 205°C
- Max RoR: 10°C/min
- Min RoR: 3°C/min (stall detection)

Recommend ONE of:
1. CONTINUE (no changes)
2. REDUCE_HEAT <percentage>
3. INCREASE_HEAT <percentage>
4. REDUCE_FAN <percentage>
5. INCREASE_FAN <percentage>
6. DROP_BEANS (end roast)

Respond in JSON: {"action": "REDUCE_HEAT", "value": 60, "reason": "..."}
```

---

## Data Flow

### Roaster Status Response
```json
{
  "status": "roasting",
  "session_active": true,
  "sensors": {
    "bean_temp": 185.5,
    "chamber_temp": 190.2,
    "heat_level": 75,
    "fan_speed": 45,
    "drum_running": true,
    "cooling_running": false
  },
  "first_crack": {
    "detected": false,
    "timestamp": null
  },
  "metrics": {
    "roast_time_seconds": 525,
    "roast_time": "8:45"
  },
  "timestamp": "2025-10-26T10:30:00Z"
}
```

### First Crack Detection Response
```json
{
  "detection_active": true,
  "first_crack_detected": false,
  "first_crack_time_relative": null,
  "first_crack_time_utc": null,
  "confidence": 0.0,
  "audio_source": "usb_microphone",
  "recent_pops": 0,
  "detection_config": {
    "threshold": 0.5,
    "min_pops": 3,
    "confirmation_window": 30.0
  }
}
```

### Control Action Request
```json
{
  "level": 60
}
```

---

## Phase 3 Execution Plan

### Phase 3.1: Mock Hardware Testing (This Week)
- ✅ MCP servers running as Python processes
- 🟡 n8n installed and configured
- 🟡 Basic workflow: poll → log
- ⚪ Add OpenAI decision node
- ⚪ Test control execution
- ⚪ Verify safety interlocks

### Phase 3.2: Real Hardware (Next Week)
- ⚪ Connect Hottop roaster (USB serial)
- ⚪ Set `ROASTER_MOCK_MODE=0`
- ⚪ Connect USB microphone
- ⚪ Start first crack detection
- ⚪ Execute supervised roast
- ⚪ Validate autonomous roast

### Phase 3.3: Production Deployment (Later)
- ⚪ Add .NET Aspire orchestration
- ⚪ Containerize MCP servers
- ⚪ Cloudflare Tunnel for remote access
- ⚪ n8n Cloud integration
- ⚪ Monitoring and alerting

---

## Safety Design

**Three Layers of Safety:**

1. **Hard Limits** (n8n workflow)
   - Bean temp ≥ 205°C → Emergency stop
   - RoR > 10°C/min → Reduce heat to 50%
   - Data age > 4s → Stop actions, alert

2. **LLM Guardrails** (OpenAI prompt)
   - Never suggest heat > 90%
   - Never suggest fan < 20% after FC
   - Always verify action makes sense

3. **MCP Server Validation** (Python)
   - Bounds checking on all inputs
   - Rate limiting on control changes
   - Hardware state verification

**Emergency Stop Pathway:**
```
Safety violation detected → Log error → Stop workflow → 
Drop beans → Start cooling → Alert user
```

---

## Testing Strategy

### Mock Hardware Tests
1. **Normal Roast Simulation**
   - Verify temperature curves
   - Check FC detection triggers
   - Validate development phase control

2. **Edge Cases**
   - Stalled roast (low RoR)
   - Runaway temperature
   - Late first crack
   - Early first crack

3. **Safety Triggers**
   - Max temp exceeded
   - Data timeout
   - Invalid sensor readings

### Real Hardware Tests
1. **Supervised Roasts**
   - Human operator monitoring
   - Manual override ready
   - Compare to manual profile

2. **Autonomous Roasts**
   - Different bean types
   - Light/medium/dark profiles
   - Verify consistency

---

## Success Criteria

**Phase 3.1 Complete When:**
- ✅ n8n workflow polls both MCP servers
- ✅ OpenAI makes control decisions
- ✅ Mock hardware responds correctly
- ✅ Safety interlocks trigger properly
- ✅ End-to-end test completes successfully

**Phase 3.2 Complete When:**
- ✅ Real roaster connected and controlled
- ✅ First crack detected from live audio
- ✅ Autonomous roast completes safely
- ✅ Target profile achieved (±5°C, ±2% dev time)

---

## Next Steps

1. Install n8n locally
2. Create basic polling workflow
3. Test MCP server connectivity
4. Add OpenAI decision node
5. Implement control actions
6. Test with mock hardware
