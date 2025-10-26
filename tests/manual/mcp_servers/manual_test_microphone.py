#!/usr/bin/env python3
"""
Test script for FirstCrackDetector with USB microphone.
"""
import sys
import time
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from inference import FirstCrackDetector


def main():
    # Configuration
    checkpoint_path = "experiments/final_model/model.pt"
    duration = 30  # Run for 30 seconds
    
    print("="*70)
    print("FirstCrackDetector Microphone Test")
    print("="*70)
    print(f"Model: {checkpoint_path}")
    print(f"Test duration: {duration} seconds")
    print()
    
    # List available audio devices
    import sounddevice as sd
    print("Available audio devices:")
    print(sd.query_devices())
    print()
    
    # Initialize detector with microphone
    print("Initializing detector with USB microphone...")
    try:
        detector = FirstCrackDetector(
            use_microphone=True,
            checkpoint_path=checkpoint_path,
            threshold=0.5,
            min_pops=3,
            confirmation_window=30.0,
            window_size=10.0,
            overlap=0.5,
            sample_rate=16000
        )
        print("✓ Detector initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize detector: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Start detection
    print("\nStarting microphone detection...")
    print("-"*70)
    print("🎤 Listening... (speak or make sounds to test)")
    print("-"*70)
    
    try:
        detector.start()
        
        # Monitor for specified duration
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < duration:
            result = detector.is_first_crack()
            elapsed = detector.get_elapsed_time()
            
            if result is False:
                if last_status != "waiting":
                    print(f"[{elapsed}] 🔍 Monitoring audio stream...")
                    last_status = "waiting"
            else:
                detected, timestamp = result
                print(f"[{elapsed}] 🔥 FIRST CRACK DETECTED at {timestamp}!")
                last_status = "detected"
                # Continue monitoring after detection
            
            time.sleep(2)
        
        print("-"*70)
        
        # Final status
        elapsed = detector.get_elapsed_time()
        result = detector.is_first_crack()
        print(f"\nTest completed after {elapsed}")
        
        if result is False:
            print("❌ No first crack detected (expected - not roasting)")
        else:
            detected, timestamp = result
            print(f"✅ First crack detected at: {timestamp}")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n✗ Error during detection: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        print("\nStopping detector...")
        detector.stop()
        print("✓ Detector stopped")
    
    print("\n" + "="*70)
    print("Microphone test complete!")
    print("="*70)
    print("\nNote: Since you're not roasting, detection is not expected.")
    print("This test verifies that microphone streaming is working.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
