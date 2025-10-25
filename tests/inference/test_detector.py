#!/usr/bin/env python3
"""
Test script for FirstCrackDetector with audio file.
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
    audio_file = "data/raw/roast-1-costarica-hermosa-hp-a.wav"
    checkpoint_path = "experiments/final_model/model.pt"
    
    print("="*70)
    print("FirstCrackDetector Test")
    print("="*70)
    print(f"Audio file: {audio_file}")
    print(f"Model: {checkpoint_path}")
    print()
    
    # Initialize detector
    print("Initializing detector...")
    try:
        detector = FirstCrackDetector(
            audio_file=audio_file,
            checkpoint_path=checkpoint_path,
            threshold=0.5,
            min_pops=3,
            confirmation_window=30.0,
            window_size=10.0,
            overlap=0.5
        )
        print("✓ Detector initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize detector: {e}")
        return 1
    
    # Start detection
    print("\nStarting detection...")
    print("-"*70)
    try:
        detector.start()
        
        # Monitor for first crack
        last_status = None
        while detector.is_running:
            result = detector.is_first_crack()
            elapsed = detector.get_elapsed_time()
            
            if result is False:
                if last_status != "waiting":
                    print(f"[{elapsed}] Waiting for first crack...")
                    last_status = "waiting"
            else:
                detected, timestamp = result
                print(f"[{elapsed}] 🔥 FIRST CRACK DETECTED at {timestamp}!")
                last_status = "detected"
                # Continue monitoring for a bit after detection
                time.sleep(3)
                break
            
            time.sleep(2)
        
        print("-"*70)
        
        # Final status
        result = detector.is_first_crack()
        if result is False:
            print("\n❌ No first crack detected")
        else:
            detected, timestamp = result
            print(f"\n✅ First crack detected at: {timestamp}")
        
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
    print("Test complete!")
    print("="*70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
