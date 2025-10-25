"""Hardware interface for coffee roaster control.

Supports multiple roaster implementations:
- MockRoaster: Simulated roaster for testing with realistic thermal model
- HottopRoaster: Real Hottop KN-8828B-2K+ hardware via pyhottop library
- StubRoaster: Simple stub for demos without hardware (future)
"""
from abc import ABC, abstractmethod
from datetime import datetime
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
        self._bean_temp = 20.0
        self._chamber_temp = 20.0
        self._heat = 0
        self._fan = 0
    
    def connect(self) -> bool:
        """Simulate connection."""
        self._connected = True
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
            port: USB serial port (e.g. '/dev/tty.usbserial-1420')
                  If None, will auto-discover
        """
        self._port = port
        self._connected = False
        # pyhottop will be initialized in M3 Task 3.2
    
    def connect(self) -> bool:
        """Connect to real Hottop hardware.
        
        Will be implemented in M3 Task 3.2 with pyhottop integration.
        """
        raise NotImplementedError(
            "HottopRoaster.connect() - To be implemented in M3 Task 3.2"
        )
    
    def disconnect(self):
        """Disconnect from hardware."""
        raise NotImplementedError(
            "HottopRoaster.disconnect() - To be implemented in M3 Task 3.2"
        )
    
    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected
    
    def get_roaster_info(self) -> dict:
        """Return Hottop roaster info."""
        return self.ROASTER_INFO.copy()


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
