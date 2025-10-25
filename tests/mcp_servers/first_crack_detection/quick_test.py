#!/usr/bin/env python3
"""Quick test to verify server starts and model loads correctly."""
import sys
from pathlib import Path

# Test 1: Config loading
print("1️⃣  Testing configuration loading...")
from src.mcp_servers.first_crack_detection.config import load_config
config = load_config()
print(f"   ✅ Config loaded: {config.model_checkpoint}")
print(f"   ✅ Model exists: {Path(config.model_checkpoint).exists()}")

# Test 2: Session Manager initialization  
print("\n2️⃣  Testing session manager initialization...")
from src.mcp_servers.first_crack_detection.session_manager import DetectionSessionManager
manager = DetectionSessionManager(config)
print(f"   ✅ Session manager initialized")

# Test 3: Audio file validation
print("\n3️⃣  Finding test audio file...")
audio_files = list(Path("data/raw").glob("*.wav"))
if not audio_files:
    print("   ⚠️  No audio files found in data/raw")
    sys.exit(0)

test_audio = str(audio_files[0])
print(f"   ✅ Found: {Path(test_audio).name}")

# Test 4: Start detection
print("\n4️⃣  Starting detection (this will load the model)...")
from src.mcp_servers.first_crack_detection.models import AudioConfig
audio_config = AudioConfig(
    audio_source_type="audio_file",
    audio_file_path=test_audio
)

try:
    result = manager.start_session(audio_config)
    print(f"   ✅ Detection started: {result.session_id}")
    print(f"   ✅ Audio source: {result.audio_source_details}")
    
    # Test 5: Get status
    print("\n5️⃣  Getting status...")
    import time
    time.sleep(2)  # Let it process a bit
    
    status = manager.get_status()
    print(f"   ✅ Session active: {status.session_active}")
    print(f"   ✅ Elapsed time: {status.elapsed_time}")
    print(f"   ✅ First crack detected: {status.first_crack_detected}")
    
    # Test 6: Stop detection
    print("\n6️⃣  Stopping detection...")
    summary = manager.stop_session()
    print(f"   ✅ Session stopped")
    print(f"   ✅ Duration: {summary.session_summary['duration']}")
    print(f"   ✅ First crack: {summary.session_summary['first_crack_detected']}")
    
    print("\n✅ ALL TESTS PASSED! MCP server is ready to use.")
    
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
