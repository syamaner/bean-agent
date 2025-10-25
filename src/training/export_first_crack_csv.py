#!/usr/bin/env python3
"""
Export first crack detection timestamps to CSV format.

Processes audio files and outputs first crack events in CSV format:
filename,timestamp
"""
import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Optional

import torch

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.ast_model import FirstCrackClassifier, ModelInitConfig
from training.inference import SlidingWindowInference


def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def get_actual_first_crack_time(audio_filename: str, annotations_dir: Path) -> Optional[str]:
    """
    Get actual first crack timestamp from annotation JSON file.
    
    Args:
        audio_filename: Name of the audio file (e.g., 'roast-1.wav')
        annotations_dir: Directory containing annotation JSON files
    
    Returns:
        Formatted timestamp (MM:SS) or None if not found
    """
    # Construct annotation filename (stem + .json)
    audio_stem = Path(audio_filename).stem
    annotation_path = annotations_dir / f"{audio_stem}.json"
    
    if not annotation_path.exists():
        return None
    
    try:
        with open(annotation_path, 'r') as f:
            data = json.load(f)
        
        # Find first annotation with label "first_crack"
        first_crack_annotations = [
            ann for ann in data.get('annotations', [])
            if ann.get('label') == 'first_crack'
        ]
        
        if not first_crack_annotations:
            return None
        
        # Get the earliest start_time
        earliest_time = min(ann['start_time'] for ann in first_crack_annotations)
        return format_timestamp(earliest_time)
    
    except Exception as e:
        print(f"  ⚠️  Error reading annotation for {audio_filename}: {e}")
        return None


def process_files_to_csv(
    checkpoint_path: Path,
    audio_dir: Path,
    output_csv: Path,
    annotations_dir: Optional[Path] = None,
    window_size: float = 10.0,
    overlap: float = 0.7,
    threshold: float = 0.5,
    min_duration: float = 2.0,
    min_pops: int = 3,
    confirmation_window: float = 30.0,
    min_gap: float = 10.0
):
    """
    Process audio files and export first crack timestamps to CSV.
    
    Args:
        checkpoint_path: Path to model checkpoint
        audio_dir: Directory containing audio files
        output_csv: Path to output CSV file
        window_size: Window size in seconds
        overlap: Window overlap ratio
        threshold: Detection threshold
        min_duration: Minimum event duration
    """
    
    # Load model
    print("Loading model...")
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    config = checkpoint['config']
    
    device = config.get('device', 'mps' if torch.backends.mps.is_available() else 'cpu')
    model_config = ModelInitConfig(device=device)
    model = FirstCrackClassifier(model_config)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    
    print(f"Model loaded on device: {device}\n")
    
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
    
    print(f"Found {len(audio_files)} audio files to process\n")
    
    # Collect all first crack events
    all_events = []
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"[{i}/{len(audio_files)}] Processing: {audio_file.name}")
        
        # Get actual first crack time from annotations if available
        actual_fc_time = None
        if annotations_dir:
            actual_fc_time = get_actual_first_crack_time(audio_file.name, annotations_dir)
            if actual_fc_time:
                print(f"  Actual first crack (from annotations): {actual_fc_time}")
        
        # Process audio
        events, predictions = inference.process_audio(
            audio_file,
            min_event_duration=min_duration,
            min_pops=min_pops,
            confirmation_window=confirmation_window,
            min_gap=min_gap
        )
        
        # Add events to list (only use first detected event for comparison)
        if events:
            event = events[0]  # Take the first detected event
            all_events.append({
                'filename': audio_file.name,
                'predicted_timestamp': format_timestamp(event.start_time),
                'actual_timestamp': actual_fc_time if actual_fc_time else 'N/A',
                'confidence': event.confidence
            })
            print(f"  Predicted first crack: {format_timestamp(event.start_time)} "
                  f"(confidence: {event.confidence:.3f})")
        else:
            # No detection - still add row with actual time if available
            all_events.append({
                'filename': audio_file.name,
                'predicted_timestamp': 'N/A',
                'actual_timestamp': actual_fc_time if actual_fc_time else 'N/A',
                'confidence': 0.0
            })
            print(f"  No first crack events detected")
        
        print()
    
    # Write to CSV
    print(f"Writing results to {output_csv}...")
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'predicted_fc', 'actual_fc', 'confidence'])
        
        for event in all_events:
            writer.writerow([
                event['filename'],
                event['predicted_timestamp'],
                event['actual_timestamp'],
                f"{event['confidence']:.3f}"
            ])
    
    print(f"✅ CSV file created: {output_csv}")
    print(f"\nTotal files processed: {len(all_events)}")
    
    # Print summary
    print("\n" + "="*80)
    print("FIRST CRACK DETECTION SUMMARY")
    print("="*80)
    print(f"{'Filename':<40} {'Predicted':<12} {'Actual':<12} {'Conf':<8}")
    print("-"*80)
    for event in all_events:
        print(f"{event['filename']:<40} "
              f"{event['predicted_timestamp']:<12} "
              f"{event['actual_timestamp']:<12} "
              f"{event['confidence']:.3f}")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Export first crack detection timestamps to CSV"
    )
    parser.add_argument('--checkpoint', type=str, required=True,
                        help='Path to model checkpoint')
    parser.add_argument('--audio-dir', type=str, required=True,
                        help='Directory containing audio files')
    parser.add_argument('--annotations-dir', type=str, default='data/labels',
                        help='Directory containing annotation JSON files (default: data/labels)')
    parser.add_argument('--output', type=str, default='first_crack_detections.csv',
                        help='Output CSV file path')
    parser.add_argument('--window-size', type=float, default=10.0,
                        help='Window size in seconds')
    parser.add_argument('--overlap', type=float, default=0.7,
                        help='Window overlap ratio 0-1')
    parser.add_argument('--threshold', type=float, default=0.5,
                        help='Detection threshold')
    parser.add_argument('--min-duration', type=float, default=2.0,
                        help='Minimum event duration in seconds')
    parser.add_argument('--min-pops', type=int, default=3,
                        help='Minimum positive windows to confirm first crack')
    parser.add_argument('--confirmation-window', type=float, default=30.0,
                        help='Time window for counting pops (seconds)')
    parser.add_argument('--min-gap', type=float, default=10.0,
                        help='Merge events separated by gaps shorter than this')
    
    args = parser.parse_args()
    
    checkpoint_path = Path(args.checkpoint)
    audio_dir = Path(args.audio_dir)
    annotations_dir = Path(args.annotations_dir) if args.annotations_dir else None
    output_csv = Path(args.output)
    
    if not checkpoint_path.exists():
        print(f"❌ Checkpoint not found: {checkpoint_path}")
        sys.exit(1)
    
    if not audio_dir.exists():
        print(f"❌ Audio directory not found: {audio_dir}")
        sys.exit(1)
    
    process_files_to_csv(
        checkpoint_path=checkpoint_path,
        audio_dir=audio_dir,
        output_csv=output_csv,
        annotations_dir=annotations_dir,
        window_size=args.window_size,
        overlap=args.overlap,
        threshold=args.threshold,
        min_duration=args.min_duration,
        min_pops=args.min_pops,
        confirmation_window=args.confirmation_window,
        min_gap=args.min_gap
    )


if __name__ == '__main__':
    main()
