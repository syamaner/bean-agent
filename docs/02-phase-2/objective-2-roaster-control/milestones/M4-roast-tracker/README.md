# Milestone 4: Roast Tracker

Complete roast lifecycle tracking with TDD methodology.

## Overview

The RoastTracker component tracks all roast events and computes metrics:
- T0 (beans added) detection from temperature drops
- Rate of Rise (RoR) calculation
- Development time tracking (first crack → drop)
- Bean drop recording and final metrics

## Tasks

- ✅ [Task 4.1: T0 Detection](task-4.1-t0.md) - 6 tests
- ✅ [Task 4.2: Rate of Rise](task-4.2-ror.md) - 7 tests
- ✅ [Task 4.3: Development Time](task-4.3-dev-time.md) - 7 tests
- ✅ [Task 4.4: Bean Drop](task-4.4-drop.md) - 7 tests

## Status

**✅ COMPLETE** - 2025-01-25

- **Tests**: 27 passing
- **Total Project Tests**: 80 passing, 1 skipped
- **Methodology**: Test-Driven Development (TDD)
- **Coverage**: 100% of roast tracker logic

## API Summary

```python
tracker = RoastTracker(config)

# Lifecycle events
tracker.update(sensor_reading)                    # Auto-detects T0
tracker.report_first_crack(timestamp, temp)       # Agent reports
tracker.record_drop(timestamp, temp)              # Agent records drop

# Queries
tracker.get_t0() -> Optional[datetime]
tracker.get_rate_of_rise() -> Optional[float]
tracker.get_development_time_percent() -> Optional[float]
tracker.get_metrics() -> RoastMetrics            # Complete snapshot
```

## Next Steps

Milestone 5: Session Manager - Thread-safe orchestration of hardware + tracker
