#!/usr/bin/env python3
"""
Process audio annotations into labeled chunks.

Reads annotation JSON files and extracts audio segments,
saving them to first_crack/ or no_first_crack/ directories.

Usage:
  python src/data_prep/audio_processor.py \
    --annotations data/labels \
    --audio-dir data/raw \
    --output data/processed
"""
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import librosa
import soundfile as sf
import numpy as np


def load_audio(path: Path, sr: int = 44100) -> Tuple[np.ndarray, int]:
    """Load audio file and convert to mono if needed."""
    audio, sample_rate = librosa.load(path, sr=sr, mono=True)
    return audio, sample_rate


def extract_chunk(
    audio: np.ndarray,
    start_time: float,
    end_time: float,
    sr: int
) -> np.ndarray:
    """Extract a time segment from audio array."""
    start_sample = int(start_time * sr)
    end_sample = int(end_time * sr)
    return audio[start_sample:end_sample]


def save_chunk(audio: np.ndarray, path: Path, sr: int):
    """Save audio chunk to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, audio, sr)


def process_annotation_file(
    annotation_path: Path,
    audio_dir: Path,
    output_dir: Path,
    sr: int = 44100
) -> Dict[str, int]:
    """
    Process a single annotation file.
    
    Returns:
        Dictionary with counts per label
    """
    # Load annotation
    with annotation_path.open('r') as f:
        annotation = json.load(f)
    
    audio_file = annotation['audio_file']
    audio_path = audio_dir / audio_file
    
    if not audio_path.exists():
        print(f"⚠️  Audio file not found: {audio_path}")
        return {}
    
    print(f"\n📁 Processing: {audio_file}")
    
    # Load audio
    audio, sample_rate = load_audio(audio_path, sr=sr)
    print(f"   Duration: {len(audio)/sample_rate:.1f}s, Sample rate: {sample_rate}Hz")
    
    # Process each annotation
    counts = {'first_crack': 0, 'no_first_crack': 0}
    stem = Path(audio_file).stem
    
    for ann in annotation['annotations']:
        label = ann['label']
        start_time = ann['start_time']
        end_time = ann['end_time']
        chunk_id = ann['id']
        
        # Extract chunk
        chunk = extract_chunk(audio, start_time, end_time, sample_rate)
        
        # Determine output path
        output_subdir = output_dir / label
        chunk_filename = f"{stem}_{chunk_id}.wav"
        output_path = output_subdir / chunk_filename
        
        # Save chunk
        save_chunk(chunk, output_path, sample_rate)
        counts[label] += 1
    
    print(f"   ✅ Extracted {len(annotation['annotations'])} chunks")
    print(f"      - first_crack: {counts['first_crack']}")
    print(f"      - no_first_crack: {counts['no_first_crack']}")
    
    return counts


def generate_summary_report(
    output_dir: Path,
    all_counts: List[Dict[str, int]],
    annotation_files: List[Path]
):
    """Generate and save summary report."""
    total_first_crack = sum(c.get('first_crack', 0) for c in all_counts)
    total_no_first_crack = sum(c.get('no_first_crack', 0) for c in all_counts)
    total_chunks = total_first_crack + total_no_first_crack
    
    # Calculate statistics for each label
    stats = {}
    for label in ['first_crack', 'no_first_crack']:
        label_dir = output_dir / label
        if label_dir.exists():
            chunks = list(label_dir.glob('*.wav'))
            if chunks:
                durations = []
                for chunk_path in chunks:
                    audio, sr = librosa.load(chunk_path, sr=None, mono=True)
                    durations.append(len(audio) / sr)
                
                stats[label] = {
                    'count': len(chunks),
                    'total_duration': sum(durations),
                    'mean_duration': np.mean(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                }
    
    # Create report
    report_lines = [
        "# Audio Processing Summary",
        "",
        f"**Generated**: {Path(__file__).name}",
        "",
        "## Overview",
        "",
        f"- **Total files processed**: {len(annotation_files)}",
        f"- **Total chunks created**: {total_chunks}",
        f"  - first_crack: {total_first_crack}",
        f"  - no_first_crack: {total_no_first_crack}",
        "",
        "## Chunk Statistics",
        "",
    ]
    
    for label, label_stats in stats.items():
        report_lines.extend([
            f"### {label}",
            "",
            f"- Count: {label_stats['count']}",
            f"- Total duration: {label_stats['total_duration']:.1f}s ({label_stats['total_duration']/60:.1f} min)",
            f"- Mean duration: {label_stats['mean_duration']:.1f}s",
            f"- Min duration: {label_stats['min_duration']:.1f}s",
            f"- Max duration: {label_stats['max_duration']:.1f}s",
            "",
        ])
    
    # Calculate balance
    if total_chunks > 0:
        fc_ratio = (total_first_crack / total_chunks) * 100
        nfc_ratio = (total_no_first_crack / total_chunks) * 100
        report_lines.extend([
            "## Class Balance",
            "",
            f"- first_crack: {fc_ratio:.1f}%",
            f"- no_first_crack: {nfc_ratio:.1f}%",
            "",
        ])
    
    # Per-file breakdown
    report_lines.extend([
        "## Per-File Breakdown",
        "",
        "| File | First Crack | No First Crack | Total |",
        "|------|-------------|----------------|-------|",
    ])
    
    for ann_file, counts in zip(annotation_files, all_counts):
        fc = counts.get('first_crack', 0)
        nfc = counts.get('no_first_crack', 0)
        total = fc + nfc
        report_lines.append(f"| {ann_file.stem} | {fc} | {nfc} | {total} |")
    
    # Save report
    report_path = output_dir / 'processing_summary.md'
    report_path.write_text('\n'.join(report_lines))
    print(f"\n📊 Summary report saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Process audio annotations into labeled chunks'
    )
    parser.add_argument(
        '--annotations',
        type=Path,
        default=Path('data/labels'),
        help='Directory containing annotation JSON files'
    )
    parser.add_argument(
        '--audio-dir',
        type=Path,
        default=Path('data/raw'),
        help='Directory containing audio WAV files'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/processed'),
        help='Output directory for processed chunks'
    )
    parser.add_argument(
        '--sample-rate',
        type=int,
        default=44100,
        help='Sample rate for output audio (default: 44100)'
    )
    args = parser.parse_args()
    
    # Find annotation files
    # Include all converted per-file annotation JSONs, excluding Label Studio exports/backups
    candidates = sorted(args.annotations.glob('*.json'))
    annotation_files = [p for p in candidates if not (p.name.startswith('project-') or p.name.startswith('labelstudio-export-'))]
    
    if not annotation_files:
        print(f"❌ No annotation files found in {args.annotations}")
        print(f"   Hint: run convert_labelstudio_export.py to generate per-file annotations")
        return
    
    print(f"🎵 Audio Chunk Processor")
    print(f"=" * 50)
    print(f"Annotation files: {len(annotation_files)}")
    print(f"Audio directory: {args.audio_dir}")
    print(f"Output directory: {args.output}")
    print(f"Sample rate: {args.sample_rate}Hz")
    
    # Process each annotation file
    all_counts = []
    for ann_file in annotation_files:
        counts = process_annotation_file(
            ann_file,
            args.audio_dir,
            args.output,
            sr=args.sample_rate
        )
        all_counts.append(counts)
    
    # Generate summary
    generate_summary_report(args.output, all_counts, annotation_files)
    
    print(f"\n✅ Processing complete!")
    print(f"   Output: {args.output}")
    print(f"   - {args.output}/first_crack/")
    print(f"   - {args.output}/no_first_crack/")


if __name__ == '__main__':
    main()
