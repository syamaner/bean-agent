"""
Audio data augmentation utilities.

Applies simple waveform-level augmentations compatible with AST feature extraction.
"""
from __future__ import annotations

import numpy as np
import torch
import librosa


def time_stretch(audio: torch.Tensor, rate: float) -> torch.Tensor:
    """Time-stretch waveform using librosa (expects 1D tensor)."""
    y = audio.detach().cpu().numpy()
    y_out = librosa.effects.time_stretch(y, rate=rate)
    return torch.from_numpy(y_out).float()


def pitch_shift(audio: torch.Tensor, sr: int, n_steps: float) -> torch.Tensor:
    """Pitch-shift waveform by n_steps semitones using librosa."""
    y = audio.detach().cpu().numpy()
    y_out = librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)
    return torch.from_numpy(y_out).float()


def add_background_noise(audio: torch.Tensor, snr_db: float = 20.0) -> torch.Tensor:
    """Add Gaussian noise at a given SNR (in dB)."""
    y = audio.detach().cpu().numpy()
    rms_signal = np.sqrt(np.mean(y**2) + 1e-8)
    rms_noise = rms_signal / (10 ** (snr_db / 20.0))
    noise = np.random.normal(0, rms_noise, size=y.shape)
    y_out = y + noise
    return torch.from_numpy(y_out).float()


def volume_gain(audio: torch.Tensor, gain_db: float) -> torch.Tensor:
    """Apply volume gain in dB."""
    factor = 10 ** (gain_db / 20.0)
    return (audio * factor).float()


class RandomAugment:
    """Compose random augmentations with given probabilities."""

    def __init__(
        self,
        sample_rate: int = 16000,
        p_time_stretch: float = 0.3,
        p_pitch_shift: float = 0.3,
        p_noise: float = 0.3,
        p_volume: float = 0.3,
    ):
        self.sr = sample_rate
        self.p_time_stretch = p_time_stretch
        self.p_pitch_shift = p_pitch_shift
        self.p_noise = p_noise
        self.p_volume = p_volume

    def __call__(self, audio: torch.Tensor) -> torch.Tensor:
        y = audio
        # Time stretch
        if torch.rand(1).item() < self.p_time_stretch:
            rate = float(torch.empty(1).uniform_(0.9, 1.1).item())
            y = time_stretch(y, rate)
        # Pitch shift
        if torch.rand(1).item() < self.p_pitch_shift:
            n_steps = float(torch.empty(1).uniform_(-2.0, 2.0).item())
            y = pitch_shift(y, self.sr, n_steps)
        # Background noise
        if torch.rand(1).item() < self.p_noise:
            snr = float(torch.empty(1).uniform_(10.0, 30.0).item())
            y = add_background_noise(y, snr_db=snr)
        # Volume
        if torch.rand(1).item() < self.p_volume:
            gain = float(torch.empty(1).uniform_(-6.0, 6.0).item())
            y = volume_gain(y, gain)
        return y
