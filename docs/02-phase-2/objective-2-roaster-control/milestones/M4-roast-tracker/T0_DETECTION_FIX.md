# T0 Detection Fix - Gradual Drop Handling

## Date
2025-11-15

## Issue Description

The T0 (bean addition) detection was failing when temperature dropped from 170°C to 88°C. The system showed:
```json
{
  "bean_temp_c": 88,
  "t0_detected": false,
  "beans_added_temp_c": null
}
```

## Root Cause

The original T0 detection algorithm **only compared the last two consecutive readings** in the temperature buffer:

```python
# OLD ALGORITHM
prev_timestamp, prev_temp = self._temp_buffer[-2]
curr_temp = reading.bean_temp_c

drop = prev_temp - curr_temp

if drop > self._config.t0_detection_threshold:  # Default: 10°C
    self._t0 = reading.timestamp
    self._beans_added_temp = prev_temp
```

### Why This Failed

1. **Gradual drops missed**: If temp dropped as 170→165→160→...→95→90→88, each consecutive pair showed <10°C drop
2. **Polling gaps**: If polling paused/restarted, the 170°C reading wasn't in the buffer
3. **Only looked at immediate previous reading**: Didn't track the maximum preheat temperature

## Solution

Track the **maximum preheat temperature** and compare current temp against that:

```python
# NEW ALGORITHM
curr_temp = reading.bean_temp_c

# Track maximum preheat temperature
if self._max_preheat_temp is None or curr_temp > self._max_preheat_temp:
    self._max_preheat_temp = curr_temp

# Check if temperature has dropped significantly from the max preheat temp
if self._max_preheat_temp is not None:
    drop = self._max_preheat_temp - curr_temp
    
    if drop > self._config.t0_detection_threshold:
        self._t0 = reading.timestamp
        self._beans_added_temp = self._max_preheat_temp
        logger.info(
            f"✅ T0 DETECTED: Temp dropped from {self._max_preheat_temp:.1f}°C "
            f"to {curr_temp:.1f}°C (drop: {drop:.1f}°C)"
        )
```

## Benefits

1. **Handles gradual drops**: Detects beans even if temp drops slowly over many readings
2. **Robust**: Works regardless of how many readings between preheat and current temp
3. **Accurate**: Captures true preheat temperature (170°C in your case, not an intermediate value)
4. **Backward compatible**: All existing tests still pass

## Test Coverage

Added 3 new test cases:
1. `test_t0_detected_on_gradual_drop` - Verifies 170→165→...→90 gradual drop works
2. `test_t0_detected_after_polling_gap` - Confirms behavior when polling restarts
3. `test_t0_detected_with_high_then_low_temp_readings` - Tests 170→88 direct scenario

Total T0 tests: **9 tests** (was 6)

## Example Scenarios

### Scenario 1: Your Case (170°C → 88°C)
```
Readings: 170°C, 165°C, 160°C, ... 95°C, 90°C, 88°C

OLD: ❌ No detection (each step <10°C)
NEW: ✅ Detected (max=170°C, current=88°C, drop=82°C)
```

### Scenario 2: Sudden Drop
```
Readings: 170°C, 155°C

OLD: ✅ Detected (15°C drop)
NEW: ✅ Detected (15°C drop)
```

### Scenario 3: Small Fluctuations
```
Readings: 170°C, 165°C, 168°C, 165°C

OLD: ❌ No detection (correct)
NEW: ❌ No detection (correct - only 5°C from max)
```

## Configuration

No configuration changes needed. The default threshold of 10°C works with both algorithms.

```python
TrackerConfig(
    t0_detection_threshold=10.0  # Works for both sudden and gradual drops now
)
```

## Next Time You Test

When running your agent with the roaster, you should now see:
```json
{
  "bean_temp_c": 88,
  "t0_detected": true,
  "beans_added_temp_c": 170.0,
  "t0_timestamp_utc": "2025-11-15T21:10:00Z"
}
```

**Important**: The tracker must see at least one reading during preheat (≥170°C) before beans are added. If you start polling after beans are already added, T0 won't be detected.

## Files Modified

1. `src/mcp_servers/roaster_control/roast_tracker.py` - Improved detection algorithm
2. `tests/unit/mcp_servers/roaster_control/test_roast_tracker.py` - Added 3 new tests
3. `docs/02-phase-2/objective-2-roaster-control/milestones/M4-roast-tracker/task-4.1-t0.md` - Updated docs
4. `src/mcp_servers/roaster_control/README.md` - Updated known limitations

## Test Results

```bash
./venv/bin/python -m pytest tests/unit/mcp_servers/roaster_control/test_roast_tracker.py::TestT0Detection -v
# Result: 9 passed in 0.37s

./venv/bin/python -m pytest tests/unit/mcp_servers/roaster_control/test_roast_tracker.py -v
# Result: 30 passed in 0.35s
```

## References

- Original task: `docs/02-phase-2/objective-2-roaster-control/milestones/M4-roast-tracker/task-4.1-t0.md`
- RoastTracker implementation: `src/mcp_servers/roaster_control/roast_tracker.py`
- Test suite: `tests/unit/mcp_servers/roaster_control/test_roast_tracker.py`
