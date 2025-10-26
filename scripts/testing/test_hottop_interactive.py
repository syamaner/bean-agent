#!/usr/bin/env python3
"""Hottop roaster test - based on Artisan's working protocol."""
import serial
import time

PORT = "/dev/tty.usbserial-DN016OJ3"

def send_command(conn, heater=0, fan=0, main_fan=0, solenoid=0, drum_motor=1, cooling_motor=0):
    """Send command using Artisan's protocol."""
    cmd = bytearray([0x00] * 36)
    cmd[0] = 0xA5
    cmd[1] = 0x96
    cmd[2] = 0xB0
    cmd[3] = 0xA0
    cmd[4] = 0x01
    cmd[5] = 0x01
    cmd[6] = 0x24
    cmd[10] = int(heater)  # 0-100
    cmd[11] = int(round(fan / 10.0))  # convert 0-100 to 0-10
    cmd[12] = int(round(main_fan / 10.0))  # convert 0-100 to 0-10
    cmd[16] = solenoid
    cmd[17] = drum_motor
    if heater > 0:
        cmd[17] = 1  # Drum must be on when heating
    cmd[18] = cooling_motor
    cmd[35] = sum(cmd[:35]) & 0xFF
    
    conn.write(bytes(cmd))
    time.sleep(0.05)

def read_temps(conn):
    """Read temperature response using Artisan's parsing."""
    if conn.in_waiting >= 36:
        msg = conn.read(36)
        if len(msg) == 36 and msg[0] == 0xA5 and msg[1] == 0x96:
            # Validate checksum
            if msg[35] == (sum(msg[:35]) & 0xFF):
                # Parse temperatures (Artisan's method)
                et_raw = msg[23] * 256 + msg[24]  # Chamber/Environment temp
                bt_raw = msg[25] * 256 + msg[26]  # Bean temp
                
                # Convert from tenths of Fahrenheit to Celsius
                et_f = et_raw / 10.0
                bt_f = bt_raw / 10.0
                et_c = (et_f - 32) * 5.0 / 9.0
                bt_c = (bt_f - 32) * 5.0 / 9.0
                
                return {'bean_c': bt_c, 'chamber_c': et_c}
    return None

print("="*60)
print("HOTTOP ROASTER TEST (Artisan Protocol)")
print("="*60)
print()

conn = serial.Serial(PORT, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=0.5)
print("✓ Connected to roaster")
print()

try:
    input("Press ENTER to start drum motor...")
    print("\n1. Starting drum motor...")
    send_command(conn, drum_motor=1)
    time.sleep(1)
    print("   ✓ Drum started")
    
    input("\nPress ENTER to read temperatures...")
    print("\n2. Reading temperatures (5 readings)...")
    for i in range(5):
        send_command(conn, drum_motor=1)
        time.sleep(0.3)
        temps = read_temps(conn)
        if temps:
            print(f"   Bean: {temps['bean_c']:6.1f}°C  |  Chamber: {temps['chamber_c']:6.1f}°C")
        time.sleep(0.5)
    
    input("\nPress ENTER to set fan to 50%...")
    print("\n3. Setting fan to 50%...")
    send_command(conn, drum_motor=1, fan=50)
    time.sleep(1)
    print("   ✓ Fan set to 50%")
    
    input("\nPress ENTER to set heat to 30%...")
    print("\n4. Setting heat to 30%...")
    send_command(conn, drum_motor=1, fan=50, heater=30)
    time.sleep(1)
    print("   ✓ Heat set to 30%")
    
    input("\nPress ENTER to turn OFF heat and fan...")
    print("\n5. Turning OFF heat and fan...")
    send_command(conn, drum_motor=1, heater=0, fan=0)
    time.sleep(1)
    print("   ✓ Heat and fan OFF")
    
    input("\nPress ENTER to open bean drop door...")
    print("\n6. Opening bean drop door (solenoid + cooling)...")
    send_command(conn, drum_motor=0, solenoid=1, cooling_motor=1, main_fan=100)
    time.sleep(2)
    print("   ✓ Bean drop opened")
    
    input("\nPress ENTER to close bean drop door...")
    print("\n7. Closing bean drop door...")
    send_command(conn, drum_motor=0, solenoid=0, cooling_motor=0, main_fan=0)
    time.sleep(1)
    print("   ✓ Bean drop closed")
    
    input("\nPress ENTER to STOP roaster...")
    print("\n8. Stopping roaster (all OFF)...")
    send_command(conn, drum_motor=0, heater=0, fan=0, main_fan=0, solenoid=0, cooling_motor=0)
    time.sleep(1)
    print("   ✓ Roaster stopped")
    
finally:
    conn.close()
    print("\n✓ Disconnected")
    print("\n" + "="*60)
    print("TEST COMPLETE!")
    print("="*60)
