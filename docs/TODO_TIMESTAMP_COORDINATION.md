# TODO: Timestamp Coordination Between FC Detector and Roaster Control

**Priority**: HIGH  
**Phase**: Phase 2 Objective 2 - Post M4 Completion  
**Status**: TODO

---

## Problem

Currently there's a mismatch in how timestamps are represented between the two MCP servers:

### First Crack Detection MCP
- Returns **relative time** from audio start: `"timestamp": "08:06"` (MM:SS format)
- This is relative to when microphone monitoring started
- Not a UTC timestamp

### Roaster Control MCP
- Expects **absolute UTC timestamp**: `datetime` object in UTC
- Uses for all time calculations (T0, first crack, development time, etc.)
- All timestamps stored/compared in UTC

---

## Current Agent Flow (BROKEN)

```
1. Agent: Call first_crack_detection.get_first_crack_status()
   Response: { "first_crack_detected": true, "timestamp": "08:06" }
   ❌ This is relative time (8 min 6 sec from audio start)

2. Agent: Call roaster_control.get_roast_status()
   Response: { "bean_temp_c": 205.5, ... }

3. Agent: Call roaster_control.report_first_crack(
            timestamp="2025-01-25T08:06:00Z",  ❌ MIXING RELATIVE + UTC
            temperature=205.5
          )
```

**Issue**: Agent would need to:
- Track when audio monitoring started
- Convert relative "08:06" to absolute UTC timestamp
- This is error-prone and adds complexity to agent logic

---

## Proposed Solution

### Option 1: FC Detector Returns UTC Timestamp (RECOMMENDED)

**Modify First Crack Detection MCP** to return UTC timestamp when detection occurs:

```python
# In first_crack_detector.py
def is_first_crack(self) -> Tuple[bool, Optional[str]]:
    # ... detection logic ...
    if first_crack_detected:
        utc_timestamp = datetime.now(UTC)
        return True, utc_timestamp.isoformat()  # "2025-01-25T19:58:00Z"
```

**Agent Flow (FIXED)**:
```
1. Agent: Call first_crack_detection.get_first_crack_status()
   Response: { 
       "first_crack_detected": true, 
       "timestamp_utc": "2025-01-25T19:58:00Z",  ✅ Absolute UTC
       "timestamp_relative": "08:06"  ✅ Human-readable (optional)
   }

2. Agent: Call roaster_control.get_roast_status()
   Response: { "bean_temp_c": 205.5, ... }

3. Agent: Call roaster_control.report_first_crack(
            timestamp="2025-01-25T19:58:00Z",  ✅ Pure UTC
            temperature=205.5
          )
```

**Benefits**:
- ✅ No conversion logic in agent
- ✅ Both servers use UTC consistently
- ✅ Servers can run on different machines (no shared clock issues)
- ✅ Still provides relative time for human display

---

### Option 2: Agent Tracks Start Time (NOT RECOMMENDED)

Agent could track when monitoring started and do the conversion:

```python
# Agent would need to:
monitoring_start = datetime.now(UTC)  # Track when audio starts
# ... later ...
relative_time = "08:06"  # From FC detector
minutes, seconds = parse_mm_ss(relative_time)
fc_utc = monitoring_start + timedelta(minutes=minutes, seconds=seconds)
```

**Why Not**:
- ❌ More complex agent logic
- ❌ Error-prone (what if agent restarts?)
- ❌ Doesn't work if servers run on different machines
- ❌ Clock skew issues

---

## Implementation Plan

### Step 1: Update First Crack Detection MCP ✅ (Phase 2 Obj 1 - Already Complete)

**File**: `src/mcp_servers/first_crack_detection/session_manager.py`

Need to modify `DetectionSessionManager` to:
1. Track UTC timestamp when first crack detected
2. Return both UTC and relative timestamps in status

```python
class DetectionSessionManager:
    def __init__(self):
        self._first_crack_utc: Optional[datetime] = None
        # ... existing code ...
    
    def get_status(self) -> StatusInfo:
        fc_detected, relative_time = self._detector.is_first_crack()
        
        # Capture UTC timestamp on first detection
        if fc_detected and self._first_crack_utc is None:
            self._first_crack_utc = datetime.now(UTC)
        
        return StatusInfo(
            first_crack_detected=fc_detected,
            timestamp_relative=relative_time,  # "08:06"
            timestamp_utc=self._first_crack_utc.isoformat() if self._first_crack_utc else None
        )
```

### Step 2: Update Data Models

**File**: `src/mcp_servers/first_crack_detection/models.py`

```python
class StatusInfo(BaseModel):
    first_crack_detected: bool
    timestamp_relative: Optional[str] = None  # "MM:SS" format
    timestamp_utc: Optional[str] = None  # ISO 8601 format
    # ... existing fields ...
```

### Step 3: Update Agent Logic (Phase 3)

Agent should use `timestamp_utc` when calling `report_first_crack()`:

```python
# Agent code (Phase 3)
fc_status = await fc_mcp.get_first_crack_status()
if fc_status["first_crack_detected"]:
    roast_status = await roaster_mcp.get_roast_status()
    await roaster_mcp.report_first_crack(
        timestamp=fc_status["timestamp_utc"],  # Use UTC!
        temperature=roast_status["bean_temp_c"]
    )
```

---

## Testing Strategy

1. **Unit Test**: Verify StatusInfo includes both timestamps
2. **Integration Test**: Verify UTC timestamp captured at detection moment
3. **Agent Test**: Verify agent uses UTC timestamp correctly
4. **Clock Skew Test**: Run servers on different machines, verify still works

---

## Notes

- **Distributed Systems**: These components will run on different servers/containers in production
- **Clock Sync**: UTC ensures consistency even with minor clock skew
- **Human Display**: Relative time ("08:06") still useful for UI/logging
- **Backward Compatibility**: Return both timestamps initially, deprecate relative later if needed

---

## Timeline

- **Review**: After M4 completion (Roast Tracker done)
- **Implementation**: During Phase 2 cleanup or Phase 3 agent integration
- **Testing**: Before Phase 3 agent deployment

---

**Created**: 2025-01-25  
**Updated**: 2025-01-25  
**Owner**: To be assigned
