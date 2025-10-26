#!/usr/bin/env python3
"""
Generate spectrogram for a full raw audio file to show multiple first cracks.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import librosa
import librosa.display
import numpy as np
from pathlib import Path
import json


def generate_full_spectrogram(audio_path: Path, annotations_path: Path = None, 
                            output_path: Path = None, sample_rate: int = 16000):
    """Generate spectrogram for full audio file with optional annotations."""
    
    print(f"🎨 Generating full spectrogram for: {audio_path.name}")
    
    # Load audio
    audio, sr = librosa.load(audio_path, sr=sample_rate, mono=True)
    duration = len(audio) / sr
    print(f"   Duration: {duration:.1f} seconds")
    
    # Generate mel spectrogram
    mel_spec = librosa.feature.melspectrogram(
        y=audio,
        sr=sr,
        n_mels=128,
        fmax=8000,
        hop_length=512,  # More time resolution for long audio
        n_fft=2048
    )
    
    # Convert to dB scale
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    
    # Create figure
    plt.figure(figsize=(20, 10))
    
    # Plot spectrogram
    img = librosa.display.specshow(
        mel_spec_db,
        x_axis='time',
        y_axis='mel',
        sr=sr,
        fmax=8000,
        hop_length=512,
        cmap='viridis'
    )
    
    # Add annotations if available
    if annotations_path and annotations_path.exists():
        try:
            with open(annotations_path, 'r') as f:
                annotations = json.load(f)
            
            # Parse chunk annotations to find first crack regions
            chunks = annotations.get('annotations', [])
            first_crack_chunks = [chunk for chunk in chunks if chunk.get('label') == 'first_crack']
            print(f"   Found {len(first_crack_chunks)} first crack chunks")
            
            # Mark first crack regions
            for i, chunk in enumerate(first_crack_chunks[:15]):  # Limit to first 15
                start_time = chunk['start_time']
                end_time = chunk['end_time']
                
                # Draw vertical lines at start and end of first crack regions
                plt.axvspan(start_time, end_time, color='red', alpha=0.3, 
                           label='First Crack Region' if i == 0 else "")
                
                # Add time labels for first few regions
                if i < 8:  # Don't overcrowd with too many labels
                    mid_time = (start_time + end_time) / 2
                    plt.text(mid_time, plt.ylim()[1] * 0.95, 
                            f'{start_time:.0f}s', 
                            rotation=90, verticalalignment='top',
                            color='red', fontweight='bold', fontsize=8,
                            bbox=dict(boxstyle='round,pad=0.2', 
                                    facecolor='white', alpha=0.8))
            
            if first_crack_chunks:
                plt.legend(loc='upper right', fontsize=12)
                
        except Exception as e:
            print(f"   ⚠️ Could not load annotations: {e}")
    
    # Formatting
    plt.title(f"Full Roast Spectrogram: {audio_path.name}", 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Time (seconds)', fontsize=14)
    plt.ylabel('Frequency (Hz)', fontsize=14)
    
    # Add colorbar
    cbar = plt.colorbar(img, format='%+2.0f dB')
    cbar.set_label('Power (dB)', fontsize=12)
    
    # Add info box
    info_text = f'Duration: {duration:.1f}s\nSample Rate: {sr}Hz\nFreq Range: 0-8000Hz'
    plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes, 
             fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"   ✅ Saved: {output_path}")
    
    plt.close()
    return True


def main():
    """Generate spectrogram for a raw audio file."""
    
    # Look for a good candidate raw file
    raw_dir = Path("data/raw")
    labels_dir = Path("data/labels")
    output_dir = Path("spectrograms_samples")
    output_dir.mkdir(exist_ok=True)
    
    # Try to find roast files (likely to have multiple first cracks)
    raw_files = list(raw_dir.glob("*.wav"))
    roast_files = [f for f in raw_files if "roast" in f.name.lower()]
    
    if roast_files:
        # Prefer roast-1 file as it has good first crack annotations
        roast_1_files = [f for f in roast_files if "roast-1" in f.name]
        chosen_file = roast_1_files[0] if roast_1_files else roast_files[0]
    else:
        chosen_file = raw_files[0] if raw_files else None
    
    if not chosen_file:
        print("❌ No audio files found in data/raw/")
        return
    
    # Look for corresponding annotation file
    possible_annotations = [
        labels_dir / f"{chosen_file.stem}.json",
        labels_dir / f"{chosen_file.name}.json"
    ]
    
    annotation_file = None
    for ann_path in possible_annotations:
        if ann_path.exists():
            annotation_file = ann_path
            break
    
    print("🎨 Generating Full Audio Spectrogram")
    print("=" * 50)
    print(f"Audio file: {chosen_file.name}")
    if annotation_file:
        print(f"Annotations: {annotation_file.name}")
    else:
        print("Annotations: None found")
    
    output_file = output_dir / "3_full_audio_spectrogram.png"
    
    success = generate_full_spectrogram(
        chosen_file, 
        annotation_file, 
        output_file
    )
    
    if success:
        print(f"\n✅ Full spectrogram generated!")
        print(f"   Check: {output_file}")


if __name__ == '__main__':
    main()