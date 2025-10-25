# Phase 2 Objective 1 - Implementation Plan
## First Crack Detection MCP Server

**Status**: Ready to Start  
**Last Updated**: 2025-01-25  
**Estimated Duration**: 3-4 days

---

## Overview

Build an MCP server that wraps the existing FirstCrackDetector, exposing it as standardized MCP tools for n8n workflow integration. The server will support three audio sources (file, USB mic, built-in mic) and provide real-time first crack detection status with local/UTC timestamps.

**Client**: n8n workflow engine (local development, cloud production)  
**Transport**: stdio (Phase 2), HTTP + Cloudflare tunnel (Phase 3)

---

## Milestones
| Milestone | Tasks | Estimated Time | Status |
|-----------|-------|----------------|--------|
| **M1: Project Setup** | 4 tasks | 2-3 hours | ✅ Complete |
| **M2: Core Components** | 6 tasks | 6-8 hours | 🟡 In Progress (6/6) |
| **M3: MCP Server Implementation** | 5 tasks | 4-6 hours | ✅ Complete |
| **M4: Testing & Validation** | 4 tasks | 3-4 hours | ✅ Complete |
| **M5: Documentation** | 3 tasks | 2-3 hours | ⚪ Not Started |
| **M5: Documentation** | 3 tasks | 2-3 hours | ⚪ Not Started |

**Total Estimated Time**: 17-24 hours (3-4 days)

**Legend**: ✅ Complete | 🟡 In Progress | ⚪ Not Started | 🔴 Blocked

---

## Milestone 1: Project Setup

### Task 1.1: Create Directory Structure ⚪
**Description**: Set up MCP server project directory structure under src/.

**Commands**:
```bash
# Create MCP server source directories
mkdir -p src/mcp_servers/first_crack_detection

# Create test directories
mkdir -p tests/mcp_servers/first_crack_detection/{unit,integration}

# Create config directory
mkdir -p config/first_crack_detection

# Create docs directory
mkdir -p docs/mcp_servers/first_crack_detection

# Create placeholder files
touch src/mcp_servers/__init__.py
touch src/mcp_servers/first_crack_detection/__init__.py
touch tests/mcp_servers/__init__.py
touch tests/mcp_servers/first_crack_detection/__init__.py
touch config/first_crack_detection/config.example.json
touch config/first_crack_detection/.env.example
touch docs/mcp_servers/first_crack_detection/README.md
touch docs/mcp_servers/first_crack_detection/DEPLOYMENT.md
```

**Deliverables**:
- Directory structure created
- Placeholder files in place

**Success Criteria**: All directories exist, structure matches design doc.

---

### Task 1.2: Create requirements.txt ⚪
**Description**: Define dependencies for MCP server.

**Note**: We'll add MCP server dependencies to the existing root `requirements.txt` to maintain single environment.

**Contents**:
```
# MCP SDK
mcp>=0.1.0

# Existing dependencies (from Phase 1)
torch>=2.1.0
transformers>=4.35.0
librosa>=0.10.0
sounddevice>=0.4.0
numpy>=1.24.0

# Data validation
pydantic>=2.0.0

# Timezone handling
python-dateutil>=2.8.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# Logging
structlog>=23.1.0
```

**Deliverables**:
- requirements.txt created

**Success Criteria**: All dependencies listed with version constraints.

---

### Task 1.3: Install Dependencies & Verify Environment ⚪
**Description**: Install new dependencies in existing venv and verify.

**Commands**:
```bash
# Activate venv
source venv/bin/activate

# Install MCP server dependencies (added to root requirements.txt)
pip install mcp pydantic python-dateutil structlog pytest-asyncio

# Verify installations
python -c "import mcp; print(f'MCP SDK installed')"
python -c "import pydantic; print(f'Pydantic: {pydantic.__version__}')"
```

**Deliverables**:
- All dependencies installed
- No conflicts with existing Phase 1 dependencies

**Success Criteria**: Import tests pass, no errors.

---

### Task 1.4: Create Configuration Files ⚪
**Description**: Create example and template configuration files.

**File 1**: `config/first_crack_detection/config.example.json`
```json
{
  "model_checkpoint": "/path/to/experiments/final_model/model.pt",
  "detection_defaults": {
    "threshold": 0.5,
    "min_pops": 3,
    "confirmation_window": 30.0
  },
  "audio": {
    "sample_rate": 16000,
    "window_size": 10.0,
    "overlap": 0.7
  },
  "logging": {
    "level": "INFO",
    "format": "json"
  }
}
```

**File 2**: `config/first_crack_detection/.env.example`
```bash
# Optional environment variable overrides
FIRST_CRACK_MODEL_CHECKPOINT=/path/to/model.pt
FIRST_CRACK_LOG_LEVEL=INFO
```

**Deliverables**:
- config.example.json
- .env.example

**Success Criteria**: Files created, documented.

---

## Milestone 2: Core Components

**Approach**: Test-Driven Development (TDD) - Red, Green, Refactor

**TDD Workflow for Each Task**:
1. 🔴 **RED**: Write failing test first
2. 🟢 **GREEN**: Write minimal code to make test pass
3. 🔵 **REFACTOR**: Clean up code, improve design
4. ✅ **VERIFY**: Run all tests to ensure nothing broke

**Benefits**:
- Catch bugs early
- Clear requirements from tests
- Confidence in refactoring
- Better code design

### Task 2.1: Implement Data Models (models.py) ✅
**Description**: Create Pydantic models for all data structures using TDD.
**Status**: Complete (2025-01-25)
**Test Results**: 19/19 tests passing

**File**: `src/mcp_servers/first_crack_detection/models.py`

**TDD Approach**:

**Step 1: 🔴 RED - Write Tests First**

Create `tests/mcp_servers/first_crack_detection/unit/test_models.py`:
- Test AudioConfig validation (file path required when type=audio_file)
- Test DetectionConfig defaults and ranges
- Test SessionInfo structure
- Test StatusInfo with/without detection
- Test SessionSummary
- Test ServerConfig

**Step 2: 🟢 GREEN - Implement Models**

Create `src/mcp_servers/first_crack_detection/models.py`:
1. `AudioConfig` - Audio source configuration
2. `DetectionConfig` - Detection parameters  
3. `SessionInfo` - Start response
4. `StatusInfo` - Status response
5. `SessionSummary` - Stop response
6. `ServerConfig` - Server configuration
7. `DetectionSession` (dataclass) - Internal state

**Step 3: 🔵 REFACTOR - Clean Up**
- Add docstrings
- Organize imports
- Add helper methods if needed

**Testing**:
```bash
# Run tests (watch them fail, then pass)
pytest tests/mcp_servers/first_crack_detection/unit/test_models.py -v
```

**Success Criteria**: 
- ✅ All tests pass
- ✅ Models have proper validation
- ✅ Type hints complete
- ✅ Edge cases covered

---

### Task 2.2: Implement Custom Exceptions (models.py) ✅
**Description**: Create exception hierarchy for error handling.
**Status**: Complete (2025-01-25)
**Test Results**: 12/12 tests passing

**Exceptions**:
- `DetectionError` (base)
- `ModelNotFoundError`
- `MicrophoneNotAvailableError`
- `FileNotFoundError`
- `SessionAlreadyActiveError`
- `ThreadCrashError`
- `InvalidAudioSourceError`

**Each Exception Includes**:
- `error_code` class attribute
- Human-readable message
- Optional `details` dict

**Success Criteria**: All exceptions defined with error codes.

---

### Task 2.3: Implement Audio Device Management (audio_devices.py) ✅
**Description**: Audio device discovery and validation.
**Status**: Complete (2025-01-25)
**Test Results**: 16/16 tests passing

**File**: `src/mcp_servers/first_crack_detection/audio_devices.py`

**Functions**:
```python
def list_audio_devices() -> List[Dict[str, Any]]:
    """List all input devices."""

def find_usb_microphone() -> Optional[int]:
    """Find first USB audio input device."""

def find_builtin_microphone() -> Optional[int]:
    """Find built-in microphone."""

def get_device_info(device_index: int) -> Dict[str, Any]:
    """Get device details."""

def validate_audio_source(config: AudioConfig) -> Tuple[bool, str]:
    """Validate audio source availability."""
```

**Testing**:
```bash
# List devices on current machine
python -m src.mcp_servers.first_crack_detection.audio_devices

# Unit tests
pytest tests/mcp_servers/first_crack_detection/unit/test_audio_devices.py -v
```

**Success Criteria**:
- Can enumerate audio devices
- USB/built-in detection works
- Validation function returns helpful errors

---

### Task 2.4: Implement Utilities (utils.py) ✅
**Description**: Timezone and formatting utilities.
**Status**: Complete (2025-01-25)
**Test Results**: 15/15 tests passing

**File**: `src/mcp_servers/first_crack_detection/utils.py`

**Functions**:
```python
def get_local_timezone() -> ZoneInfo:
    """Get system local timezone."""

def to_local_time(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to local timezone."""

def format_elapsed_time(seconds: float) -> str:
    """Format seconds as MM:SS."""

def setup_logging(config: ServerConfig):
    """Configure structured logging."""
```

**Testing**:
```bash
pytest tests/mcp_servers/first_crack_detection/unit/test_utils.py -v
```

**Success Criteria**: All utility functions tested, timezone conversion works.

**TDD Summary**:
- 🔴 RED: Created 15 failing tests for timezone, formatting, and logging utilities
- 🟢 GREEN: Implemented all utility functions to pass tests
- 🔵 REFACTOR: Fixed timezone detection to use ZoneInfo.key attribute
- ✅ VERIFIED: All 62 unit tests passing (models + exceptions + audio_devices + utils)

---

### Task 2.5: Implement Configuration Manager (config.py) ✅
**Description**: Configuration loading with env var overrides.

**File**: `src/mcp_servers/first_crack_detection/config.py`

**Functions**:
```python
def load_config(config_path: Optional[str] = None) -> ServerConfig:
    """
    Load configuration from file and environment variables.
    
    Priority: env vars > config file > defaults
    """
    # Load from JSON file
    # Override with env vars
    # Validate
    # Return ServerConfig
```

**Testing**:
```bash
# Test with example config
python -c "from src.mcp_servers.first_crack_detection.config import load_config; print(load_config('config/first_crack_detection/config.example.json'))"

# Unit tests
pytest tests/mcp_servers/first_crack_detection/unit/test_config.py -v
```

**Success Criteria**: Config loading works, env var overrides work.

**TDD Summary**:
- 🔴 RED: Created 11 failing tests for config loading, env var overrides, and validation
- 🟢 GREEN: Implemented load_config with JSON parsing, env var priority, defaults, nested config flattening
- 🔵 REFACTOR: Added Field validators to ServerConfig for proper validation
- ✅ VERIFIED: All 73 unit tests passing (models + exceptions + audio_devices + utils + config)

---

### Task 2.6: Implement DetectionSessionManager (session_manager.py) ✅
**Description**: Core session management logic.
**Status**: Complete (2025-01-25)
**Test Results**: 13/13 tests passing

**File**: `src/mcp_servers/first_crack_detection/session_manager.py`

**Class**: `DetectionSessionManager`

**Methods**:
```python
def __init__(self, config: ServerConfig)
def start_session(self, audio_config: AudioConfig) -> SessionInfo
def get_status(self) -> StatusInfo
def stop_session(self) -> SessionSummary
def _validate_audio_source(self, config: AudioConfig)
def _validate_model_checkpoint(self)
def _create_detector(self, audio_config: AudioConfig) -> FirstCrackDetector
def _get_session_info(self, already_running: bool) -> SessionInfo
def _build_status_info(self, result: Union[bool, Tuple]) -> StatusInfo
def _build_session_summary(self, session: DetectionSession) -> SessionSummary
```

**Testing**:
```bash
# Unit tests with mocked FirstCrackDetector
pytest tests/mcp_servers/first_crack_detection/unit/test_session_manager.py -v
```

**Success Criteria**:
- All methods implemented
- Thread-safe (uses lock)
- Idempotency enforced
- Unit tests pass

**TDD Summary**:
- 🔴 RED: Created 13 comprehensive tests covering session lifecycle, thread safety, idempotency, validation, error handling
- 🟢 GREEN: Implemented DetectionSessionManager with full lifecycle management, thread locking, FirstCrackDetector integration
- 🔵 REFACTOR: Fixed test mocks to properly return tuples from detector
- ✅ VERIFIED: All 86 unit tests passing - **Milestone 2 Complete!**

**Implementation Highlights**:
- Thread-safe singleton-style session management with threading.Lock
- Idempotent start/stop operations
- Comprehensive validation (model checkpoint, audio files, microphones)
- UTC + local timezone support for all timestamps
- Proper cleanup and resource management
- Detailed status and summary responses

---

## Milestone 3: MCP Server Implementation

### Task 3.1: Implement MCP Server Skeleton (server.py) ⚪
**Description**: Set up MCP server with tool registration.

**File**: `src/mcp_servers/first_crack_detection/server.py`

**Structure**:
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Initialize
session_manager = DetectionSessionManager(config)
server = Server("first-crack-detection-server")

# Register tools (next task)

async def main():
    """Run MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

**Success Criteria**: Server starts, no errors, ready for tool registration.

---

### Task 3.2: Implement Tool: start_first_crack_detection ⚪
**Description**: Tool handler for starting detection.

**Implementation**:
```python
@server.tool()
async def start_first_crack_detection(
    audio_source_type: str,
    audio_file_path: str = None,
    detection_config: dict = None
) -> dict:
    """Start first crack detection monitoring."""
    try:
        # Parse inputs
        audio_cfg = AudioConfig(
            audio_source_type=audio_source_type,
            audio_file_path=audio_file_path
        )
        detect_cfg = DetectionConfig(**(detection_config or {}))
        
        # Start session
        result = session_manager.start_session(audio_cfg)
        
        return {
            "status": "success",
            "result": result.dict()
        }
    except DetectionError as e:
        return {
            "status": "error",
            "error": {
                "code": e.error_code,
                "message": str(e),
                "details": {}
            }
        }
```

**Testing**: Manual testing with:
- Python script calling server via stdio
- n8n workflow nodes (if available)
- MCP inspector tool

**Success Criteria**: Tool callable, returns expected responses.

---

### Task 3.3: Implement Tool: get_first_crack_status ⚪
**Description**: Tool handler for querying status.

**Implementation**:
```python
@server.tool()
async def get_first_crack_status() -> dict:
    """Get current detection status."""
    try:
        status = session_manager.get_status()
        return {
            "status": "success",
            "result": status.dict()
        }
    except ThreadCrashError as e:
        return {
            "status": "error",
            "error": {
                "code": "DETECTION_THREAD_CRASHED",
                "message": str(e),
                "details": {}
            }
        }
```

**Success Criteria**: Tool callable, returns status correctly.

---

### Task 3.4: Implement Tool: stop_first_crack_detection ⚪
**Description**: Tool handler for stopping detection.

**Implementation**:
```python
@server.tool()
async def stop_first_crack_detection() -> dict:
    """Stop detection and cleanup."""
    try:
        summary = session_manager.stop_session()
        return {
            "status": "success",
            "result": summary.dict()
        }
    except DetectionError as e:
        return {
            "status": "error",
            "error": {
                "code": e.error_code,
                "message": str(e),
                "details": {}
            }
        }
```

**Success Criteria**: Tool callable, stops session, returns summary.

---

### Task 3.5: Implement Health Resource ⚪
**Description**: Health check resource for monitoring.

**Implementation**:
```python
@server.resource("health")
async def health() -> dict:
    """Server health status."""
    return {
        "status": "healthy",
        "model_loaded": Path(config.model_checkpoint).exists(),
        "model_checkpoint": config.model_checkpoint,
        "device": "mps" if torch.backends.mps.is_available() else "cpu",
        "version": "1.0.0"
    }
```

**Success Criteria**: Health resource returns correct status.

---

## Milestone 4: Testing & Validation

### Task 4.1: Unit Tests for All Components ⚪
**Description**: Complete unit test coverage.

**Tests**:
```bash
# Run all unit tests
pytest tests/mcp_servers/first_crack_detection/unit/ -v --cov=src/mcp_servers/first_crack_detection --cov-report=term-missing

# Target: >80% coverage
```

**Test Files**:
- `test_models.py` - Pydantic validation
- `test_audio_devices.py` - Device discovery
- `test_utils.py` - Utilities
- `test_config.py` - Configuration
- `test_session_manager.py` - Session management (with mocks)

**Success Criteria**: All unit tests pass, >80% coverage.

---

### Task 4.2: Integration Test: File-Based Detection ⚪
**Description**: End-to-end test with audio file.

**Test File**: `tests/integration/test_file_detection.py`

**Scenario**:
```python
async def test_file_detection_workflow():
    """Test full workflow with audio file."""
    # Start server
    # Call start_first_crack_detection (audio_file)
    # Poll get_first_crack_status
    # Verify detection result
    # Call stop_first_crack_detection
    # Verify summary
```

**Success Criteria**: 
- Can start/stop with audio file
- Returns expected detection results
- Timestamps correct

---

### Task 4.3: Integration Test: Error Scenarios ⚪
**Description**: Test all error paths.

**Scenarios**:
1. Start with missing model checkpoint
2. Start with non-existent audio file
3. Start with unavailable microphone
4. Start while session already active
5. Get status with no active session
6. Simulate thread crash

**Success Criteria**: All error scenarios handled gracefully with correct error codes.

---

### Task 4.4: Manual Testing with Real Hardware ⚪
**Description**: Test with real USB microphone on development machine.

**Test Cases**:
1. Start with USB mic
2. Start with built-in mic
3. Verify audio capture works
4. Test detection on real roast recording

**Commands**:
```bash
# Start server
python -m src.mcp_servers.first_crack_detection.server

# Test with:
# 1. Python test script (JSON-RPC over stdio)
# 2. n8n workflow (HTTP node + Execute Command node)
# 3. MCP inspector tool
```

**Success Criteria**: 
- Works with real USB mic
- Works with built-in mic
- Audio capture confirmed
- Detection results accurate

---

## Milestone 5: Documentation

### Task 5.1: Write README.md ⚪
**Description**: User-facing documentation for MCP server.

**File**: `docs/mcp_servers/first_crack_detection/README.md`

**Sections**:
1. Overview
2. Installation
3. Configuration
4. Running the Server
5. MCP Tools Reference
6. Error Codes
7. Troubleshooting
8. Examples

**Success Criteria**: Complete, clear documentation for end users.

---

### Task 5.2: Write DEPLOYMENT.md ⚪
**Description**: Deployment and integration guide.

**File**: `docs/mcp_servers/first_crack_detection/DEPLOYMENT.md`

**Sections**:
1. Prerequisites
2. Installation Steps
3. Configuration Setup
4. Integrating with Claude Desktop
5. Integrating with Custom Agents
6. Production Considerations
7. Monitoring & Logging

**Success Criteria**: Step-by-step deployment guide complete.

---

### Task 5.3: Update Project Documentation ⚪
**Description**: Update main project docs to reference new MCP server.

**Files to Update**:
1. `docs/requirements/phase-2.md` - Mark Objective 1 complete
2. `PHASE2_PLAN.md` - Create or update
3. `README.md` - Add link to MCP server

**Success Criteria**: All project-level docs updated.

---

## Testing Checklist

### Functional Tests
- [ ] Start detection with audio file
- [ ] Start detection with USB microphone
- [ ] Start detection with built-in microphone
- [ ] Get status (no session)
- [ ] Get status (active session)
- [ ] Get status (first crack detected)
- [ ] Stop detection
- [ ] Idempotency (start when running)
- [ ] Idempotency (stop when not running)
- [ ] Health check

### Error Handling Tests
- [ ] Model checkpoint not found
- [ ] Audio file not found
- [ ] USB microphone not available
- [ ] Built-in microphone not available
- [ ] Invalid audio source type
- [ ] Thread crash during detection
- [ ] Stop during active detection

### Non-Functional Tests
- [ ] Thread safety (concurrent calls)
- [ ] Memory leaks (long-running session)
- [ ] Performance (status query <50ms)
- [ ] Timezone conversion accuracy
- [ ] Logging output (structured JSON)

---

## Definition of Done

**Phase 2 Objective 1 Complete When**:
- ✅ All code implemented and reviewed
- ✅ All unit tests pass (>80% coverage)
- ✅ Integration tests pass
- ✅ Manual testing with real hardware successful
- ✅ Documentation complete (README, DEPLOYMENT, API docs)
- ✅ MCP server runs without errors
- ✅ Tools callable from Claude Desktop or test client
- ✅ Error handling verified for all scenarios
- ✅ Configuration system working
- ✅ Health check functional

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| MCP SDK API changes | Low | High | Pin SDK version, test early |
| Thread safety issues | Medium | High | Extensive locking, unit tests |
| Audio device detection fails | Medium | Medium | Fallback logic, clear errors |
| FirstCrackDetector incompatibility | Low | High | Minimal changes to detector |
| Performance degradation | Low | Medium | Profile early, optimize if needed |

---

## Next Steps After Completion

1. **Objective 2**: Build Roaster Control MCP Server (pyhottop integration)
2. **n8n Workflows**: Build roasting orchestration workflows
3. **Phase 3**: Production deployment
   - HTTP + SSE transport
   - Cloudflare tunnel setup
   - Auth0 integration
   - Raspberry Pi deployment

---

## Progress Tracking

**Update this section as milestones complete:**

- **M1: Project Setup** - ✅ Complete (2025-01-25)
- **M2: Core Components** - ✅ Complete (6/6 tasks complete, 2025-01-25)
  - ✅ Task 2.1: Data Models (19 tests)
  - ✅ Task 2.2: Custom Exceptions (12 tests)
  - ✅ Task 2.3: Audio Device Management (16 tests)
  - ✅ Task 2.4: Utilities (15 tests)
  - ⚪ Task 2.5: Configuration Manager (Complete (2025-01-25) - 11 tests)
  - ⚪ Task 2.6: Session Manager (pending)
  - **Total Unit Tests Passing**: 73/73
- **M3: MCP Server Implementation** - ⚪ Not Started
- **M4: Testing & Validation** - ⚪ Not Started
- **M5: Documentation** - ⚪ Not Started

**Last Updated**: 2025-01-25  
**Current Milestone**: M3 - MCP Server Implementation  
**Current Task**: 3.1 - MCP Server Skeleton  
**Next Review**: After M2 completion

---

## References

- [Phase 2 Objective 1 Requirements](../requirements/phase-2-objective-1-requirements.md)
- [Phase 2 Objective 1 Design](../design/phase-2-objective-1-design.md)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FirstCrackDetector Implementation](../../src/inference/first_crack_detector.py)
