# Warp MCP Server Setup

This guide explains how to add the Roaster Control MCP server to Warp.

## Prerequisites

1. Python 3.11+ with venv activated
2. All dependencies installed: `pip install -r requirements.txt`
3. Warp terminal installed

## Configuration

### For Warp MCP Settings

Add this configuration to Warp's MCP settings:

**Server Name:** `roaster-control`

**Command:**
```bash
/Users/sertanyamaner/git/coffee-roasting/venv/bin/python /Users/sertanyamaner/git/coffee-roasting/src/mcp_servers/roaster_control/mcp_server.py
```

**Environment Variables:** (optional)
```json
{
  "PYTHONPATH": "/Users/sertanyamaner/git/coffee-roasting"
}
```

## Hardware Modes

### Mock Mode (Default - Safe Testing)

The server starts in mock mode by default. This uses a simulated roaster with thermal modeling.

**Location:** `mcp_server.py` line 33
```python
mock_mode=True  # Mock hardware for safe testing
```

**Features:**
- Realistic temperature simulation
- No physical hardware required
- Safe for experimentation
- Time progresses at normal speed (1x)

### Real Hardware Mode (Hottop KN-8828B-2K+)

To use real hardware:

1. **Connect roaster** via USB
2. **Find serial port:**
   ```bash
   ls /dev/tty.usbserial-*
   ```
3. **Update configuration** in `mcp_server.py`:
   ```python
   mock_mode=False,  # Use real hardware
   port="/dev/tty.usbserial-DN016OJ3",  # Your actual port
   ```
4. **Restart MCP server** in Warp

## Testing the Connection

### 1. Check MCP Server List

In Warp, you should see the `roaster-control` MCP server listed.

### 2. Test with Health Check

Ask Warp:
```
Can you read the health status from the roaster-control MCP?
```

Expected response will include:
- Status: healthy
- Hardware mode: mock or real
- Session active: true/false
- Roaster info

### 3. Test Basic Commands

```
Using the roaster-control MCP:
1. Get the current roast status
2. Set heat to 50%
3. Set fan to 30%
```

## Available Tools

### Control Tools
- `set_heat` - Heat level (0-100%, 10% increments)
- `set_fan` - Fan speed (0-100%, 10% increments)
- `start_roaster` - Start drum motor
- `stop_roaster` - Stop drum motor
- `drop_beans` - Open drop door and start cooling
- `start_cooling` - Start cooling fan
- `stop_cooling` - Stop cooling fan

### Monitoring Tools
- `report_first_crack` - Report FC detection (timestamp + temperature)
- `get_roast_status` - Get complete status (sensors, metrics, timestamps)

### Resources
- `health://status` - Server health and roaster info

## Example Agent Workflows

### Simple Status Check
```
Check the roast status and tell me:
- Current bean temperature
- Current chamber temperature
- Heat level
- Fan speed
- Is the drum running?
```

### Preheat Test
```
Using the roaster-control MCP, please:
1. Start the roaster drum
2. Set heat to 80%
3. Set fan to 30%
4. Monitor the temperature every 5 seconds and tell me when it reaches 150°C
```

### Complete Roast Simulation (Mock Mode Only)
```
Simulate a complete coffee roast using the roaster-control MCP:
1. Preheat to 170°C
2. Report when ready for beans
3. Simulate bean drop (temp will drop to ~80°C)
4. Roast until you see temperature reach 205°C
5. Reduce heat to 50% and fan to 60%
6. Continue until 220°C
7. Drop the beans
8. Show me the final metrics
```

## Troubleshooting

### Server Not Starting

1. **Check Python path:**
   ```bash
   which python
   /Users/sertanyamaner/git/coffee-roasting/venv/bin/python
   ```

2. **Test manually:**
   ```bash
   cd /Users/sertanyamaner/git/coffee-roasting
   ./venv/bin/python src/mcp_servers/roaster_control/mcp_server.py
   ```

3. **Check logs:** Look for error messages in Warp's MCP server logs

### Connection Errors (Real Hardware)

1. **Verify USB connection:**
   ```bash
   ls -l /dev/tty.usbserial-*
   ```

2. **Check permissions:**
   ```bash
   sudo chmod 666 /dev/tty.usbserial-*
   ```

3. **Test pyhottop directly:**
   ```bash
   ./venv/bin/python tests/mcp_servers/roaster_control/integration/test_hottop_manual.py
   ```

### Tools Not Responding

1. **Check session is started:** Health check should show `session_active: true`
2. **Verify hardware connection:** Health check shows roaster info
3. **Check error messages:** Use `get_roast_status` to see any error states

## Safety Notes

### Mock Mode
- ✅ Safe for all experiments
- ✅ No physical hardware affected
- ✅ Instant reset by restarting server

### Real Hardware Mode
- ⚠️ **ALWAYS ATTEND** - Never leave roaster unattended
- ⚠️ **EMPTY DRUM** - Test with empty drum first
- ⚠️ **LOW HEAT** - Start with low heat settings
- ⚠️ **MONITOR** - Watch temperatures continuously
- ⚠️ **EMERGENCY STOP** - Know how to manually shut off roaster

### Temperature Limits
- Bean temp warning: >250°C
- Chamber temp warning: >300°C
- These are LOG WARNINGS only - no automatic shutoff

## Switching Between Modes

### To Mock Mode:
1. Edit `mcp_server.py` line 33: `mock_mode=True`
2. Restart MCP server in Warp
3. Verify with health check: `hardware_mode: "mock"`

### To Real Hardware:
1. Connect roaster via USB
2. Find port: `ls /dev/tty.usbserial-*`
3. Edit `mcp_server.py`:
   - Line 33: `mock_mode=False`
   - Line 34: Update port path
4. Restart MCP server in Warp
5. Verify with health check: `hardware_mode: "real"`

## Status Indicators

### Healthy Connection
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "hardware_mode": "mock",
  "session_active": true,
  "roaster_info": {
    "brand": "Mock",
    "model": "Simulator v1.0",
    "version": "1.0.0"
  }
}
```

### Session Active
```json
{
  "session_active": true,
  "roaster_running": false,
  "sensors": {
    "bean_temp_c": 20.0,
    "chamber_temp_c": 20.0,
    "fan_speed_percent": 0,
    "heat_level_percent": 0
  }
}
```

## Next Steps

1. **Test in mock mode** - Verify all tools work
2. **Try agent workflows** - Let agent control the roast
3. **Switch to real hardware** - When ready for actual roasting
4. **Monitor metrics** - Track T0, RoR, development time

---

**Ready to roast! 🔥☕**

For issues or questions, see the main README.md or check test files for examples.
