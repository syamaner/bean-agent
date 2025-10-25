# Data Preparation Pipeline Guide

Complete step-by-step guide to run the entire data preparation pipeline from raw audio to training-ready datasets.

**Last Updated**: 2025-10-18  
**Status**: Milestones 1-3 Complete

---

## Overview

This guide covers the complete data preparation workflow:
1. **Setup** - Environment and dependencies
2. **Annotation** - Label audio with Label Studio
3. **Processing** - Extract audio chunks
4. **Splitting** - Create train/val/test splits
5. **Verification** - Validate dataset quality

---

## Prerequisites

- Python 3.11+
- Virtual environment activated
- Raw audio files in `data/raw/`

---

## Quick Reference - All Commands

```bash
# 1. Setup (one-time)
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Annotate with Label Studio
./venv/bin/label-studio start
# (Use web UI to annotate, then export)

# 3. Convert annotations
./venv/bin/python src/data_prep/convert_labelstudio_export.py \
    --input data/labels/project-1-at-TIMESTAMP.json \
    --output data/labels

# 4. Process into chunks
./venv/bin/python src/data_prep/audio_processor.py \
    --annotations data/labels \
    --audio-dir data/raw \
    --output data/processed

# 5. Split dataset
./venv/bin/python src/data_prep/dataset_splitter.py \
    --input data/processed \
    --output data/splits \
    --train 0.7 --val 0.15 --test 0.15 --seed 42

# 6. Verify chunks
./venv/bin/python src/data_prep/verify_chunks.py --data data/processed

# 7. Test data loading
./venv/bin/python src/data_prep/test_dataloader.py

# 8. Generate spectrograms (optional)
./venv/bin/python src/utils/visualize_spectrograms.py \
    --data data/splits/train \
    --output data/spectrograms
```

---

## Detailed Step-by-Step Guide

## Step 1: Environment Setup (One-Time)

### 1.1 Create Virtual Environment

```bash
# Create venv with Python 3.11
python3.11 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

**Expected Output**: Virtual environment created at `venv/`

### 1.2 Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected Output**: All packages installed, including:
- PyTorch 2.9.0
- Transformers 4.57.1
- Librosa 0.11.0
- Label Studio 1.21.0

**Verify**:
```bash
./venv/bin/python tests/validation/test_mps.py
./venv/bin/python tests/validation/test_audio.py
```

---

## Step 2: Audio Annotation

### 2.1 Start Label Studio

```bash
./venv/bin/label-studio start
```

**What happens**:
- Server starts at http://localhost:8080
- Browser opens automatically
- Create account (first time only - local credentials)

### 2.2 Annotate Audio Files

**See**: `docs/ANNOTATION_WORKFLOW.md` for complete workflow

**Quick steps**:
1. Create/open project: "Coffee Roast First Crack Detection"
2. Import audio files from `data/raw/`
3. Configure interface with `tools/label-studio/label-studio-config.xml`
4. Annotate each file:
   - Mark first_crack regions (red)
   - Mark no_first_crack regions (blue)
   - ~20-25 regions per 10-minute file
5. Submit each task

**Expected Time**: ~30-45 minutes for 4 files

### 2.3 Export Annotations

1. Click **"Export"** button
2. Select **"JSON"** format
3. Download file
4. Move to project:

```bash
mv ~/Downloads/project-1-at-*.json data/labels/

# Create backup
cp data/labels/project-1-at-*.json \
   data/labels/labelstudio-export-$(date +%Y%m%d-%H%M).json
```

**Expected Output**: JSON file in `data/labels/`

---

## Step 3: Convert Annotations

### 3.1 Run Conversion Script

```bash
./venv/bin/python src/data_prep/convert_labelstudio_export.py \
    --input data/labels/project-1-at-2025-10-18-20-44-9bc9cd1d.json \
    --output data/labels \
    --data-root data/raw
```

**Parameters**:
- `--input`: Label Studio export JSON path
- `--output`: Directory to save converted annotations (default: `data/labels`)
- `--data-root`: Directory with WAV files (default: `data/raw`)

**Expected Output**:
```
Wrote data/labels/roast-1-costarica-hermosa-hp-a.json
Wrote data/labels/roast-2-costarica-hermosa-hp-a.json
Wrote data/labels/roast-3-costarica-hermosa-hp-a.json
Wrote data/labels/roast-4-costarica-hermosa-hp-a.json
Converted 4 tasks -> data/labels
```

### 3.2 Verify Conversion

```bash
# Check files created
ls -lh data/labels/roast-*.json

# View summary
./venv/bin/python -c "
import json
from pathlib import Path
for f in sorted(Path('data/labels').glob('roast-*.json')):
    d = json.load(f.open())
    print(f'{f.name}: {len(d[\"annotations\"])} regions')
"
```

**Expected**: 4 JSON files, ~20-25 regions each

---

## Step 4: Process into Audio Chunks

### 4.1 Run Audio Processor

```bash
./venv/bin/python src/data_prep/audio_processor.py \
    --annotations data/labels \
    --audio-dir data/raw \
    --output data/processed \
    --sample-rate 44100
```

**Parameters**:
- `--annotations`: Directory with annotation JSON files
- `--audio-dir`: Directory with WAV files
- `--output`: Output directory for chunks
- `--sample-rate`: Sample rate for output (default: 44100)

**Expected Output**:
```
Processing: roast-1-costarica-hermosa-hp-a.wav
  Duration: 639.7s, Sample rate: 44100Hz
  ✅ Extracted 23 chunks
     - first_crack: 4
     - no_first_crack: 19
...
📊 Summary report saved to: data/processed/processing_summary.md
✅ Processing complete!
```

### 4.2 Verify Chunks

```bash
# Count chunks
echo "First crack: $(ls data/processed/first_crack/*.wav | wc -l)"
echo "No first crack: $(ls data/processed/no_first_crack/*.wav | wc -l)"

# View processing summary
cat data/processed/processing_summary.md
```

**Expected**: ~87 total chunks (14 first_crack, 73 no_first_crack)

---

## Step 5: Create Dataset Splits

### 5.1 Run Splitter

```bash
./venv/bin/python src/data_prep/dataset_splitter.py \
    --input data/processed \
    --output data/splits \
    --train 0.7 \
    --val 0.15 \
    --test 0.15 \
    --seed 42
```

**Parameters**:
- `--input`: Directory with processed chunks
- `--output`: Output directory for splits
- `--train`: Train split ratio (default: 0.7)
- `--val`: Validation split ratio (default: 0.15)
- `--test`: Test split ratio (default: 0.15)
- `--seed`: Random seed for reproducibility (default: 42)

**Expected Output**:
```
first_crack:
  Train: 9 (64.3%)
  Val:   2 (14.3%)
  Test:  3 (21.4%)

no_first_crack:
  Train: 51 (69.9%)
  Val:   11 (15.1%)
  Test:  11 (15.1%)

✅ Copied 60 files to data/splits/train
✅ Copied 13 files to data/splits/val
✅ Copied 14 files to data/splits/test
```

### 5.2 Verify Splits

```bash
# View split report
cat data/splits/split_report.md

# Count files per split
for split in train val test; do
  echo "$split: $(find data/splits/$split -name '*.wav' | wc -l) files"
done
```

---

## Step 6: Verify Chunk Quality

### 6.1 Run Verification Script

```bash
./venv/bin/python src/data_prep/verify_chunks.py \
    --data data/processed \
    --samples 10
```

**Parameters**:
- `--data`: Directory with processed chunks
- `--samples`: Number of random samples to check per class (default: 10)

**Expected Output**:
```
Found chunks:
  - first_crack: 14
  - no_first_crack: 73

📊 Results:
  ✅ OK: 18/20
  ⚠️  Issues: 2/20

📈 Duration statistics:
  Mean: 29.9s
  Min: 15.6s
  Max: 35.6s

✅ Success rate: 90.0%
```

**Success Criteria**: >90% success rate is good (some clipping on loud first cracks is expected)

---

## Step 7: Test Data Loading

### 7.1 Test PyTorch DataLoader

```bash
./venv/bin/python src/data_prep/test_dataloader.py
```

**Expected Output**:
```
✅ Train loader: 8 batches
✅ Val loader: 2 batches
✅ Test loader: 2 batches

Batch 0:
  Audio shape: torch.Size([8, 160000])
  Labels shape: torch.Size([8])
  
Class weights:
  No first crack: 0.588
  First crack: 3.333

Target device: mps
✅ Successfully moved data to mps
✅ All tests passed!
```

### 7.2 Test Individual Dataset

```bash
# Test train set
./venv/bin/python src/data_prep/audio_dataset.py data/splits/train

# Test validation set
./venv/bin/python src/data_prep/audio_dataset.py data/splits/val

# Test test set
./venv/bin/python src/data_prep/audio_dataset.py data/splits/test
```

---

## Step 8: Generate Spectrograms (Optional)

### 8.1 Visualize Spectrograms

```bash
./venv/bin/python src/utils/visualize_spectrograms.py \
    --data data/splits/train \
    --output data/spectrograms \
    --samples 3
```

**Parameters**:
- `--data`: Directory with audio splits
- `--output`: Output directory for images
- `--samples`: Samples per class to visualize (default: 3)

**Expected Output**:
```
✅ Saved: data/spectrograms/spectrograms_first_crack.png
✅ Saved: data/spectrograms/spectrograms_no_first_crack.png
✅ Saved: data/spectrograms/spectrogram_comparison.png
```

### 8.2 View Spectrograms

```bash
# Open comparison image
open data/spectrograms/spectrogram_comparison.png
```

**Look for**:
- First crack: Sharp vertical lines/bursts
- No first crack: Smoother, continuous patterns

---

## Troubleshooting

### Issue: Label Studio won't start

```bash
# Check if already running
ps aux | grep label-studio

# Kill existing process
pkill -f label-studio

# Restart
./venv/bin/label-studio start
```

### Issue: Conversion script can't find audio files

```bash
# Verify audio files exist
ls -lh data/raw/*.wav

# Check annotation file references correct filenames
cat data/labels/project-1-at-*.json | grep audio_file

# Ensure paths are correct
./venv/bin/python src/data_prep/convert_labelstudio_export.py \
    --input data/labels/YOUR-FILE.json \
    --output data/labels \
    --data-root data/raw  # Make sure this is correct
```

### Issue: Audio processor finds no annotations

```bash
# Check annotation files exist and have correct naming
ls -lh data/labels/roast-*.json

# Verify JSON format
cat data/labels/roast-1-*.json | python -m json.tool | head -20
```

### Issue: Dataset splitter shows imbalanced splits

- This is expected with small datasets
- The splitter uses stratified splitting to maintain class balance
- Slight variations are normal (especially with only 14 first_crack samples)

### Issue: MPS not available

```bash
# Verify MPS support
./venv/bin/python tests/validation/test_mps.py

# If MPS not available, training will use CPU (slower but works)
# Ensure you're on Apple Silicon (M1/M2/M3)
```

---

## File Structure After Completion

```
coffee-roasting/
├── data/
│   ├── raw/                               # Original recordings
│   │   └── roast-*.wav (4 files)
│   ├── labels/                            # Annotations
│   │   ├── labelstudio-export-*.json
│   │   └── roast-*.json (4 files)
│   ├── processed/                         # Audio chunks
│   │   ├── first_crack/*.wav (14 files)
│   │   ├── no_first_crack/*.wav (73 files)
│   │   └── processing_summary.md
│   ├── splits/                            # Train/val/test splits
│   │   ├── train/
│   │   │   ├── first_crack/ (9 files)
│   │   │   └── no_first_crack/ (51 files)
│   │   ├── val/
│   │   │   ├── first_crack/ (2 files)
│   │   │   └── no_first_crack/ (11 files)
│   │   ├── test/
│   │   │   ├── first_crack/ (3 files)
│   │   │   └── no_first_crack/ (11 files)
│   │   └── split_report.md
│   └── spectrograms/                      # Visualizations
│       └── *.png (3 files)
└── src/
    ├── data_prep/                         # Processing scripts
    │   ├── convert_labelstudio_export.py
    │   ├── audio_processor.py
    │   ├── dataset_splitter.py
    │   ├── verify_chunks.py
    │   ├── audio_dataset.py
    │   └── test_dataloader.py
    └── utils/
        └── visualize_spectrograms.py
```

---

## Dataset Statistics

After completing all steps, you should have:

| Metric | Value |
|--------|-------|
| Total audio chunks | 87 |
| First crack samples | 14 (16.1%) |
| No first crack samples | 73 (83.9%) |
| Train set | 60 samples (69.0%) |
| Validation set | 13 samples (14.9%) |
| Test set | 14 samples (16.1%) |
| Sample rate | 16kHz (resampled for AST) |
| Chunk duration | ~30s (variable) |
| Target length (training) | 10s (padded/truncated) |

---

## Re-running the Pipeline

### For New Recordings

1. Copy new WAV files to `data/raw/`
2. Start Label Studio and add files to project
3. Annotate new files
4. Re-export and re-convert (Steps 2-3)
5. Re-run audio processor (Step 4)
6. Re-run splitter (Step 5)

### For Updated Annotations

If you edit existing annotations in Label Studio:

1. Re-export from Label Studio
2. Re-run conversion (Step 3)
3. Re-run audio processor (Step 4)
4. Re-run splitter (Step 5)

**Note**: Re-running will overwrite existing chunks and splits!

---

## Validation Checklist

Before proceeding to training, verify:

- [ ] All 4 annotation JSON files created
- [ ] ~87 audio chunks extracted
- [ ] Processing summary looks correct
- [ ] Train/val/test splits created with balanced classes
- [ ] Chunk verification shows >90% success rate
- [ ] DataLoader test passes
- [ ] Data successfully moves to MPS device
- [ ] Spectrograms show clear differences between classes

---

## Next Steps

Once data preparation is complete:

1. **Model Implementation** (Milestone 4)
   - Select and load AST model
   - Configure for binary classification
   - Test forward pass

2. **Training Pipeline** (Milestone 5)
   - Implement training loop
   - Add logging and checkpointing
   - Run initial training

3. **Evaluation** (Milestone 6)
   - Test on held-out set
   - Generate performance metrics
   - Measure inference latency

---

## Related Documentation

- **Complete annotation workflow**: `docs/ANNOTATION_WORKFLOW.md`
- **Label Studio guide**: `tools/label-studio/LABEL_STUDIO_GUIDE.md`
- **Task validation**: `tests/VALIDATION.md`
- **Implementation plan**: `PHASE1_PLAN.md`

---

## Command Cheat Sheet

```bash
# Activate environment
source venv/bin/activate

# Start Label Studio
./venv/bin/label-studio start

# Convert annotations
./venv/bin/python src/data_prep/convert_labelstudio_export.py \
    --input data/labels/PROJECT-EXPORT.json --output data/labels

# Process chunks
./venv/bin/python src/data_prep/audio_processor.py

# Split dataset
./venv/bin/python src/data_prep/dataset_splitter.py

# Verify
./venv/bin/python src/data_prep/verify_chunks.py
./venv/bin/python src/data_prep/test_dataloader.py

# Visualize
./venv/bin/python src/utils/visualize_spectrograms.py
```

---

**Version**: 1.0  
**Status**: Milestones 1-3 Complete  
**Last Updated**: 2025-10-18
