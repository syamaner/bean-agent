# pyhottop API Mapping

**Source**: https://github.com/splitkeycoffee/pyhottop  
**Analyzed**: 2025-10-25  
**Version**: 0.1.0 (BETA)

---

## Overview

pyhottop provides Python interface to Hottop KN-8828b-2k+ roaster via USB-serial connection. The library uses a threaded architecture with a control process managing serial communication and a user-facing `Hottop` object.

**Important**: Library is meant for building applications, not standalone roasting control.

---

## Connection

### Setup Requirements
1. Install CP210x USB driver (Silicon Labs)
2. USB-serial connection to roaster
3. Auto-discovery or manual port specification

### `Hottop` Class Initialization

```python
from pyhottop.pyhottop import Hottop

hottop = Hottop()
```

**Default Constants**:
- `BAUDRATE = 115200`
- `BYTE_SIZE = 8`
- `PARITY = "N"`
- `STOPBITS = 1`
- `TIMEOUT = 1`
- `INTERVAL = 0.6` (default polling interval, seconds)

### Connection Methods

```python
# Auto-discover USB port
hottop.connect()

# Manual port specification  
hottop.connect(interface="/dev/cu.usbserial-DA01PEYC")
```

**Returns**: `bool`  
**Raises**: `SerialConnectionError` if connection fails

**Auto-discovery logic**:
- macOS: scans `/dev/cu.*` for `usbserial-*` pattern
- Linux: scans `/dev/tty[A-Za-z]*`
- Windows: scans `COM1-COM256`

---

## Control Settings

### Configuration Dictionary

The `_config` dictionary controls roaster settings:

```python
{
    'heater': int,         # 0-10 (heat level, 10% increments)
    'fan': int,            # 0-10 (fan speed, 10% increments) 
    'main_fan': int,       # 0-10 (cooling fan)
    'drum_motor': int,     # 0 or 1 (drum on/off)
    'solenoid': int,       # 0 or 1 (bean drop door)
    'cooling_motor': int,  # 0 or 1 (cooling motor)
    'interval': float      # polling interval in seconds
}
```

**Key Mappings for Our Requirements**:
- **Heat Control**: `heater` (0-10, where 10 = 100%)
- **Fan Control**: `fan` (0-10, where 10 = 100%)
- **Start Drum**: `drum_motor = 1`
- **Stop Drum**: `drum_motor = 0`
- **Drop Beans**: `solenoid = 1` (opens door)
- **Start Cooling**: `cooling_motor = 1`, `main_fan = 10`
- **Stop Cooling**: `cooling_motor = 0`

**Important**: When `heater > 0`, drum motor is automatically set to 1 (safety feature).

---

## Sensor Readings

### Reading Dictionary Format

Readings returned via callback contain:

```python
{
    'heater': int,              # Current heat setting (0-10)
    'fan': int,                 # Current fan setting (0-10)
    'main_fan': int,            # Cooling fan setting (0-10)
    'environment_temp': float,  # Chamber temperature (°F)
    'bean_temp': float,         # Bean probe temperature (°F)
    'solenoid': int,            # Door state (0=closed, 1=open)
    'drum_motor': int,          # Drum state (0=off, 1=on)
    'cooling_motor': int,       # Cooling motor state
    'chaff_tray': int,          # Chaff tray detection
    'valid': bool               # Reading validation status
}
```

**Note**: Temperatures are in Fahrenheit! Need conversion to Celsius:
```python
def fahrenheit2celsius(f):
    return (f - 32) / 1.8
```

**Validation**: Readings include `valid` flag. Invalid readings occur when:
- Temperatures outside bounds (50-500°F)
- Binary settings not 0 or 1
- Buffer checksum fails

---

## Monitoring & Callbacks

### Starting Monitoring

pyhottop uses a threaded model with callbacks:

```python
def my_callback(settings):
    """Process readings from roaster."""
    if settings['valid']:
        bean_temp_f = settings['bean_temp']
        chamber_temp_f = settings['environment_temp']
        # ... process data

# Start monitoring (starts background thread)
hottop.start_monitor(callback=my_callback)
```

**Control Process**:
- Runs in separate thread (`ControlProcess`)
- Polls roaster at configured interval
- Calls callback with each reading
- Validates checksums
- Auto-retries on errors (max 3 attempts)

### Stopping Monitoring

```python
hottop.stop_monitor()
```

---

## Control Commands

### Setting Heat

```python
# Set heat to 60% (0-10 scale, so 6 = 60%)
hottop._config['heater'] = 6
hottop._q.put(hottop._config)
```

### Setting Fan

```python
# Set fan to 80% (0-10 scale, so 8 = 80%)
hottop._config['fan'] = 8
hottop._q.put(hottop._config)
```

### Start/Stop Drum

```python
# Start drum
hottop._config['drum_motor'] = 1
hottop._q.put(hottop._config)

# Stop drum
hottop._config['drum_motor'] = 0
hottop._q.put(hottop._config)
```

### Drop Beans

```python
# Convenience method
hottop.drop()  # Sets solenoid=1, cooling_motor=1, heater=0

# Or manually
hottop._config['solenoid'] = 1
hottop._q.put(hottop._config)
```

### Cooling Control

```python
# Start cooling
hottop._config['cooling_motor'] = 1
hottop._config['main_fan'] = 10
hottop._q.put(hottop._config)

# Stop cooling
hottop._config['cooling_motor'] = 0
hottop._q.put(hottop._config)
```

---

## Communication Protocol

### Configuration Update Flow

1. User modifies `hottop._config` dictionary
2. User pushes config to queue: `hottop._q.put(hottop._config)`
3. Control thread reads queue on next iteration
4. Control thread generates 36-byte config array
5. Config written to serial interface
6. Roaster responds with 36-byte status

### Serial Protocol Details

**Write (Control)**:
- 36-byte array
- Fixed header: `[0xA5, 0x96, 0xB0, 0xA0, 0x01, 0x01, 0x24, ...]`
- Control bytes at specific positions:
  - `[10]`: heater
  - `[11]`: fan
  - `[12]`: main_fan
  - `[16]`: solenoid
  - `[17]`: drum_motor
  - `[18]`: cooling_motor
- Checksum at `[35]`: sum of bytes `[0:35] & 0xFF`

**Read (Status)**:
- 36-byte response
- Header validation: `[0]=0xA5, [1]=0x96`
- Sensor bytes:
  - `[10]`: heater
  - `[11]`: fan
  - `[12]`: main_fan
  - `[16]`: solenoid
  - `[17]`: drum_motor
  - `[18]`: cooling_motor
  - `[19]`: chaff_tray
  - `[23:24]`: environment temp (2 bytes, hex)
  - `[25:26]`: bean temp (2 bytes, hex)
- Checksum at `[35]`

---

## Mapping to Our Requirements

### Our API → pyhottop Mapping

| Our Requirement | pyhottop Implementation |
|----------------|------------------------|
| `set_heat(percent)` | `_config['heater'] = percent // 10` then push to queue |
| `set_fan(percent)` | `_config['fan'] = percent // 10` then push to queue |
| `start_roaster()` | `_config['drum_motor'] = 1` then push |
| `stop_roaster()` | `_config['drum_motor'] = 0` then push |
| `drop_beans()` | Call `hottop.drop()` or set solenoid=1 |
| `start_cooling()` | Set `cooling_motor=1, main_fan=10` |
| `stop_cooling()` | Set `cooling_motor=0` |
| Read bean temp | `fahrenheit2celsius(settings['bean_temp'])` |
| Read chamber temp | `fahrenheit2celsius(settings['environment_temp'])` |
| Read heat level | `settings['heater'] * 10` |
| Read fan speed | `settings['fan'] * 10` |

### Conversion Notes

1. **Temperature**: pyhottop returns °F, we need °C
   ```python
   celsius = (fahrenheit - 32) / 1.8
   ```

2. **Percentage**: pyhottop uses 0-10 scale, we use 0-100%
   ```python
   pyhottop_value = our_percent // 10
   our_percent = pyhottop_value * 10
   ```

3. **Validation**: Always check `settings['valid']` before using readings

---

## Mock Support

pyhottop includes a `MockProcess` for simulation:

```python
hottop._simulate = True
hottop.connect()  # Returns True without real connection
```

**Note**: Mock implementation details in `pyhottop/mock.py`. We'll build our own `MockHardware` with more realistic simulation for our needs.

---

## Error Handling

### Exceptions

- `SerialConnectionError`: Connection failures
- `InvalidInput`: Invalid configuration values

### Validation

- Temperature bounds: 50-500°F (~10-260°C)
- Binary settings: must be 0 or 1
- Checksum validation on every read
- Auto-retry up to 3 times on read errors

### Connection Recovery

- Auto-close/reopen connection on buffer errors
- Retry logic for failed reads
- Cache last valid reading if errors persist

---

## Threading Model

```
User Thread                Control Thread (ControlProcess)
     │                              │
     ├─ hottop.connect()           │
     ├─ hottop.start_monitor()     │
     │                              ├─ _wake_up() (prime roaster)
     │                              ├─ while not exit:
     │                              │   ├─ check queue for config
     │                              │   ├─ _read_settings() from serial
     │                              │   ├─ _validate_checksum()
     │                              │   ├─ callback(settings)
     │                              │   ├─ _send_config() to serial
     │                              │   └─ sleep(interval)
     ├─ modify _config             │
     ├─ push to _q                 │
     │                              │
     ├─ hottop.stop_monitor()      │
     │                              └─ exit
```

**Key Points**:
- Control thread runs continuously
- User updates config via queue
- Callback executes in control thread context
- Need to be thread-safe in callback

---

## Implementation Notes for Our Wrapper

### HottopHardware Class Design

```python
class HottopHardware(HardwareInterface):
    def __init__(self, config: HardwareConfig):
        self._hottop = Hottop()
        self._port = config.port
        self._connected = False
        self._latest_reading = None
        self._lock = threading.Lock()
        
    def connect(self) -> bool:
        """Connect to roaster."""
        try:
            self._hottop.connect(interface=self._port)
            self._hottop.start_monitor(callback=self._on_reading)
            self._connected = True
            return True
        except SerialConnectionError as e:
            raise RoasterConnectionError(str(e))
    
    def _on_reading(self, settings: dict):
        """Callback from pyhottop - store latest reading."""
        with self._lock:
            if settings['valid']:
                self._latest_reading = settings
    
    def read_sensors(self) -> SensorReading:
        """Read cached sensor values."""
        with self._lock:
            if self._latest_reading is None:
                raise RoasterNotConnectedError()
            
            return SensorReading(
                timestamp=datetime.now(UTC),
                bean_temp_c=(self._latest_reading['bean_temp'] - 32) / 1.8,
                chamber_temp_c=(self._latest_reading['environment_temp'] - 32) / 1.8,
                fan_speed_percent=self._latest_reading['fan'] * 10,
                heat_level_percent=self._latest_reading['heater'] * 10
            )
    
    def set_heat(self, percent: int):
        """Set heat level."""
        self._hottop._config['heater'] = percent // 10
        self._hottop._q.put(self._hottop._config)
    
    # ... similar for other controls
```

### Key Considerations

1. **Caching**: Store latest reading from callback, return cached value in `read_sensors()`
2. **Thread Safety**: Use locks when accessing shared state
3. **Temperature Conversion**: Always convert F→C
4. **Percentage Conversion**: Always convert 0-10→0-100
5. **Validation**: Check `valid` flag before using readings
6. **Polling Interval**: pyhottop default is 0.6s, we want 1.0s (configure via `_config['interval']`)

---

## Resources

- Repository: https://github.com/splitkeycoffee/pyhottop
- PyPI: https://pypi.org/project/pyhottop/
- USB Driver: https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers
- Diagnostic Tool: `pyhottop-test test`

---

**Document Version**: 1.0  
**Created**: 2025-10-25  
**Status**: Complete
