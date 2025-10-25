"""Hardware interface for Hottop roaster control."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class HardwareInterface(ABC):
    """Abstract base class for roaster hardware."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to roaster hardware."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from hardware."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection status."""
        pass
    
    # More methods will be defined in Milestone 3


class MockHardware(HardwareInterface):
    """Simulated roaster for testing."""
    
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