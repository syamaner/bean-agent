#!/usr/bin/env python3
"""
Test the data loading pipeline with DataLoader.

Tests batching, shuffling, and ensures data can be loaded efficiently.
"""
from pathlib import Path

import torch
from audio_dataset import create_dataloaders


def test_dataloader():
    """Test dataloader functionality."""
    print("🧪 Testing Data Loading Pipeline")
    print("=" * 50)
    
    # Create dataloaders
    print("\n1. Creating dataloaders...")
    train_loader, val_loader, test_loader = create_dataloaders(
        train_dir=Path('data/splits/train'),
        val_dir=Path('data/splits/val'),
        test_dir=Path('data/splits/test'),
        batch_size=8,
        num_workers=0,
        sample_rate=16000,
        target_length=10
    )
    
    print(f"   ✅ Train loader: {len(train_loader)} batches")
    print(f"   ✅ Val loader: {len(val_loader)} batches")
    print(f"   ✅ Test loader: {len(test_loader)} batches")
    
    # Test train loader
    print("\n2. Testing train loader...")
    train_dataset = train_loader.dataset
    stats = train_dataset.get_statistics()
    print(f"   Total samples: {stats['total_samples']}")
    print(f"   No first crack: {stats['no_first_crack']}")
    print(f"   First crack: {stats['first_crack']}")
    print(f"   Sample rate: {stats['sample_rate']}Hz")
    print(f"   Target length: {stats['target_length_sec']}s")
    
    # Load first batch
    print("\n3. Loading first batch...")
    for batch_idx, (audio, labels) in enumerate(train_loader):
        print(f"   Batch {batch_idx}:")
        print(f"     Audio shape: {audio.shape}")
        print(f"     Labels shape: {labels.shape}")
        print(f"     Labels: {labels.tolist()}")
        print(f"     Audio dtype: {audio.dtype}")
        print(f"     Audio range: [{audio.min():.3f}, {audio.max():.3f}]")
        break
    
    # Test iteration through all data
    print("\n4. Testing full iteration...")
    total_samples = 0
    label_counts = {0: 0, 1: 0}
    
    for audio, labels in train_loader:
        total_samples += len(labels)
        for label in labels:
            label_counts[label.item()] += 1
    
    print(f"   ✅ Iterated through {total_samples} samples")
    print(f"   Label distribution:")
    print(f"     No first crack (0): {label_counts[0]}")
    print(f"     First crack (1): {label_counts[1]}")
    
    # Test validation loader
    print("\n5. Testing validation loader...")
    val_dataset = val_loader.dataset
    val_stats = val_dataset.get_statistics()
    print(f"   Total samples: {val_stats['total_samples']}")
    print(f"   No first crack: {val_stats['no_first_crack']}")
    print(f"   First crack: {val_stats['first_crack']}")
    
    # Test test loader
    print("\n6. Testing test loader...")
    test_dataset = test_loader.dataset
    test_stats = test_dataset.get_statistics()
    print(f"   Total samples: {test_stats['total_samples']}")
    print(f"   No first crack: {test_stats['no_first_crack']}")
    print(f"   First crack: {test_stats['first_crack']}")
    
    # Class weights for handling imbalance
    print("\n7. Class weights for training:")
    class_weights = train_dataset.get_class_weights()
    print(f"   No first crack: {class_weights[0]:.3f}")
    print(f"   First crack: {class_weights[1]:.3f}")
    print(f"   (Higher weight = more emphasis during training)")
    
    # Check device compatibility
    print("\n8. Checking device compatibility...")
    device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
    print(f"   Target device: {device}")
    
    # Move a batch to device
    for audio, labels in train_loader:
        audio_device = audio.to(device)
        labels_device = labels.to(device)
        print(f"   ✅ Successfully moved data to {device}")
        print(f"      Audio device: {audio_device.device}")
        print(f"      Labels device: {labels_device.device}")
        break
    
    print("\n✅ All tests passed!")
    print("\nData loading pipeline is ready for training.")


if __name__ == '__main__':
    test_dataloader()
