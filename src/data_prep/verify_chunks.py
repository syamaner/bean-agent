#!/usr/bin/env python3
"""
Verify audio chunks quality by sampling and checking metadata.

Usage:
  python src/data_prep/verify_chunks.py --data data/processed
"""
import argparse
import random
from pathlib import Path

import librosa
import numpy as np


def verify_chunk(chunk_path: Path) -> dict:
    """Verify a single audio chunk."""
    try:
        audio, sr = librosa.load(chunk_path, sr=None, mono=True)
        duration = len(audio) / sr
        
        # Check for issues
        issues = []
        
        # Check duration (should be reasonable)
        if duration < 5:
            issues.append(f"Very short: {duration:.1f}s")
        if duration > 60:
            issues.append(f"Very long: {duration:.1f}s")
        
        # Check for silence
        rms = np.sqrt(np.mean(audio**2))
        if rms < 0.001:
            issues.append("Possibly silent")
        
        # Check for clipping
        if np.max(np.abs(audio)) > 0.99:
            issues.append("Possible clipping")
        
        return {
            'path': chunk_path,
            'duration': duration,
            'sample_rate': sr,
            'rms': rms,
            'issues': issues,
            'ok': len(issues) == 0
        }
    except Exception as e:
        return {
            'path': chunk_path,
            'ok': False,
            'issues': [f"Error loading: {e}"]
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, default=Path('data/processed'))
    parser.add_argument('--samples', type=int, default=10, 
                       help='Number of random samples per category')
    args = parser.parse_args()
    
    print("🔍 Audio Chunk Verification")
    print("=" * 50)
    
    # Get all chunks
    first_crack_chunks = list((args.data / 'first_crack').glob('*.wav'))
    no_first_crack_chunks = list((args.data / 'no_first_crack').glob('*.wav'))
    
    print(f"\nFound chunks:")
    print(f"  - first_crack: {len(first_crack_chunks)}")
    print(f"  - no_first_crack: {len(no_first_crack_chunks)}")
    
    # Sample random chunks
    fc_sample = random.sample(first_crack_chunks, min(args.samples, len(first_crack_chunks)))
    nfc_sample = random.sample(no_first_crack_chunks, min(args.samples, len(no_first_crack_chunks)))
    
    print(f"\nVerifying {len(fc_sample)} first_crack samples...")
    fc_results = [verify_chunk(p) for p in fc_sample]
    
    print(f"Verifying {len(nfc_sample)} no_first_crack samples...")
    nfc_results = [verify_chunk(p) for p in nfc_sample]
    
    # Report
    all_results = fc_results + nfc_results
    ok_count = sum(1 for r in all_results if r['ok'])
    issue_count = len(all_results) - ok_count
    
    print(f"\n📊 Results:")
    print(f"  ✅ OK: {ok_count}/{len(all_results)}")
    print(f"  ⚠️  Issues: {issue_count}/{len(all_results)}")
    
    # Show issues
    if issue_count > 0:
        print(f"\n⚠️  Chunks with issues:")
        for r in all_results:
            if not r['ok']:
                print(f"  - {r['path'].name}")
                for issue in r['issues']:
                    print(f"      {issue}")
    
    # Stats
    durations = [r['duration'] for r in all_results if 'duration' in r]
    if durations:
        print(f"\n📈 Duration statistics:")
        print(f"  Mean: {np.mean(durations):.1f}s")
        print(f"  Min: {min(durations):.1f}s")
        print(f"  Max: {max(durations):.1f}s")
    
    # Manual verification suggestion
    print(f"\n💡 Manual verification:")
    print(f"   Listen to a few chunks:")
    print(f"   - First crack: {fc_sample[0].name if fc_sample else 'N/A'}")
    print(f"   - No first crack: {nfc_sample[0].name if nfc_sample else 'N/A'}")
    print(f"\n   To play in terminal (if you have sox/play):")
    print(f"   play data/processed/first_crack/{fc_sample[0].name if fc_sample else 'FILE.wav'}")
    
    success_rate = (ok_count / len(all_results)) * 100 if all_results else 0
    print(f"\n{'✅' if success_rate > 95 else '⚠️'} Success rate: {success_rate:.1f}%")
    
    if success_rate > 95:
        print("   Chunks look good! Ready for training.")
    else:
        print("   Review issues before proceeding.")


if __name__ == '__main__':
    main()
