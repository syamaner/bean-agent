"""
Evaluation metrics for binary first crack detection.
"""
from typing import Dict
import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    classification_report
)


class MetricsCalculator:
    """Calculate and track classification metrics."""
    
    def __init__(self, num_classes: int = 2):
        self.num_classes = num_classes
        self.reset()
    
    def reset(self):
        """Reset all tracked values."""
        self.all_preds = []
        self.all_labels = []
        self.all_probs = []
    
    def update(
        self,
        predictions: torch.Tensor,
        labels: torch.Tensor,
        probabilities: torch.Tensor = None
    ):
        """
        Update metrics with a batch.
        
        Args:
            predictions: Predicted class indices [batch]
            labels: True labels [batch]
            probabilities: Optional class probabilities [batch, num_classes]
        """
        self.all_preds.extend(predictions.detach().cpu().numpy().tolist())
        self.all_labels.extend(labels.detach().cpu().numpy().tolist())
        
        if probabilities is not None:
            self.all_probs.extend(probabilities.detach().cpu().numpy().tolist())
    
    def compute(self) -> Dict[str, float]:
        """
        Compute all metrics.
        
        Returns:
            Dictionary of metric name -> value
        """
        preds = np.array(self.all_preds)
        labels = np.array(self.all_labels)
        
        metrics = {
            'accuracy': accuracy_score(labels, preds),
            'precision': precision_score(labels, preds, average='binary', zero_division=0),
            'recall': recall_score(labels, preds, average='binary', zero_division=0),
            'f1': f1_score(labels, preds, average='binary', zero_division=0),
        }
        
        # Add per-class metrics
        precision_per_class = precision_score(labels, preds, average=None, zero_division=0)
        recall_per_class = recall_score(labels, preds, average=None, zero_division=0)
        
        metrics['precision_no_first_crack'] = precision_per_class[0]
        metrics['precision_first_crack'] = precision_per_class[1]
        metrics['recall_no_first_crack'] = recall_per_class[0]
        metrics['recall_first_crack'] = recall_per_class[1]
        
        # ROC-AUC if probabilities available
        if len(self.all_probs) > 0:
            probs = np.array(self.all_probs)
            # Use probability of positive class (first_crack)
            metrics['roc_auc'] = roc_auc_score(labels, probs[:, 1])
        
        return metrics
    
    def compute_confusion_matrix(self) -> np.ndarray:
        """Compute confusion matrix."""
        return confusion_matrix(self.all_labels, self.all_preds)
    
    def get_classification_report(self, target_names=None) -> str:
        """Get detailed classification report."""
        if target_names is None:
            target_names = ['no_first_crack', 'first_crack']
        return classification_report(
            self.all_labels,
            self.all_preds,
            target_names=target_names
        )


def calculate_batch_accuracy(
    predictions: torch.Tensor,
    labels: torch.Tensor
) -> float:
    """Quick accuracy calculation for a single batch."""
    correct = (predictions == labels).sum().item()
    total = labels.size(0)
    return correct / total if total > 0 else 0.0
