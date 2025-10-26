# Coffee Roasting Agent - Project Status

**Last Updated**: 2025-10-26

## Project Overview
AI-powered autonomous coffee roasting system with:
- **First Crack Detection**: ML model detecting coffee first crack from audio
- **Roaster Control**: Hardware control for Hottop roaster (heat, fan, drum motor)
- **AI Agent**: OpenAI-powered autonomous roasting agent using MCP servers
- **.NET Aspire**: Orchestration layer managing Python MCP servers and AI agent

## Status: Demo/Mock Cleanup Complete ✅

**Date**: 2025-10-26

Successfully removed fake roasting infrastructure and simplified to single mock flag for testing.

### Three Different Mode Systems

#### 1. Demo Mode (`DEMO_MODE` env var)
- Used by both roaster control and FC detection servers
- When `"true"`, uses `DemoRoaster` with canned scenarios
- Checked FIRST in `sse_server.py` startup (line 394-395)
- Files: `demo_scenario.py`, `demo_roaster.py`

#### 2. Mock Mode (`ROASTER_MOCK_MODE` env var)
- Used only by roaster control server
- When `"1"`, uses `MockRoaster` (fake hardware simulator)
- Only checked if demo mode is `false`
- File: `hardware.py` (MockRoaster class)

#### 3. Demo Scenario (`DEMO_SCENARIO` env var)
- Selects which pre-defined scenario to run in demo mode
- Options: `quick_roast`, `medium_roast`, `light_roast`
- File: `demo_scenario.py`

### The Conflict

The Python `sse_server.py` startup logic (lines 394-411):
```python
demo_scenario = get_demo_scenario()  # Returns DemoScenario if DEMO_MODE="true", else None
demo_mode = demo_scenario is not None

if demo_mode:
    hardware = DemoRoaster(scenario=demo_scenario)
else:
    if config.hardware.mock_mode:  # Only checked if NOT demo mode
        hardware = MockRoaster()
    else:
        hardware = HottopRoaster(port=config.hardware.port)
```

**Problem**: Demo mode is checked first, so even if `ROASTER_MOCK_MODE="0"`, the system uses `DemoRoaster` if `DEMO_MODE="true"`.

### Aspire Parameter Translation Issues

**Root Cause**: Aspire parameters are resource objects, not strings.

Attempts that failed:
1. `.WithEnvironment("DEMO_MODE", demoMode)` - passes parameter object, not string value
2. `.WithEnvironment(ctx => { ctx.EnvironmentVariables["VAR"] = builder.Configuration["..."] })` - Configuration not accessible in callback
3. Reading `builder.Configuration["Parameters:demo-mode"]` before resource creation - value not available yet

**Result**: Environment variables don't get set to correct string values (`"true"`/`"false"` or `"1"`/`"0"`), causing Python servers to read incorrect values.

## What Works ✅

- Auth0 authentication (secrets in environment variables via `set_env.sh`)
- MCP server communication (HTTP+SSE transport)
- AI agent autonomous roasting logic with:
  - Pre-FC phase monitoring
  - Post-FC heat/fan adjustments
  - Development time tracking
  - Drop decision making
- First crack detection integration
- Demo mode runs successfully with fast timelines
- Git history cleaned of secrets
- Timezone-aware datetime handling (UTC everywhere)
- First crack temperature reporting

## What Doesn't Work ❌

- Cannot disable demo/mock modes to use real hardware
- Launch profiles don't properly set environment variables
- Parameter values don't convert to correct string format for Python
- Too many overlapping mode systems

## Key Files

### Aspire / .NET
- `Phase3/CoffeeRoasting.AppHost/Program.cs` - Aspire host, parameter setup
- `Phase3/CoffeeRoasting.AppHost/Properties/launchSettings.json` - Launch profiles (demo, real-hardware)

### Python MCP Servers
- `src/mcp_servers/roaster_control/sse_server.py` - Server startup logic (conflicting mode checks)
- `src/mcp_servers/roaster_control/mcp_server.py` - MCP server entry point (reads ROASTER_MOCK_MODE)
- `src/mcp_servers/roaster_control/models.py` - ServerConfig, HardwareConfig
- `src/mcp_servers/demo_scenario.py` - Demo mode detection and scenarios
- `src/mcp_servers/roaster_control/hardware.py` - MockRoaster, HottopRoaster
- `src/mcp_servers/roaster_control/demo_roaster.py` - DemoRoaster with canned timelines
- `src/mcp_servers/roaster_control/session_manager.py` - RoastSessionManager

### AI Agent
- `Phase3/autonomous_agent.py` - OpenAI-powered agent with roasting logic

### Documentation
- `docs/03-phase-3/SECRETS.md` - Environment variable setup
- `set_env.sh.template` - Template for environment variables
- `WARP.md` - Project guidance for Warp AI

## Hardware Details

- **Roaster**: Hottop USB-connected coffee roaster
- **Serial Port**: `/dev/tty.usbserial-DN016OJ3` (hardcoded in `mcp_server.py` line 43)
- **Protocol**: 115200 baud, serial communication
- **Control**: Heat (0-100%), Fan (0-100%), Drum motor (on/off), Cooling (on/off)

## Recent Fixes

1. **Auth0 Secrets**: Removed from git history, moved to environment variables
2. **Timezone Issues**: Fixed offset-naive/offset-aware datetime conflicts
3. **First Crack Temperature**: Added temperature parameter to `report_first_crack` tool
4. **Emergency Drop**: Added 205°C emergency cutoff in agent logic
5. **Heat/Fan Clamping**: Agent clamps values to 0-100% range

## Changes Made ✅

### Deleted Files:
- ✅ `src/mcp_servers/demo_scenario.py` - Canned roast scenarios
- ✅ `src/mcp_servers/roaster_control/demo_roaster.py` - Fake roaster with scripted timelines
- ✅ `src/mcp_servers/roaster_control/demo_hardware.py` - Duplicate demo roaster
- ✅ `src/mcp_servers/first_crack_detection/mock_detector.py` - Auto-trigger FC detector

### Roaster Control Server:
- ✅ Removed demo mode from `sse_server.py` startup
- ✅ Simplified to single `USE_MOCK_HARDWARE` environment variable
- ✅ Updated `server.py` init and health resource
- ✅ Kept `MockRoaster` in `hardware.py` for unit testing only

### First Crack Detection Server:
- ✅ Removed all demo mode logic from `sse_server.py`
- ✅ Removed all demo mode logic from `server.py` (stdio)
- ✅ Server now loads real model and uses real microphone by default
- ✅ Cleaned up health check and tool handlers

### Aspire (.NET):
- ✅ Removed `demo-mode`, `demo-scenario` parameters from `Program.cs`
- ✅ Removed `ROASTER_MOCK_MODE` environment variable
- ✅ Added single `use-mock-hardware` parameter (defaults to "false")
- ✅ Removed `demo` and `real-hardware` launch profiles
- ✅ Updated `https` and `http` profiles for real hardware
- ✅ Added `mock` profile for testing


## Summary

**The system is now ready for real hardware! 🎉**

### Default Behavior:
- Both MCP servers start with **real hardware** by default
- Roaster control connects to Hottop via serial port
- First crack detection loads ML model and uses microphone
- No demo/mock modes unless explicitly enabled

### Testing Mode (Optional):
Set `USE_MOCK_HARDWARE=true` in Aspire or use `mock` launch profile

### Next Steps:
1. Connect Hottop roaster to USB serial port
2. Run `dotnet run` in Phase3/CoffeeRoasting.AppHost
3. Verify both servers start successfully
4. Test autonomous roasting agent with real hardware

## Notes

- **Demo mode was useful for development** but is now blocking production use
- **MockRoaster is still useful** for unit testing without hardware
- **DemoRoaster with scenarios** is overkill - can test agent logic with MockRoaster
- **Simpler is better** - one hardware interface, one mock for testing
