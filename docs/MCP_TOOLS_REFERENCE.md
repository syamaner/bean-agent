# MCP Tools Reference

This document describes the MCP (Model Context Protocol) tools exposed by the coffee-roasting project's MCP servers.

## Overview

The project exposes two MCP servers:
1. **First Crack Detection Server** - Monitors audio for first crack events during coffee roasting
2. **Roaster Control Server** - Controls physical roaster hardware (heat, fan, drum, cooling)

---

## First Crack Detection Server

**Server Name:** `first-crack-detection`  
**Purpose:** Real-time audio monitoring to detect first crack during coffee roasting  
**Transport:** stdio (JSON-RPC over stdin/stdout)

### Tools

#### `start_first_crack_detection`
Start first crack detection monitoring with specified audio source.

**Parameters:**
- `audio_source_type` (required): `"audio_file"` | `"usb_microphone"` | `"builtin_microphone"`
- `audio_file_path` (conditional): Path to audio file (required if `audio_source_type` is `"audio_file"`)
- `detection_config` (optional):
  - `threshold` (float, 0.0-1.0): Detection threshold (default: 0.5)
  - `min_pops` (int, ≥1): Minimum pops to confirm first crack (default: 3)
  - `confirmation_window` (float, ≥1.0): Confirmation window in seconds (default: 30.0)

**Returns:**
```json
{
  "status": "success",
  "result": {
    "session_state": "started",
    "session_id": "uuid",
    "started_at_utc": "2025-01-25T12:00:00Z",
    "started_at_local": "2025-01-25T04:00:00-08:00",
    "audio_source": "usb_microphone",
    "audio_source_details": "Device name or path"
  }
}
```

**Error Codes:**
- `MODEL_NOT_FOUND` - Model checkpoint not found
- `FILE_NOT_FOUND` - Audio file not found
- `MICROPHONE_NOT_AVAILABLE` - Microphone device not available
- `INVALID_AUDIO_SOURCE` - Invalid audio source type
- `SESSION_ALREADY_ACTIVE` - Session already running

**Example:**
```json
{
  "audio_source_type": "usb_microphone",
  "detection_config": {
    "threshold": 0.6,
    "min_pops": 5,
    "confirmation_window": 45.0
  }
}
```

---

#### `get_first_crack_status`
Get current first crack detection status.

**Parameters:** None

**Returns:**
```json
{
  "status": "success",
  "result": {
    "session_active": true,
    "session_id": "uuid",
    "elapsed_time": "04:32",
    "first_crack_detected": true,
    "first_crack_time_relative": "04:15",
    "first_crack_time_utc": "2025-01-25T12:04:15Z",
    "first_crack_time_local": "2025-01-25T04:04:15-08:00",
    "confidence": {
      "pops_detected": 5,
      "confirmation_window": 30.0
    },
    "started_at_utc": "2025-01-25T12:00:00Z",
    "started_at_local": "2025-01-25T04:00:00-08:00",
    "audio_source": "usb_microphone"
  }
}
```

**Error Codes:**
- `DETECTION_THREAD_CRASHED` - Detection thread has crashed

**Usage Notes:**
- Call periodically (e.g., every 5-10s) to poll for first crack
- `first_crack_detected` becomes `true` once confirmed
- `elapsed_time` and `first_crack_time_relative` are in MM:SS format
- Timestamps include both UTC and local time

---

#### `stop_first_crack_detection`
Stop first crack detection and get session summary.

**Parameters:** None

**Returns:**
```json
{
  "status": "success",
  "result": {
    "session_state": "stopped",
    "session_id": "uuid",
    "session_summary": {
      "duration": "12:45",
      "first_crack_detected": true,
      "first_crack_time": "04:15",
      "audio_source": "usb_microphone",
      "windows_processed": 765
    }
  }
}
```

**Usage Notes:**
- Stops detection thread and releases audio resources
- Returns final session statistics
- Safe to call even if no session is active (returns `"session_state": "no_active_session"`)

---

### Resources

#### `health://status`
Health check and server status.

**Type:** Resource (read via `read_resource`)

**Returns:**
```json
{
  "status": "healthy",
  "model_checkpoint": "/path/to/model.pt",
  "model_exists": true,
  "device": "mps",
  "version": "1.0.0",
  "session_active": true,
  "session_id": "uuid",
  "session_started_at": "2025-01-25T12:00:00Z"
}
```

---

## Roaster Control Server

**Server Name:** `roaster-control`  
**Purpose:** Control physical coffee roaster hardware (heat, fan, drum, cooling)  
**Transport:** stdio (JSON-RPC over stdin/stdout)  
**Hardware:** Supports Hottop KN-8828B-2K+ and mock hardware

### Tools

#### `set_heat`
Set roaster heat level.

**Parameters:**
- `level` (required, int): Heat level percentage (0-100 in 10% increments)

**Returns:**
```
Heat set to 80%
```

**Validation:**
- Must be 0-100
- Must be in 10% increments (0, 10, 20, ..., 100)

**Example:**
```json
{"level": 70}
```

---

#### `set_fan`
Set roaster fan speed.

**Parameters:**
- `speed` (required, int): Fan speed percentage (0-100 in 10% increments)

**Returns:**
```
Fan set to 60%
```

**Validation:**
- Must be 0-100
- Must be in 10% increments (0, 10, 20, ..., 100)

**Example:**
```json
{"speed": 50}
```

---

#### `start_roaster`
Start roaster drum motor.

**Parameters:** None

**Returns:**
```
Roaster drum started
```

**Usage Notes:**
- Must be called before beans can be added
- Typically called during preheat phase

---

#### `stop_roaster`
Stop roaster drum motor.

**Parameters:** None

**Returns:**
```
Roaster drum stopped
```

**Usage Notes:**
- Stops drum rotation
- Should be called after beans are dropped and cooling is complete

---

#### `drop_beans`
Open bean drop door and start cooling.

**Parameters:** None

**Returns:**
```
Beans dropped, cooling started
```

**Usage Notes:**
- Combines two operations: opens drop door and starts cooling fan
- Automatically records drop timestamp and temperature
- Called when roast is complete

---

#### `start_cooling`
Start cooling fan motor.

**Parameters:** None

**Returns:**
```
Cooling fan started
```

**Usage Notes:**
- Independent of drop operation
- Can be used for additional cooling control

---

#### `stop_cooling`
Stop cooling fan motor.

**Parameters:** None

**Returns:**
```
Cooling fan stopped
```

**Usage Notes:**
- Call after beans have cooled sufficiently
- Ends the roast session

---

#### `report_first_crack`
Report first crack detection (called by agent after First Crack MCP detects).

**Parameters:**
- `timestamp` (required, string): ISO 8601 UTC timestamp when first crack occurred
- `temperature` (required, float): Bean temperature in °C at first crack (150-250°C)

**Returns:**
```
First crack reported at 2025-01-25T12:04:15Z, 205.3°C
```

**Validation:**
- Timestamp must be valid ISO 8601 format (UTC preferred)
- Temperature must be between 150°C and 250°C

**Usage Notes:**
- Integrates first crack detection with roast metrics
- Enables development time calculation (time from FC to drop)
- Agent should call this immediately after First Crack Detection MCP confirms first crack

**Example:**
```json
{
  "timestamp": "2025-01-25T12:04:15.123Z",
  "temperature": 205.3
}
```

---

#### `get_roast_status`
Get complete roast status including sensors, metrics, and timestamps.

**Parameters:** None

**Returns:**
```json
{
  "session_active": true,
  "roaster_running": true,
  "timestamps": {
    "session_started_utc": "2025-01-25T12:00:00Z",
    "session_started_local": "2025-01-25T04:00:00-08:00",
    "t0_utc": "2025-01-25T12:02:30Z",
    "t0_local": "2025-01-25T04:02:30-08:00",
    "first_crack_utc": "2025-01-25T12:06:45Z",
    "first_crack_local": "2025-01-25T04:06:45-08:00",
    "drop_utc": null,
    "drop_local": null
  },
  "sensors": {
    "timestamp": "2025-01-25T12:07:30Z",
    "bean_temp_c": 212.5,
    "chamber_temp_c": 220.0,
    "fan_speed_percent": 60,
    "heat_level_percent": 50
  },
  "metrics": {
    "roast_elapsed_seconds": 300,
    "roast_elapsed_display": "05:00",
    "rate_of_rise_c_per_min": 8.5,
    "beans_added_temp_c": 85.0,
    "first_crack_temp_c": 205.3,
    "first_crack_time_display": "04:15",
    "development_time_seconds": 45,
    "development_time_display": "00:45",
    "development_time_percent": 15.0,
    "total_roast_duration_seconds": null
  },
  "connection": {
    "connected": true,
    "hardware_type": "mock",
    "port": null
  }
}
```

**Usage Notes:**
- Poll regularly (e.g., every 1-2s) for real-time monitoring
- `timestamps` include both UTC and local time for all events
- `sensors` provides current hardware readings
- `metrics` includes calculated values:
  - **T0 (beans added)**: Auto-detected from >10°C temperature drop
  - **Rate of Rise (RoR)**: Calculated from 60-second window
  - **Development time**: Time from first crack to now (or drop)
  - **Development time %**: (Development time / Total roast time) × 100
- `null` values indicate event hasn't occurred yet
- All temperatures in Celsius

---

### Resources

#### `health://status`
Health check and server status.

**Type:** Resource (read via `read_resource`)

**Returns:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "hardware_mode": "mock",
  "session_active": true,
  "roaster_info": {
    "model": "Mock Roaster",
    "firmware": "1.0",
    "hardware_type": "mock"
  }
}
```

---

## Error Handling

### First Crack Detection Errors
All errors return this structure:
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

### Roaster Control Errors
Errors return plain text:
```
Error: <message> (code: ERROR_CODE)
```

Common error codes:
- `ROASTER_NOT_CONNECTED` - Not connected to hardware
- `ROASTER_CONNECTION_ERROR` - Connection failed
- `INVALID_COMMAND_ERROR` - Bad command parameters
- `NO_ACTIVE_ROAST_ERROR` - No active roast session
- `BEANS_NOT_ADDED_ERROR` - T0 not detected yet

---

## Integration Pattern

### Typical Agent Workflow

```
1. Preheat Phase
   - roaster_control: start_roaster()
   - roaster_control: set_heat(100)
   - roaster_control: set_fan(30)
   - Poll roaster_control: get_roast_status() until chamber_temp_c ≥ 170°C

2. Add Beans
   - Agent adds beans manually (temp drops to ~80°C)
   - T0 auto-detected by roaster_control (>10°C drop)
   - roaster_control: set_heat(90)
   - roaster_control: set_fan(50)

3. Start First Crack Detection
   - first_crack: start_first_crack_detection({"audio_source_type": "usb_microphone"})

4. Monitor Until First Crack
   - Poll both servers every 5-10s:
     - first_crack: get_first_crack_status()
     - roaster_control: get_roast_status()
   - When first_crack_detected == true:
     - roaster_control: report_first_crack({
         "timestamp": first_crack_time_utc,
         "temperature": current_bean_temp_c
       })

5. Development Phase
   - roaster_control: set_heat(50)
   - roaster_control: set_fan(70)
   - Monitor development_time_percent
   - Target: 15-20% development time

6. Drop
   - roaster_control: drop_beans()
   - first_crack: stop_first_crack_detection()
   - Monitor cooling: get_roast_status() until bean_temp_c < 60°C

7. Complete
   - roaster_control: stop_cooling()
   - roaster_control: stop_roaster()
   - Get final metrics: get_roast_status()
```

---

## Configuration

### First Crack Detection
Configure via environment or config file:
- `MODEL_CHECKPOINT`: Path to trained model (.pt file)
- `LOG_LEVEL`: DEBUG | INFO | WARNING | ERROR (default: INFO)
- Detection parameters passed per-session via `start_first_crack_detection`

### Roaster Control
Configure via `ServerConfig`:
```python
ServerConfig(
    hardware=HardwareConfig(
        port="/dev/tty.usbserial-DN016OJ3",  # Serial port for Hottop
        baud_rate=115200,
        timeout=1.0,
        mock_mode=False  # True for testing without hardware
    ),
    tracker=TrackerConfig(
        t0_detection_threshold=10.0,  # °C drop to detect beans
        polling_interval=1.0,  # Sensor polling rate (seconds)
        ror_window_size=60,  # RoR calculation window (seconds)
        development_time_target_min=15.0,  # Target dev time % (min)
        development_time_target_max=20.0  # Target dev time % (max)
    ),
    logging_level="INFO",
    timezone="America/Los_Angeles"
)
```

Set `USE_MOCK_HARDWARE=true` environment variable for mock mode.

---

## Safety Notes

1. **Attended Operation Required** - Servers provide monitoring but don't auto-cut power
2. **Overheat Warnings** - Logs warnings at bean_temp > 250°C or chamber_temp > 300°C
3. **Stall Detection** - Warns if RoR < -2°C/min after T0
4. **Input Validation** - All parameters validated before hardware commands
5. **Thread Safety** - All operations protected with locks for concurrent access

---

## Device Compatibility

### First Crack Detection
- **Audio Input**: USB microphone, built-in microphone, or audio file
- **Model Device**: Automatically selects MPS (Apple Silicon) → CUDA → CPU
- **Sample Rate**: 16kHz (auto-resampled from input)

### Roaster Control
- **Hottop KN-8828B-2K+**: Full support via pyhottop library
- **Mock Hardware**: Realistic thermal simulation for testing
- **Serial Port**: Configurable (typical: `/dev/tty.usbserial-*` on macOS)

---

## Observability

Both servers support optional observability via OpenTelemetry:
- **Logging**: Structured logs with context
- **Tracing**: Distributed traces for tool calls
- **Metrics**: Custom metrics for detection events, heat adjustments, sensor readings

Enable by ensuring `observability` package is available in Python path.
