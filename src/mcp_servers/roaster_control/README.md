# Roaster Control MCP Server

MCP (Model Context Protocol) server for controlling coffee roasters through an AI agent interface.

## Features

- **Hardware abstraction** - Support for multiple roaster types (Hottop, Mock, Stub)
- **Thread-safe operation** - Background sensor polling with lock protection
- **Comprehensive metrics** - T0 detection, RoR, development time tracking
- **Safety monitoring** - Overheat detection and stall warnings
- **9 control tools** - Heat, fan, drum, cooling, drop, first crack reporting, status
- **Full validation** - Configuration, input, and timezone validation

## Architecture

```
┌─────────────────────┐
│   MCP Server        │  9 tools exposed to agents
│   (server.py)       │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ Session Manager     │  Thread-safe orchestration
│ (session_manager.py)│  • Polling thread (1 Hz)
└──────────┬──────────┘  • Lock protection
           │              • Status queries
┌──────────▼──────────┐
│  Hardware Interface │  Abstract base class
│  (hardware.py)      │
└──────────┬──────────┘
           │
    ┌──────┴──────┬──────────┐
    │             │          │
┌───▼───┐    ┌───▼───┐  ┌──▼──┐
│ Mock  │    │Hottop │  │Stub │
│Roaster│    │Roaster│  │     │
└───────┘    └───────┘  └─────┘
```

## Usage

### Initialize Server

```python
from src.mcp_servers.roaster_control import init_server, ServerConfig

# Default configuration (mock mode)
init_server()

# Custom configuration
config = ServerConfig(
    hardware=HardwareConfig(
        mock_mode=False,
        port="/dev/tty.usbserial-DN016OJ3",
        baud_rate=115200
    ),
    tracker=TrackerConfig(
        t0_detection_threshold=10.0,
        polling_interval=1.0
    )
)
init_server(config)
```

### MCP Tools

#### Control Tools
- `set_heat(percent: int)` - Set heat level (0-100%, 10% increments)
- `set_fan(percent: int)` - Set fan speed (0-100%, 10% increments)
- `start_roaster()` - Start drum motor
- `stop_roaster()` - Stop drum motor
- `drop_beans()` - Open drop door and start cooling
- `start_cooling()` - Start cooling fan
- `stop_cooling()` - Stop cooling fan

#### Monitoring Tools
- `report_first_crack(timestamp: str, temperature: float)` - Report FC detection
- `get_roast_status()` - Get complete status (sensors, metrics, timestamps)

### Example Agent Workflow

```python
# 1. Preheat
await call_tool("start_roaster", {})
await call_tool("set_heat", {"percent": 100})
await call_tool("set_fan", {"percent": 30})

# 2. Monitor until 170°C, add beans (temp drops to 80°C)
# T0 auto-detected by temperature drop

# 3. Roast until first crack detected
await call_tool("report_first_crack", {
    "timestamp": "2025-01-25T12:34:56Z",
    "temperature": 205.0
})

# 4. Development phase
await call_tool("set_heat", {"percent": 50})
await call_tool("set_fan", {"percent": 60})

# 5. Drop at target temp
await call_tool("drop_beans", {})

# 6. Get final metrics
status = await call_tool("get_roast_status", {})
```

## Configuration

### HardwareConfig
- `port` - Serial port for real hardware
- `baud_rate` - Baud rate (validated: 9600-921600, standard values only)
- `timeout` - Serial timeout (0.1-60s)
- `mock_mode` - Use mock hardware (default: True)

### TrackerConfig
- `t0_detection_threshold` - Temperature drop to detect beans (0-100°C, default: 10°C)
- `polling_interval` - Sensor polling rate (0.1-10s, default: 1.0s)
- `ror_window_size` - RoR calculation window (10-300s, default: 60s)
- `development_time_target_min/max` - Target dev time range (0-100%, default: 15-20%)

### ServerConfig
- `hardware` - Hardware configuration
- `tracker` - Tracker configuration
- `logging_level` - Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- `timezone` - Timezone for local timestamps (default: America/Los_Angeles)

## Hardware Implementations

### MockRoaster
Realistic thermal simulation for testing.

**Features:**
- Thermal model with heat/fan/cooling effects
- Bean thermal lag (~10°C cooler than chamber)
- Time acceleration for testing (time_scale parameter)
- Temperature limits: 15-300°C chamber, 15-250°C bean

**Constants:**
- MAX_HEAT_RATE_C_PER_SEC = 2.0
- MAX_FAN_COOLING_C_PER_SEC = 0.5
- COOLING_MODE_RATE_C_PER_SEC = 5.0
- BEAN_LAG_TEMP_OFFSET_C = 10.0

### HottopRoaster
Real Hottop KN-8828B-2K+ hardware via pyhottop library.

**Requirements:**
- Physical roaster connected via USB
- pyhottop library installed
- Correct serial port configured

**Features:**
- Full pyhottop integration
- Callback-based sensor updates
- Native drop sequence support

### StubRoaster
Simple stub for demos without simulation.

## Safety Features

### Overheat Detection
Logs warnings (attended operation only):
- Bean temperature > 250°C
- Chamber temperature > 300°C

### Stall Detection
Logs warning if:
- Rate of rise < -2°C/min after T0
- Temperature buffer has 30+ readings

### Input Validation
- Heat/fan: 0-100% in 10% increments
- First crack temp: 150-250°C
- Timestamps: ISO 8601 UTC format
- Configuration: Cross-field validation

## Metrics Tracked

### Automatic
- **T0 (beans added)** - Auto-detected from >10°C temperature drop
- **Rate of Rise** - Calculated from 60-second window (°C/min)
- **Roast elapsed time** - Time since T0 (seconds + MM:SS display)

### Agent-Reported
- **First crack** - Timestamp and temperature
- **Development time** - Time from FC to now/drop (seconds, display, %)
- **Drop** - Timestamp and temperature (via drop_beans tool)

### Computed
- **Total roast duration** - T0 to drop (seconds)
- **Development time %** - Dev time / total roast time

## Thread Safety

All operations are thread-safe:
- Background polling thread (daemon, 1 Hz default)
- Lock protection on shared state
- Status queries safe during polling
- Clean shutdown with thread join (2s timeout)

## Error Handling

### Exception Hierarchy
- `RoasterError` (base)
  - `RoasterNotConnectedError` - Not connected to hardware
  - `RoasterConnectionError` - Connection failed
  - `InvalidCommandError` - Bad command parameters
  - `NoActiveRoastError` - No active session
  - `BeansNotAddedError` - T0 not detected

### Error Responses
All tools return formatted error messages with error codes:
```json
{
  "text": "Error: <message> (code: ERROR_CODE)"
}
```

## Testing

### Unit Tests (100 tests)
```bash
./venv/bin/python -m pytest tests/mcp_servers/roaster_control/unit -v
```

### Integration Tests (22 tests)
```bash
./venv/bin/python -m pytest tests/mcp_servers/roaster_control/integration -v
```

### Full Roast Simulation
Accelerated end-to-end test (preheat → beans → FC → development → drop):
```bash
./venv/bin/python -m pytest tests/mcp_servers/roaster_control/integration/test_server.py::TestFullRoastSimulation -v
```

### Manual Hardware Test
```bash
./venv/bin/python tests/mcp_servers/roaster_control/integration/test_hottop_manual.py
```

## Logging

Uses Python `logging` module:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

Logs include:
- Polling errors (ERROR level)
- Safety warnings (WARNING level)
- Time acceleration warning (WARNING level)

## Development

### Adding a New Roaster

1. Subclass `HardwareInterface`
2. Implement all abstract methods:
   - `connect()`, `disconnect()`, `is_connected()`
   - `get_roaster_info()`, `is_drum_running()`
   - `read_sensors()` - Return SensorReading
   - Control methods: `set_heat()`, `set_fan()`, `start_drum()`, etc.
3. Add validation (10% increments, connection checks)
4. Write unit tests

### Running Tests
```bash
# All tests
./venv/bin/python -m pytest tests/mcp_servers/roaster_control -v

# Specific test file
./venv/bin/python -m pytest tests/mcp_servers/roaster_control/unit/test_hardware.py -v

# With coverage
./venv/bin/python -m pytest tests/mcp_servers/roaster_control --cov=src/mcp_servers/roaster_control
```

## Known Limitations

1. **Attended operation only** - Safety warnings don't auto-cut power
2. **T0 detection** - Requires >10°C drop, may miss gradual bean additions
3. **Mock thermal model** - Simplified, not calibrated to real roasters
4. **Single roaster** - One active session at a time
5. **Polling rate** - 1 Hz default may miss rapid changes

## Future Enhancements

- [ ] Export roast profiles (CSV/JSON)
- [ ] Artisan/RoastLog format compatibility
- [ ] Multiple roaster sessions
- [ ] Acoustic first crack detection fallback
- [ ] Configurable safety auto-shutoff
- [ ] Web dashboard
- [ ] Historical roast comparison

## License

See repository root LICENSE file.
