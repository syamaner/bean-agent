"""Hardware interface for coffee roaster control.

Supports multiple roaster implementations:
- MockRoaster: Simulated roaster for testing with realistic thermal model
- HottopRoaster: Real Hottop KN-8828B-2K+ hardware via pyhottop library
- StubRoaster: Simple stub for demos without hardware (future)
"""
from abc import ABC, abstractmethod
from datetime import datetime, UTC
from typing import Optional


class HardwareInterface(ABC):
    """Abstract base class for roaster hardware.
    
    This interface allows supporting multiple roaster brands and models.
    Implementations must provide:
    - Connection management
    - Sensor reading (temperatures, settings)
    - Control commands (heat, fan, drum, cooling, drop)
    """
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to roaster hardware.
        
        Returns:
            True if connection successful, False otherwise
        """
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from hardware and cleanup resources."""
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check current connection status.
        
        Returns:
            True if connected and ready, False otherwise
        """
    
    @abstractmethod
    def get_roaster_info(self) -> dict:
        """Get roaster model and identification info.
        
        Returns:
            Dict with keys: 'brand', 'model', 'version'
        """
    
    @abstractmethod
    def is_drum_running(self) -> bool:
        """Check if drum motor is currently running.
        
        Returns:
            True if drum is running, False otherwise
        """
    
    # More methods will be defined in Milestone 3


class MockRoaster(HardwareInterface):
    """Simulated roaster for testing.
    
    Provides realistic thermal simulation for development and testing
    without requiring physical hardware.
    """
    
    ROASTER_INFO = {
        "brand": "Mock",
        "model": "Simulator v1.0",
        "version": "1.0.0"
    }
    
    # Thermal simulation constants
    MAX_HEAT_RATE_C_PER_SEC = 2.0  # Max heating at 100% heat
    MAX_FAN_COOLING_C_PER_SEC = 0.5  # Max cooling at 100% fan
    COOLING_MODE_RATE_C_PER_SEC = 5.0  # Rapid cooling when cooling active
    BEAN_LAG_TEMP_OFFSET_C = 10.0  # Beans are ~10°C cooler than chamber
    BEAN_THERMAL_LAG_FACTOR = 0.1  # Beans reach 10% of target per second
    MIN_TEMP_C = 15.0  # Minimum simulated temperature
    MAX_CHAMBER_TEMP_C = 300.0  # Maximum chamber temperature
    MAX_BEAN_TEMP_C = 250.0  # Maximum bean temperature
    
    def __init__(self, time_scale: float = 1.0):
        """Initialize mock roaster.
        
        Args:
            time_scale: Time acceleration factor (1.0 = real-time, 100.0 = 100x faster)
                       Useful for testing to simulate long roasts quickly.
                       WARNING: Only use values > 1.0 in automated tests.
        """
        import logging
        
        self._connected = False
        self._bean_temp = 20.0  # Room temperature
        self._chamber_temp = 20.0
        self._heat = 0
        self._fan = 0
        self._drum_running = False
        self._cooling = False
        self._simulation_start = None
        self._last_update = None
        self._time_scale = time_scale
        
        # Warn if time acceleration is enabled (should only be in tests)
        if time_scale != 1.0:
            logger = logging.getLogger(__name__)
            logger.warning(
                f"MockRoaster initialized with time_scale={time_scale}. "
                f"This should only be used in automated tests!"
            )
    
    def connect(self) -> bool:
        """Simulate connection."""
        import time
        self._connected = True
        self._simulation_start = time.time()
        self._last_update = time.time()
        return True
    
    def disconnect(self):
        """Simulate disconnection."""
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected
    
    def get_roaster_info(self) -> dict:
        """Return mock roaster info."""
        return self.ROASTER_INFO.copy()
    
    def is_drum_running(self) -> bool:
        """Check if drum motor is running."""
        return self._drum_running
    
    def read_sensors(self):
        """Read simulated sensor values.
        
        Returns:
            SensorReading with current simulated values
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .models import SensorReading
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        # Update simulation based on time passed
        self._update_simulation()
        
        return SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=round(self._bean_temp, 1),
            chamber_temp_c=round(self._chamber_temp, 1),
            fan_speed_percent=self._fan,
            heat_level_percent=self._heat
        )
    
    def set_heat(self, percent: int):
        """Set heat level.
        
        Args:
            percent: Heat percentage (0-100 in 10% increments)
        
        Raises:
            RoasterNotConnectedError: If not connected
            InvalidCommandError: If invalid value
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._validate_percentage(percent, "heat")
        self._heat = percent
    
    def set_fan(self, percent: int):
        """Set fan speed.
        
        Args:
            percent: Fan percentage (0-100 in 10% increments)
        
        Raises:
            RoasterNotConnectedError: If not connected
            InvalidCommandError: If invalid value
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._validate_percentage(percent, "fan")
        self._fan = percent
    
    def start_drum(self):
        """Start drum motor.
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._drum_running = True
    
    def stop_drum(self):
        """Stop drum motor.
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._drum_running = False
    
    def drop_beans(self):
        """Open bean drop door (also stops drum and starts cooling).
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._drum_running = False
        self._cooling = True
    
    def start_cooling(self):
        """Start cooling fan.
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._cooling = True
    
    def stop_cooling(self):
        """Stop cooling fan.
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._cooling = False
    
    def _validate_percentage(self, value: int, name: str):
        """Validate percentage is in valid range and 10% increments.
        
        Args:
            value: Percentage value
            name: Parameter name for error message
        
        Raises:
            InvalidCommandError: If validation fails
        """
        from .exceptions import InvalidCommandError
        
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
        """Update simulated temperatures based on heat/fan/time.
        
        Uses simplified thermal model:
        - Heat increases chamber temperature
        - Fan cools chamber temperature
        - Cooling mode rapidly decreases temperature
        - Bean temperature lags chamber temperature
        - Drum must be running for heat to transfer
        """
        import time
        
        now = time.time()
        dt = (now - self._last_update) * self._time_scale  # Apply time acceleration
        self._last_update = now
        
        if not self._drum_running:
            # No heat transfer without drum running
            return
        
        # Thermal model parameters (°C per second)
        heat_effect = (self._heat / 100.0) * self.MAX_HEAT_RATE_C_PER_SEC
        fan_effect = (self._fan / 100.0) * self.MAX_FAN_COOLING_C_PER_SEC
        cooling_effect = self.COOLING_MODE_RATE_C_PER_SEC if self._cooling else 0
        
        # Update chamber temperature
        chamber_delta = (heat_effect - fan_effect - cooling_effect) * dt
        self._chamber_temp += chamber_delta
        
        # Bean temperature lags chamber (thermal mass effect)
        # Beans try to reach chamber temp, but with lag
        bean_target = self._chamber_temp - self.BEAN_LAG_TEMP_OFFSET_C
        bean_delta = (bean_target - self._bean_temp) * self.BEAN_THERMAL_LAG_FACTOR * dt
        self._bean_temp += bean_delta
        
        # Clamp to realistic values
        self._chamber_temp = max(self.MIN_TEMP_C, min(self.MAX_CHAMBER_TEMP_C, self._chamber_temp))
        self._bean_temp = max(self.MIN_TEMP_C, min(self.MAX_BEAN_TEMP_C, self._bean_temp))


class HottopRoaster(HardwareInterface):
    """Real Hottop KN-8828B-2K+ roaster hardware.
    
    Uses direct serial communication following Artisan protocol.
    Sends continuous control commands at 0.3s intervals (required by Hottop).
    Note: Requires physical roaster connected via USB.
    """
    
    ROASTER_INFO = {
        "brand": "Hottop",
        "model": "KN-8828B-2K+",
        "version": "serial-direct"
    }
    
    def __init__(self, port: Optional[str] = None):
        """Initialize Hottop roaster interface.
        
        Args:
            port: USB serial port (e.g. '/dev/tty.usbserial-DN016OJ3')
                  If None, defaults to common Hottop port
        """
        import serial
        import threading
        
        self._port = port or "/dev/tty.usbserial-DN016OJ3"
        self._connected = False
        self._serial: Optional[serial.Serial] = None
        
        # Control state (continuously sent to roaster)
        # Initialize with SAFE defaults - everything OFF
        self._state = {
            'heater': 0,       # 0-100%
            'fan': 0,          # 0-100%
            'main_fan': 0,     # 0-100%
            'solenoid': 0,     # 0=closed, 1=open (bean drop)
            'drum_motor': 0,   # 0=off, 1=on
            'cooling_motor': 0 # 0=off, 1=on
        }
        
        # Latest sensor readings from roaster
        self._latest_bean_temp = 0.0
        self._latest_chamber_temp = 0.0
        
        # Command loop thread
        self._running = False
        self._command_thread: Optional[threading.Thread] = None
        self._state_lock = threading.Lock()
    
    def connect(self) -> bool:
        """Connect to real Hottop hardware.
        
        Returns:
            True if connected successfully
        
        Raises:
            RoasterConnectionError: If connection fails
        """
        import serial
        import threading
        from .exceptions import RoasterConnectionError
        
        try:
            # Open serial connection
            self._serial = serial.Serial(
                self._port,
                baudrate=115200,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=0.5
            )
            self._connected = True
            
            # Start continuous command loop (required by Hottop protocol)
            # Commands are sent every 0.3s with current state
            self._running = True
            self._command_thread = threading.Thread(
                target=self._command_loop,
                daemon=True,
                name="HottopCommandLoop"
            )
            self._command_thread.start()
            
            return True
        except serial.SerialException as e:
            raise RoasterConnectionError(f"Serial connection failed: {e}")
        except Exception as e:
            raise RoasterConnectionError(f"Failed to connect: {e}")
    
    def disconnect(self):
        """Disconnect from hardware and stop command loop."""
        if self._connected:
            # Stop command loop
            self._running = False
            if self._command_thread and self._command_thread.is_alive():
                self._command_thread.join(timeout=1.0)
            
            # Close serial connection
            if self._serial and self._serial.is_open:
                self._serial.close()
            
            self._connected = False
            self._serial = None
    
    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected
    
    def get_roaster_info(self) -> dict:
        """Return Hottop roaster info."""
        return self.ROASTER_INFO.copy()
    
    def is_drum_running(self) -> bool:
        """Check if drum motor is running."""
        with self._state_lock:
            return self._state['drum_motor'] == 1
    
    def read_sensors(self):
        """Read current sensor values from Hottop.
        
        Returns:
            SensorReading with current values
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .models import SensorReading
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        with self._state_lock:
            return SensorReading(
                timestamp=datetime.now(UTC),
                bean_temp_c=round(self._latest_bean_temp, 1),
                chamber_temp_c=round(self._latest_chamber_temp, 1),
                fan_speed_percent=self._state['main_fan'],
                heat_level_percent=self._state['heater']
            )
    
    def set_heat(self, percent: int):
        """Set heat level.
        
        Args:
            percent: Heat percentage (0-100 in 10% increments)
        
        Raises:
            RoasterNotConnectedError: If not connected
            InvalidCommandError: If invalid value
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._validate_percentage(percent, "heat")
        
        with self._state_lock:
            self._state['heater'] = percent
            # Auto-enable drum when heat is on (required by Hottop)
            if percent > 0:
                self._state['drum_motor'] = 1
    
    def set_fan(self, percent: int):
        """Set fan speed (main fan).
        
        Args:
            percent: Fan percentage (0-100 in 10% increments)
        
        Raises:
            RoasterNotConnectedError: If not connected
            InvalidCommandError: If invalid value
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._validate_percentage(percent, "fan")
        
        with self._state_lock:
            self._state['main_fan'] = percent
    
    def start_drum(self):
        """Start drum motor.
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        with self._state_lock:
            self._state['drum_motor'] = 1
    
    def stop_drum(self):
        """Stop drum motor.
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        with self._state_lock:
            self._state['drum_motor'] = 0
            # Also turn off heat (safety - can't heat without drum)
            self._state['heater'] = 0
    
    def drop_beans(self):
        """Open bean drop door and start cooling.
        
        This will:
        - Stop drum motor
        - Turn off heat
        - Open solenoid (bean drop door)
        - Start cooling motor and fan at 100%
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        with self._state_lock:
            self._state['drum_motor'] = 0
            self._state['heater'] = 0
            self._state['solenoid'] = 1
            self._state['cooling_motor'] = 1
            self._state['main_fan'] = 100
    
    def start_cooling(self):
        """Start cooling motor and fan.
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        with self._state_lock:
            self._state['cooling_motor'] = 1
            self._state['main_fan'] = 100
    
    def stop_cooling(self):
        """Stop cooling motor and close bean drop door.
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        with self._state_lock:
            self._state['cooling_motor'] = 0
            self._state['solenoid'] = 0
            self._state['main_fan'] = 0
    
    def _validate_percentage(self, value: int, name: str):
        """Validate percentage is in valid range and 10% increments.
        
        Args:
            value: Percentage value
            name: Parameter name for error message
        
        Raises:
            InvalidCommandError: If validation fails
        """
        from .exceptions import InvalidCommandError
        
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
    
    def _command_loop(self):
        """Continuously send commands to roaster at 0.3s intervals.
        
        This is required by the Hottop protocol - commands must be sent
        continuously or the roaster will stop responding.
        
        Also reads temperature responses and updates sensor values.
        """
        import time
        
        while self._running and self._connected:
            try:
                # Send command with current state
                self._send_command()
                
                # Read temperature response
                temps = self._read_temps()
                if temps:
                    with self._state_lock:
                        self._latest_bean_temp = temps['bean_c']
                        self._latest_chamber_temp = temps['chamber_c']
                
                # Wait 0.3 seconds between commands
                time.sleep(0.3)
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in command loop: {e}")
                time.sleep(0.3)
    
    def _send_command(self):
        """Send control command to roaster using Artisan protocol.
        
        Sends current state every 0.3s. State only changes when explicitly set.
        """
        if not self._serial or not self._serial.is_open:
            return
        
        with self._state_lock:
            # Build 36-byte command packet
            cmd = bytearray([0x00] * 36)
            cmd[0] = 0xA5  # Header
            cmd[1] = 0x96
            cmd[2] = 0xB0
            cmd[3] = 0xA0
            cmd[4] = 0x01
            cmd[5] = 0x01
            cmd[6] = 0x24
            cmd[10] = int(self._state['heater'])  # 0-100%
            cmd[11] = int(round(self._state['fan'] / 10.0))  # 0-10 scale
            cmd[12] = int(round(self._state['main_fan'] / 10.0))  # 0-10 scale
            cmd[16] = self._state['solenoid']
            cmd[17] = self._state['drum_motor']
            cmd[18] = self._state['cooling_motor']
            cmd[35] = sum(cmd[:35]) & 0xFF  # Checksum
        
        self._serial.write(bytes(cmd))
    
    def _read_temps(self) -> Optional[dict]:
        """Read temperature response from roaster.
        
        Returns:
            Dict with 'bean_c' and 'chamber_c' keys, or None if no valid data
        """
        if not self._serial or not self._serial.is_open:
            return None
        
        available = self._serial.in_waiting
        if available >= 36:
            data = self._serial.read(available)
            
            # Find valid 36-byte message starting with A5 96
            for offset in range(len(data) - 35):
                if data[offset] == 0xA5 and data[offset+1] == 0x96:
                    msg = data[offset:offset+36]
                    if len(msg) == 36:
                        checksum = sum(msg[:35]) & 0xFF
                        if msg[35] == checksum:
                            # Big-endian temperature values in Celsius
                            et_c = msg[23] * 256 + msg[24]
                            bt_c = msg[25] * 256 + msg[26]
                            return {'bean_c': bt_c, 'chamber_c': et_c}
        
        return None


class StubRoaster(HardwareInterface):
    """Simple stub roaster for public demos.
    
    Returns fixed values without simulation.
    Useful for demos when you don't want to show changing temperatures.
    """
    
    ROASTER_INFO = {
        "brand": "Demo",
        "model": "Stub v1.0",
        "version": "1.0.0"
    }
    
    def __init__(self):
        self._connected = False
        self._drum_running = False
    
    def connect(self) -> bool:
        """Simulate connection."""
        self._connected = True
        return True
    
    def disconnect(self):
        """Disconnect."""
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check connection."""
        return self._connected
    
    def get_roaster_info(self) -> dict:
        """Return stub roaster info."""
        return self.ROASTER_INFO.copy()
    
    def is_drum_running(self) -> bool:
        """Check if drum motor is running."""
        return self._drum_running
