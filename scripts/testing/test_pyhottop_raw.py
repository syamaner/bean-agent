#!/usr/bin/env python3
"""Test raw pyhottop library with Hottop hardware."""
import time
from pyhottop.pyhottop import Hottop

PORT = "/dev/tty.usbserial-DN016OJ3"

print("=" * 60)
print("RAW PYHOTTOP TEST")
print("=" * 60)
print()

# Initialize
print(f"1. Initializing Hottop on {PORT}...")
hottop = Hottop()

# Callback to see data
def callback(data):
    config = data.get('config', {})
    print(f"   Callback: Bean={config.get('bean_temp', 0)}°C, "
          f"Chamber={config.get('environment_temp', 0)}°C, "
          f"Heat={config.get('heater', 0)}, Fan={config.get('fan', 0)}")

print("2. Connecting...")
try:
    hottop.connect(interface=PORT)
    print("   ✓ Connected!")
except Exception as e:
    print(f"   ✗ Connection failed: {e}")
    exit(1)

print("3. Starting control loop with callback...")
hottop.start(func=callback)
time.sleep(2)

print("4. Starting drum motor...")
hottop.set_drum_motor(True)
time.sleep(3)

print("5. Setting heat to 30%...")
hottop.set_heater(30)
time.sleep(3)

print("6. Setting fan to 3 (30%)...")
hottop.set_fan(3)
time.sleep(3)

print("7. Reading current state...")
time.sleep(2)

print("8. Setting heat to 0%...")
hottop.set_heater(0)
time.sleep(2)

print("9. Setting fan to 0...")
hottop.set_fan(0)
time.sleep(2)

print("10. Stopping drum motor...")
hottop.set_drum_motor(False)
time.sleep(2)

print("11. Ending control loop...")
hottop.end()

print("12. Closing connection...")
if hasattr(hottop, '_conn') and hottop._conn:
    hottop._conn.close()

print()
print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)
