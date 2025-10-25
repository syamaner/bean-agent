"""
PyTorch Dataset for first crack detection using Audio Spectrogram Transformer.

This dataset loads audio chunks and converts them to spectrograms for model input.
"""
from pathlib import Path
from typing import Tuple, Optional, Dict

import torch
from torch.utils.data import Dataset
import librosa
import numpy as np


class FirstCrackDataset(Dataset):
    """
    Dataset for first crack detection.
    
    Loads audio chunks and converts to spectrograms for AST model input.
    """
    
    # Label mapping
    LABEL_TO_IDX = {
        'no_first_crack': 0,
        'first_crack': 1
    }
    IDX_TO_LABEL = {v: k for k, v in LABEL_TO_IDX.items()}
    
    def __init__(
        self,
        data_dir: Path,
        sample_rate: int = 16000,  # AST typically uses 16kHz
        target_length: int = 10,    # seconds
        transform: Optional[callable] = None,
        crop_mode: str = "start"
    ):
        """
        Initialize dataset.
        
        Args:
            data_dir: Directory containing label subdirectories (first_crack/, no_first_crack/)
            sample_rate: Target sample rate for audio (AST uses 16kHz)
            target_length: Target length in seconds (will pad/truncate)
            transform: Optional transform to apply to spectrograms
            crop_mode: How to crop when audio > target length. One of:
                - 'start': take first target window (backwards compatible default)
                - 'center': centered crop
                - 'random': random crop
        """
        self.data_dir = Path(data_dir)
        self.sample_rate = sample_rate
        self.target_length = target_length
        self.target_samples = int(sample_rate * target_length)
        self.transform = transform
        self.crop_mode = crop_mode
        
        # Collect all audio files with labels
        self.samples = []
        for label_name, label_idx in self.LABEL_TO_IDX.items():
            label_dir = self.data_dir / label_name
            if label_dir.exists():
                for audio_file in sorted(label_dir.glob('*.wav')):
                    self.samples.append((audio_file, label_idx))
        
        if len(self.samples) == 0:
            raise ValueError(f"No audio files found in {data_dir}")
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """
        Load and process a single sample.
        
        Returns:
            (audio_tensor, label)
        """
        audio_path, label = self.samples[idx]
        
        # Load audio
        audio, sr = librosa.load(audio_path, sr=self.sample_rate, mono=True)
        
        # Pad or crop to target length
        audio = self._pad_or_crop(audio)
        
        # Convert to tensor
        audio_tensor = torch.FloatTensor(audio)
        
        # Apply transform if specified
        if self.transform:
            audio_tensor = self.transform(audio_tensor)
        
        return audio_tensor, label
    
    def _pad_or_crop(self, audio: np.ndarray) -> np.ndarray:
        """Pad or crop audio to target length using selected crop_mode."""
        n = len(audio)
        t = self.target_samples
        if n < t:
            # Pad with zeros at the end
            pad_length = t - n
            return np.pad(audio, (0, pad_length), mode='constant')
        if n == t:
            return audio
        # n > t: crop depending on mode
        if self.crop_mode == 'start':
            start = 0
        elif self.crop_mode == 'center':
            start = max(0, (n - t) // 2)
        elif self.crop_mode == 'random':
            # Use numpy RNG for speed; fallback bounds safe
            max_start = max(0, n - t)
            start = int(np.random.randint(0, max_start + 1)) if max_start > 0 else 0
        else:
            # Fallback to start for unknown modes
            start = 0
        end = start + t
        return audio[start:end]
    
    def get_label_name(self, label_idx: int) -> str:
        """Convert label index to name."""
        return self.IDX_TO_LABEL[label_idx]
    
    def get_class_weights(self) -> torch.Tensor:
        """
        Calculate class weights for handling imbalance.
        
        Returns inverse frequency weights.
        """
        label_counts = {0: 0, 1: 0}
        for _, label in self.samples:
            label_counts[label] += 1
        
        total = len(self.samples)
        weights = torch.FloatTensor([
            total / (len(label_counts) * label_counts[0]),
            total / (len(label_counts) * label_counts[1])
        ])
        return weights
    
    def get_statistics(self) -> Dict:
        """Get dataset statistics."""
        label_counts = {0: 0, 1: 0}
        for _, label in self.samples:
            label_counts[label] += 1
        
        return {
            'total_samples': len(self.samples),
            'no_first_crack': label_counts[0],
            'first_crack': label_counts[1],
            'class_ratio': label_counts[1] / label_counts[0] if label_counts[0] > 0 else 0,
            'sample_rate': self.sample_rate,
            'target_length_sec': self.target_length,
            'target_samples': self.target_samples
        }


def create_dataloaders(
    train_dir: Path,
    val_dir: Path,
    test_dir: Optional[Path] = None,
    batch_size: int = 8,
    num_workers: int = 0,
    sample_rate: int = 16000,
    target_length: int = 10,
    train_crop_mode: str = "random",
    eval_crop_mode: str = "center"
) -> Tuple:
    """
    Create train, validation, and optionally test dataloaders.
    
    Args:
        train_dir: Path to training data
        val_dir: Path to validation data
        test_dir: Optional path to test data
        batch_size: Batch size
        num_workers: Number of worker processes for data loading
        sample_rate: Target sample rate
        target_length: Target audio length in seconds
    
    Returns:
        (train_loader, val_loader) or (train_loader, val_loader, test_loader)
    """
    from torch.utils.data import DataLoader
    
    # Create datasets
    train_dataset = FirstCrackDataset(
        train_dir,
        sample_rate,
        target_length,
        transform=None,
        crop_mode=train_crop_mode
    )
    val_dataset = FirstCrackDataset(
        val_dir,
        sample_rate,
        target_length,
        transform=None,
        crop_mode=eval_crop_mode
    )
    
    # Create dataloaders (pin_memory=False for MPS compatibility)
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=False
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=False
    )
    
    if test_dir:
        test_dataset = FirstCrackDataset(
            test_dir,
            sample_rate,
            target_length,
            transform=None,
            crop_mode=eval_crop_mode
        )
        test_loader = DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=False
        )
        return train_loader, val_loader, test_loader
    
    return train_loader, val_loader


if __name__ == '__main__':
    # Simple test
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python audio_dataset.py <data_dir>")
        sys.exit(1)
    
    data_dir = Path(sys.argv[1])
    
    print(f"Loading dataset from: {data_dir}")
    dataset = FirstCrackDataset(data_dir)
    
    print(f"\nDataset Statistics:")
    stats = dataset.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\nClass Weights:")
    weights = dataset.get_class_weights()
    print(f"  no_first_crack: {weights[0]:.3f}")
    print(f"  first_crack: {weights[1]:.3f}")
    
    print(f"\nSample:")
    audio, label = dataset[0]
    print(f"  Audio shape: {audio.shape}")
    print(f"  Label: {label} ({dataset.get_label_name(label)})")
