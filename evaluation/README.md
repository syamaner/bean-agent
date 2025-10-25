# Model Evaluation

This directory contains model evaluation results, performance metrics, and historical tracking for the first crack detection model.

## Purpose

Unlike `tests/` which validates that implementation tasks are completed correctly, this directory focuses on:
- Model performance evaluation (accuracy, precision, recall, F1)
- Inference latency and throughput benchmarks
- Historical performance tracking across training runs
- Comparison between different model versions
- Production readiness assessment

## Structure

```
evaluation/
├── metrics/              # Custom evaluation metrics implementations
├── results/              # Evaluation results for each model version
│   └── [model_version]/  # e.g., baseline_v1, ast_v2, etc.
│       ├── test_set_results.json
│       ├── confusion_matrix.png
│       ├── roc_curve.png
│       └── evaluation_report.md
├── history/              # Historical performance tracking
│   └── performance_history.csv
└── README.md            # This file
```

## Performance Tracking

### Metrics

Key metrics tracked for each model version:

**Classification Metrics:**
- Accuracy
- Precision (first crack detection)
- Recall (first crack detection)
- F1-Score
- False Positive Rate
- False Negative Rate
- Confusion Matrix
- ROC-AUC

**Performance Metrics:**
- Inference latency (mean, p50, p95, p99)
- Throughput (samples/second)
- Memory usage
- GPU utilization

**Data Metrics:**
- Training set size
- Validation set size
- Test set size
- Class balance

### Historical Tracking

`history/performance_history.csv` maintains a record of all model versions:

```csv
timestamp,model_version,accuracy,precision,recall,f1_score,false_positive_rate,inference_latency_ms,training_samples,notes
2025-10-18,baseline_v1,0.95,0.94,0.96,0.95,0.04,450,120,Initial model with 4 recordings
```

## Evaluation Workflow

1. **Train model** → Save to `experiments/runs/[version]/`
2. **Run evaluation** → `python src/training/evaluate.py`
3. **Generate reports** → Save to `evaluation/results/[version]/`
4. **Update history** → Append to `history/performance_history.csv`
5. **Compare versions** → Review historical trends

## Target Performance

From Phase 1 requirements:

- ✅ First crack detection accuracy: **>95%**
- ✅ Inference latency: **<2 seconds** for 30-second chunks
- ✅ False positive rate: **<5%**

## Model Comparison

When comparing model versions, consider:

1. **Accuracy vs. Latency trade-off**
2. **Robustness to different roast profiles**
3. **Generalization to new bean varieties**
4. **Resource requirements (memory, GPU)**
5. **Ease of deployment**

## Creating New Evaluation

For each new model version:

```bash
# Run evaluation
python src/training/evaluate.py \
    --model experiments/runs/[version]/best_model.pt \
    --test-data data/splits/test \
    --output evaluation/results/[version]/

# Update performance history
python src/training/update_history.py \
    --results evaluation/results/[version]/test_set_results.json
```

## Viewing Historical Performance

```bash
# View all model versions
cat evaluation/history/performance_history.csv

# Plot performance trends
python src/utils/plot_history.py
```

---

**Note:** This directory is for model evaluation. For implementation task validation, see `tests/VALIDATION.md`.
