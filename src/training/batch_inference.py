#!/usr/bin/env python3
"""
Batch inference on multiple audio files.

Processes all audio files in a directory and generates a summary report.
"""
import argparse
import sys
from pathlib import Path
import time
import json

import torch
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.ast_model import FirstCrackClassifier, ModelInitConfig
from inference import SlidingWindowInference, DetectionEvent


def process_directory(
    checkpoint_path: Path,
    audio_dir: Path,
    output_dir: Path,
    window_size: float = 10.0,
    overlap: float = 0.5,
    threshold: float = 0.5,
    min_duration: float = 2.0
):
    """Process all audio files in a directory."""
    
    # Load model
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    config = checkpoint['config']
    
    device = config.get('device', 'mps' if torch.backends.mps.is_available() else 'cpu')
    model_config = ModelInitConfig(device=device)
    model = FirstCrackClassifier(model_config)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    
    print(f"Model loaded on device: {device}")
    
    # Create inference engine
    inference = SlidingWindowInference(
        model=model,
        window_size=window_size,
        overlap=overlap,
        threshold=threshold,
        sample_rate=config['sample_rate']
    )
    
    # Find all audio files
    audio_files = sorted(audio_dir.glob('*.wav'))
    
    if not audio_files:
        print(f"❌ No .wav files found in {audio_dir}")
        return
    
    print(f"\n{'='*70}")
    print(f"Found {len(audio_files)} audio files to process")
    print(f"{'='*70}\n")
    
    # Process each file
    results = []
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}] Processing: {audio_file.name}")
        print("-"*70)
        
        start_time = time.time()
        events, predictions = inference.process_audio(audio_file, min_duration)
        processing_time = time.time() - start_time
        
        # Get audio duration
        audio, duration = inference.load_audio(audio_file)
        
        # Save individual results
        output_file = output_dir / f"{audio_file.stem}_results.txt"
        from inference import save_results
        save_results(output_file, audio_file, events, predictions, config['sample_rate'])
        
        # Collect summary
        results.append({
            'filename': audio_file.name,
            'duration': duration,
            'num_events': len(events),
            'events': [
                {
                    'start': e.start_time,
                    'end': e.end_time,
                    'duration': e.end_time - e.start_time,
                    'confidence': e.confidence
                }
                for e in events
            ],
            'processing_time': processing_time,
            'realtime_factor': duration / processing_time
        })
        
        print(f"\n✅ Detected {len(events)} events")
        print(f"⏱  Processing time: {processing_time:.2f}s "
              f"(RTF: {duration/processing_time:.2f}x)")
    
    # Generate summary report
    print(f"\n{'='*70}")
    print(f"BATCH PROCESSING SUMMARY")
    print(f"{'='*70}")
    
    total_duration = sum(r['duration'] for r in results)
    total_processing = sum(r['processing_time'] for r in results)
    total_events = sum(r['num_events'] for r in results)
    avg_rtf = np.mean([r['realtime_factor'] for r in results])
    
    print(f"\nFiles processed: {len(results)}")
    print(f"Total audio duration: {total_duration:.1f}s ({total_duration/60:.1f} min)")
    print(f"Total processing time: {total_processing:.1f}s ({total_processing/60:.1f} min)")
    print(f"Average RTF: {avg_rtf:.2f}x")
    print(f"Total events detected: {total_events}")
    
    print(f"\nPer-file results:")
    print(f"{'File':<40} {'Events':>8} {'Duration':>10} {'RTF':>8}")
    print("-"*70)
    for r in results:
        print(f"{r['filename']:<40} {r['num_events']:>8} "
              f"{r['duration']:>9.1f}s {r['realtime_factor']:>7.2f}x")
    
    # Save JSON summary
    summary_file = output_dir / "batch_summary.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'checkpoint': str(checkpoint_path),
            'parameters': {
                'window_size': window_size,
                'overlap': overlap,
                'threshold': threshold,
                'min_duration': min_duration
            },
            'summary': {
                'num_files': len(results),
                'total_audio_duration': total_duration,
                'total_processing_time': total_processing,
                'average_rtf': float(avg_rtf),
                'total_events': total_events
            },
            'files': results
        }, f, indent=2)
    
    print(f"\n✅ Summary saved to: {summary_file}")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Batch inference on multiple audio files"
    )
    parser.add_argument('--checkpoint', type=str, required=True,
                        help='Path to model checkpoint')
    parser.add_argument('--audio-dir', type=str, required=True,
                        help='Directory containing audio files')
    parser.add_argument('--output-dir', type=str, default='inference_results',
                        help='Output directory for results')
    parser.add_argument('--window-size', type=float, default=10.0,
                        help='Window size in seconds')
    parser.add_argument('--overlap', type=float, default=0.5,
                        help='Window overlap ratio 0-1')
    parser.add_argument('--threshold', type=float, default=0.5,
                        help='Detection threshold')
    parser.add_argument('--min-duration', type=float, default=2.0,
                        help='Minimum event duration in seconds')
    
    args = parser.parse_args()
    
    checkpoint_path = Path(args.checkpoint)
    audio_dir = Path(args.audio_dir)
    output_dir = Path(args.output_dir)
    
    if not checkpoint_path.exists():
        print(f"❌ Checkpoint not found: {checkpoint_path}")
        sys.exit(1)
    
    if not audio_dir.exists():
        print(f"❌ Audio directory not found: {audio_dir}")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    process_directory(
        checkpoint_path=checkpoint_path,
        audio_dir=audio_dir,
        output_dir=output_dir,
        window_size=args.window_size,
        overlap=args.overlap,
        threshold=args.threshold,
        min_duration=args.min_duration
    )


if __name__ == '__main__':
    main()
