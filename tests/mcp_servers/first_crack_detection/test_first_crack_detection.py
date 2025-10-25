#!/usr/bin/env python3
"""
Test first crack detection with actual inference.

This test will:
1. Start detection with a real roast audio file
2. Monitor for first crack detection (up to 60 seconds)
3. Report when first crack is detected
"""
import sys
import time
from pathlib import Path

print("🔥 First Crack Detection Test")
print("=" * 60)

# Setup
print("\n1️⃣  Loading configuration...")
from src.mcp_servers.first_crack_detection.config import load_config
config = load_config()
print(f"   Model: {Path(config.model_checkpoint).name}")
print(f"   Threshold: {config.default_threshold}")
print(f"   Min pops: {config.default_min_pops}")
print(f"   Confirmation window: {config.default_confirmation_window}s")

# Find audio file
print("\n2️⃣  Finding roast audio file...")
audio_files = list(Path("data/raw").glob("*.wav"))
if not audio_files:
    print("   ❌ No audio files found in data/raw")
    sys.exit(1)

test_audio = str(audio_files[0])
print(f"   Audio file: {Path(test_audio).name}")

# Initialize session manager
print("\n3️⃣  Initializing detection system...")
from src.mcp_servers.first_crack_detection.session_manager import DetectionSessionManager
from src.mcp_servers.first_crack_detection.models import AudioConfig

manager = DetectionSessionManager(config)
audio_config = AudioConfig(
    audio_source_type="audio_file",
    audio_file_path=test_audio
)

# Start detection
print("\n4️⃣  Starting detection (loading model, this may take a moment)...")
result = manager.start_session(audio_config)
print(f"   ✅ Session started: {result.session_id}")
print(f"   Started at: {result.started_at_local}")
print(f"\n" + "=" * 60)
print("🎧 MONITORING FOR FIRST CRACK...")
print("=" * 60 + "\n")

# Monitor for first crack
try:
    max_duration = 120  # Monitor for up to 2 minutes
    check_interval = 1.0  # Check every second
    last_elapsed = "00:00"
    
    for i in range(int(max_duration / check_interval)):
        time.sleep(check_interval)
        
        status = manager.get_status()
        
        if not status.session_active:
            print(f"\n⚠️  Session ended (file finished processing)")
            break
        
        elapsed = status.elapsed_time
        detected = status.first_crack_detected
        
        # Only print update every 5 seconds or on change
        if elapsed != last_elapsed and (int(elapsed.split(':')[1]) % 5 == 0 or detected):
            if detected:
                fc_time = status.first_crack_time_relative
                fc_local = status.first_crack_time_local
                print(f"\n{'=' * 60}")
                print(f"🎉 FIRST CRACK DETECTED!")
                print(f"{'=' * 60}")
                print(f"   Relative time: {fc_time}")
                print(f"   Absolute time (local): {fc_local}")
                print(f"   Absolute time (UTC): {status.first_crack_time_utc}")
                print(f"   Current elapsed: {elapsed}")
                print(f"{'=' * 60}\n")
                
                # Continue monitoring for a bit
                print("   Continuing to monitor for 5 more seconds...")
                time.sleep(5)
                break
            else:
                print(f"   [{elapsed}] Listening... (no first crack yet)")
            
            last_elapsed = elapsed
    
    else:
        print(f"\n⏱️  Monitoring timeout reached ({max_duration}s)")
    
finally:
    # Stop detection
    print(f"\n5️⃣  Stopping detection...")
    summary = manager.stop_session()
    
    print(f"\n" + "=" * 60)
    print("📊 SESSION SUMMARY")
    print("=" * 60)
    print(f"Session ID: {summary.session_id}")
    print(f"Duration: {summary.session_summary['duration']}")
    print(f"First crack detected: {summary.session_summary['first_crack_detected']}")
    
    if summary.session_summary['first_crack_detected']:
        print(f"First crack time: {summary.session_summary.get('first_crack_time', 'N/A')}")
        print(f"\n✅ SUCCESS! First crack was detected.")
    else:
        print(f"\n⚠️  No first crack detected in monitored duration.")
        print(f"   This could mean:")
        print(f"   - First crack happens later in the roast")
        print(f"   - Detection threshold needs adjustment")
        print(f"   - Audio quality issues")
    
    print(f"\nAudio source: {summary.session_summary['audio_source']}")
    print("=" * 60)

print("\n✅ Test complete!")
