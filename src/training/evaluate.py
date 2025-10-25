#!/usr/bin/env python3
"""
Evaluation script for trained model on test set.
"""
import argparse
import sys
from pathlib import Path

import torch
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_prep.audio_dataset import FirstCrackDataset
from torch.utils.data import DataLoader
from models.ast_model import FirstCrackClassifier, ModelInitConfig
from utils.metrics import MetricsCalculator


def evaluate_model(model, test_loader, device):
    """Evaluate model on test set."""
    model.eval()
    metrics = MetricsCalculator()
    
    print("\nEvaluating model on test set...")
    with torch.inference_mode():
        for audio, labels in tqdm(test_loader, desc="Testing"):
            audio = audio.to(device)
            labels = labels.to(device)
            
            # Forward pass
            logits = model(audio)
            probs = torch.softmax(logits, dim=-1)
            preds = torch.argmax(probs, dim=-1)
            
            metrics.update(preds, labels, probs)
    
    return metrics


def plot_confusion_matrix(cm, output_path):
    """Plot and save confusion matrix."""
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm, 
        annot=True, 
        fmt='d', 
        cmap='Blues',
        xticklabels=['no_first_crack', 'first_crack'],
        yticklabels=['no_first_crack', 'first_crack']
    )
    plt.title('Confusion Matrix - Test Set')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Saved confusion matrix to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate model on test set")
    parser.add_argument('--checkpoint', type=str, required=True,
                        help='Path to model checkpoint')
    parser.add_argument('--test-dir', type=str, default='data/splits/test',
                        help='Path to test data')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory for results (default: checkpoint dir)')
    parser.add_argument('--batch-size', type=int, default=8,
                        help='Batch size')
    
    args = parser.parse_args()
    
    # Load checkpoint
    checkpoint_path = Path(args.checkpoint)
    if not checkpoint_path.exists():
        print(f"❌ Checkpoint not found: {checkpoint_path}")
        sys.exit(1)
    
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    config = checkpoint['config']
    
    print(f"Loading checkpoint from: {checkpoint_path}")
    print(f"Checkpoint from epoch: {checkpoint['epoch']}")
    print(f"Best val F1: {checkpoint.get('best_val_f1', 'N/A'):.4f}")
    
    # Setup output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = checkpoint_path.parent.parent / "evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load test data
    test_dir = Path(args.test_dir)
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        sys.exit(1)
    
    test_dataset = FirstCrackDataset(
        test_dir,
        sample_rate=config['sample_rate'],
        target_length=config['target_length_sec']
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=False
    )
    
    print(f"\nTest set: {len(test_dataset)} samples")
    test_stats = test_dataset.get_statistics()
    print(f"  first_crack: {test_stats['first_crack']}")
    print(f"  no_first_crack: {test_stats['no_first_crack']}")
    
    # Create model and load weights
    device = config.get('device', 'mps' if torch.backends.mps.is_available() else 'cpu')
    model_config = ModelInitConfig(device=device)
    model = FirstCrackClassifier(model_config)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    
    print(f"\nModel device: {device}")
    
    # Evaluate
    metrics = evaluate_model(model, test_loader, device)
    
    # Compute and print results
    results = metrics.compute()
    
    print("\n" + "="*60)
    print("TEST SET EVALUATION RESULTS")
    print("="*60)
    print(f"\nAccuracy:  {results['accuracy']:.4f}")
    print(f"Precision: {results['precision']:.4f}")
    print(f"Recall:    {results['recall']:.4f}")
    print(f"F1 Score:  {results['f1']:.4f}")
    
    if 'roc_auc' in results:
        print(f"ROC-AUC:   {results['roc_auc']:.4f}")
    
    print(f"\nPer-Class Metrics:")
    print(f"  no_first_crack - Precision: {results['precision_no_first_crack']:.4f}, "
          f"Recall: {results['recall_no_first_crack']:.4f}")
    print(f"  first_crack    - Precision: {results['precision_first_crack']:.4f}, "
          f"Recall: {results['recall_first_crack']:.4f}")
    
    print("\n" + "="*60)
    print("CLASSIFICATION REPORT")
    print("="*60)
    print(metrics.get_classification_report())
    
    print("\n" + "="*60)
    print("CONFUSION MATRIX")
    print("="*60)
    cm = metrics.compute_confusion_matrix()
    print(cm)
    print("\n(Rows: True Label, Columns: Predicted Label)")
    
    # Save results
    results_file = output_dir / "test_results.txt"
    with open(results_file, 'w') as f:
        f.write("TEST SET EVALUATION RESULTS\n")
        f.write("="*60 + "\n\n")
        f.write(f"Checkpoint: {checkpoint_path}\n")
        f.write(f"Epoch: {checkpoint['epoch']}\n")
        f.write(f"Test samples: {len(test_dataset)}\n\n")
        
        f.write(f"Accuracy:  {results['accuracy']:.4f}\n")
        f.write(f"Precision: {results['precision']:.4f}\n")
        f.write(f"Recall:    {results['recall']:.4f}\n")
        f.write(f"F1 Score:  {results['f1']:.4f}\n")
        if 'roc_auc' in results:
            f.write(f"ROC-AUC:   {results['roc_auc']:.4f}\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("CLASSIFICATION REPORT\n")
        f.write("="*60 + "\n")
        f.write(metrics.get_classification_report())
        
        f.write("\n" + "="*60 + "\n")
        f.write("CONFUSION MATRIX\n")
        f.write("="*60 + "\n")
        f.write(str(cm) + "\n")
    
    print(f"\n✅ Results saved to {results_file}")
    
    # Plot confusion matrix
    cm_plot = output_dir / "confusion_matrix.png"
    plot_confusion_matrix(cm, cm_plot)
    
    print("\n" + "="*60)
    print("EVALUATION COMPLETE")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
