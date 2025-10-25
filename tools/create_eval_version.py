#!/usr/bin/env python3
"""
Create a new versioned evaluation results directory with metadata tracking.

Usage:
    python tools/create_eval_version.py \
        --name "hp_tuning_lr_001" \
        --model-path "experiments/runs/v2" \
        --changes "Reduced learning rate to 0.001"
"""

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path


def get_git_commit():
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_previous_version():
    """Get the most recent evaluation version."""
    results_dir = Path("evaluation/results")
    versions = sorted([d for d in results_dir.iterdir() if d.is_dir()])
    if versions:
        return versions[-1].name
    return None


def create_evaluation_version(name: str, model_path: str, changes: dict):
    """Create a new versioned evaluation directory with metadata."""
    
    # Create directory name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    version_name = f"{timestamp}_{name}"
    version_dir = Path("evaluation/results") / version_name
    version_dir.mkdir(parents=True, exist_ok=True)
    
    # Get previous version for comparison
    previous_version = get_previous_version()
    
    # Create metadata
    metadata = {
        "experiment_id": version_name,
        "timestamp": datetime.now().isoformat(),
        "model_version": name,
        "experiment_path": model_path,
        "git_commit": get_git_commit(),
        
        "model_config": {
            "architecture": changes.get("model_architecture", "AST"),
            "notes": changes.get("model_notes", "")
        },
        
        "data": {
            "training_samples": changes.get("training_samples"),
            "annotation_version": changes.get("annotation_version"),
            "data_changes": changes.get("data_changes", "")
        },
        
        "hyperparameters": {
            "learning_rate": changes.get("learning_rate"),
            "batch_size": changes.get("batch_size"),
            "epochs": changes.get("epochs"),
            "notes": changes.get("hp_notes", "")
        },
        
        "changes_from_previous": {
            "previous_version": previous_version,
            "model": changes.get("model_changes", "No changes"),
            "hyperparameters": changes.get("hp_changes", "No changes"),
            "data": changes.get("data_changes", "No changes"),
            "annotations": changes.get("annotation_changes", "No changes"),
            "summary": changes.get("summary", "")
        }
    }
    
    # Write metadata
    metadata_file = version_dir / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ Created evaluation version: {version_name}")
    print(f"  Directory: {version_dir}")
    print(f"  Metadata: {metadata_file}")
    print(f"\nNext steps:")
    print(f"  1. Run your evaluation and save results to: {version_dir}/")
    print(f"  2. Update evaluation/history/performance_history.csv")
    print(f"  3. Commit the results: git add {version_dir}")
    
    return version_dir


def main():
    parser = argparse.ArgumentParser(
        description="Create new versioned evaluation directory"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Short name for this version (e.g., 'hp_tuning', 'more_data')"
    )
    parser.add_argument(
        "--model-path",
        required=True,
        help="Path to the experiment run (e.g., 'experiments/runs/v2')"
    )
    parser.add_argument(
        "--changes",
        required=True,
        help="Summary of what changed"
    )
    parser.add_argument(
        "--model-changes",
        help="Specific model architecture changes"
    )
    parser.add_argument(
        "--hp-changes",
        help="Hyperparameter changes"
    )
    parser.add_argument(
        "--data-changes",
        help="Data or annotation changes"
    )
    parser.add_argument(
        "--training-samples",
        type=int,
        help="Number of training samples"
    )
    
    args = parser.parse_args()
    
    changes = {
        "summary": args.changes,
        "model_changes": args.model_changes or "No changes",
        "hp_changes": args.hp_changes or "No changes",
        "data_changes": args.data_changes or "No changes",
        "training_samples": args.training_samples,
    }
    
    create_evaluation_version(args.name, args.model_path, changes)


if __name__ == "__main__":
    main()
