#!/usr/bin/env python3
"""
Visualize spectrograms from audio samples to verify preprocessing.

Generates spectrograms for both first_crack and no_first_crack samples
to visually inspect differences.
"""
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import librosa
import librosa.display
import numpy as np
from pathlib import Path
import random


def generate_spectrogram(audio_path: Path, sample_rate: int = 16000):
    """Generate mel spectrogram from audio file."""
    # Load audio
    audio, sr = librosa.load(audio_path, sr=sample_rate, mono=True)
    
    # Generate mel spectrogram
    mel_spec = librosa.feature.melspectrogram(
        y=audio,
        sr=sr,
        n_mels=128,
        fmax=8000
    )
    
    # Convert to dB scale
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    
    return mel_spec_db, sr


def visualize_samples(data_dir: Path, output_dir: Path, samples_per_class: int = 3):
    """
    Visualize spectrograms from random samples of each class.
    
    Args:
        data_dir: Directory containing first_crack/ and no_first_crack/ subdirs
        output_dir: Where to save visualization images
        samples_per_class: Number of samples to visualize per class
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🎨 Spectrogram Visualization")
    print("=" * 50)
    
    # Collect files by label
    labels = ['no_first_crack', 'first_crack']
    files_by_label = {}
    
    for label in labels:
        label_dir = data_dir / label
        if label_dir.exists():
            files = list(label_dir.glob('*.wav'))
            files_by_label[label] = random.sample(files, min(samples_per_class, len(files)))
            print(f"Found {len(files)} files for {label}")
    
    # Generate spectrograms
    print(f"\nGenerating spectrograms...")
    
    for label in labels:
        if label not in files_by_label:
            continue
        
        files = files_by_label[label]
        n_samples = len(files)
        
        # Create figure with subplots
        fig, axes = plt.subplots(n_samples, 1, figsize=(12, 4 * n_samples))
        if n_samples == 1:
            axes = [axes]
        
        for idx, audio_file in enumerate(files):
            print(f"  Processing: {audio_file.name}")
            
            # Generate spectrogram
            mel_spec_db, sr = generate_spectrogram(audio_file)
            
            # Plot
            ax = axes[idx]
            img = librosa.display.specshow(
                mel_spec_db,
                x_axis='time',
                y_axis='mel',
                sr=sr,
                fmax=8000,
                ax=ax,
                cmap='viridis'
            )
            
            ax.set_title(f"{label}: {audio_file.name}", fontsize=10)
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Frequency (Hz)')
            
            # Add colorbar
            plt.colorbar(img, ax=ax, format='%+2.0f dB')
        
        plt.tight_layout()
        
        # Save figure
        output_file = output_dir / f'spectrograms_{label}.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"  ✅ Saved: {output_file}")
        plt.close()
    
    # Create comparison figure (one sample from each class)
    print(f"\nCreating comparison figure...")
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    for idx, label in enumerate(labels):
        if label not in files_by_label or not files_by_label[label]:
            continue
        
        audio_file = files_by_label[label][0]
        mel_spec_db, sr = generate_spectrogram(audio_file)
        
        ax = axes[idx]
        img = librosa.display.specshow(
            mel_spec_db,
            x_axis='time',
            y_axis='mel',
            sr=sr,
            fmax=8000,
            ax=ax,
            cmap='viridis'
        )
        
        ax.set_title(f"{label.replace('_', ' ').title()}", fontsize=14, fontweight='bold')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Frequency (Hz)')
        plt.colorbar(img, ax=ax, format='%+2.0f dB')
    
    plt.suptitle('Spectrogram Comparison: First Crack vs No First Crack', 
                 fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    comparison_file = output_dir / 'spectrogram_comparison.png'
    plt.savefig(comparison_file, dpi=150, bbox_inches='tight')
    print(f"  ✅ Saved: {comparison_file}")
    plt.close()
    
    print(f"\n✅ Visualization complete!")
    print(f"   Output directory: {output_dir}")
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"   - Generated spectrograms use mel scale (128 bins)")
    print(f"   - Frequency range: 0-8000 Hz")
    print(f"   - Sample rate: 16000 Hz")
    print(f"   - Color scale: dB (louder = brighter)")
    print(f"\n💡 Look for:")
    print(f"   - First crack: Sharp vertical lines/bursts in spectrogram")
    print(f"   - No first crack: Smoother, more continuous patterns")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--data',
        type=Path,
        default=Path('data/splits/train'),
        help='Directory containing audio data'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/spectrograms'),
        help='Output directory for visualizations'
    )
    parser.add_argument(
        '--samples',
        type=int,
        default=3,
        help='Number of samples per class to visualize'
    )
    args = parser.parse_args()
    
    visualize_samples(args.data, args.output, args.samples)
