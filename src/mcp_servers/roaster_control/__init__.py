"""Roaster control MCP server.

Provides hardware abstraction, session management, and MCP tools
for controlling coffee roasters.
"""
from .server import server, init_server
from .models import (
    ServerConfig,
    HardwareConfig,
    TrackerConfig,
    SensorReading,
    RoastMetrics,
    RoastStatus,
)
from .hardware import HardwareInterface, MockRoaster, HottopRoaster, StubRoaster
from .session_manager import RoastSessionManager
from .exceptions import (
    RoasterError,
    RoasterNotConnectedError,
    RoasterConnectionError,
    InvalidCommandError,
    NoActiveRoastError,
    BeansNotAddedError,
)

__all__ = [
    # Server
    "server",
    "init_server",
    # Models
    "ServerConfig",
    "HardwareConfig",
    "TrackerConfig",
    "SensorReading",
    "RoastMetrics",
    "RoastStatus",
    # Hardware
    "HardwareInterface",
    "MockRoaster",
    "HottopRoaster",
    "StubRoaster",
    # Session
    "RoastSessionManager",
    # Exceptions
    "RoasterError",
    "RoasterNotConnectedError",
    "RoasterConnectionError",
    "InvalidCommandError",
    "NoActiveRoastError",
    "BeansNotAddedError",
]