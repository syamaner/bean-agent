import librosa
import numpy as np
import os
from pathlib import Path

# Get project root directory (2 levels up from this script)
project_root = Path(__file__).parent.parent.parent
audio_path = project_root / "data" / "raw" / "roast-1-costarica-hermosa-hp-a.wav"
print(f"Loading: {audio_path}")

# Load audio at 44.1kHz sample rate, convert to mono
audio, sr = librosa.load(str(audio_path), sr=44100, mono=True)

print(f"\nAudio loaded successfully!")
print(f"Sample rate: {sr}Hz")
print(f"Audio shape: {audio.shape}")
print(f"Duration: {len(audio)/sr:.2f} seconds")
print(f"Data type: {audio.dtype}")
print(f"Min value: {audio.min():.4f}")
print(f"Max value: {audio.max():.4f}")
print(f"Mean value: {audio.mean():.4f}")
