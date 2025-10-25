# Phase 2 Implementation Plan: MCP Tools & Integration

## Overview
Goal: Integrate the first crack detection model with roaster control via MCP servers and an orchestrator, enabling closed-loop roasting assistance with safety guarantees.

Timeline: 1–2 weeks

Success Criteria:
- End-to-end loop runs locally with mock mode and with hardware-in-the-loop.
- No missed first-crack events (recall 100%); <5% false positives after temporal filtering.
- Roaster controls adjust safely within configured bounds; emergency-stop path proven.
- All components observable (logs, metrics) and reproducible (configs, versions).

---

## Architecture
Components:
- Audio Detection MCP Server (Python): wraps AST model inference and event aggregation.
- Roaster Control MCP Server (Python): wraps pyhottop for read/write of roaster state.
- Orchestrator (n8n or MCP client workflow): queries both servers, computes actions, applies controls.
- Shared schema/contracts: stable tool names and JSON payloads.

Proposed repo layout additions:
```
tools/
  mcp/
    audio_server/
      server.py
      config.yaml
      README.md
      tests/
    roaster_server/
      server.py
      config.yaml
      README.md
      tests/
  orchestrator/
    n8n/
      flows/
      README.md
docs/
  PHASE2_DESIGN.md
  INTEGRATION_TESTS.md
  OPERATIONS.md
```

Dependencies (add to requirements or dedicated files in each server):
- mcp (Python SDK)
- sounddevice or pyaudio (audio capture) and soundfile
- numpy, librosa (preproc)
- pyserial (if required by pyhottop)
- pyhottop (as submodule or pip if published)

**Environment Management**: See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for virtual environment setup.
- Always activate the virtual environment before running Python scripts: `source venv/bin/activate`
- Update requirements.txt after installing new dependencies: `pip freeze > requirements.txt`
- Each MCP server may have its own requirements.txt in its directory

---

## Contracts (MCP Tool Specs)
Common envelopes:
- All responses include: `ok` (bool), `data`, `error` (nullable string), `ts` (RFC3339).
- Numerical units documented (Celsius, %, seconds).

**Roasting Phase Model**:
- **Phases** (durations): `idle`, `drying` (~charge to 150°C), `maillard` (~150°C to FC), `development` (FC to drop), `cooling` (post-drop)
- **Events** (timestamps): `charge` (beans dropped), `first_crack` (FC detected), `drop` (beans ejected)
- **Phase percentages**: Each phase duration as % of total roast time
  - `development_pct` = (development_sec / elapsed_sec) * 100
  - **Target**: 15-20% for optimal light roast
  - **Control strategy**: If temp rising too fast after FC (<195°C but dev_pct < 15%), reduce heat and increase fan to stretch development phase

Audio Detection Server (namespace: audio):
- Tool: audio.start_detection
  - Input: `{ "source": "file|microphone", "path": string|null, "checkpoint_path": string, "window_size": number, "overlap": number, "threshold": number, "min_pops": number, "confirmation_window": number }`
  - Output: `{ "session_id": string }`
  - Notes: Creates a FirstCrackDetector instance, calls `.start()`, returns session UUID. For file input, `path` is required. For microphone input, path is null and uses USB device.
- Tool: audio.get_status
  - Input: `{ "session_id": string }`
  - Output: `{ "is_running": bool, "elapsed_time": string|null, "first_crack_detected": bool, "first_crack_time": string|null }`
  - Notes: Polls detector state (`.is_first_crack()`, `.get_elapsed_time()`, `.is_running`). Times are in "MM:SS" format.
- Tool: audio.stop_detection
  - Input: `{ "session_id": string }`
  - Output: `{ "success": bool }`
  - Notes: Calls `.stop()` on detector instance and cleans up.
- Tool: audio.health
  - Input: `{}`
  - Output: `{ "model": string, "device": "cpu|mps|cuda", "ready": bool }`
- Notes: MCP server maintains dict of `{session_id: FirstCrackDetector}` instances. Client starts session, polls status every 2-5s, stops when done. Background threads handled by Python class.

Roaster Control Server (namespace: roaster):
- Tool: roaster.get_state
  - Input: `{}`
  - Output: `{ "bean_temp_c": number, "env_temp_c": number, "fan_pct": number, "heat_pct": number, "elapsed_sec": number, "phase": "idle|drying|maillard|development|cooling", "events": { "charge_ts": number|null, "first_crack_ts": number|null, "drop_ts": number|null }, "phase_durations": { "drying_sec": number|null, "maillard_sec": number|null, "development_sec": number|null }, "phase_percentages": { "drying_pct": number|null, "maillard_pct": number|null, "development_pct": number|null } }`
  - Notes:
    - `phase`: Current roasting phase (duration-based)
    - `elapsed_sec`: Seconds since charge event
    - `events`: Key event timestamps (epoch seconds)
      - `charge_ts`: Moment beans dropped (roast start)
      - `first_crack_ts`: First crack detected
      - `drop_ts`: Beans ejected for cooling
    - `phase_durations`: Computed phase durations in seconds
    - `phase_percentages`: Phase durations as % of total roast time (since charge)
      - **Critical**: `development_pct` should be 15-20% for optimal roast
      - Used to adjust controls: if temp rising too fast after FC, reduce heat/increase fan to stretch development phase before hitting target drop temp (~195°C)
    - Phase transitions: idle → drying (at charge) → maillard (at ~150°C) → development (at first_crack) → cooling (at drop)
- Tool: roaster.set_controls
  - Input: `{ "fan_pct": number|null, "heat_pct": number|null }`
  - Output: `{ "applied": { "fan_pct": number|null, "heat_pct": number|null } }`
- Tool: roaster.actions
  - Input: `{ "cmd": "stop|drop_and_cool" }`
  - Output: `{ "cmd": string, "accepted": bool }`
- Tool: roaster.health
  - Input: `{}`
  - Output: `{ "port": string, "connected": bool, "mock": bool }`

---

## Milestones

### M1: Design & Scaffolding (Day 1)
- Finalize tool contracts (above) and configuration format.
- Create server skeletons, configs, and READMEs.
- Provide mock mode for both servers.
Acceptance: `mcp list-tools` shows expected tools; health endpoints return ready in mock mode.

### M2: Audio Detection MCP Server (Days 1–3)
- Load final model from `experiments/final_model/model.pt` and associated preprocessing.
- Implement windowing (default: 10s windows, 5s hop) and temporal NMS/aggregation (`min_gap_sec` ≥ 1.0).
- Add thresholding + consecutive-window debouncing to reduce FPs.
- CLI for file input and (optional) mic capture.
- Health checks and graceful error handling.
Acceptance: On 4 known roasts, detects all first-crack segments; RTF ≥ 50x; configurable thresholds persist via config.

### M3: Roaster Control MCP Server (Days 2–4)
- Integrate `pyhottop`; add connection auto-detect and `--mock` fallback.
- Implement state polling, control setting with rate limits (fan/heat step max per 2s), and safety bounds (fan 0–100, heat 0–100).
- Calculate and return `phase_durations` (seconds) and `phase_percentages` (% of elapsed time) based on event timestamps.
- Implement guarded actions: emergency stop, drop-and-cool require `confirm=true` flag unless `safety_override`.
Acceptance: In mock mode, state evolves deterministically with accurate phase percentages; in hardware mode, read/write verified on bench.

### M4: Orchestrator Workflow (Days 4–6)
- n8n flow or lightweight MCP client loop implementing initial policy:
  - Start audio detection session at roast start (audio.start_detection with source="microphone").
  - Poll roaster state and audio status at 2s intervals (roaster.get_state, audio.get_status).
  - On first crack detection: update roaster state with `first_crack_ts`, transition phase to `development`.
  - Control policy: at FC event, reduce heat by 20–30%, increase fan by 10–20%.
  - During development phase: monitor `development_pct` from `phase_percentages`.
    - If temp rising too fast (RoR > target_max) and dev_pct < 15%, aggressively adjust controls to stretch development phase.
    - Stop when 15% ≤ development_pct ≤ 20% and 195°C ≤ bean_temp < 200°C.
  - Cleanup: call audio.stop_detection at roast end.
- Configurable parameters (heat_drop_pct, fan_raise_pct, target_ror, target temps); dry-run mode (no writes).
Acceptance: Simulated and mock runs produce expected adjustments; logs show phase transitions, percentages, and control decisions.

### M5: Integration & Safety (Days 6–7)
- System-level safety: max temp ceiling, maximum RoR, action cooldowns, watchdog timeouts, heartbeat between components.
- Emergency-stop tested end-to-end.
Acceptance: Fault injection tests pass; no unsafe commands issued under simulated anomalies.

### M6: Observability (Day 7)
- Structured logs (JSON) with correlation IDs; rotating log files.
- Metrics: detection count, FP rate, control changes, temps, RoR, phase percentages (esp. development_pct), latency.
- Data export: per-roast JSON/CSV with full state history (temps, phases, percentages, events) + raw detection traces.
Acceptance: Sample roast log and metrics dashboard produced; development_pct plotted over time.

### M7: Field Validation (Days 8–10)
- Test plan for 3–5 roasts; collect ground truth timestamps.
- Post-hoc analysis to tune thresholds and min_gap.
Acceptance: 100% recall, FP <5% on field data; finalized parameters documented.

---

## Implementation Details

Configuration (per server):
```yaml
# path=null start=null
model_checkpoint: experiments/final_model/model.pt
sample_rate: 16000  # match model requirements
window_sec: 10.0
hop_sec: 5.0
threshold: 0.5
min_gap_sec: 1.0
device: auto  # mps|cuda|cpu
logging:
  level: INFO
  json: true
```

Audio server skeleton:
```python path=null start=null
from mcp import Server
import uuid
from first_crack_detector import FirstCrackDetector

srv = Server(name="audio")
active_sessions = {}  # session_id -> FirstCrackDetector

@srv.tool("audio.start_detection")
def start_detection(source: str, path: str|None, checkpoint_path: str, 
                    window_size: float = 10.0, overlap: float = 0.5, 
                    threshold: float = 0.5, min_pops: int = 3, 
                    confirmation_window: float = 30.0):
    # Create detector instance
    if source == "file":
        detector = FirstCrackDetector(audio_file=path, checkpoint_path=checkpoint_path,
                                      window_size=window_size, overlap=overlap,
                                      threshold=threshold, min_pops=min_pops,
                                      confirmation_window=confirmation_window)
    else:  # microphone
        detector = FirstCrackDetector(use_microphone=True, checkpoint_path=checkpoint_path,
                                      window_size=window_size, overlap=overlap,
                                      threshold=threshold, min_pops=min_pops,
                                      confirmation_window=confirmation_window)
    
    detector.start()
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = detector
    return {"ok": True, "data": {"session_id": session_id}, "error": None}

@srv.tool("audio.get_status")
def get_status(session_id: str):
    detector = active_sessions.get(session_id)
    if not detector:
        return {"ok": False, "data": None, "error": "Session not found"}
    
    result = detector.is_first_crack()
    return {
        "ok": True, 
        "data": {
            "is_running": detector.is_running,
            "elapsed_time": detector.get_elapsed_time(),
            "first_crack_detected": result is not False,
            "first_crack_time": result[1] if result is not False else None
        },
        "error": None
    }

@srv.tool("audio.stop_detection")
def stop_detection(session_id: str):
    detector = active_sessions.get(session_id)
    if not detector:
        return {"ok": False, "data": {"success": False}, "error": "Session not found"}
    
    detector.stop()
    del active_sessions[session_id]
    return {"ok": True, "data": {"success": True}, "error": None}

@srv.tool("audio.health")
def health():
    return {"ok": True, "data": {"model": "ast", "device": "mps", "ready": True}, "error": None}

if __name__ == "__main__":
    srv.run()
```

Roaster server skeleton:
```python path=null start=null
from mcp import Server

srv = Server(name="roaster")

@srv.tool("roaster.get_state")
def get_state():
    # query pyhottop or mock
    return {
        "ok": True, 
        "data": {
            "bean_temp_c": 175.2, 
            "env_temp_c": 195.0, 
            "fan_pct": 30, 
            "heat_pct": 80, 
            "elapsed_sec": 420, 
            "phase": "maillard",
            "events": {
                "charge_ts": 1729292400,  # example epoch timestamp
                "first_crack_ts": None,
                "drop_ts": None
            },
            "phase_durations": {
                "drying_sec": 240,
                "maillard_sec": None,  # still in progress
                "development_sec": None
            },
            "phase_percentages": {
                "drying_pct": 57.1,  # 240/420 * 100
                "maillard_pct": None,  # still in progress
                "development_pct": None
            }
        }, 
        "error": None
    }

@srv.tool("roaster.set_controls")
def set_controls(fan_pct: float|None = None, heat_pct: float|None = None):
    # clamp, rate-limit, apply
    return {"ok": True, "data": {"applied": {"fan_pct": fan_pct, "heat_pct": heat_pct}}, "error": None}

@srv.tool("roaster.actions")
def actions(cmd: str, confirm: bool = False):
    # guard sensitive ops
    return {"ok": True, "data": {"cmd": cmd, "accepted": confirm}, "error": None}

if __name__ == "__main__":
    srv.run()
```

Decision policy (pseudo):
```python path=null start=null
# Start detection at roast beginning
session = audio.start_detection(source="microphone", checkpoint_path="experiments/final_model/model.pt")
session_id = session['session_id']

# Main control loop
while True:
    state = roaster.get_state()
    audio_status = audio.get_status(session_id=session_id)
    
    # React to first crack detection
    if audio_status['first_crack_detected'] and state['events']['first_crack_ts'] is None:
        # Mark first crack timestamp in roaster state
        state['events']['first_crack_ts'] = now
        
        # Adjust controls for development phase
        target_heat = max(0, state['heat_pct'] - heat_drop_pct)  # reduce 20-30%
        target_fan = min(100, state['fan_pct'] + fan_raise_pct)   # increase 10-20%
        roaster.set_controls(fan_pct=target_fan, heat_pct=target_heat)

# Maintain development window during development phase
if state['phase'] == 'development':
    dev_pct = state['phase_percentages']['development_pct']
    bean_temp = state['bean_temp_c']
    
    # Calculate RoR (rate of rise) from recent temp history
    ror = calculate_ror(temp_history, window_sec=60)
    
    # If temp rising too fast and dev% still too low, stretch development phase
    if bean_temp < 195 and dev_pct < 15 and ror > target_ror_max:
        # Aggressively slow down: reduce heat, increase fan
        target_heat = max(0, state['heat_pct'] - 10)
        target_fan = min(100, state['fan_pct'] + 10)
        roaster.set_controls(fan_pct=target_fan, heat_pct=target_heat)
    
    # Drop beans when development window achieved and temp at target
    if 15 <= dev_pct <= 20 and 195 <= bean_temp < 200:
        roaster.actions(cmd="drop_and_cool", confirm=True)
    
    # Safety: force drop if temp exceeds 200C regardless of dev%
    if bean_temp >= 200:
        roaster.actions(cmd="drop_and_cool", confirm=True)
        break
    
    time.sleep(2)  # Poll every 2 seconds

# Cleanup
audio.stop_detection(session_id=session_id)
```

Safety rules:
- Clamp: 0 ≤ fan_pct, heat_pct ≤ 100; max delta per 2s (e.g., 15%).
- Hard ceilings: bean_temp_c ≤ 205; env_temp_c ≤ 230; watchdog if stale data > 4s.
- Emergency path: any component can invoke `roaster.actions {cmd: "stop"}`; operator can always override.

---

## Testing Strategy
- Unit tests: tool input validation, aggregation logic, clamping/rate limits.
- Integration tests (mock mode): end-to-end loop with scripted audio and simulated roaster.
- Hardware tests: bench with roaster unplugged heater (if possible) or low-risk dry-run; verify reads/writes.
- Performance: RTF, per-call latency, orchestrator loop jitter.

Artifacts:
- docs/INTEGRATION_TESTS.md
- Sample logs and metrics in `experiments/integration/`.

---

## Operations & Observability
- Structured logging (JSON) with `component`, `corr_id`, `roast_id`.
- Metrics: Prometheus textfile or CSV per roast; simple plots script for analysis.
- Data retention: store detections, states, control actions per roast.

---

## Risks & Mitigations
- Model FPs in noisy environments → stricter threshold + min_gap; microphone placement guidance.
- pyhottop connection instability → retries, backoff, explicit health; mock fallback.
- Timing drift → monotonic clocks, heartbeat validation.
- Safety violations → clamps, rate limits, watchdog, manual override.

---

## Deliverables
- tools/mcp/audio_server with working MCP server and README.
- tools/mcp/roaster_server with working MCP server and README.
- Orchestrator flow and dry-run demo.
- docs/PHASE2_DESIGN.md, docs/INTEGRATION_TESTS.md, docs/OPERATIONS.md.
- Field validation report with tuned parameters.

---

## Next Steps
- Scaffold both MCP servers and commit configs (mock mode first).
- Implement audio aggregation; validate against existing 4 roasts.
- Connect pyhottop in controlled bench; complete orchestrator dry-run.
- Prepare test plan and schedule field validation.
