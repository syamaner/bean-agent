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
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from hardware and cleanup resources."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check current connection status.
        
        Returns:
            True if connected and ready, False otherwise
        """
        pass
    
    @abstractmethod
    def get_roaster_info(self) -> dict:
        """Get roaster model and identification info.
        
        Returns:
            Dict with keys: 'brand', 'model', 'version'
        """
        pass
    
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
    
    def __init__(self):
        self._connected = False
        self._bean_temp = 20.0  # Room temperature
        self._chamber_temp = 20.0
        self._heat = 0
        self._fan = 0
        self._drum_running = False
        self._cooling = False
        self._simulation_start = None
        self._last_update = None
    
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
        dt = now - self._last_update
        self._last_update = now
        
        if not self._drum_running:
            # No heat transfer without drum running
            return
        
        # Thermal model parameters (°C per second)
        heat_effect = (self._heat / 100.0) * 2.0  # Max 2°C/sec at 100% heat
        fan_effect = (self._fan / 100.0) * 0.5    # Max 0.5°C/sec cooling
        cooling_effect = 5.0 if self._cooling else 0  # Rapid cooling
        
        # Update chamber temperature
        chamber_delta = (heat_effect - fan_effect - cooling_effect) * dt
        self._chamber_temp += chamber_delta
        
        # Bean temperature lags chamber (thermal mass effect)
        # Beans try to reach chamber temp, but with lag
        bean_target = self._chamber_temp - 10.0  # Beans are ~10°C cooler
        bean_delta = (bean_target - self._bean_temp) * 0.1 * dt  # 10% per second
        self._bean_temp += bean_delta
        
        # Clamp to realistic values
        self._chamber_temp = max(15.0, min(300.0, self._chamber_temp))
        self._bean_temp = max(15.0, min(250.0, self._bean_temp))


class HottopRoaster(HardwareInterface):
    """Real Hottop KN-8828B-2K+ roaster hardware.
    
    Uses pyhottop library for USB serial communication.
    Note: Requires physical roaster connected via USB.
    """
    
    ROASTER_INFO = {
        "brand": "Hottop",
        "model": "KN-8828B-2K+",
        "version": "pyhottop"
    }
    
    def __init__(self, port: Optional[str] = None):
        """Initialize Hottop roaster interface.
        
        Args:
            port: USB serial port (e.g. '/dev/tty.usbserial-DN016OJ3')
                  If None, will auto-discover
        """
        from pyhottop.pyhottop import Hottop
        
        self._port = port
        self._connected = False
        self._hottop = Hottop()
        self._latest_reading = None
        self._callback_thread = None
    
    def connect(self) -> bool:
        """Connect to real Hottop hardware.
        
        Returns:
            True if connected successfully
        
        Raises:
            RoasterConnectionError: If connection fails
        """
        from .exceptions import RoasterConnectionError
        from pyhottop.pyhottop import SerialConnectionError
        
        try:
            self._hottop.connect(interface=self._port)
            self._connected = True
            
            # Start the pyhottop control loop with callback
            self._hottop.start(func=self._process_callback)
            
            return True
        except SerialConnectionError as e:
            raise RoasterConnectionError(str(e))
        except Exception as e:
            raise RoasterConnectionError(f"Failed to connect: {e}")
    
    def disconnect(self):
        """Disconnect from hardware."""
        if self._connected:
            try:
                self._hottop.end()
                if hasattr(self._hottop, '_conn') and self._hottop._conn:
                    self._hottop._conn.close()
            finally:
                self._connected = False
    
    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected
    
    def get_roaster_info(self) -> dict:
        """Return Hottop roaster info."""
        return self.ROASTER_INFO.copy()
    
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
        
        # Get the latest callback data
        if self._latest_reading is None:
            # Return safe defaults if no data yet
            return SensorReading(
                timestamp=datetime.now(UTC),
                bean_temp_c=0.0,
                chamber_temp_c=0.0,
                fan_speed_percent=0,
                heat_level_percent=0
            )
        
        return self._latest_reading
    
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
        
        # pyhottop.set_heater expects 0-100
        self._hottop.set_heater(percent)
    
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
        
        # pyhottop expects 0-10 scale for fan
        hottop_value = percent // 10
        self._hottop.set_fan(hottop_value)
    
    def start_drum(self):
        """Start drum motor.
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._hottop.set_drum_motor(True)
    
    def stop_drum(self):
        """Stop drum motor.
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._hottop.set_drum_motor(False)
    
    def drop_beans(self):
        """Open bean drop door (triggers pyhottop drop sequence).
        
        This will:
        - Stop drum
        - Turn off heat
        - Open solenoid
        - Start cooling motor and fan
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        # pyhottop.drop() handles the full drop sequence
        self._hottop.drop()
    
    def start_cooling(self):
        """Start cooling fan.
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._hottop.set_cooling_motor(True)
    
    def stop_cooling(self):
        """Stop cooling fan.
        
        Raises:
            RoasterNotConnectedError: If not connected
        """
        from .exceptions import RoasterNotConnectedError
        
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._hottop.set_cooling_motor(False)
    
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
    
    def _process_callback(self, data: dict):
        """Process pyhottop callback data and update latest reading.
        
        Args:
            data: Callback data from pyhottop with keys:
                  config: dict with bean_temp, environment_temp, heater, fan, etc.
                  time: optional roast time in minutes
                  roasting: optional roasting status
        
        Note:
            Temperature values from pyhottop depend on roaster configuration:
            - Celsius mode: Values are already in °C
            - Fahrenheit mode: Values in °F (need conversion)
            This implementation assumes Celsius mode (typical for KN-8828B-2K+)
        """
        from .models import SensorReading
        
        config = data.get('config', {})
        
        # Extract temps (assuming roaster is in Celsius mode)
        # If roaster is in Fahrenheit mode, values would need F→C conversion
        bean_temp_c = config.get('bean_temp', 0)
        chamber_temp_c = config.get('environment_temp', 0)
        
        # Extract control values (0-10 scale, convert to 0-100%)
        heater = config.get('heater', 0) * 10
        fan = config.get('fan', 0) * 10
        
        self._latest_reading = SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=round(bean_temp_c, 1),
            chamber_temp_c=round(chamber_temp_c, 1),
            fan_speed_percent=fan,
            heat_level_percent=heater
        )


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
