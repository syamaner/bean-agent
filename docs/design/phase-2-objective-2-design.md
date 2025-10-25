# Phase 2 Objective 2 - Design Document
## Roaster Control MCP Server

**Status**: Design Approved  
**Created**: 2025-10-25  
**Phase**: 2 (MCP Server Development)  
**Objective**: 2 of 2

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  n8n / .NET Aspire Agent                │
│                    (LLM Orchestrator)                   │
└─────────────────────┬───────────────────────────────────┘
                      │ MCP Protocol (stdio/JSON-RPC)
                      │
┌─────────────────────▼───────────────────────────────────┐
│            Roaster Control MCP Server                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │              MCP Server (server.py)               │  │
│  │  • Tool handlers (9 control + 1 query)            │  │
│  │  • Health resource                                │  │
│  │  • Error mapping                                  │  │
│  └───────────────────┬───────────────────────────────┘  │
│                      │                                   │
│  ┌───────────────────▼───────────────────────────────┐  │
│  │       RoastSessionManager (session_manager.py)    │  │
│  │  • Single session lifecycle                       │  │
│  │  • Thread-safe operations (Lock)                  │  │
│  │  • Hardware interface orchestration               │  │
│  │  • RoastTracker integration                       │  │
│  │  • Polling loop (1 Hz)                            │  │
│  └───────┬──────────────────────────┬────────────────┘  │
│          │                          │                    │
│  ┌───────▼────────────┐   ┌────────▼────────────────┐  │
│  │  HardwareInterface │   │   RoastTracker          │  │
│  │   (hardware.py)    │   │   (roast_tracker.py)    │  │
│  │                    │   │                         │  │
│  │  • HottopHardware  │   │  • T0 detection         │  │
│  │  • MockHardware    │   │  • RoR calculation      │  │
│  │  • Commands        │   │  • First crack tracking │  │
│  │  • Sensor polling  │   │  • Dev time calc        │  │
│  └───────┬────────────┘   │  • Drop recording       │  │
│          │                └─────────────────────────┘  │
└──────────┼───────────────────────────────────────────┘
           │ USB Serial
           │
┌──────────▼────────────┐
│  Hottop KN-8828B-2K+  │
│      Roaster          │
└───────────────────────┘
```

---

## Component Design

### 1. MCP Server Layer (`server.py`)

**Responsibility**: MCP protocol handling and tool exposure

**Tools Exposed**:

```python
# Control Tools (roast:admin scope)
@server.tool()
async def set_heat(target_percent: int) -> dict:
    """Set roaster heat to target % (0-100, in 10% increments)."""

@server.tool()
async def set_fan(target_percent: int) -> dict:
    """Set fan speed to target % (0-100, in 10% increments)."""

@server.tool()
async def start_roaster() -> dict:
    """Start the roaster drum motor."""

@server.tool()
async def stop_roaster() -> dict:
    """Stop the roaster drum motor."""

@server.tool()
async def drop_beans() -> dict:
    """Open bean drop door to eject beans."""

@server.tool()
async def start_cooling() -> dict:
    """Start the cooling fan cycle."""

@server.tool()
async def stop_cooling() -> dict:
    """Stop the cooling fan."""

@server.tool()
async def report_first_crack(timestamp: str, confidence: str) -> dict:
    """Report first crack detected by detection MCP server."""

# Query Tools (roast:observer scope)
@server.tool()
async def get_roast_status() -> dict:
    """Get complete roast status snapshot."""
```

**Resources Exposed**:
```python
@server.resource("health://status")
async def get_health() -> dict:
    """Server health and configuration."""
```

**Error Handling**:
- Map exceptions to MCP error responses
- Structured error codes and messages
- Detailed logging for debugging

---

### 2. Session Manager (`session_manager.py`)

**Responsibility**: Roast session lifecycle and orchestration

**Class**: `RoastSessionManager`

**State Machine**:
```
IDLE → CONNECTED → MONITORING → ROASTING → COOLING → COMPLETE
  ↓        ↓           ↓            ↓          ↓         ↓
  └────────┴───────────┴────────────┴──────────┴─────────┘
                     ERROR (any state)
```

**Key Methods**:
```python
class RoastSessionManager:
    def __init__(self, hardware: HardwareInterface, config: ServerConfig):
        self._hardware = hardware
        self._tracker = RoastTracker(config)
        self._lock = threading.Lock()
        self._polling_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
    def start_session(self) -> SessionInfo:
        """Connect to hardware and start polling."""
        
    def stop_session(self) -> SessionSummary:
        """Stop polling and disconnect."""
        
    def get_status(self) -> RoastStatus:
        """Get current complete status snapshot."""
        
    def execute_command(self, command: ControlCommand) -> CommandResult:
        """Execute hardware control command."""
        
    def report_first_crack(self, timestamp: str, confidence: str) -> dict:
        """Record first crack event."""
        
    def _polling_loop(self):
        """Background thread: poll sensors at 1 Hz."""
        while not self._stop_event.is_set():
            readings = self._hardware.read_sensors()
            self._tracker.update(readings)
            time.sleep(1.0)
```

**Thread Safety**:
- All public methods protected with `self._lock`
- Polling thread isolated from command execution
- Status snapshots atomic

**Idempotency**:
- `start_session()`: Returns existing session if already running
- `stop_session()`: Safe to call when not running
- Control commands: Hardware handles duplicate commands

---

### 3. Hardware Interface (`hardware.py`)

**Responsibility**: Abstract hardware communication

**Abstract Base Class**:
```python
class HardwareInterface(ABC):
    @abstractmethod
    def connect(self) -> bool:
        """Connect to roaster hardware."""
        
    @abstractmethod
    def disconnect(self):
        """Disconnect from hardware."""
        
    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection status."""
        
    @abstractmethod
    def read_sensors(self) -> SensorReading:
        """Read all sensor values."""
        
    @abstractmethod
    def set_heat(self, percent: int):
        """Set heat level (0-100, 10% increments)."""
        
    @abstractmethod
    def set_fan(self, percent: int):
        """Set fan speed (0-100, 10% increments)."""
        
    @abstractmethod
    def start_drum(self):
        """Start roaster drum motor."""
        
    @abstractmethod
    def stop_drum(self):
        """Stop roaster drum motor."""
        
    @abstractmethod
    def drop_beans(self):
        """Open bean drop door."""
        
    @abstractmethod
    def start_cooling(self):
        """Start cooling fan."""
        
    @abstractmethod
    def stop_cooling(self):
        """Stop cooling fan."""
```

**Real Implementation** (`HottopHardware`):
```python
class HottopHardware(HardwareInterface):
    def __init__(self, port: str, config: HardwareConfig):
        self._hottop = None  # pyhottop client instance
        self._port = port
        self._config = config
        
    def connect(self) -> bool:
        # Initialize pyhottop connection
        # Handle USB serial setup
        
    def read_sensors(self) -> SensorReading:
        # Query pyhottop for current values
        # Return structured data
```

**Mock Implementation** (`MockHardware`):
```python
class MockHardware(HardwareInterface):
    """Simulated roaster for testing."""
    
    def __init__(self, config: HardwareConfig):
        self._bean_temp = 20.0  # Room temp
        self._chamber_temp = 20.0
        self._heat = 0
        self._fan = 0
        self._drum_running = False
        self._simulation_started = None
        
    def read_sensors(self) -> SensorReading:
        # Simulate temperature rise based on heat/fan/time
        # Realistic roast curve simulation
        
    def set_heat(self, percent: int):
        # Update simulated heat
        # Validate 10% increments
```

**Benefits**:
- Develop entire server without physical hardware
- Reproducible tests with known behaviors
- Easy to add hardware variants

---

### 4. Roast Tracker (`roast_tracker.py`)

**Responsibility**: Compute derived roast metrics

**Class**: `RoastTracker`

**State**:
```python
class RoastTracker:
    def __init__(self, config: TrackerConfig):
        # Timestamps
        self._t0: Optional[datetime] = None  # Beans added
        self._first_crack: Optional[datetime] = None
        self._drop: Optional[datetime] = None
        
        # Temperature history (rolling 60s buffer)
        self._temp_buffer: deque = deque(maxlen=60)
        
        # Captured values
        self._beans_added_temp: Optional[float] = None
        self._first_crack_temp: Optional[float] = None
        self._drop_temp: Optional[float] = None
        
        # Configuration
        self._t0_detection_threshold = config.t0_threshold  # 10°C default
```

**Key Methods**:
```python
    def update(self, reading: SensorReading):
        """Process new sensor reading."""
        self._temp_buffer.append((datetime.now(UTC), reading.bean_temp))
        
        # Auto-detect T0 if not set
        if self._t0 is None:
            self._detect_beans_added(reading)
            
    def _detect_beans_added(self, reading: SensorReading):
        """Detect sudden temperature drop indicating beans added."""
        if len(self._temp_buffer) < 2:
            return
            
        prev_temp = self._temp_buffer[-2][1]
        curr_temp = reading.bean_temp
        
        if prev_temp - curr_temp > self._t0_detection_threshold:
            self._t0 = datetime.now(UTC)
            self._beans_added_temp = prev_temp
            logger.info("beans_added_detected", 
                       temp=prev_temp, drop=prev_temp-curr_temp)
    
    def get_rate_of_rise(self) -> Optional[float]:
        """Calculate RoR: (T_now - T_60s_ago) per minute."""
        if len(self._temp_buffer) < 60:
            return None
            
        t_now, temp_now = self._temp_buffer[-1]
        t_60s_ago, temp_60s_ago = self._temp_buffer[0]
        
        delta_temp = temp_now - temp_60s_ago
        delta_time = (t_now - t_60s_ago).total_seconds() / 60.0
        
        return delta_temp / delta_time if delta_time > 0 else None
    
    def report_first_crack(self, timestamp: datetime, temp: float):
        """Record first crack event."""
        self._first_crack = timestamp
        self._first_crack_temp = temp
        
    def get_development_time_percent(self) -> Optional[float]:
        """Calculate development time percentage."""
        if self._t0 is None or self._first_crack is None:
            return None
            
        now = datetime.now(UTC)
        total_time = (now - self._t0).total_seconds()
        dev_time = (now - self._first_crack).total_seconds()
        
        return (dev_time / total_time * 100) if total_time > 0 else None
    
    def record_drop(self, temp: float):
        """Record bean drop event."""
        self._drop = datetime.now(UTC)
        self._drop_temp = temp
        
    def get_metrics(self) -> RoastMetrics:
        """Return complete metrics snapshot."""
        return RoastMetrics(
            roast_elapsed_seconds=self._get_elapsed_seconds(),
            rate_of_rise=self.get_rate_of_rise(),
            beans_added_temp=self._beans_added_temp,
            first_crack_temp=self._first_crack_temp,
            development_time_percent=self.get_development_time_percent(),
            # ... more fields
        )
```

**Algorithm: T0 Detection**
```
Initialize: prev_temp = None

On each sensor update:
  1. If prev_temp exists:
     2. Calculate drop = prev_temp - current_temp
     3. If drop > threshold (10°C):
        4. T0 = current_timestamp
        5. beans_added_temp = prev_temp
        6. Log detection
        7. Stop checking (T0 set)
  8. prev_temp = current_temp
```

**Algorithm: RoR Calculation**
```
Maintain: 60-second circular buffer of (timestamp, temp)

On request:
  1. If buffer size < 60: return None
  2. Get oldest entry: (t_old, temp_old)
  3. Get newest entry: (t_new, temp_new)
  4. delta_temp = temp_new - temp_old
  5. delta_time_minutes = (t_new - t_old) / 60
  6. RoR = delta_temp / delta_time_minutes
  7. Return RoR
```

---

### 5. Data Models (`models.py`)

**Pydantic Models for Validation**:

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class SensorReading(BaseModel):
    """Raw sensor data from hardware."""
    timestamp: datetime
    bean_temp_c: float = Field(..., ge=-50, le=300)
    chamber_temp_c: float = Field(..., ge=-50, le=300)
    fan_speed_percent: int = Field(..., ge=0, le=100)
    heat_level_percent: int = Field(..., ge=0, le=100)

class RoastMetrics(BaseModel):
    """Computed roast metrics."""
    roast_elapsed_seconds: Optional[int] = None
    roast_elapsed_display: Optional[str] = None  # MM:SS
    rate_of_rise_c_per_min: Optional[float] = None
    beans_added_temp_c: Optional[float] = None
    first_crack_temp_c: Optional[float] = None
    first_crack_time_display: Optional[str] = None
    development_time_seconds: Optional[int] = None
    development_time_display: Optional[str] = None
    development_time_percent: Optional[float] = None
    total_roast_duration_seconds: Optional[int] = None

class RoastStatus(BaseModel):
    """Complete status response."""
    session_active: bool
    roaster_running: bool
    timestamps: dict  # All event timestamps
    sensors: SensorReading
    metrics: RoastMetrics
    connection: dict

class ControlCommand(BaseModel):
    """Control command input validation."""
    action: str = Field(..., pattern="^(set_heat|set_fan|...)$")
    value: Optional[int] = None
    
    @validator('value')
    def validate_percentage(cls, v, values):
        if values.get('action') in ['set_heat', 'set_fan']:
            if v is None:
                raise ValueError("value required for heat/fan commands")
            if v % 10 != 0 or v < 0 or v > 100:
                raise ValueError("value must be 0-100 in 10% increments")
        return v

class FirstCrackReport(BaseModel):
    """First crack event report."""
    timestamp: datetime
    confidence: str
    temperature: Optional[float] = None

class SessionInfo(BaseModel):
    """Session start information."""
    session_id: str
    started_at: datetime
    started_at_local: datetime
    hardware: str
    port: str
```

---

### 6. Exception Hierarchy (`exceptions.py`)

```python
class RoasterError(Exception):
    """Base exception for roaster control."""
    def __init__(self, message: str, error_code: str):
        super().__init__(message)
        self.error_code = error_code

class RoasterNotConnectedError(RoasterError):
    def __init__(self):
        super().__init__(
            "Roaster not connected",
            "ROASTER_NOT_CONNECTED"
        )

class RoasterConnectionError(RoasterError):
    def __init__(self, details: str):
        super().__init__(
            f"Connection failed: {details}",
            "CONNECTION_ERROR"
        )

class InvalidCommandError(RoasterError):
    def __init__(self, command: str, reason: str):
        super().__init__(
            f"Invalid command '{command}': {reason}",
            "INVALID_COMMAND"
        )

class NoActiveRoastError(RoasterError):
    def __init__(self):
        super().__init__(
            "No active roast session",
            "NO_ACTIVE_ROAST"
        )

class BeansNotAddedError(RoasterError):
    def __init__(self):
        super().__init__(
            "Beans not yet added (T0 not detected)",
            "BEANS_NOT_ADDED"
        )
```

---

### 7. Configuration (`config.py`)

```python
class HardwareConfig(BaseModel):
    port: str = "/dev/tty.usbserial-1420"
    baud_rate: int = 115200
    timeout: float = 1.0
    mock_mode: bool = False  # Use MockHardware if True

class TrackerConfig(BaseModel):
    t0_detection_threshold: float = 10.0  # °C drop
    polling_interval: float = 1.0  # seconds
    ror_window_size: int = 60  # seconds
    development_time_target_min: float = 15.0  # %
    development_time_target_max: float = 20.0  # %

class ServerConfig(BaseModel):
    hardware: HardwareConfig
    tracker: TrackerConfig
    logging_level: str = "INFO"
    timezone: str = "America/Los_Angeles"

def load_config(path: Optional[str] = None) -> ServerConfig:
    """Load config from file with env var overrides."""
    # Priority: env vars > config file > defaults
```

---

## Data Flow

### Sensor Polling Flow
```
┌──────────────────┐
│  Polling Thread  │ (1 Hz)
│  (background)    │
└────────┬─────────┘
         │
         ▼
┌────────────────────────┐
│ hardware.read_sensors()│
└────────┬───────────────┘
         │ SensorReading
         ▼
┌────────────────────────┐
│  tracker.update(...)   │
│  • Detect T0           │
│  • Compute RoR         │
│  • Update buffer       │
└────────────────────────┘
```

### Status Query Flow
```
Agent                SessionManager           RoastTracker      Hardware
  │                        │                        │              │
  │ get_roast_status()     │                        │              │
  ├───────────────────────>│                        │              │
  │                        │ (acquire lock)         │              │
  │                        │                        │              │
  │                        │ get_metrics()          │              │
  │                        ├───────────────────────>│              │
  │                        │<───────────────────────┤              │
  │                        │    RoastMetrics        │              │
  │                        │                        │              │
  │                        │ read_sensors()         │              │
  │                        ├───────────────────────────────────────>│
  │                        │<───────────────────────────────────────┤
  │                        │    SensorReading       │              │
  │                        │                        │              │
  │                        │ (build RoastStatus)    │              │
  │<───────────────────────┤                        │              │
  │    RoastStatus         │ (release lock)         │              │
```

### Control Command Flow
```
Agent                SessionManager           Hardware
  │                        │                      │
  │ set_heat(70)           │                      │
  ├───────────────────────>│                      │
  │                        │ (validate input)     │
  │                        │ (acquire lock)       │
  │                        │                      │
  │                        │ hardware.set_heat(70)│
  │                        ├─────────────────────>│
  │                        │                      │ (send USB cmd)
  │                        │<─────────────────────┤
  │                        │    success           │
  │<───────────────────────┤                      │
  │    {success: true}     │ (release lock)       │
```

---

## Testing Strategy

### Unit Tests

**Models** (`test_models.py`): ~20 tests
- Pydantic validation
- Field constraints
- Custom validators

**Hardware** (`test_hardware.py`): ~25 tests
- MockHardware behavior
- Sensor simulation
- Command validation
- Connection handling

**Tracker** (`test_roast_tracker.py`): ~30 tests
- T0 detection with various scenarios
- RoR calculation accuracy
- Development time percentages
- Edge cases (no T0, no first crack, etc.)

**Session Manager** (`test_session_manager.py`): ~25 tests
- Session lifecycle
- Thread safety
- Idempotency
- Error handling

### Integration Tests

**Server** (`test_server.py`): ~10 tests
- Tool calls with MockHardware
- End-to-end workflows
- Error propagation
- Health checks

### Manual Tests

**With MockHardware**:
- Full roast simulation
- Control commands during simulated roast
- Status queries during roast
- First crack integration

---

## Deployment

### Development Setup
```bash
# Add to Warp MCP config
{
  "mcpServers": {
    "roaster-control": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "src.mcp_servers.roaster_control"],
      "cwd": "/path/to/coffee-roasting",
      "env": {
        "PYTHONPATH": "/path/to/coffee-roasting",
        "ROASTER_PORT": "/dev/tty.usbserial-1420",
        "ROASTER_MOCK_MODE": "true"
      }
    }
  }
}
```

### Production Setup (Phase 3)
- Real hardware connection
- Auth0 token validation
- HTTP transport
- Monitoring and logging

---

## References

- [Requirements Document](../requirements/phase-2-objective-2-requirements.md)
- [Phase 2 Objective 1 Design](phase-2-objective-1-design.md)
- [pyhottop Library](https://github.com/splitkeycoffee/pyhottop)
- [MCP Specification](https://spec.modelcontextprotocol.io/)

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-25  
**Status**: Approved for Implementation
