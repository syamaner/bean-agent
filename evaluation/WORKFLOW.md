# Evaluation Results Versioning Workflow

This document describes how to keep evaluation results tidy and traceable across model iterations.

## Directory Structure

```
evaluation/
├── results/
│   ├── 20251018_baseline_v1/         # Timestamp + descriptive name
│   │   ├── metadata.json             # What changed: model, data, hyperparameters
│   │   ├── first_crack_detections.csv
│   │   ├── roast-1_inference_results.txt
│   │   └── ...
│   ├── 20251019_hp_tuning_lr_001/
│   │   ├── metadata.json
│   │   └── ...
│   └── 20251020_more_data_v2/
└── history/
    └── performance_history.csv       # All results in one place

```

## Workflow: Creating a New Evaluation

### Step 1: Create versioned directory

Before running evaluation, create a new version:

```bash
python tools/create_eval_version.py \
    --name "hp_tuning_lr_001" \
    --model-path "experiments/runs/v2" \
    --changes "Reduced learning rate from 0.01 to 0.001" \
    --hp-changes "learning_rate: 0.01 → 0.001" \
    --training-samples 8
```

This creates: `evaluation/results/20251019_hp_tuning_lr_001/metadata.json`

### Step 2: Run evaluation

Save results to the versioned directory:

```bash
python src/training/evaluate.py \
    --model experiments/runs/v2/best_model.pt \
    --test-data data/splits/test \
    --output evaluation/results/20251019_hp_tuning_lr_001/
```

### Step 3: Update performance history

Add metrics to the historical CSV:

```bash
python tools/update_performance_history.py \
    --version 20251019_hp_tuning_lr_001 \
    --accuracy 0.97 \
    --precision 0.96 \
    --recall 0.98 \
    --f1 0.97 \
    --training-samples 8 \
    --test-samples 2 \
    --notes "Improved recall with lower learning rate"
```

### Step 4: Version in git

```bash
git add evaluation/results/20251019_hp_tuning_lr_001/
git add evaluation/history/performance_history.csv
git commit -m "eval: hp tuning with lr=0.001"
```

## Tracking Changes

The `metadata.json` file tracks what changed between versions:

```json
{
  "experiment_id": "20251019_hp_tuning_lr_001",
  "changes_from_previous": {
    "previous_version": "20251018_baseline_v1",
    "model": "No changes",
    "hyperparameters": "learning_rate: 0.01 → 0.001",
    "data": "No changes",
    "annotations": "No changes"
  }
}
```

## Common Scenarios

### Adding More Training Data

```bash
python tools/create_eval_version.py \
    --name "more_data_10_roasts" \
    --model-path "experiments/runs/v3" \
    --changes "Added 6 new roast recordings" \
    --data-changes "training_samples: 4 → 10 recordings" \
    --training-samples 10
```

### Changing Annotations

```bash
python tools/create_eval_version.py \
    --name "refined_annotations_v2" \
    --model-path "experiments/runs/v4" \
    --changes "Re-annotated first crack timestamps with finer precision" \
    --data-changes "annotation_version: v1 → v2, refined timestamps"
```

### Model Architecture Change

```bash
python tools/create_eval_version.py \
    --name "ast_larger_context" \
    --model-path "experiments/runs/v5" \
    --changes "Increased context window from 10s to 30s" \
    --model-changes "input_length: 10 → 30 seconds"
```

## Comparing Versions

### View all results

```bash
cat evaluation/history/performance_history.csv | column -t -s,
```

### Compare two versions

```bash
# View metadata side by side
diff -y \
    evaluation/results/20251018_baseline_v1/metadata.json \
    evaluation/results/20251019_hp_tuning_lr_001/metadata.json
```

### Plot trends over time

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('evaluation/history/performance_history.csv')
df.plot(x='timestamp', y=['accuracy', 'precision', 'recall', 'f1_score'])
plt.show()
```

## What Gets Versioned?

✅ **Tracked in git:**
- metadata.json (always)
- CSV result files
- Text summaries
- performance_history.csv

❌ **Not tracked (too large):**
- PNG/JPG visualizations
- Large inference logs
- Model checkpoints (tracked in experiments/)

## Best Practices

1. **Create version before running evaluation** - captures intent
2. **Use descriptive names** - `hp_tuning_lr_001` not `test2`
3. **Document changes** - be specific about what changed
4. **Update history immediately** - don't forget metrics
5. **Commit together** - results + history CSV in same commit
6. **Link to experiments/** - track which model checkpoint was used

## Troubleshooting

**Q: I forgot to create a version directory first**

```bash
# Move files into a new versioned directory
mkdir -p evaluation/results/20251019_forgotten_run
mv first_crack_detections.csv evaluation/results/20251019_forgotten_run/
# Then manually create metadata.json
```

**Q: How do I find which version performed best?**

```bash
# Sort by F1 score
sort -t, -k5 -nr evaluation/history/performance_history.csv | head -5
```

**Q: Can I delete old versions?**

Yes, but keep metadata for reference:
```bash
# Archive old inference logs but keep metadata
tar -czf 20251018_baseline_v1_inference.tar.gz \
    evaluation/results/20251018_baseline_v1/*_inference_results.txt
rm evaluation/results/20251018_baseline_v1/*_inference_results.txt
```
