#!/usr/bin/env python3
"""
Training script for first crack detection model.

Trains an Audio Spectrogram Transformer (AST) for binary classification.
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_prep.audio_dataset import FirstCrackDataset, create_dataloaders
from models.ast_model import FirstCrackClassifier, ModelInitConfig
from models.config import TRAINING_CONFIG
from utils.metrics import MetricsCalculator, calculate_batch_accuracy


class Trainer:
    """Training manager for first crack detection."""
    
    def __init__(
        self,
        model: FirstCrackClassifier,
        train_loader: DataLoader,
        val_loader: DataLoader,
        config: Dict,
        experiment_dir: Path,
        use_class_weights: bool = True
    ):
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.config = config
        self.experiment_dir = experiment_dir
        self.device = model.device
        
        # Create experiment directories
        self.checkpoints_dir = experiment_dir / "checkpoints"
        self.logs_dir = experiment_dir / "logs"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup loss function with class weights
        if use_class_weights:
            class_weights = train_loader.dataset.get_class_weights()
            self.criterion = nn.CrossEntropyLoss(weight=class_weights.to(self.device))
            print(f"Using class weights: {class_weights.tolist()}")
        else:
            self.criterion = nn.CrossEntropyLoss()
        
        # Setup optimizer
        self.optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=config['learning_rate'],
            weight_decay=config['weight_decay']
        )
        
        # Learning rate scheduler
        total_steps = len(train_loader) * config['num_epochs']
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=total_steps
        )
        
        # TensorBoard writer
        self.writer = SummaryWriter(log_dir=str(self.logs_dir))
        
        # Training state
        self.current_epoch = 0
        self.best_val_f1 = 0.0
        self.best_val_accuracy = 0.0
        self.epochs_without_improvement = 0
        self.global_step = 0
        
        # Save config
        config_path = experiment_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Saved config to {config_path}")
    
    def train_epoch(self) -> Dict[str, float]:
        """Train for one epoch."""
        self.model.train()
        
        total_loss = 0.0
        metrics = MetricsCalculator()
        
        pbar = tqdm(self.train_loader, desc=f"Epoch {self.current_epoch+1} [Train]")
        for batch_idx, (audio, labels) in enumerate(pbar):
            audio = audio.to(self.device)
            labels = labels.to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            logits = self.model(audio)
            loss = self.criterion(logits, labels)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping
            if self.config.get('max_grad_norm'):
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(),
                    self.config['max_grad_norm']
                )
            
            self.optimizer.step()
            self.scheduler.step()
            
            # Track metrics
            total_loss += loss.item()
            probs = torch.softmax(logits, dim=-1)
            preds = torch.argmax(probs, dim=-1)
            metrics.update(preds, labels, probs)
            
            # Update progress bar
            batch_acc = calculate_batch_accuracy(preds, labels)
            pbar.set_postfix({
                'loss': f"{loss.item():.4f}",
                'acc': f"{batch_acc:.3f}",
                'lr': f"{self.scheduler.get_last_lr()[0]:.2e}"
            })
            
            # Log to TensorBoard
            self.writer.add_scalar('train/batch_loss', loss.item(), self.global_step)
            self.writer.add_scalar('train/batch_acc', batch_acc, self.global_step)
            self.writer.add_scalar('train/lr', self.scheduler.get_last_lr()[0], self.global_step)
            self.global_step += 1
        
        # Compute epoch metrics
        avg_loss = total_loss / len(self.train_loader)
        epoch_metrics = metrics.compute()
        epoch_metrics['loss'] = avg_loss
        
        return epoch_metrics
    
    @torch.inference_mode()
    def validate(self) -> Dict[str, float]:
        """Validate on validation set."""
        self.model.eval()
        
        total_loss = 0.0
        metrics = MetricsCalculator()
        
        pbar = tqdm(self.val_loader, desc=f"Epoch {self.current_epoch+1} [Val]")
        for audio, labels in pbar:
            audio = audio.to(self.device)
            labels = labels.to(self.device)
            
            # Forward pass
            logits = self.model(audio)
            loss = self.criterion(logits, labels)
            
            # Track metrics
            total_loss += loss.item()
            probs = torch.softmax(logits, dim=-1)
            preds = torch.argmax(probs, dim=-1)
            metrics.update(preds, labels, probs)
            
            batch_acc = calculate_batch_accuracy(preds, labels)
            pbar.set_postfix({
                'loss': f"{loss.item():.4f}",
                'acc': f"{batch_acc:.3f}"
            })
        
        # Compute metrics
        avg_loss = total_loss / len(self.val_loader)
        val_metrics = metrics.compute()
        val_metrics['loss'] = avg_loss
        
        # Print classification report
        print("\nValidation Classification Report:")
        print(metrics.get_classification_report())
        print("\nConfusion Matrix:")
        print(metrics.compute_confusion_matrix())
        
        return val_metrics
    
    def save_checkpoint(self, is_best: bool = False, filename: str = None):
        """Save model checkpoint."""
        if filename is None:
            filename = f"checkpoint_epoch_{self.current_epoch+1}.pt"
        
        checkpoint = {
            'epoch': self.current_epoch + 1,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'best_val_f1': self.best_val_f1,
            'best_val_accuracy': self.best_val_accuracy,
            'config': self.config,
        }
        
        checkpoint_path = self.checkpoints_dir / filename
        torch.save(checkpoint, checkpoint_path)
        print(f"Saved checkpoint to {checkpoint_path}")
        
        if is_best:
            best_path = self.checkpoints_dir / "best_model.pt"
            torch.save(checkpoint, best_path)
            print(f"✨ New best model saved to {best_path}")
    
    def load_checkpoint(self, checkpoint_path: Path):
        """Load model checkpoint."""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        self.current_epoch = checkpoint['epoch']
        self.best_val_f1 = checkpoint.get('best_val_f1', 0.0)
        self.best_val_accuracy = checkpoint.get('best_val_accuracy', 0.0)
        
        print(f"Loaded checkpoint from {checkpoint_path}")
        print(f"Resuming from epoch {self.current_epoch}")
    
    def train(self, num_epochs: int, early_stopping_patience: int = 5):
        """
        Main training loop.
        
        Args:
            num_epochs: Number of epochs to train
            early_stopping_patience: Stop if no improvement for N epochs
        """
        print(f"\n{'='*60}")
        print(f"Starting training for {num_epochs} epochs")
        print(f"Device: {self.device}")
        print(f"Train samples: {len(self.train_loader.dataset)}")
        print(f"Val samples: {len(self.val_loader.dataset)}")
        print(f"{'='*60}\n")
        
        for epoch in range(num_epochs):
            self.current_epoch = epoch
            
            # Train
            train_metrics = self.train_epoch()
            
            # Validate
            val_metrics = self.validate()
            
            # Log epoch metrics
            print(f"\n{'='*60}")
            print(f"Epoch {epoch+1}/{num_epochs} Summary:")
            print(f"  Train - Loss: {train_metrics['loss']:.4f}, "
                  f"Acc: {train_metrics['accuracy']:.3f}, "
                  f"F1: {train_metrics['f1']:.3f}")
            print(f"  Val   - Loss: {val_metrics['loss']:.4f}, "
                  f"Acc: {val_metrics['accuracy']:.3f}, "
                  f"F1: {val_metrics['f1']:.3f}")
            print(f"  Val   - Recall(FC): {val_metrics['recall_first_crack']:.3f}, "
                  f"Precision(FC): {val_metrics['precision_first_crack']:.3f}")
            print(f"{'='*60}\n")
            
            # TensorBoard logging
            for metric_name, value in train_metrics.items():
                self.writer.add_scalar(f'train_epoch/{metric_name}', value, epoch)
            for metric_name, value in val_metrics.items():
                self.writer.add_scalar(f'val_epoch/{metric_name}', value, epoch)
            
            # Check for improvement (using F1 score as primary metric)
            is_best = val_metrics['f1'] > self.best_val_f1
            if is_best:
                self.best_val_f1 = val_metrics['f1']
                self.best_val_accuracy = val_metrics['accuracy']
                self.epochs_without_improvement = 0
            else:
                self.epochs_without_improvement += 1
            
            # Save checkpoints
            self.save_checkpoint(is_best=is_best)
            
            # Save latest model every 5 epochs
            if (epoch + 1) % 5 == 0:
                self.save_checkpoint(filename=f"checkpoint_latest.pt")
            
            # Early stopping
            if self.epochs_without_improvement >= early_stopping_patience:
                print(f"\n⚠️  Early stopping triggered after {epoch+1} epochs")
                print(f"No improvement for {early_stopping_patience} epochs")
                break
        
        # Training complete
        print(f"\n{'='*60}")
        print(f"🎉 Training Complete!")
        print(f"Best validation F1: {self.best_val_f1:.4f}")
        print(f"Best validation accuracy: {self.best_val_accuracy:.4f}")
        print(f"{'='*60}\n")
        
        self.writer.close()


def main():
    parser = argparse.ArgumentParser(description="Train first crack detection model")
    parser.add_argument('--data-dir', type=str, default='data/splits',
                        help='Directory containing train/val/test splits')
    parser.add_argument('--experiment-name', type=str, default=None,
                        help='Experiment name (default: timestamp)')
    parser.add_argument('--batch-size', type=int, default=None,
                        help='Batch size (default: from config)')
    parser.add_argument('--num-epochs', type=int, default=None,
                        help='Number of epochs (default: from config)')
    parser.add_argument('--learning-rate', type=float, default=None,
                        help='Learning rate (default: from config)')
    parser.add_argument('--resume', type=str, default=None,
                        help='Path to checkpoint to resume from')
    parser.add_argument('--no-class-weights', action='store_true',
                        help='Disable class weights for imbalanced data')
    
    args = parser.parse_args()
    
    # Setup paths
    data_dir = Path(args.data_dir)
    train_dir = data_dir / "train"
    val_dir = data_dir / "val"
    
    if not train_dir.exists() or not val_dir.exists():
        print(f"❌ Error: Train or val directory not found in {data_dir}")
        sys.exit(1)
    
    # Create experiment directory
    if args.experiment_name:
        exp_name = args.experiment_name
    else:
        exp_name = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    experiment_dir = Path("experiments") / "runs" / exp_name
    experiment_dir.mkdir(parents=True, exist_ok=True)
    print(f"Experiment directory: {experiment_dir}")
    
    # Load and override config
    config = TRAINING_CONFIG.copy()
    if args.batch_size:
        config['batch_size'] = args.batch_size
    if args.num_epochs:
        config['num_epochs'] = args.num_epochs
    if args.learning_rate:
        config['learning_rate'] = args.learning_rate
    
    # Set random seed
    torch.manual_seed(config['seed'])
    
    # Create dataloaders
    print("Loading datasets...")
    train_loader, val_loader = create_dataloaders(
        train_dir=train_dir,
        val_dir=val_dir,
        batch_size=config['batch_size'],
        num_workers=0,  # MPS works best with num_workers=0
        sample_rate=config['sample_rate'],
        target_length=config['target_length_sec'],
        train_crop_mode=config.get('train_crop_mode', 'random'),
        eval_crop_mode=config.get('eval_crop_mode', 'center')
    )
    
    # Print dataset statistics
    print("\nDataset Statistics:")
    train_stats = train_loader.dataset.get_statistics()
    val_stats = val_loader.dataset.get_statistics()
    print(f"Train: {train_stats['total_samples']} samples "
          f"({train_stats['first_crack']} first_crack, "
          f"{train_stats['no_first_crack']} no_first_crack)")
    print(f"Val:   {val_stats['total_samples']} samples "
          f"({val_stats['first_crack']} first_crack, "
          f"{val_stats['no_first_crack']} no_first_crack)")
    
    # Create model
    print("\nInitializing model...")
    model_config = ModelInitConfig(device=config['device'])
    model = FirstCrackClassifier(model_config)
    print(f"Model device: {model.device}")
    
    # Create trainer
    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        config=config,
        experiment_dir=experiment_dir,
        use_class_weights=not args.no_class_weights
    )
    
    # Resume from checkpoint if specified
    if args.resume:
        trainer.load_checkpoint(Path(args.resume))
    
    # Train
    trainer.train(
        num_epochs=config['num_epochs'],
        early_stopping_patience=5
    )


if __name__ == '__main__':
    main()
