#!/usr/bin/env python3
"""
Update performance_history.csv with results from a new evaluation.

Usage:
    python tools/update_performance_history.py \
        --version 20251018_baseline_v1 \
        --accuracy 0.95 \
        --precision 0.94 \
        --recall 0.96 \
        --f1 0.95 \
        --notes "Initial baseline model"
"""

import argparse
import csv
from datetime import datetime
from pathlib import Path


def update_history(version: str, metrics: dict):
    """Append new results to performance history."""
    
    history_file = Path("evaluation/history/performance_history.csv")
    
    # Prepare row
    row = {
        "timestamp": datetime.now().isoformat(),
        "model_version": version,
        "accuracy": metrics.get("accuracy", ""),
        "precision": metrics.get("precision", ""),
        "recall": metrics.get("recall", ""),
        "f1_score": metrics.get("f1", ""),
        "false_positive_rate": metrics.get("fpr", ""),
        "false_negative_rate": metrics.get("fnr", ""),
        "inference_latency_ms": metrics.get("latency_ms", ""),
        "training_samples": metrics.get("training_samples", ""),
        "validation_samples": metrics.get("validation_samples", ""),
        "test_samples": metrics.get("test_samples", ""),
        "notes": metrics.get("notes", "")
    }
    
    # Append to CSV
    with open(history_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writerow(row)
    
    print(f"✓ Updated performance history: {history_file}")
    print(f"  Version: {version}")
    print(f"  Metrics: accuracy={row['accuracy']}, f1={row['f1_score']}")


def main():
    parser = argparse.ArgumentParser(
        description="Update performance history with new evaluation results"
    )
    parser.add_argument("--version", required=True, help="Version ID (e.g., 20251018_baseline_v1)")
    parser.add_argument("--accuracy", type=float, help="Accuracy")
    parser.add_argument("--precision", type=float, help="Precision")
    parser.add_argument("--recall", type=float, help="Recall")
    parser.add_argument("--f1", type=float, help="F1 score")
    parser.add_argument("--fpr", type=float, help="False positive rate")
    parser.add_argument("--fnr", type=float, help="False negative rate")
    parser.add_argument("--latency-ms", type=float, help="Inference latency (ms)")
    parser.add_argument("--training-samples", type=int, help="Number of training samples")
    parser.add_argument("--validation-samples", type=int, help="Number of validation samples")
    parser.add_argument("--test-samples", type=int, help="Number of test samples")
    parser.add_argument("--notes", help="Additional notes")
    
    args = parser.parse_args()
    
    metrics = {
        "accuracy": args.accuracy,
        "precision": args.precision,
        "recall": args.recall,
        "f1": args.f1,
        "fpr": args.fpr,
        "fnr": args.fnr,
        "latency_ms": args.latency_ms,
        "training_samples": args.training_samples,
        "validation_samples": args.validation_samples,
        "test_samples": args.test_samples,
        "notes": args.notes
    }
    
    update_history(args.version, metrics)


if __name__ == "__main__":
    main()
