# Phase 2 Objective 2 - Implementation Plan
## Roaster Control MCP Server

**Status**: In Progress - M4 (Roast Tracker)  
**Created**: 2025-10-25  
**Last Updated**: 2025-01-25  
**Estimated Duration**: 2-3 days (18 hours focused work)

---

## Overview

Build an MCP server that provides programmatic control of the Hottop KN-8828B-2K+ roaster using the `pyhottop` library. The server will expose 9 tools for hardware control, sensor reading, and roast metric computation.

**Approach**: Small, regular commits after each milestone using TDD methodology.

**Client**: n8n workflow / .NET Aspire agent  
**Transport**: stdio (Phase 2), HTTP + Auth0 (Phase 3)

---

## Milestones

| Milestone | Tasks | Est. Time | Status |
|-----------|-------|-----------|--------|
| **M1: Project Setup & pyhottop Research** | 5 tasks | 2 hours | ✅ Complete |
| **M2: Data Models & Exceptions (TDD)** | 2 tasks | 2 hours | ✅ Complete |
| **M3: Hardware Wrapper (TDD)** | 3 tasks | 3 hours | ✅ Complete |
| **M4: Roast Tracker (TDD)** | 4 tasks | 4 hours | ✅ Complete |
| **M5: Session Manager (TDD)** | 3 tasks | 3 hours | ✅ Complete |
| **M6: MCP Server Implementation** | 4 tasks | 2 hours | ⚪ Not Started |
| **M7: Configuration & Documentation** | 4 tasks | 2 hours | ⚪ Not Started |

**Total**: 18 hours (~2-3 days focused work)

**Legend**: ✅ Complete | 🟡 In Progress | ⚪ Not Started | 🔴 Blocked

---

## Milestones M1-M3: COMPLETED ✅

### Summary of Completed Work:
- **M1: Project Setup** ✅ - Directory structure, dependencies (pyhottop, pyserial), pytest config
- **M2: Models & Exceptions** ✅ - 20 tests passing (SensorReading, RoastMetrics, exceptions hierarchy)
- **M3: Hardware Wrapper** ✅ - 28 tests passing
  - `MockRoaster` with thermal simulation (24 tests)
  - `HottopRoaster` with real hardware integration (2 tests, 1 skipped)
  - `StubRoaster` for demos (2 tests)
  - Manual integration test verified with physical roaster

**Test Status**: 53 tests passing, 1 skipped  
**Documentation**: See [M3_HARDWARE_WRAPPER_STATUS.md](../M3_HARDWARE_WRAPPER_STATUS.md)

---

## Milestone 1: Project Setup & pyhottop Research

**Goal**: Install pyhottop, understand API, create basic structure

**Estimated Time**: 2 hours

### Task 1.1: Research pyhottop Library ⚪

**Description**: Understand pyhottop API and map to our requirements.

**Steps**:
1. Clone pyhottop repository: `git clone https://github.com/splitkeycoffee/pyhottop.git /tmp/pyhottop`
2. Read source code and documentation
3. Identify available methods for:
   - Connection management
   - Sensor reading (bean temp, chamber temp, fan, heat)
   - Control commands (heat, fan, drum, cooling, drop)
4. Create API mapping document

**Deliverables**:
- `docs/research/pyhottop-api-mapping.md` - API reference for our use

**Success Criteria**: Clear understanding of pyhottop capabilities and limitations.

---

### Task 1.2: Add pyhottop to Dependencies ⚪

**Description**: Add pyhottop to requirements.txt and install.

**Commands**:
```bash
# Add to requirements.txt
echo "# Phase 2 Objective 2: Roaster Control" >> requirements.txt
echo "pyhottop>=0.1.0  # Hottop roaster USB control" >> requirements.txt
echo "pyserial>=3.5  # USB serial communication" >> requirements.txt

# Install
source venv/bin/activate
pip install pyhottop pyserial

# Verify
python -c "import pyhottop; print('pyhottop installed')"
```

**Deliverables**:
- Updated requirements.txt
- pyhottop installed in venv

**Success Criteria**: Import test passes.

---

### Task 1.3: Create Directory Structure ⚪

**Description**: Set up roaster control MCP server directory structure.

**Commands**:
```bash
# Create source directories
mkdir -p src/mcp_servers/roaster_control
touch src/mcp_servers/roaster_control/__init__.py
touch src/mcp_servers/roaster_control/__main__.py
touch src/mcp_servers/roaster_control/models.py
touch src/mcp_servers/roaster_control/exceptions.py
touch src/mcp_servers/roaster_control/hardware.py
touch src/mcp_servers/roaster_control/roast_tracker.py
touch src/mcp_servers/roaster_control/session_manager.py
touch src/mcp_servers/roaster_control/server.py
touch src/mcp_servers/roaster_control/config.py
touch src/mcp_servers/roaster_control/utils.py

# Create test directories
mkdir -p tests/mcp_servers/roaster_control/{unit,integration,manual}
touch tests/mcp_servers/roaster_control/__init__.py
touch tests/mcp_servers/roaster_control/unit/__init__.py
touch tests/mcp_servers/roaster_control/unit/test_models.py
touch tests/mcp_servers/roaster_control/unit/test_exceptions.py
touch tests/mcp_servers/roaster_control/unit/test_hardware.py
touch tests/mcp_servers/roaster_control/unit/test_roast_tracker.py
touch tests/mcp_servers/roaster_control/unit/test_session_manager.py
touch tests/mcp_servers/roaster_control/integration/__init__.py
touch tests/mcp_servers/roaster_control/integration/test_server.py
touch tests/mcp_servers/roaster_control/manual/__init__.py

# Create config directories
mkdir -p config/roaster_control
touch config/roaster_control/config.json
touch config/roaster_control/config.example.json
touch config/roaster_control/.env.example

# Create docs directories
mkdir -p docs/mcp_servers/roaster_control
mkdir -p docs/research
touch docs/mcp_servers/roaster_control/README.md
touch docs/mcp_servers/roaster_control/API.md
touch docs/mcp_servers/roaster_control/TESTING.md
```

**Deliverables**:
- Complete directory structure
- Placeholder files

**Success Criteria**: All directories exist, structure matches design doc.

---

### Task 1.4: Configure pytest ⚪

**Description**: Ensure pytest works with new test structure.

**File**: `pytest.ini` (update if exists, or create)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=src/mcp_servers/roaster_control
    --cov-report=term-missing
    --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
    manual: Manual tests requiring human interaction
env =
    PYTHONPATH=.
```

**Commands**:
```bash
# Verify pytest setup
./venv/bin/pytest tests/mcp_servers/roaster_control/ --collect-only
```

**Deliverables**:
- pytest.ini configured
- Test discovery working

**Success Criteria**: pytest finds test files (even if empty).

---

### Task 1.5: Create Mock Hardware Stub ⚪

**Description**: Create minimal MockHardware for development.

**File**: `src/mcp_servers/roaster_control/hardware.py`

```python
"""Hardware interface for Hottop roaster control."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

class HardwareInterface(ABC):
    """Abstract base class for roaster hardware."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to roaster hardware."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from hardware."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection status."""
        pass
    
    # More methods defined in M3

class MockHardware(HardwareInterface):
    """Simulated roaster for testing."""
    
    def __init__(self):
        self._connected = False
        self._bean_temp = 20.0
        self._chamber_temp = 20.0
        self._heat = 0
        self._fan = 0
    
    def connect(self) -> bool:
        self._connected = True
        return True
    
    def disconnect(self):
        self._connected = False
    
    def is_connected(self) -> bool:
        return self._connected
```

**Deliverables**:
- hardware.py with abstract interface
- MockHardware stub implementation

**Success Criteria**: Can import and instantiate MockHardware.

---

**Milestone 1 Complete**: ✅  
**Commit Message**: `M1: Setup roaster control MCP server structure and pyhottop integration`

---

## Milestone 2: Data Models & Exceptions (TDD)

**Goal**: Define all Pydantic models and exception hierarchy using TDD

**Estimated Time**: 2 hours

**TDD Workflow**: 🔴 RED → 🟢 GREEN → 🔵 REFACTOR → ✅ VERIFY

### Task 2.1: Implement Data Models (TDD) ⚪

**Description**: Create Pydantic models with validation using TDD.

**Step 1: 🔴 RED - Write Tests First**

**File**: `tests/mcp_servers/roaster_control/unit/test_models.py`

```python
"""Tests for data models."""
import pytest
from datetime import datetime, UTC
from src.mcp_servers.roaster_control.models import (
    SensorReading, RoastMetrics, RoastStatus,
    ControlCommand, FirstCrackReport, SessionInfo,
    HardwareConfig, TrackerConfig, ServerConfig
)

class TestSensorReading:
    def test_valid_reading(self):
        """Test valid sensor reading creation."""
        reading = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=185.5,
            chamber_temp_c=195.0,
            fan_speed_percent=70,
            heat_level_percent=60
        )
        assert reading.bean_temp_c == 185.5
        assert reading.fan_speed_percent == 70
    
    def test_temperature_validation_too_low(self):
        """Test temperature below valid range."""
        with pytest.raises(ValueError):
            SensorReading(
                timestamp=datetime.now(UTC),
                bean_temp_c=-100,  # Invalid
                chamber_temp_c=195.0,
                fan_speed_percent=70,
                heat_level_percent=60
            )
    
    def test_temperature_validation_too_high(self):
        """Test temperature above valid range."""
        with pytest.raises(ValueError):
            SensorReading(
                timestamp=datetime.now(UTC),
                bean_temp_c=400,  # Invalid
                chamber_temp_c=195.0,
                fan_speed_percent=70,
                heat_level_percent=60
            )
    
    def test_percentage_validation(self):
        """Test percentage field validation."""
        with pytest.raises(ValueError):
            SensorReading(
                timestamp=datetime.now(UTC),
                bean_temp_c=185.5,
                chamber_temp_c=195.0,
                fan_speed_percent=150,  # Invalid
                heat_level_percent=60
            )

# More test classes for other models...
# Total target: ~20 tests
```

**Step 2: 🟢 GREEN - Implement Models**

**File**: `src/mcp_servers/roaster_control/models.py`

```python
"""Data models for roaster control."""
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
    roast_elapsed_display: Optional[str] = None
    rate_of_rise_c_per_min: Optional[float] = None
    beans_added_temp_c: Optional[float] = None
    first_crack_temp_c: Optional[float] = None
    first_crack_time_display: Optional[str] = None
    development_time_seconds: Optional[int] = None
    development_time_display: Optional[str] = None
    development_time_percent: Optional[float] = None
    total_roast_duration_seconds: Optional[int] = None

# More models...
```

**Step 3: 🔵 REFACTOR - Improve**
- Add helper methods
- Improve validation messages
- Add model_config settings

**Step 4: ✅ VERIFY**
```bash
./venv/bin/pytest tests/mcp_servers/roaster_control/unit/test_models.py -v
```

**Target**: ~20 tests passing

**Deliverables**:
- models.py with 8+ Pydantic models
- test_models.py with ~20 tests
- All tests passing

---

### Task 2.2: Implement Exception Hierarchy (TDD) ⚪

**Description**: Create custom exceptions with TDD.

**Step 1: 🔴 RED - Write Tests**

**File**: `tests/mcp_servers/roaster_control/unit/test_exceptions.py`

```python
"""Tests for custom exceptions."""
import pytest
from src.mcp_servers.roaster_control.exceptions import (
    RoasterError, RoasterNotConnectedError,
    RoasterConnectionError, InvalidCommandError,
    NoActiveRoastError, BeansNotAddedError
)

class TestRoasterError:
    def test_base_exception(self):
        """Test base RoasterError."""
        error = RoasterError("Test error", "TEST_ERROR")
        assert str(error) == "Test error"
        assert error.error_code == "TEST_ERROR"

class TestRoasterNotConnectedError:
    def test_not_connected_error(self):
        """Test RoasterNotConnectedError."""
        error = RoasterNotConnectedError()
        assert "not connected" in str(error).lower()
        assert error.error_code == "ROASTER_NOT_CONNECTED"

# More test classes...
# Total target: ~10 tests
```

**Step 2: 🟢 GREEN - Implement Exceptions**

**File**: `src/mcp_servers/roaster_control/exceptions.py`

```python
"""Custom exceptions for roaster control."""

class RoasterError(Exception):
    """Base exception for roaster control."""
    def __init__(self, message: str, error_code: str):
        super().__init__(message)
        self.error_code = error_code

class RoasterNotConnectedError(RoasterError):
    """Raised when roaster is not connected."""
    def __init__(self):
        super().__init__(
            "Roaster not connected",
            "ROASTER_NOT_CONNECTED"
        )

# More exceptions...
```

**Step 3: ✅ VERIFY**
```bash
./venv/bin/pytest tests/mcp_servers/roaster_control/unit/test_exceptions.py -v
```

**Target**: ~10 tests passing

**Deliverables**:
- exceptions.py with 6+ custom exceptions
- test_exceptions.py with ~10 tests
- All tests passing

---

**Milestone 2 Complete**: ✅  
**Commit Message**: `M2: Add data models and exceptions with TDD (30 tests passing)`

---

## Milestone 3: Hardware Wrapper (TDD)

**Goal**: Wrap pyhottop with abstract interface and mock implementation

**Estimated Time**: 3 hours

### Task 3.1: Complete HardwareInterface ABC (TDD) ⚪

**Description**: Define complete abstract interface with tests.

**Step 1: 🔴 RED - Write Interface Tests**

**File**: `tests/mcp_servers/roaster_control/unit/test_hardware.py`

```python
"""Tests for hardware interface."""
import pytest
from src.mcp_servers.roaster_control.hardware import (
    HardwareInterface, MockHardware, HottopHardware
)
from src.mcp_servers.roaster_control.models import SensorReading
from src.mcp_servers.roaster_control.exceptions import (
    RoasterNotConnectedError, InvalidCommandError
)

class TestMockHardware:
    """Test MockHardware implementation."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.hardware = MockHardware()
    
    def test_initial_state(self):
        """Test hardware initial state."""
        assert not self.hardware.is_connected()
    
    def test_connect(self):
        """Test connection."""
        result = self.hardware.connect()
        assert result is True
        assert self.hardware.is_connected()
    
    def test_disconnect(self):
        """Test disconnection."""
        self.hardware.connect()
        self.hardware.disconnect()
        assert not self.hardware.is_connected()
    
    def test_read_sensors_when_not_connected(self):
        """Test reading sensors when not connected."""
        with pytest.raises(RoasterNotConnectedError):
            self.hardware.read_sensors()
    
    def test_read_sensors_when_connected(self):
        """Test reading sensors when connected."""
        self.hardware.connect()
        reading = self.hardware.read_sensors()
        assert isinstance(reading, SensorReading)
        assert reading.bean_temp_c >= 0
        assert reading.chamber_temp_c >= 0
    
    def test_set_heat_validation(self):
        """Test heat setting validation."""
        self.hardware.connect()
        
        # Valid values
        self.hardware.set_heat(60)
        assert self.hardware._heat == 60
        
        # Invalid: not 10% increment
        with pytest.raises(InvalidCommandError):
            self.hardware.set_heat(65)
        
        # Invalid: out of range
        with pytest.raises(InvalidCommandError):
            self.hardware.set_heat(150)
    
    def test_set_fan_validation(self):
        """Test fan setting validation."""
        self.hardware.connect()
        
        self.hardware.set_fan(80)
        assert self.hardware._fan == 80
        
        with pytest.raises(InvalidCommandError):
            self.hardware.set_fan(75)
    
    def test_temperature_simulation(self):
        """Test temperature rises with heat."""
        self.hardware.connect()
        
        initial_temp = self.hardware.read_sensors().bean_temp_c
        
        # Set heat and let simulation run
        self.hardware.set_heat(100)
        self.hardware.start_drum()
        
        # Simulate time passing
        import time
        time.sleep(0.1)
        
        # Temperature should increase
        new_temp = self.hardware.read_sensors().bean_temp_c
        assert new_temp > initial_temp

# More tests...
# Total target: ~25 tests
```

**Step 2: 🟢 GREEN - Implement Full MockHardware**

**File**: `src/mcp_servers/roaster_control/hardware.py`

```python
"""Hardware interface for Hottop roaster control."""
from abc import ABC, abstractmethod
from datetime import datetime, UTC
from typing import Optional
import time

from .models import SensorReading, HardwareConfig
from .exceptions import (
    RoasterNotConnectedError,
    InvalidCommandError,
    RoasterConnectionError
)

class HardwareInterface(ABC):
    """Abstract base class for roaster hardware."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to roaster hardware."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from hardware."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection status."""
        pass
    
    @abstractmethod
    def read_sensors(self) -> SensorReading:
        """Read all sensor values."""
        pass
    
    @abstractmethod
    def set_heat(self, percent: int):
        """Set heat level (0-100, 10% increments)."""
        pass
    
    @abstractmethod
    def set_fan(self, percent: int):
        """Set fan speed (0-100, 10% increments)."""
        pass
    
    @abstractmethod
    def start_drum(self):
        """Start roaster drum motor."""
        pass
    
    @abstractmethod
    def stop_drum(self):
        """Stop roaster drum motor."""
        pass
    
    @abstractmethod
    def drop_beans(self):
        """Open bean drop door."""
        pass
    
    @abstractmethod
    def start_cooling(self):
        """Start cooling fan."""
        pass
    
    @abstractmethod
    def stop_cooling(self):
        """Stop cooling fan."""
        pass

class MockHardware(HardwareInterface):
    """Simulated roaster for testing."""
    
    def __init__(self, config: Optional[HardwareConfig] = None):
        self._connected = False
        self._bean_temp = 20.0  # Room temp
        self._chamber_temp = 20.0
        self._heat = 0
        self._fan = 0
        self._drum_running = False
        self._cooling = False
        self._simulation_start = None
        self._last_update = time.time()
    
    def connect(self) -> bool:
        """Simulate connection."""
        self._connected = True
        self._simulation_start = time.time()
        return True
    
    def disconnect(self):
        """Simulate disconnection."""
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected
    
    def read_sensors(self) -> SensorReading:
        """Read simulated sensor values."""
        if not self._connected:
            raise RoasterNotConnectedError()
        
        # Update simulation
        self._update_simulation()
        
        return SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=round(self._bean_temp, 1),
            chamber_temp_c=round(self._chamber_temp, 1),
            fan_speed_percent=self._fan,
            heat_level_percent=self._heat
        )
    
    def set_heat(self, percent: int):
        """Set heat level."""
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._validate_percentage(percent, "heat")
        self._heat = percent
    
    def set_fan(self, percent: int):
        """Set fan speed."""
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._validate_percentage(percent, "fan")
        self._fan = percent
    
    def start_drum(self):
        """Start drum motor."""
        if not self._connected:
            raise RoasterNotConnectedError()
        self._drum_running = True
    
    def stop_drum(self):
        """Stop drum motor."""
        if not self._connected:
            raise RoasterNotConnectedError()
        self._drum_running = False
    
    def drop_beans(self):
        """Open drop door."""
        if not self._connected:
            raise RoasterNotConnectedError()
        self._drum_running = False
        self.start_cooling()
    
    def start_cooling(self):
        """Start cooling fan."""
        if not self._connected:
            raise RoasterNotConnectedError()
        self._cooling = True
    
    def stop_cooling(self):
        """Stop cooling fan."""
        if not self._connected:
            raise RoasterNotConnectedError()
        self._cooling = False
    
    def _validate_percentage(self, value: int, name: str):
        """Validate percentage is in 10% increments."""
        if value < 0 or value > 100:
            raise InvalidCommandError(
                f"set_{name}",
                f"Value must be 0-100, got {value}"
            )
        if value % 10 != 0:
            raise InvalidCommandError(
                f"set_{name}",
                f"Value must be in 10% increments, got {value}"
            )
    
    def _update_simulation(self):
        """Update simulated temperatures based on heat/fan."""
        now = time.time()
        dt = now - self._last_update
        self._last_update = now
        
        if not self._drum_running:
            return
        
        # Simplified thermal model
        # Heat increases temperature, fan cools
        heat_effect = self._heat / 100.0 * 2.0  # °C/sec
        fan_effect = self._fan / 100.0 * 0.5  # °C/sec cooling
        cooling_effect = 5.0 if self._cooling else 0  # °C/sec
        
        # Bean temperature follows chamber with lag
        chamber_delta = (heat_effect - fan_effect - cooling_effect) * dt
        self._chamber_temp += chamber_delta
        
        # Bean temp lags chamber by ~10°C
        bean_target = self._chamber_temp - 10.0
        bean_delta = (bean_target - self._bean_temp) * 0.1 * dt
        self._bean_temp += bean_delta
        
        # Clamp to realistic values
        self._chamber_temp = max(20.0, min(300.0, self._chamber_temp))
        self._bean_temp = max(20.0, min(250.0, self._bean_temp))

class HottopHardware(HardwareInterface):
    """Real Hottop hardware using pyhottop library."""
    
    def __init__(self, config: HardwareConfig):
        self._config = config
        self._hottop = None
        self._connected = False
    
    def connect(self) -> bool:
        """Connect to real hardware via pyhottop."""
        # TODO: Implement in M3 task 3.2
        raise NotImplementedError("Real hardware not yet implemented")
    
    # Other methods raise NotImplementedError for now
```

**Step 3: ✅ VERIFY**
```bash
./venv/bin/pytest tests/mcp_servers/roaster_control/unit/test_hardware.py -v
```

**Target**: ~25 tests passing

**Deliverables**:
- Complete HardwareInterface ABC
- Full MockHardware with simulation
- HottopHardware stub
- test_hardware.py with ~25 tests

---

### Task 3.2: Implement HottopHardware (Stub) ⚪

**Description**: Implement real hardware wrapper (stub for now, will complete when hardware available).

**Note**: Without physical hardware, this will be a documented stub that can be completed later.

**File**: Update `src/mcp_servers/roaster_control/hardware.py`

```python
class HottopHardware(HardwareInterface):
    """Real Hottop hardware using pyhottop library."""
    
    def __init__(self, config: HardwareConfig):
        self._config = config
        self._hottop = None
        self._connected = False
        self._port = config.port
        self._baud_rate = config.baud_rate
    
    def connect(self) -> bool:
        """Connect to real hardware via USB serial."""
        try:
            # Import pyhottop
            import pyhottop
            
            # Initialize connection
            # TODO: Update with actual pyhottop API from M1 research
            # self._hottop = pyhottop.Hottop(port=self._port, baud=self._baud_rate)
            # self._hottop.connect()
            
            self._connected = True
            return True
            
        except Exception as e:
            raise RoasterConnectionError(str(e))
    
    # Other methods: See docs/research/pyhottop-api-mapping.md
    # Will implement when hardware available
```

**Deliverables**:
- HottopHardware with documented stubs
- Ready for real implementation when hardware available

---

### Task 3.3: Add Utilities (utils.py) ⚪

**Description**: Common utility functions (from first crack detector).

**File**: `src/mcp_servers/roaster_control/utils.py`

```python
"""Utility functions for roaster control."""
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Tuple

def format_time(seconds: int) -> str:
    """Format seconds as MM:SS."""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"

def get_timestamps(dt: datetime, timezone: str) -> Tuple[datetime, datetime]:
    """Get UTC and local timestamps."""
    utc_time = dt if dt.tzinfo else dt.replace(tzinfo=ZoneInfo("UTC"))
    local_time = utc_time.astimezone(ZoneInfo(timezone))
    return utc_time, local_time
```

**Deliverables**:
- utils.py with helper functions

---

**Milestone 3 Complete**: ✅  
**Commit Message**: `M3: Implement hardware wrapper with MockHardware (25 tests passing)`

---

## Milestone 4: Roast Tracker (TDD)

**Goal**: Implement roast metrics computation logic

**Estimated Time**: 4 hours (most complex component)

**Progress**: M4 Complete (27 tests), M5 Complete (24 tests), M6-M7 remaining

### Task 4.1: Implement T0 Detection (TDD) ✅

**Description**: Auto-detect bean addition from temperature drop.

**Step 1: 🔴 RED - Write T0 Detection Tests**

**File**: `tests/mcp_servers/roaster_control/unit/test_roast_tracker.py`

```python
"""Tests for roast tracker."""
import pytest
from datetime import datetime, UTC, timedelta
from src.mcp_servers.roaster_control.roast_tracker import RoastTracker
from src.mcp_servers/roaster_control.models import (
    SensorReading, TrackerConfig
)

class TestT0Detection:
    """Test bean addition detection."""
    
    def setup_method(self):
        """Setup tracker."""
        config = TrackerConfig(t0_detection_threshold=10.0)
        self.tracker = RoastTracker(config)
    
    def test_t0_not_detected_initially(self):
        """Test T0 is None initially."""
        assert self.tracker.get_t0() is None
    
    def test_t0_detected_on_temperature_drop(self):
        """Test T0 detected when temp drops >10°C."""
        # Preheat phase
        reading1 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=170.0,
            chamber_temp_c=180.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading1)
        assert self.tracker.get_t0() is None
        
        # Beans added - temp drops
        reading2 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=155.0,  # Dropped 15°C
            chamber_temp_c=175.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading2)
        
        # T0 should be detected
        assert self.tracker.get_t0() is not None
        assert self.tracker.get_beans_added_temp() == 170.0
    
    def test_t0_not_detected_on_small_drop(self):
        """Test T0 not detected for small temperature drops."""
        reading1 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=170.0,
            chamber_temp_c=180.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading1)
        
        reading2 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=165.0,  # Only 5°C drop
            chamber_temp_c=175.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading2)
        
        assert self.tracker.get_t0() is None
    
    def test_t0_only_detected_once(self):
        """Test T0 is only detected once."""
        # First detection
        reading1 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=170.0,
            chamber_temp_c=180.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading1)
        
        reading2 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=150.0,
            chamber_temp_c=175.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading2)
        
        t0_first = self.tracker.get_t0()
        
        # Another big drop (shouldn't change T0)
        reading3 = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=130.0,  # Another big drop
            chamber_temp_c=170.0,
            fan_speed_percent=50,
            heat_level_percent=100
        )
        self.tracker.update(reading3)
        
        assert self.tracker.get_t0() == t0_first

# More test classes for RoR, development time, etc.
# Total target: ~30 tests
```

**Step 2: 🟢 GREEN - Implement RoastTracker**

**File**: `src/mcp_servers/roaster_control/roast_tracker.py`

```python
"""Roast metrics tracker."""
from datetime import datetime, UTC
from typing import Optional, Deque
from collections import deque
import structlog

from .models import SensorReading, RoastMetrics, TrackerConfig
from .utils import format_time

logger = structlog.get_logger()

class RoastTracker:
    """Tracks and computes roast metrics from sensor readings."""
    
    def __init__(self, config: TrackerConfig):
        self._config = config
        
        # Timestamps
        self._t0: Optional[datetime] = None
        self._first_crack: Optional[datetime] = None
        self._drop: Optional[datetime] = None
        
        # Temperature buffer (60 seconds)
        self._temp_buffer: Deque = deque(maxlen=60)
        
        # Captured values
        self._beans_added_temp: Optional[float] = None
        self._first_crack_temp: Optional[float] = None
        self._drop_temp: Optional[float] = None
    
    def update(self, reading: SensorReading):
        """Process new sensor reading."""
        self._temp_buffer.append((reading.timestamp, reading.bean_temp_c))
        
        # Auto-detect T0 if not set
        if self._t0 is None:
            self._detect_beans_added(reading)
    
    def _detect_beans_added(self, reading: SensorReading):
        """Detect sudden temperature drop indicating beans added."""
        if len(self._temp_buffer) < 2:
            return
        
        prev_timestamp, prev_temp = self._temp_buffer[-2]
        curr_temp = reading.bean_temp_c
        
        drop = prev_temp - curr_temp
        
        if drop > self._config.t0_detection_threshold:
            self._t0 = reading.timestamp
            self._beans_added_temp = prev_temp
            logger.info(
                "beans_added_detected",
                temp=prev_temp,
                drop=drop,
                threshold=self._config.t0_detection_threshold
            )
    
    def get_t0(self) -> Optional[datetime]:
        """Get T0 (beans added time)."""
        return self._t0
    
    def get_beans_added_temp(self) -> Optional[float]:
        """Get temperature when beans were added."""
        return self._beans_added_temp
    
    # More methods implemented in subsequent tasks
```

**Step 3: ✅ VERIFY**
```bash
./venv/bin/pytest tests/mcp_servers/roaster_control/unit/test_roast_tracker.py::TestT0Detection -v
```

**Deliverables**:
- T0 detection implemented
- Tests passing

---

### Task 4.2: Implement RoR Calculation (TDD) ✅

**Description**: Calculate rate of rise from 60-second buffer.

**Add tests and implementation for**:
- `get_rate_of_rise()` method
- Buffer management
- Edge cases (< 60 seconds of data)

**Target**: ~8 more tests

---

### Task 4.3: Implement Development Time Tracking (TDD) ⚪

**Description**: Track first crack and compute development time percentage.

**Add tests and implementation for**:
- `report_first_crack(timestamp, temp)` method
- `get_development_time_percent()` method
- Development time displays

**Target**: ~7 more tests

---

### Task 4.4: Implement Drop Recording (TDD) ⚪

**Description**: Record bean drop event and final metrics.

**Add tests and implementation for**:
- `record_drop(temp)` method
- Total roast duration
- get_metrics() complete implementation

**Target**: ~5 more tests

---

**Milestone 4 Complete**: ✅  
**Commit Message**: `M4: Implement roast tracker with T0, RoR, and development time (30 tests passing)`

---

## Milestone 5: Session Manager (TDD)

**Goal**: Orchestrate hardware and tracker with thread-safe operations

**Estimated Time**: 3 hours

### Task 5.1: Implement Session Lifecycle (TDD) ⚪

**Description**: Session start/stop with hardware and tracker integration.

**Tests**: `tests/mcp_servers/roaster_control/unit/test_session_manager.py`

**Implementation**: `src/mcp_servers/roaster_control/session_manager.py`

**Key features**:
- start_session() - Connect hardware, start polling thread
- stop_session() - Stop polling, disconnect
- Thread-safe with threading.Lock
- Idempotent operations

**Target**: ~10 tests

---

### Task 5.2: Implement Control Commands (TDD) ⚪

**Description**: Execute hardware control commands with validation.

**Key features**:
- execute_command(command) method
- Route to appropriate hardware methods
- Validate before execution
- Error handling

**Target**: ~8 tests

---

### Task 5.3: Implement Status Queries (TDD) ⚪

**Description**: Build complete RoastStatus from hardware + tracker.

**Key features**:
- get_status() - Complete status snapshot
- Atomic with lock
- Combine sensor readings and metrics
- Format timestamps (UTC + local)

**Target**: ~7 tests

---

**Milestone 5 Complete**: ✅  
**Commit Message**: `M5: Implement session manager with thread-safe operations (25 tests passing)`

---

## Milestone 6: MCP Server Implementation

**Goal**: Wire up MCP protocol with all components

**Estimated Time**: 2 hours

### Task 6.1: Implement MCP Server Skeleton ⚪

**Description**: Create MCP server with global session manager.

**File**: `src/mcp_servers/roaster_control/server.py`

```python
"""MCP server for roaster control."""
import structlog
from mcp.server import Server
from mcp.types import Tool, Resource

from .session_manager import RoastSessionManager
from .hardware import MockHardware
from .config import load_config
from .exceptions import RoasterError

logger = structlog.get_logger()

# Global state
_session_manager: Optional[RoastSessionManager] = None
_config = None

# Create MCP server
server = Server("roaster-control")

def init_server():
    """Initialize server with configuration."""
    global _session_manager, _config
    
    _config = load_config()
    
    # Create hardware (mock or real based on config)
    if _config.hardware.mock_mode:
        hardware = MockHardware(_config.hardware)
    else:
        hardware = HottopHardware(_config.hardware)
    
    _session_manager = RoastSessionManager(hardware, _config)
    
    logger.info("server_initialized", mock_mode=_config.hardware.mock_mode)

# Tool implementations in next tasks
```

---

### Task 6.2: Implement Control Tools ⚪

**Description**: Implement 8 control tools.

```python
@server.tool()
async def set_heat(target_percent: int) -> dict:
    """Set roaster heat to target percentage."""
    try:
        result = _session_manager.set_heat(target_percent)
        return {"success": True, "heat_set": target_percent}
    except RoasterError as e:
        return {"success": False, "error": str(e), "error_code": e.error_code}

# Similar for: set_fan, start_roaster, stop_roaster,
# drop_beans, start_cooling, stop_cooling, report_first_crack
```

---

### Task 6.3: Implement Query Tool ⚪

**Description**: Implement get_roast_status tool.

```python
@server.tool()
async def get_roast_status() -> dict:
    """Get complete roast status."""
    try:
        status = _session_manager.get_status()
        return status.model_dump()
    except RoasterError as e:
        return {"error": str(e), "error_code": e.error_code}
```

---

### Task 6.4: Implement Health Resource & Main ⚪

**Description**: Add health resource and module entry point.

```python
@server.resource("health://status")
async def get_health() -> dict:
    """Server health check."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "hardware": "mock" if _config.hardware.mock_mode else "real",
        "session_active": _session_manager.is_active() if _session_manager else False
    }
```

**File**: `src/mcp_servers/roaster_control/__main__.py`

```python
"""Entry point for roaster control MCP server."""
import asyncio
import sys
from .server import server, init_server

async def main():
    """Run MCP server."""
    init_server()
    
    # Run stdio server
    from mcp.server.stdio import stdio_server
    async with stdio_server() as streams:
        await server.run(
            streams[0],  # read stream
            streams[1],  # write stream
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

---

**Milestone 6 Complete**: ✅  
**Commit Message**: `M6: Implement MCP server with 9 tools and health resource`

---

## Milestone 7: Configuration & Documentation

**Goal**: Finalize config system and comprehensive documentation

**Estimated Time**: 2 hours

### Task 7.1: Implement Configuration System ⚪

**Description**: Config loading with env var overrides.

**File**: `src/mcp_servers/roaster_control/config.py`

```python
"""Configuration management."""
import json
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

class HardwareConfig(BaseModel):
    port: str = "/dev/tty.usbserial-1420"
    baud_rate: int = 115200
    timeout: float = 1.0
    mock_mode: bool = True  # Default to mock for safety

class TrackerConfig(BaseModel):
    t0_detection_threshold: float = 10.0
    polling_interval: float = 1.0
    ror_window_size: int = 60
    development_time_target_min: float = 15.0
    development_time_target_max: float = 20.0

class ServerConfig(BaseModel):
    hardware: HardwareConfig = HardwareConfig()
    tracker: TrackerConfig = TrackerConfig()
    logging_level: str = "INFO"
    timezone: str = "America/Los_Angeles"

def load_config(path: Optional[str] = None) -> ServerConfig:
    """Load configuration from file and environment."""
    # Default path
    if path is None:
        path = "config/roaster_control/config.json"
    
    # Load from file if exists
    config_dict = {}
    config_path = Path(path)
    if config_path.exists():
        with open(config_path) as f:
            config_dict = json.load(f)
    
    # Environment variable overrides
    if "ROASTER_PORT" in os.environ:
        config_dict.setdefault("hardware", {})["port"] = os.environ["ROASTER_PORT"]
    
    if "ROASTER_MOCK_MODE" in os.environ:
        config_dict.setdefault("hardware", {})["mock_mode"] = \
            os.environ["ROASTER_MOCK_MODE"].lower() == "true"
    
    return ServerConfig(**config_dict)
```

**Config files**:
- `config/roaster_control/config.json`
- `config/roaster_control/config.example.json`
- `config/roaster_control/.env.example`

---

### Task 7.2: Write README.md ⚪

**Description**: Main server documentation.

**File**: `docs/mcp_servers/roaster_control/README.md`

**Sections**:
- Overview
- Features
- Installation
- Configuration
- Usage Examples
- Development
- Testing
- Troubleshooting

---

### Task 7.3: Write API.md ⚪

**Description**: Complete API reference for all tools.

**File**: `docs/mcp_servers/roaster_control/API.md`

**Sections**:
- Tool specifications (all 9 tools)
- Request/response schemas
- Error codes
- Examples

---

### Task 7.4: Manual Testing ⚪

**Description**: Test end-to-end with mock hardware.

**Script**: `tests/mcp_servers/roaster_control/manual/test_full_roast.py`

```python
"""Manual test: Simulate full roast cycle."""
import time
import asyncio
from src.mcp_servers.roaster_control.server import init_server, _session_manager

async def simulate_roast():
    """Simulate a complete roast cycle."""
    print("=== Roast Simulation ===\n")
    
    # Initialize
    init_server()
    manager = _session_manager
    
    # Start session
    print("1. Starting session...")
    manager.start_session()
    time.sleep(1)
    
    # Preheat
    print("\n2. Preheating...")
    manager.set_heat(100)
    manager.start_roaster()
    
    for i in range(10):
        status = manager.get_status()
        print(f"   Bean temp: {status.sensors.bean_temp_c:.1f}°C")
        time.sleep(1)
    
    # Simulate bean drop (will trigger T0 detection)
    print("\n3. Beans added (T0)...")
    # Temperature will drop in MockHardware simulation
    
    # Continue roasting
    print("\n4. Roasting...")
    for i in range(60):
        status = manager.get_status()
        if status.metrics.roast_elapsed_seconds:
            print(f"   Time: {status.metrics.roast_elapsed_display} | "
                  f"Temp: {status.sensors.bean_temp_c:.1f}°C | "
                  f"RoR: {status.metrics.rate_of_rise_c_per_min or 0:.1f}°C/min")
        time.sleep(1)
    
    # Report first crack
    print("\n5. First crack detected!")
    manager.report_first_crack("2025-10-25T18:00:00Z", "3 pops")
    
    # Development phase
    print("\n6. Development phase...")
    for i in range(30):
        status = manager.get_status()
        if status.metrics.development_time_percent:
            print(f"   Dev time: {status.metrics.development_time_percent:.1f}%")
        time.sleep(1)
    
    # Drop beans
    print("\n7. Dropping beans...")
    manager.drop_beans()
    
    # Final status
    print("\n8. Roast complete!")
    final_status = manager.get_status()
    print(f"   Total time: {final_status.metrics.total_roast_duration_seconds}s")
    print(f"   Final temp: {final_status.sensors.bean_temp_c:.1f}°C")
    
    # Stop
    manager.stop_session()
    print("\n=== Simulation Complete ===")

if __name__ == "__main__":
    asyncio.run(simulate_roast())
```

**Run**:
```bash
./venv/bin/python tests/mcp_servers/roaster_control/manual/test_full_roast.py
```

---

**Milestone 7 Complete**: ✅  
**Commit Message**: `M7: Add configuration, documentation, and manual tests (Phase 2 Obj 2 complete)`

---

## Testing Summary

### Unit Tests
- models.py: ~20 tests
- exceptions.py: ~10 tests
- hardware.py: ~25 tests
- roast_tracker.py: ~30 tests
- session_manager.py: ~25 tests
- **Total**: ~110 unit tests

### Integration Tests
- server.py: ~10 tests
- **Total**: ~10 integration tests

### Manual Tests
- Full roast simulation
- Control commands
- Error scenarios

### Target Coverage
- >90% code coverage
- All critical paths tested
- Edge cases covered

---

## Success Criteria

**Phase 2 Objective 2 Complete** when:
- ✅ All 120+ tests passing
- ✅ MCP server runs and exposes 9 tools
- ✅ MockHardware simulation works realistically
- ✅ get_roast_status() returns complete data
- ✅ All control commands validated
- ✅ Metrics computed correctly (T0, RoR, dev time)
- ✅ Thread-safe implementation verified
- ✅ Documentation complete
- ✅ Manual roast simulation successful
- ✅ Ready for Warp integration
- ✅ Ready for real hardware testing

---

## Post-Completion

### Next Steps
1. Integrate both MCP servers in Warp
2. Test coordinated workflow (detection → control)
3. Complete HottopHardware with real roaster
4. Phase 3: Auth0, HTTP, production deployment

### Known Limitations
- HottopHardware is a stub (needs real hardware)
- Single session only
- In-memory state (no persistence)
- stdio transport only (no HTTP yet)
- No authentication (Phase 3)

---

## References

- [Requirements](../requirements/phase-2-objective-2-requirements.md)
- [Design](../design/phase-2-objective-2-design.md)
- [Phase 2 Requirements](../requirements/phase-2.md)
- [Phase 2 Objective 1 Complete](../mcp_servers/PHASE2_OBJ1_COMPLETE.md)

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-25  
**Status**: Ready for Implementation
