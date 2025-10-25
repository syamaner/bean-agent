## Dataset Overview

**Total Samples:** 298 chunks from 9 roasting sessions

### Overall Class Balance

| Class | Count | Percentage | Avg Duration |
|-------|-------|------------|--------------|
| **first_crack** | 145 | 48.7% | 4.5s |
| **no_first_crack** | 153 | 51.3% | 4.0s |

### Split Distribution

| Split | Total Samples | first_crack | no_first_crack | Split Ratio |
|-------|---------------|-------------|----------------|-------------|
| **Train** | 208 | 101 (48.6%) | 107 (51.4%) | 69.8% |
| **Validation** | 45 | 22 (48.9%) | 23 (51.1%) | 15.1% |
| **Test** | 45 | 22 (48.9%) | 23 (51.1%) | 15.1% |

### Class Balance Across Splits

| Class | Train | Validation | Test | Total |
|-------|-------|------------|------|-------|
| **first_crack** | 101 | 22 | 22 | 145 |
| **no_first_crack** | 107 | 23 | 23 | 153 |

### Per-Session Breakdown

| Recording Session | first_crack | no_first_crack | Total | Balance |
|-------------------|-------------|----------------|-------|---------|
| 25-10-19_1103-costarica-hermosa-5 | 13 | 14 | 27 | 48.1% / 51.9% |
| 25-10-19_1136-brazil-1 | 19 | 19 | 38 | 50.0% / 50.0% |
| 25-10-19_1204-brazil-2 | 20 | 15 | 35 | 57.1% / 42.9% |
| 25-10-19_1236-brazil-3 | 18 | 17 | 35 | 51.4% / 48.6% |
| 25-10-19_1315-brazil4 | 15 | 14 | 29 | 51.7% / 48.3% |
| roast-1-costarica-hermosa-hp-a | 16 | 17 | 33 | 48.5% / 51.5% |
| roast-2-costarica-hermosa-hp-a | 16 | 19 | 35 | 45.7% / 54.3% |
| roast-3-costarica-hermosa-hp-a | 13 | 19 | 32 | 40.6% / 59.4% |
| roast-4-costarica-hermosa-hp-a | 15 | 19 | 34 | 44.1% / 55.9% |

**Key Observations:**
- Nearly balanced dataset (48.7% vs 51.3%)
- Stratified split maintains balance across train/val/test
- 9 recording sessions, mix of Costa Rica and Brazil beans
- Average chunk duration: 4.2 seconds
- Total annotated audio: ~21 minutes

---

## Evaluation Metrics

For this binary classification task, we use multiple metrics to comprehensively assess model performance:

### Accuracy
**Definition:** The proportion of correct predictions (both true positives and true negatives) among all predictions.

```
Accuracy = (TP + TN) / (TP + TN + FP + FN)
```

**Why it matters:** Provides an overall sense of model correctness. However, accuracy alone can be misleading with imbalanced datasets.

### Precision
**Definition:** Of all samples predicted as `first_crack`, what proportion actually were first crack events?

```
Precision = TP / (TP + FP)
```

**Why it matters:** High precision means fewer false alarms. Critical when we don't want to prematurely adjust roaster settings based on incorrect detections.

### Recall (Sensitivity)
**Definition:** Of all actual `first_crack` events, what proportion did the model correctly identify?

```
Recall = TP / (TP + FN)
```

**Why it matters:** High recall means we catch most first crack events. Missing first crack (false negative) could result in over-roasting.

### F1 Score
**Definition:** The harmonic mean of precision and recall, providing a single balanced metric.

```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

**Why it matters:** Balances precision and recall. Useful when both false positives and false negatives are costly.

### ROC-AUC (Area Under the Receiver Operating Characteristic Curve)
**Definition:** Measures the model's ability to distinguish between classes across all classification thresholds.

- **ROC Curve:** Plots True Positive Rate (Recall) vs False Positive Rate at various thresholds
- **AUC:** Area under this curve (1.0 = perfect, 0.5 = random guessing)

**Why it matters:** Threshold-independent metric showing overall classification performance. Values above 0.8 indicate good discrimination.

### Confusion Matrix

The confusion matrix visualizes the model's predictions versus actual labels:

```
                    Predicted
                    first_crack  no_first_crack
Actual  first_crack      TP            FN
        no_first_crack   FP            TN
```

Where:
- **TP (True Positive):** Correctly predicted first crack
- **TN (True Negative):** Correctly predicted no first crack
- **FP (False Positive):** Predicted first crack, but was actually no first crack (false alarm)
- **FN (False Negative):** Predicted no first crack, but was actually first crack (missed detection)

**Example from our model:**

```
                    Predicted
                    first_crack  no_first_crack
Actual  first_crack      20            2
        no_first_crack    3           20
```

From this confusion matrix:
- **Accuracy:** (20+20)/45 = 88.9%
- **Precision:** 20/(20+3) = 87.0%
- **Recall:** 20/(20+2) = 90.9%
- **F1 Score:** 2×(0.87×0.909)/(0.87+0.909) = 88.9%

**Interpreting our results:**
- Only 2 missed first crack events (FN) - low risk of over-roasting
- Only 3 false alarms (FP) - minimal unnecessary interventions
- Strong diagonal (TP and TN) indicates good class separation

This balanced performance is crucial for real-time roasting control where both missing first crack and triggering false adjustments have consequences.
