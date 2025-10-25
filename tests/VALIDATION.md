# Task Validation Guide

This document provides instructions for validating that Phase 1 implementation tasks are completed correctly using test scripts in `validation/`.

**Note:** This is for implementation task validation. For model performance evaluation and metrics tracking, see the `evaluation/` directory at the project root.

---

## Milestone 1: Project Setup & Environment

### Task 1.1: Create Project Directory Structure

**Validation Command:**
```bash
find . -type d -maxdepth 3 | grep -E "data|src|tools|experiments" | sort
```

**Expected Output:**
```
./data
./data/labels
./data/processed
./data/processed/first_crack
./data/processed/no_first_crack
./data/raw
./data/splits
./data/splits/test
./data/splits/train
./data/splits/val
./experiments
./experiments/runs
./src
./src/data_prep
./src/models
./src/training
./src/utils
./tools
```

**Success Criteria:** All directories present

---

### Task 1.2: Set Up Python Virtual Environment

**Validation Commands:**
```bash
# Check virtual environment exists
ls -la venv/

# Check Python version in venv
./venv/bin/python --version

# Check pip version
./venv/bin/pip --version
```

**Expected Output:**
- Python 3.11.x
- pip 25.2 or higher

**Success Criteria:** Virtual environment created with Python 3.11

---

### Task 1.3: Install Dependencies

**Validation Command:**
```bash
./venv/bin/pip list | grep -E "torch|transformers|librosa|numpy|pandas|matplotlib|scikit-learn|tensorboard"
```

**Expected Output:**
```
librosa                 0.11.0
matplotlib              3.10.x
numpy                   2.3.x
pandas                  2.3.x
scikit-learn            1.7.x
tensorboard             2.20.x
torch                   2.9.0
torchaudio              2.9.0
transformers            4.57.x
```

**Success Criteria:** All required packages installed

---

### Task 1.4: Verify MPS Support

**Validation Script:** `validation/test_mps.py`

**Run Command:**
```bash
./venv/bin/python tests/validation/test_mps.py
```

**Expected Output:**
```
PyTorch version: 2.9.0
MPS available: True
MPS built: True
MPS computation successful!
Result shape: torch.Size([100, 100])
Device: mps:0
```

**Success Criteria:** 
- MPS available: True
- MPS built: True
- Computation completes without errors

---

### Task 1.5: Test Basic Audio Loading

**Validation Script:** `validation/test_audio.py`

**Run Command:**
```bash
./venv/bin/python tests/validation/test_audio.py
```

**Expected Output:**
```
Loading: ../../data/raw/roast-1-costarica-hermosa-hp-a.wav

Audio loaded successfully!
Sample rate: 44100Hz
Audio shape: (28211611,)
Duration: 639.72 seconds
Data type: float32
Min value: -1.0000
Max value: 1.0000
Mean value: -0.0000
```

**Success Criteria:**
- Audio loads without errors
- Sample rate: 44100Hz
- Duration: ~10-11 minutes (typical roast time)
- Data type: float32
- Values normalized between -1.0 and 1.0

---

## Milestone 2: Manual Data Preparation

### Task 2.1: Create Annotation JSON Schema

**Validation Command:**
```bash
cat data/labels/schema.json
cat data/labels/template.json
```

**Success Criteria:** Both schema and template files exist and are valid JSON

---

### Task 2.2: Listen and Identify First Crack

**Manual Task:** No automated validation

**Checklist:**
- [ ] All 4 WAV files copied to `data/raw/`
- [ ] First crack timestamps identified for each file
- [ ] Timestamps documented in `data/labels/first_crack_notes.txt`

---

### Task 2.3: Generate Annotation Files

**Validation Command:**
```bash
ls -la data/labels/*.json | grep roast
```

**Expected Output:**
```
roast-1-costarica-hermosa-hp-a.json
roast-2-costarica-hermosa-hp-a.json
roast-3-costarica-hermosa-hp-a.json
roast-4-costarica-hermosa-hp-a.json
```

**Success Criteria:** 4 JSON annotation files created, one for each recording

---

## Running All Validations

To run all automated validation tests:

```bash
# Milestone 1 validations
echo "=== Task 1.1: Directory Structure ==="
find . -type d -maxdepth 3 | grep -E "data|src|tools|experiments" | sort

echo "\n=== Task 1.2: Virtual Environment ==="
./venv/bin/python --version
./venv/bin/pip --version

echo "\n=== Task 1.3: Dependencies ==="
./venv/bin/pip list | grep -E "torch|transformers|librosa"

echo "\n=== Task 1.4: MPS Support ==="
./venv/bin/python tests/validation/test_mps.py

echo "\n=== Task 1.5: Audio Loading ==="
./venv/bin/python tests/validation/test_audio.py
```

---

## Adding New Validation Tests

When creating new validation tests:

1. Create test script in `tests/validation/`
2. Use descriptive naming: `test_<feature>.py`
3. Add documentation to this file with:
   - Task number and name
   - Run command
   - Expected output
   - Success criteria
4. Update the "Running All Validations" section

---

## Troubleshooting

### MPS Not Available
- Ensure you're running on Apple Silicon (M1/M2/M3)
- Update macOS to latest version
- Reinstall PyTorch: `pip install --upgrade torch`

### Audio Loading Fails
- Check file exists: `ls -la data/raw/`
- Verify file format: `file data/raw/*.wav`
- Install additional audio codecs if needed

### Dependencies Missing
- Activate virtual environment: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

---

**Last Updated:** 2025-10-18
