# Phase 2 Objective 2 - Requirements
## Roaster Control MCP Server

**Status**: Requirements Defined  
**Created**: 2025-10-25  
**Phase**: 2 (MCP Server Development)  
**Objective**: 2 of 2

---

## Overview

Build an MCP server that provides programmatic control of the Hottop KN-8828B-2K+ coffee roaster using the `pyhottop` Python library. The server will expose tools for controlling roaster operations, reading sensors, and computing derived roast metrics for use by an LLM-based roasting agent.

**Client**: n8n workflow engine or .NET Aspire agent (Phase 3)  
**Transport**: stdio (Phase 2), HTTP with Auth0 (Phase 3)  
**Hardware**: Hottop KN-8828B-2K+ roaster connected via USB

---

## Functional Requirements

### FR1: Hardware Control

#### FR1.1: Heat Control
- **Requirement**: Set roaster heat level to target percentage
- **Range**: 0-100%
- **Granularity**: 10% increments only (0, 10, 20, ..., 100)
- **Interface**: `set_heat(target_percent: int)`
- **Validation**: Reject values not in 10% increments
- **Authorization**: Requires "roast:admin" scope

#### FR1.2: Fan Control
- **Requirement**: Set fan speed to target percentage
- **Range**: 0-100%
- **Granularity**: 10% increments only (0, 10, 20, ..., 100)
- **Interface**: `set_fan(target_percent: int)`
- **Validation**: Reject values not in 10% increments
- **Authorization**: Requires "roast:admin" scope

#### FR1.3: Roaster Operations
**Start Roaster**
- **Requirement**: Start the drum motor
- **Interface**: `start_roaster()`
- **Authorization**: Requires "roast:admin" scope

**Stop Roaster**
- **Requirement**: Stop the drum motor
- **Interface**: `stop_roaster()`
- **Authorization**: Requires "roast:admin" scope

**Drop Beans**
- **Requirement**: Open bean drop door to eject beans
- **Interface**: `drop_beans()`
- **Side Effect**: Automatically triggers cooling cycle
- **Authorization**: Requires "roast:admin" scope

**Cooling Control**
- **Requirement**: Control cooling fan cycle
- **Interface**: `start_cooling()`, `stop_cooling()`
- **Authorization**: Requires "roast:admin" scope

---

### FR2: Sensor Readings

#### FR2.1: Temperature Sensors
- **Bean Temperature**: Read current bean probe temperature (°C)
- **Chamber Temperature**: Read current chamber temperature (°C)
- **Update Frequency**: Polled every 1 second
- **Precision**: 0.1°C

#### FR2.2: Control State Sensors
- **Heat Level**: Current heat setting (% 0-100)
- **Fan Speed**: Current fan speed (% 0-100)
- **Update Frequency**: Polled every 1 second

---

### FR3: Derived Roast Metrics

#### FR3.1: Roast Timer
- **Start Detection (T0)**: Automatic detection when beans added
  - **Detection Logic**: Monitor bean temperature for sudden drop >10°C
  - **Bean Addition Temperature**: Capture temperature at T0 (typically ~170°C)
- **Timer Display**: Duration since T0 in seconds and MM:SS format
- **State**: NULL before T0 detected

#### FR3.2: Rate of Rise (RoR)
- **Definition**: Temperature change per minute
- **Formula**: `(Bean_Temp[T] - Bean_Temp[T-60s]) / 1 minute`
- **Update Frequency**: Every 1 second
- **Precision**: 0.1°C/min
- **State**: NULL for first 60 seconds of roast

#### FR3.3: First Crack Event
- **Source**: Reported by First Crack Detection MCP Server
- **Interface**: `report_first_crack(timestamp: str, confidence: str)`
- **Captured Data**:
  - Timestamp (UTC + local timezone)
  - Bean temperature at first crack
  - Time since T0
- **State**: NULL before first crack reported

#### FR3.4: Development Time
- **Definition**: Duration from first crack start to bean drop
- **Real-Time Percentage**: `(T_current - T_first_crack) / (T_current - T0) * 100`
- **Target Range**: 15-20% for light roasts on this hardware
- **Display**: Seconds, MM:SS, and percentage
- **State**: NULL before first crack

#### FR3.5: Drop Event
- **Trigger**: When `drop_beans()` called
- **Captured Data**:
  - Drop timestamp (UTC + local)
  - Bean temperature at drop
  - Total roast duration (T_drop - T0)
- **State**: NULL before beans dropped

---

### FR4: Status Query

#### FR4.1: Complete Status Snapshot
- **Interface**: `get_roast_status()`
- **Authorization**: Requires "roast:observer" scope (read-only)
- **Response Format**:

```json
{
  "session_active": true,
  "roaster_running": true,
  
  "timestamps": {
    "session_start": "2025-10-25T17:30:00Z",
    "session_start_local": "2025-10-25T10:30:00-07:00",
    "beans_added": "2025-10-25T17:32:00Z",
    "beans_added_local": "2025-10-25T10:32:00-07:00",
    "first_crack": "2025-10-25T17:40:23Z",
    "first_crack_local": "2025-10-25T10:40:23-07:00",
    "drop": null,
    "drop_local": null
  },
  
  "sensors": {
    "chamber_temp_c": 195.5,
    "bean_temp_c": 185.2,
    "fan_speed_percent": 70,
    "heat_level_percent": 60
  },
  
  "metrics": {
    "roast_elapsed_seconds": 503,
    "roast_elapsed_display": "08:23",
    "rate_of_rise_c_per_min": 12.5,
    "beans_added_temp_c": 170.0,
    "first_crack_temp_c": 195.0,
    "first_crack_time_display": "08:23",
    "development_time_seconds": 0,
    "development_time_display": "00:00",
    "development_time_percent": 0.0,
    "total_roast_duration_seconds": null
  },
  
  "connection": {
    "status": "connected",
    "hardware": "Hottop KN-8828B-2K+",
    "port": "/dev/tty.usbserial-1420",
    "last_update": "2025-10-25T17:40:23Z"
  }
}
```

#### FR4.2: Health Check
- **Interface**: MCP Resource `health://status`
- **Purpose**: Server health and configuration info
- **Authorization**: None (public)

---

### FR5: Session Management

#### FR5.1: Session Lifecycle
- **Start**: Automatic when roaster connected
- **Active State**: While roaster running and monitoring
- **Stop**: Manual via `stop_session()` or automatic on error
- **Single Session**: Only one active roast per server instance

#### FR5.2: Connection Management
- **Auto-Connect**: Connect to roaster on server start
- **Reconnection**: Auto-reconnect on USB disconnection
- **Health Monitoring**: Periodic connection checks
- **Graceful Shutdown**: Clean disconnect on server stop

---

## Non-Functional Requirements

### NFR1: Performance
- **Sensor Polling**: 1 Hz (every 1 second)
- **Status Query Latency**: <100ms
- **Control Command Latency**: <200ms
- **Metric Computation**: Real-time, <10ms overhead

### NFR2: Reliability
- **Thread Safety**: All operations thread-safe with locks
- **Idempotency**: Control commands safe to call multiple times
- **Error Recovery**: Auto-reconnect on connection loss
- **Data Persistence**: In-memory only (Phase 2), no database

### NFR3: Safety
- **Validation**: All inputs validated before hardware commands
- **Error Handling**: Graceful degradation on hardware errors
- **Connection Monitoring**: Detect and report disconnections
- **Emergency Stop**: Stop commands always work

### NFR4: Maintainability
- **Hardware Abstraction**: Mock interface for testing
- **Configuration**: External config file + env vars
- **Logging**: Structured logging (structlog)
- **Testing**: TDD with >90% coverage target

### NFR5: Security (Phase 3)
- **Authentication**: Auth0 JWT tokens (Phase 3)
- **Authorization**: Role-based access control
  - **roast:admin**: Full control (all tools)
  - **roast:observer**: Read-only (get_roast_status only)
- **Transport**: stdio (Phase 2), HTTPS (Phase 3)

---

## Integration Requirements

### IR1: pyhottop Library Integration
- **Library**: https://github.com/splitkeycoffee/pyhottop
- **Connection**: USB serial communication
- **Hardware**: Hottop KN-8828B-2K+
- **Abstraction**: Wrap pyhottop behind HardwareInterface

### IR2: First Crack Detection Integration
- **Interface**: Agent calls `report_first_crack()` when detected
- **Data Flow**: First Crack MCP Server → Agent → Roaster MCP Server
- **Timestamp Sync**: Use ISO8601 UTC timestamps

### IR3: Warp/n8n Integration
- **Protocol**: MCP (Model Context Protocol)
- **Transport**: stdio via JSON-RPC
- **Discovery**: Tools auto-discovered by MCP client
- **Configuration**: Environment variables for paths/ports

---

## Constraints

### C1: Hardware Constraints
- **Single Connection**: Only one USB connection at a time
- **10% Increments**: Heat and fan control limited by hardware
- **Polling Only**: No push notifications from hardware
- **USB Required**: Physical connection to roaster

### C2: Development Constraints
- **No Physical Hardware**: Use mock interface for development
- **Manual Testing**: Real hardware testing required before production
- **macOS Only**: Development on macOS (M3 Max)
- **Python 3.11**: Compatibility with existing environment

### C3: Phase 2 Scope
- **stdio Transport Only**: HTTP transport deferred to Phase 3
- **No Auth**: Authorization deferred to Phase 3
- **In-Memory State**: No persistence, resets on restart
- **Single Session**: One roast at a time

---

## Out of Scope (Phase 3)

- HTTP + Server-Sent Events (SSE) transport
- Auth0 authentication and authorization
- Cloudflare tunnel for remote access
- Data persistence (database/file storage)
- Multi-session support
- Historical roast data analysis
- Web UI for monitoring
- Second crack detection
- Profile management (pre-defined roast curves)

---

## Success Criteria

### Milestone Success
- ✅ All unit tests passing (target: ~100 tests)
- ✅ Integration tests passing with mock hardware
- ✅ Manual tests successful
- ✅ Code coverage >90%
- ✅ Documentation complete

### Phase 2 Objective 2 Complete
- ✅ MCP server runs and exposes 9 tools
- ✅ `get_roast_status()` returns valid data with mock hardware
- ✅ All control commands validated and accepted
- ✅ Metrics computed correctly (RoR, development time, T0 detection)
- ✅ First crack integration point working
- ✅ Thread-safe implementation verified
- ✅ Ready for Auth0 integration (Phase 3)
- ✅ Ready for real hardware testing

---

## References

- [Phase 2 Requirements](phase-2.md)
- [Hottop KN-8828B-2K+ Product Page](https://www.hottopamericas.com/KN-8828B-2Kplus.html)
- [pyhottop Library](https://github.com/splitkeycoffee/pyhottop)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Phase 2 Objective 1 Complete](../mcp_servers/PHASE2_OBJ1_COMPLETE.md)

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-25  
**Status**: Approved for Implementation
