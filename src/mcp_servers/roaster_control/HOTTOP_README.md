# HottopRoaster Implementation

## Overview

The `HottopRoaster` class provides a hardware interface for the Hottop KN-8828B-2K+ coffee roaster using the `pyhottop` library for USB serial communication.

## Features

- ✅ USB serial connection via pyhottop
- ✅ Real-time sensor reading (bean temp, chamber temp, fan, heat)
- ✅ Heat and fan control (0-100% in 10% increments)
- ✅ Drum motor control (start/stop)
- ✅ Cooling system control
- ✅ Bean drop sequence
- ✅ Automatic temperature unit conversion (F→C)
- ✅ Async callback-based sensor updates

## Hardware Requirements

- Hottop KN-8828B-2K+ roaster
- USB serial connection (typically `/dev/tty.usbserial-*` on macOS)
- Roaster must be powered ON for serial communication
- `pyhottop` library installed (`pip install pyhottop`)

## Usage

### Basic Connection

```python
from mcp_servers.roaster_control.hardware import HottopRoaster

# Initialize with port (or None for auto-discovery)
roaster = HottopRoaster(port="/dev/tty.usbserial-DN016OJ3")

# Connect (starts pyhottop control thread)
roaster.connect()

# Check connection
print(roaster.is_connected())  # True

# Get roaster info
print(roaster.get_roaster_info())
# {'brand': 'Hottop', 'model': 'KN-8828B-2K+', 'version': 'pyhottop'}

# Disconnect when done
roaster.disconnect()
```

### Reading Sensors

```python
# Read current sensor values
reading = roaster.read_sensors()

print(f"Bean: {reading.bean_temp_c}°C")
print(f"Chamber: {reading.chamber_temp_c}°C")
print(f"Fan: {reading.fan_speed_percent}%")
print(f"Heat: {reading.heat_level_percent}%")
print(f"Time: {reading.timestamp}")
```

**Note:** The roaster must be connected and the pyhottop control thread running for sensor data. Initial readings may be 0 until the first callback is received (typically within 1-2 seconds).

### Controlling Roaster

```python
# Set heat (0-100 in 10% increments)
roaster.set_heat(50)  # 50%

# Set fan (0-100 in 10% increments)
roaster.set_fan(30)   # 30%

# Control drum
roaster.start_drum()
roaster.stop_drum()

# Control cooling
roaster.start_cooling()
roaster.stop_cooling()

# Drop beans (complete drop sequence)
roaster.drop_beans()  # Stops drum, turns off heat, opens solenoid, starts cooling
```

## Implementation Details

### pyhottop Integration

The `HottopRoaster` wraps the `pyhottop.Hottop` class:

1. **Connection**: Uses `pyhottop.connect()` and starts the control thread
2. **Callbacks**: Registers `_process_callback()` to receive sensor updates
3. **Control**: Maps 0-100% values to pyhottop's expectations:
   - `set_heater(0-100)` - direct mapping
   - `set_fan(0-10)` - divides by 10
   - `set_drum_motor(bool)` - converts int to bool
   - `set_cooling_motor(bool)` - converts int to bool

### Temperature Units

The Hottop KN-8828B-2K+ can be configured for either Celsius or Fahrenheit mode. Temperature values returned depend on the roaster's configuration:

- **Celsius mode** (default for KN-8828B-2K+): Values are already in °C, no conversion needed
- **Fahrenheit mode**: Values in °F, requires conversion to °C

```python
# Celsius mode (current implementation)
celsius = raw_value  # Already in Celsius

# Fahrenheit mode (if needed)
celsius = (raw_value - 32) * 5.0 / 9.0
```

**Note:** This implementation assumes Celsius mode. If your roaster is configured for Fahrenheit, update the `_process_callback()` method to perform F→C conversion.

### Sensor Update Flow

```
Hottop hardware → pyhottop ControlProcess (thread)
                       ↓ callback every ~0.6s
                  _process_callback()
                       ↓ converts F→C, scales values
                  self._latest_reading (cached)
                       ↓ on demand
                  read_sensors() → returns SensorReading
```

## Verification

### Hardware Verification ✅

The HottopRoaster implementation has been **verified with physical hardware** (Hottop KN-8828B-2K+ roaster):

- ✅ USB serial connection established
- ✅ Drum motor control (start/stop)
- ✅ Main fan control (0-100%)
- ✅ Heat control (0-100%)
- ✅ Bean drop door (solenoid)
- ✅ Cooling motor control
- ✅ Temperature readings (Bean & Chamber in °C)
- ✅ Continuous command mode (Artisan-compatible)

**Test Date:** October 25, 2025  
**Roaster Model:** Hottop KN-8828B-2K+ (Celsius mode)  
**Port:** `/dev/tty.usbserial-DN016OJ3`  
**Protocol:** Artisan-compatible serial protocol

See `test_hottop_auto.py` in the project root for the automated verification script.

## Testing

### Unit Tests

Run standard unit tests (no hardware required):

```bash
./venv/bin/pytest tests/mcp_servers/roaster_control/unit/test_hardware.py::TestHottopRoaster -v
```

These tests verify:
- Roaster info
- Initialization
- Port configuration

### Integration Tests (Manual)

**REQUIRES PHYSICAL HARDWARE:**

```bash
# Make sure roaster is connected and powered on
./venv/bin/python tests/mcp_servers/roaster_control/integration/test_hottop_manual.py
```

This script:
- Connects to the roaster
- Reads sensors for 10 seconds
- Tests safe control commands (fan, drum)
- Disconnects cleanly

## Known Issues & Limitations

### Serial Communication Errors

If the roaster is not powered on or not responding, pyhottop may throw errors:

```
TypeError: byte indices must be integers or slices, not str
```

**Solution:** Ensure the roaster is powered ON before connecting.

### Callback Latency

First sensor reading may return zeros until the pyhottop callback fires (typically 1-2 seconds after connection).

**Workaround:** Add a short delay after `connect()` before reading sensors, or check that readings are non-zero.

### Thread Management

The pyhottop library runs a background thread (`ControlProcess`) that continuously polls the roaster. This thread must be properly stopped via `disconnect()` to avoid:
- Resource leaks
- Serial port staying open
- Background thread continuing after program exit

**Best Practice:** Always use `try/finally` or context managers to ensure `disconnect()` is called.

## Troubleshooting

### Port Not Found

```python
# Auto-discover (may not work on all systems)
roaster = HottopRoaster(port=None)

# List available serial ports
import serial.tools.list_ports
for port in serial.tools.list_ports.comports():
    print(port.device)
```

### Connection Refused

- Check USB cable is connected
- Verify roaster is powered ON
- Check permissions: `ls -l /dev/tty.usbserial-*`
- Try unplugging and replugging USB

### Sensor Readings Always Zero

- Wait 2-3 seconds after `connect()` for first callback
- Check roaster is powered ON and responding
- Enable pyhottop debug logging (it's verbose by default)

## Safety Notes

⚠️ **IMPORTANT SAFETY WARNINGS:**

1. **Never leave roaster unattended** when controlled via software
2. **Monitor temperatures** - implement safety limits in your code
3. **Test thoroughly** before using in production roasting
4. **Have manual override** - keep physical controls accessible
5. **Fire safety** - have fire suppression nearby during roasting

The authors and contributors are not responsible for any damage, injury, or fire resulting from use of this software.

## Architecture

```
HardwareInterface (abstract)
       ↑
       │ implements
       │
HottopRoaster
       │
       │ uses
       ↓
pyhottop.Hottop → USB Serial → Physical Roaster
```

## Future Enhancements

Potential improvements for future versions:

- [ ] Add support for main fan control
- [ ] Add solenoid control (bean drop door)
- [ ] Expose roast event tracking from pyhottop
- [ ] Add automatic reconnection on serial errors
- [ ] Context manager support (`with HottopRoaster(...) as roaster:`)
- [ ] Async/await API option
- [ ] Configurable callback intervals
- [ ] Temperature safety limits and alarms

## References

- [pyhottop GitHub](https://github.com/splitkeycoffee/pyhottop)
- [Hottop Roaster Documentation](https://www.hottoproaster.com/)
- [Hardware Interface Design](./hardware.py)
- [Manual Test Script](../../tests/mcp_servers/roaster_control/integration/test_hottop_manual.py)
