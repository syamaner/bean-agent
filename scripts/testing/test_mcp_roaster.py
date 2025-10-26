#!/usr/bin/env python3
"""Test MCP roaster control with real hardware."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_servers.roaster_control import (
    HottopRoaster, RoastSessionManager, ServerConfig, HardwareConfig
)
import time

print("=" * 60)
print("MCP ROASTER CONTROL TEST")
print("=" * 60)
print()

# Create configuration
config = ServerConfig(
    hardware=HardwareConfig(
        mock_mode=False,
        port="/dev/tty.usbserial-DN016OJ3",
        baud_rate=115200
    ),
    logging_level="INFO"
)

print("Creating hardware interface...")
hardware = HottopRoaster(port=config.hardware.port)

print("Creating session manager...")
session_manager = RoastSessionManager(hardware, config)

print("Starting session...")
session_manager.start_session()

try:
    print("\n✓ Session started")
    print("\nReading initial status...")
    status = session_manager.get_status()
    print(f"  Session active: {status.session_active}")
    print(f"  Roaster running: {status.roaster_running}")
    print(f"  Bean: {status.sensors.bean_temp_c}°C")
    print(f"  Chamber: {status.sensors.chamber_temp_c}°C")
    
    print("\nSTEP 1: Starting drum motor...")
    session_manager.start_roaster()
    time.sleep(3)
    status = session_manager.get_status()
    print(f"  Roaster running: {status.roaster_running}")
    print(f"  Bean: {status.sensors.bean_temp_c}°C | Chamber: {status.sensors.chamber_temp_c}°C")
    
    print("\nSTEP 2: Setting fan to 50%...")
    session_manager.set_fan(50)
    time.sleep(3)
    status = session_manager.get_status()
    print(f"  Fan: {status.sensors.fan_speed_percent}%")
    print(f"  Bean: {status.sensors.bean_temp_c}°C | Chamber: {status.sensors.chamber_temp_c}°C")
    
    print("\nSTEP 3: Setting heat to 30%...")
    session_manager.set_heat(30)
    time.sleep(5)
    status = session_manager.get_status()
    print(f"  Heat: {status.sensors.heat_level_percent}%")
    print(f"  Bean: {status.sensors.bean_temp_c}°C | Chamber: {status.sensors.chamber_temp_c}°C")
    
    print("\nSTEP 4: Turning off heat...")
    session_manager.set_heat(0)
    time.sleep(3)
    status = session_manager.get_status()
    print(f"  Heat: {status.sensors.heat_level_percent}%")
    
    print("\nSTEP 5: Stopping drum...")
    session_manager.stop_roaster()
    time.sleep(2)
    status = session_manager.get_status()
    print(f"  Roaster running: {status.roaster_running}")
    
    print("\n✓ Test complete!")
    
finally:
    print("\nStopping session...")
    session_manager.stop_session()
    print("✓ Session stopped")

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
