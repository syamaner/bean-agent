#!/usr/bin/env python3
"""Hottop automatic test - continuous commands with 20s steps."""
import serial
import time
import threading

PORT = "/dev/tty.usbserial-DN016OJ3"

# State to send continuously
current_state = {
    'heater': 0,
    'fan': 0,
    'main_fan': 0,
    'solenoid': 0,
    'drum_motor': 0,
    'cooling_motor': 0
}

running = True

def send_command(conn):
    """Send command using Artisan's protocol."""
    cmd = bytearray([0x00] * 36)
    cmd[0] = 0xA5
    cmd[1] = 0x96
    cmd[2] = 0xB0
    cmd[3] = 0xA0
    cmd[4] = 0x01
    cmd[5] = 0x01
    cmd[6] = 0x24
    cmd[10] = int(current_state['heater'])  # 0-100
    cmd[11] = int(round(current_state['fan'] / 10.0))  # 0-10
    cmd[12] = int(round(current_state['main_fan'] / 10.0))  # 0-10
    cmd[16] = current_state['solenoid']
    cmd[17] = current_state['drum_motor']
    if current_state['heater'] > 0:
        cmd[17] = 1  # Drum must be on when heating
    cmd[18] = current_state['cooling_motor']
    cmd[35] = sum(cmd[:35]) & 0xFF
    
    conn.write(bytes(cmd))

def read_temps(conn):
    """Read temperature response."""
    available = conn.in_waiting
    if available >= 36:
        data = conn.read(available)
        # Find valid 36-byte message starting with A5 96
        for offset in range(len(data) - 35):
            if data[offset] == 0xA5 and data[offset+1] == 0x96:
                msg = data[offset:offset+36]
                if len(msg) == 36:
                    checksum = sum(msg[:35]) & 0xFF
                    if msg[35] == checksum:
                        # Big-endian, values in Celsius
                        et_c = msg[23] * 256 + msg[24]
                        bt_c = msg[25] * 256 + msg[26]
                        return {'bean_c': bt_c, 'chamber_c': et_c}
    return None

def command_loop(conn):
    """Continuously send commands at 0.3s intervals."""
    while running:
        send_command(conn)
        time.sleep(0.3)

def wait_with_temps(conn, seconds, message):
    """Wait while showing temperatures."""
    print(f"\n{message}")
    print(f"Waiting {seconds} seconds...")
    for i in range(seconds * 2):  # Check every 0.5s
        temps = read_temps(conn)
        if temps and i % 4 == 0:  # Print every 2s
            print(f"  Bean: {temps['bean_c']:6.1f}°C  |  Chamber: {temps['chamber_c']:6.1f}°C")
        time.sleep(0.5)
    print("✓ Step complete\n")

print("="*60)
print("HOTTOP AUTOMATIC TEST")
print("="*60)
print()

conn = serial.Serial(PORT, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=0.5)
print("✓ Connected to roaster\n")

# Start command loop in background
cmd_thread = threading.Thread(target=command_loop, args=(conn,), daemon=True)
cmd_thread.start()

try:
    # Step 1: Start drum
    print("STEP 1: Starting drum motor")
    current_state['drum_motor'] = 1
    wait_with_temps(conn, 20, "Drum should be running...")
    
    # Step 2: Turn on main fan 50%
    print("STEP 2: Setting main fan to 50%")
    current_state['main_fan'] = 50
    wait_with_temps(conn, 20, "Main fan at 50%, drum running...")
    
    # Step 3: Turn on heat 30%
    print("STEP 3: Setting heat to 30%")
    current_state['heater'] = 30
    wait_with_temps(conn, 20, "Heat at 30%, main fan at 50%, drum running...")
    
    # Step 4: Turn off heat
    print("STEP 4: Turning OFF heat")
    current_state['heater'] = 0
    wait_with_temps(conn, 20, "Heat OFF, main fan at 50%, drum running...")
    
    # Step 5: Open bean drop door
    print("STEP 5: Opening bean drop door")
    current_state['drum_motor'] = 0
    current_state['solenoid'] = 1
    current_state['cooling_motor'] = 1
    current_state['main_fan'] = 100
    wait_with_temps(conn, 20, "Bean drop open, cooling active...")
    
    # Step 6: Close bean drop
    print("STEP 6: Closing bean drop door")
    current_state['solenoid'] = 0
    current_state['cooling_motor'] = 0
    current_state['main_fan'] = 0
    wait_with_temps(conn, 10, "Bean drop closed...")
    
    # Step 7: Full stop
    print("STEP 7: STOPPING roaster")
    current_state['drum_motor'] = 0
    current_state['heater'] = 0
    current_state['fan'] = 0
    current_state['main_fan'] = 0
    current_state['solenoid'] = 0
    current_state['cooling_motor'] = 0
    time.sleep(2)
    print("✓ All systems OFF\n")
    
finally:
    running = False
    time.sleep(0.5)
    conn.close()
    print("✓ Disconnected")
    print("\n" + "="*60)
    print("TEST COMPLETE!")
    print("="*60)
