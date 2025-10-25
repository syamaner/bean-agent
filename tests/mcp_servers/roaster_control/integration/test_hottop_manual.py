#!/usr/bin/env python3
"""Manual integration test for HottopRoaster with real hardware.

This script is NOT run by pytest automatically. It's for manual testing
with the physical Hottop roaster connected.

Usage:
    ./venv/bin/python tests/mcp_servers/roaster_control/integration/test_hottop_manual.py

Requirements:
- Hottop KN-8828B-2K+ roaster connected via USB
- Roaster powered ON and ready
- Port /dev/tty.usbserial-DN016OJ3 available (or update PORT below)
"""
import sys
import time
sys.path.insert(0, 'src')

from src.mcp_servers.roaster_control.hardware import HottopRoaster

# Update this to match your USB serial port
PORT = "/dev/tty.usbserial-DN016OJ3"

def main():
    """Run manual integration test."""
    print("=" * 60)
    print("HottopRoaster Manual Integration Test")
    print("=" * 60)
    print()
    
    # Initialize
    print(f"Initializing HottopRoaster on port: {PORT}")
    roaster = HottopRoaster(port=PORT)
    print(f"  Roaster info: {roaster.get_roaster_info()}")
    print()
    
    # Connect
    print("Connecting to roaster...")
    try:
        roaster.connect()
        print("  ✓ Connected successfully!")
        print(f"  Connection status: {roaster.is_connected()}")
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        return 1
    print()
    
    # Wait for initial data
    print("Waiting 2 seconds for initial sensor data...")
    time.sleep(2)
    print()
    
    # Read sensors
    print("Reading sensors (10 readings, 1 second apart):")
    for i in range(10):
        try:
            reading = roaster.read_sensors()
            print(f"  [{i+1}] Bean: {reading.bean_temp_c:6.1f}°C  "
                  f"Chamber: {reading.chamber_temp_c:6.1f}°C  "
                  f"Heat: {reading.heat_level_percent:3d}%  "
                  f"Fan: {reading.fan_speed_percent:3d}%  "
                  f"Time: {reading.timestamp.strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"  [{i+1}] Error reading: {e}")
        time.sleep(1)
    print()
    
    # Test controls (SAFE - no heat, just commands)
    print("Testing control commands (safe - no heat applied):")
    
    # Test fan
    print("  Setting fan to 20%...")
    try:
        roaster.set_fan(20)
        print("    ✓ Fan set")
    except Exception as e:
        print(f"    ✗ Error: {e}")
    
    time.sleep(1)
    
    # Test drum
    print("  Starting drum...")
    try:
        roaster.start_drum()
        print("    ✓ Drum started")
    except Exception as e:
        print(f"    ✗ Error: {e}")
    
    time.sleep(1)
    
    # Read final state
    print("  Reading final sensor state...")
    try:
        reading = roaster.read_sensors()
        print(f"    Bean: {reading.bean_temp_c}°C, "
              f"Chamber: {reading.chamber_temp_c}°C, "
              f"Fan: {reading.fan_speed_percent}%")
    except Exception as e:
        print(f"    ✗ Error: {e}")
    
    print()
    
    # Cleanup
    print("Disconnecting...")
    try:
        roaster.disconnect()
        print("  ✓ Disconnected successfully")
        print(f"  Connection status: {roaster.is_connected()}")
    except Exception as e:
        print(f"  ✗ Disconnect error: {e}")
    
    print()
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
