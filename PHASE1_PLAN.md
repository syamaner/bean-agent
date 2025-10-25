# Phase 1 Implementation Plan: Audio Model Training

## Overview
This document outlines the detailed implementation plan for Phase 1: Fine-tuning an Audio Spectrogram Transformer to detect first crack in coffee roasting.

**Current Status**: 🟢 Training Complete - Ready for Deployment Prep  
**Last Updated**: 2025-10-18

---

## Milestones

### M1: Project Setup & Environment ✅
- [x] 1.1 Create project directory structure
- [x] 1.2 Set up Python virtual environment
- [x] 1.3 Install dependencies
- [x] 1.4 Verify MPS (Metal Performance Shaders) support on M3 Max
- [x] 1.5 Test basic audio loading with librosa

### M2: Data Annotation with Label Studio ✅
- [x] 2.1 Set up Label Studio annotation project
- [x] 2.2 Import 4 WAV files into Label Studio
- [x] 2.3 Annotate audio files (identify first crack regions)
- [x] 2.4 Export annotations from Label Studio (JSON)
- [x] 2.5 Convert Label Studio JSON to our format
- [x] 2.6 Process annotations into audio chunks
- [x] 2.7 Verify audio chunks quality (listen to samples)

### M3: Dataset Creation ✅
- [x] 3.1 Implement balanced train/val/test splitter
- [x] 3.2 Create dataset statistics report
- [x] 3.3 Implement PyTorch Dataset class for AST
- [x] 3.4 Test data loading pipeline
- [x] 3.5 Verify spectrogram generation

### M4: Model Implementation ✅
- [x] 4.1 Research and select best AST base model (see docs/MODEL_SELECTION.md)
- [x] 4.2 Implement AST model wrapper for binary classification (src/models/ast_model.py)
- [x] 4.3 Test model loading and forward pass (script added: src/models/test_model.py)
- [x] 4.4 Configure training hyperparameters (src/models/config.py)
- [x] 4.5 Implement data augmentation strategies (src/data_prep/augmentations.py)

### M5: Training Pipeline ✅
- [x] 5.1 Implement training loop with MPS support
- [x] 5.2 Add logging and checkpointing
- [x] 5.3 Implement evaluation metrics (accuracy, precision, recall, F1)
- [x] 5.4 Run initial training experiment
- [x] 5.5 Analyze results and tune hyperparameters

### M6: Evaluation & Testing ✅
- [x] 6.1 Implement comprehensive evaluation script
- [x] 6.2 Generate confusion matrix and classification report
- [x] 6.3 Measure inference latency
- [x] 6.4 Test on held-out test set
- [x] 6.5 Document model performance

### M7: Inference & Deployment Prep ✅
- [x] 7.1 Implement sliding window inference
- [x] 7.2 Create real-time audio processing script
- [x] 7.3 Test with raw audio files from data/raw (modified from live mic)
- [x] 7.4 Optimize inference speed
- [x] 7.5 Save final model artifacts

### M8: Annotation Tool Setup ✅
- [x] 8.1 Research existing audio annotation tools
- [x] 8.2 Evaluate and select Label Studio
- [x] 8.3 Install Label Studio
- [x] 8.4 Create annotation configuration
- [x] 8.5 Document Label Studio workflow

### M9: Re-annotation and Model Refinement ⚪
- [x] 9.1 Update annotation guidelines to event detection approach
- [ ] 9.2 Re-annotate existing audio files with event detection
- [ ] 9.3 Export and convert new annotations
- [ ] 9.4 Re-process audio chunks (1-5 second events)
- [ ] 9.5 Recreate dataset splits
- [ ] 9.6 Update model configuration for shorter inputs
- [ ] 9.7 Update data augmentation strategy
- [ ] 9.8 Retrain model with event-based data
- [ ] 9.9 Analyze model performance and iterate on hyperparameters
- [ ] 9.10 Update inference pipeline for discrete event detection
- [ ] 9.11 Document event detection approach


---

## Detailed Task Breakdown

## Milestone 1: Project Setup & Environment

### Task 1.1: Create Project Directory Structure
**Description**: Set up the complete folder structure for code, data, and experiments.

**Structure**:
```
coffee-roasting/
├── data/
│   ├── raw/
│   ├── processed/
│   │   ├── first_crack/
│   │   └── no_first_crack/
│   ├── labels/
│   └── splits/
│       ├── train/
│       ├── val/
│       └── test/
├── src/
│   ├── data_prep/
│   ├── models/
│   ├── training/
│   └── utils/
├── tools/
├── experiments/
│   └── runs/
├── requirements.txt
└── PHASE1_PLAN.md
```

**Commands**:
```bash
mkdir -p data/{raw,processed/{first_crack,no_first_crack},labels,splits/{train,val,test}}
mkdir -p src/{data_prep,models,training,utils}
mkdir -p tools experiments/runs
```

**Success Criteria**: All directories created and visible in repository.

---

### Task 1.2: Set Up Python Virtual Environment
**Description**: Create isolated Python environment for the project.

**Commands**:
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

**Success Criteria**: Virtual environment activated, pip upgraded to latest version.

---

### Task 1.3: Install Dependencies
**Description**: Install all required Python packages.

**Create requirements.txt**:
```
torch>=2.1.0
torchaudio>=2.1.0
transformers>=4.35.0
librosa>=0.10.0
soundfile>=0.12.0
numpy>=1.24.0
pandas>=2.0.0
matplotlib>=3.7.0
seaborn>=0.12.0
scikit-learn>=1.3.0
tensorboard>=2.14.0
tqdm>=4.66.0
pydub>=0.25.0
```

**Commands**:
```bash
pip install -r requirements.txt
```

**Success Criteria**: All packages installed without errors.

---

### Task 1.4: Verify MPS Support
**Description**: Confirm PyTorch can use Apple Silicon GPU acceleration.

**Test Script** (`test_mps.py`):
```python
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"MPS available: {torch.backends.mps.is_available()}")
print(f"MPS built: {torch.backends.mps.is_built()}")

if torch.backends.mps.is_available():
    device = torch.device("mps")
    x = torch.randn(100, 100).to(device)
    y = torch.randn(100, 100).to(device)
    z = x @ y
    print("MPS computation successful!")
```

**Success Criteria**: Script runs without errors and confirms MPS is available.

---

### Task 1.5: Test Basic Audio Loading
**Description**: Verify librosa can load and process audio files.

**Test Script** (`test_audio.py`):
```python
import librosa
import numpy as np

# Create a test audio file or use sample
audio_path = "data/raw/sample.wav"  # Replace with actual file
audio, sr = librosa.load(audio_path, sr=44100, mono=True)
print(f"Audio loaded: {audio.shape} samples at {sr}Hz")
print(f"Duration: {len(audio)/sr:.2f} seconds")
```

**Success Criteria**: Can load audio files at 44.1kHz sample rate.

---

## Milestone 2: Data Annotation with Label Studio

### Task 2.1: Set Up Label Studio Annotation Project
**Description**: Launch Label Studio and create audio annotation project.

**Commands**:
```bash
# Start Label Studio
./venv/bin/label-studio start
```

**Steps**:
1. Browser opens to http://localhost:8080
2. Create account (first time only - local credentials)
3. Click "Create Project"
4. Project Name: `Coffee Roast First Crack Detection`
5. Description: `Annotating first crack events in coffee roasting audio`

**Reference**: See `tools/label-studio/LABEL_STUDIO_GUIDE.md` for detailed instructions

**Success Criteria**: Label Studio running, project created.

---

### Task 2.2: Import 4 WAV Files into Label Studio
**Description**: Import audio files into Label Studio for annotation.

**Method A - Upload Files**:
1. In project, go to "Data Import" tab
2. Click "Upload Files"
3. Select all 4 WAV files from `data/raw/`

**Method B - Import JSON** (Recommended for large files):
1. Use pre-created `tools/label-studio/import-tasks.json`
2. In project: Data Import → Upload JSON
3. Select `import-tasks.json`

**Configure Labeling Interface**:
1. Go to Settings → Labeling Interface
2. Click "Code" view
3. Copy/paste from `tools/label-studio/label-studio-config.xml`
4. Click "Save"

**Success Criteria**: All 4 audio files imported, labeling interface configured.

---

### Task 2.3: Annotate Audio Files
**Description**: Listen to recordings and mark first crack regions in Label Studio.

**Annotation Strategy**:

For each ~10-minute roast file:

1. **Quick listen**: Play entire file, identify approximate first crack time
2. **Pre-crack sections** (0 to FC - 1 min):
   - Create 30-second regions labeled `no_first_crack`
3. **First crack section** (±2 min around FC):
   - Create precise regions labeled `first_crack` during active cracking
   - Create `no_first_crack` regions between pops
4. **Post-crack sections** (FC + 1 min to end):
   - Create 30-second regions labeled `no_first_crack`

**Expected Output**: 15-25 labeled regions per file

**Workflow**:
1. Click on audio file
2. Click and drag on waveform to select region
3. Click label: `first_crack` (red) or `no_first_crack` (blue)
4. Add optional notes if needed
5. Click "Submit"
6. Repeat for next file

**Keyboard Shortcuts**:
- Space: Play/Pause
- Ctrl/Cmd + Enter: Submit
- Use zoom for precise timing

**Success Criteria**: All 4 files annotated with labeled regions.

---

### Task 2.4: Export Annotations from Label Studio
**Description**: Export completed annotations in JSON format.

**Steps**:
1. Go to project page
2. Click "Export" button
3. Select "JSON" format
4. Download file
5. Save to: `data/labels/labelstudio-export.json`

**Backup**:
```bash
cp data/labels/labelstudio-export.json data/labels/labelstudio-export-$(date +%Y%m%d).json
```

**Success Criteria**: JSON export file downloaded and saved.

---

### Task 2.5: Convert Label Studio JSON to Our Format
**Description**: Convert Label Studio export to our standardized annotation format.

**Script**: `src/data_prep/convert_labelstudio_export.py`

```python
"""
Convert Label Studio JSON export to our annotation format
"""
import json
import librosa
from pathlib import Path

def convert_labelstudio_to_annotations(labelstudio_json_path, output_dir):
    """
    Convert Label Studio export to individual annotation files
    
    Args:
        labelstudio_json_path: Path to Label Studio JSON export
        output_dir: Directory to save converted annotations
    """
    with open(labelstudio_json_path, 'r') as f:
        ls_data = json.load(f)
    
    for task in ls_data:
        audio_file = Path(task['data']['audio']).name
        audio_path = Path('data/raw') / audio_file
        
        # Get audio duration
        duration = librosa.get_duration(path=str(audio_path))
        
        # Extract annotations
        annotations = []
        if task.get('annotations'):
            for ann in task['annotations'][0]['result']:
                if ann['type'] == 'labels':
                    annotations.append({
                        'id': f"chunk_{len(annotations):03d}",
                        'start_time': ann['value']['start'],
                        'end_time': ann['value']['end'],
                        'label': ann['value']['labels'][0],
                        'confidence': 'high'
                    })
        
        # Create our format
        output = {
            'audio_file': audio_file,
            'duration': duration,
            'sample_rate': 44100,
            'annotations': annotations
        }
        
        # Save
        output_path = Path(output_dir) / f"{Path(audio_file).stem}.json"
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Converted: {audio_file} → {output_path}")

if __name__ == '__main__':
    convert_labelstudio_to_annotations(
        'data/labels/labelstudio-export.json',
        'data/labels'
    )
```

**Run**:
```bash
python src/data_prep/convert_labelstudio_export.py
```

**Success Criteria**: 4 annotation JSON files created in `data/labels/`.

---

### Task 2.6: Process Annotations into Audio Chunks
**Description**: Create script to split audio files into chunks based on annotations, then process all recordings.

**Script**: `src/data_prep/audio_processor.py`

**Key Functions**:
- `load_audio(path, sr=44100)` - Load audio file
- `extract_chunk(audio, start, end, sr)` - Extract time segment
- `save_chunk(audio, path, sr)` - Save audio chunk
- `process_annotations(annotation_file)` - Process all chunks from annotations

**Command**:
```bash
python src/data_prep/audio_processor.py --annotations data/labels/
```

**Expected Output**:
- Audio chunks saved in `data/processed/first_crack/` and `data/processed/no_first_crack/`
- Summary report showing:
  - Total chunks created
  - Number of first_crack vs no_first_crack
  - Duration distribution

**Success Criteria**: All chunks created, roughly balanced labels.

---

### Task 2.7: Verify Audio Chunks Quality
**Description**: Manual quality check of processed chunks.

**Process**:
1. Randomly sample 10 chunks from each category
2. Listen to verify labels are correct
3. Check audio quality (no clipping, correct duration)
4. Document any issues

**Success Criteria**: >95% of samples correctly labeled.

---

## Milestone 3: Dataset Creation

### Task 3.1: Implement Balanced Splitter
**Description**: Create train/val/test splits with balanced class distribution.

**Script**: `src/data_prep/dataset_splitter.py`

**Requirements**:
- 70% train, 15% validation, 15% test
- Each split maintains same class ratio
- Stratified split to ensure balance
- Random seed for reproducibility

**Success Criteria**: Split created, all chunks distributed to train/val/test directories.

---

### Task 3.2: Create Dataset Statistics Report
**Description**: Generate comprehensive statistics about the dataset.

**Script**: `src/data_prep/dataset_stats.py`

**Output Metrics**:
- Total samples per split
- Class distribution per split
- Audio duration statistics
- Sample rate consistency check
- File size distribution

**Output**: `data/dataset_report.md`

**Success Criteria**: Report generated with all statistics.

---

### Task 3.3: Implement PyTorch Dataset Class
**Description**: Create custom Dataset for loading and preprocessing audio.

**Script**: `src/data_prep/audio_dataset.py`

```python
class FirstCrackDataset(torch.utils.data.Dataset):
    """
    Dataset for first crack detection using AST
    """
    def __init__(self, data_dir, transform=None):
        # Load file paths and labels
        pass
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        # Load audio
        # Convert to spectrogram
        # Apply transforms
        # Return (spectrogram, label)
        pass
```

**Success Criteria**: Dataset can load samples and return preprocessed data.

---

### Task 3.4: Test Data Loading Pipeline
**Description**: Verify DataLoader works correctly with batching.

**Test Script**: `src/data_prep/test_dataloader.py`
```python
from torch.utils.data import DataLoader
from audio_dataset import FirstCrackDataset

# Test loading
dataset = FirstCrackDataset("data/splits/train")
loader = DataLoader(dataset, batch_size=8, shuffle=True)

for batch in loader:
    inputs, labels = batch
    print(f"Batch shape: {inputs.shape}, Labels: {labels.shape}")
    break
```

**Success Criteria**: Can iterate through batches without errors.

---

### Task 3.5: Verify Spectrogram Generation
**Description**: Visually inspect spectrograms to ensure quality.

**Script**: `src/utils/visualize_spectrograms.py`
- Load sample from each class
- Generate and display spectrogram
- Save visualization for review

**Success Criteria**: Spectrograms look correct, show expected frequency patterns.

---

## Milestone 4: Model Implementation

### Task 4.1: Research AST Base Models
**Description**: Evaluate available pretrained AST models on HuggingFace.

**Options to Consider**:
- `MIT/ast-finetuned-audioset-10-10-0.4593`
- `MIT/ast-finetuned-speech-commands-v2`
- Other audio classification models

**Criteria**:
- Pretrained on relevant audio tasks
- Good transfer learning potential
- Compatible with our input format

**Output**: Document model selection rationale

**Success Criteria**: Best model identified and documented.

---

### Task 4.2: Implement AST Model Wrapper
**Description**: Create wrapper for binary classification with AST.

**Script**: `src/models/ast_model.py`

```python
from transformers import ASTForAudioClassification, ASTFeatureExtractor

class FirstCrackClassifier:
    def __init__(self, model_name, num_labels=2):
        self.feature_extractor = ASTFeatureExtractor.from_pretrained(model_name)
        self.model = ASTForAudioClassification.from_pretrained(
            model_name,
            num_labels=num_labels,
            ignore_mismatched_sizes=True
        )
    
    def forward(self, audio):
        # Process audio through model
        pass
```

**Success Criteria**: Model can be instantiated and run forward pass.

---

### Task 4.3: Test Model Loading
**Description**: Verify model loads and runs on MPS device.

**Test**: Load model, move to MPS, run dummy forward pass

**Success Criteria**: Model runs on GPU without errors, produces output.

---

### Task 4.4: Configure Training Hyperparameters
**Description**: Define initial training configuration.

**File**: `src/models/config.py`

```python
TRAINING_CONFIG = {
    "batch_size": 8,
    "learning_rate": 5e-5,
    "num_epochs": 20,
    "warmup_steps": 100,
    "weight_decay": 0.01,
    "max_grad_norm": 1.0,
    "device": "mps",
    "seed": 42
}
```

**Success Criteria**: Config file created with reasonable initial values.

---

### Task 4.5: Implement Data Augmentation
**Description**: Add audio augmentation strategies.

**Augmentations**:
- Time stretching (0.9x - 1.1x)
- Pitch shifting (±2 semitones)
- Background noise addition
- Volume adjustment

**Script**: `src/data_prep/augmentations.py`

**Success Criteria**: Augmentations implemented and tested.

---

## Milestone 5: Training Pipeline

### Task 5.1: Implement Training Loop
**Description**: Create main training script with MPS support.

**Script**: `src/training/train.py`

**Features**:
- Training loop with progress bars
- Validation after each epoch
- Model checkpointing (best and latest)
- Learning rate scheduling
- Early stopping
- TensorBoard logging

**Success Criteria**: Can run training for multiple epochs, saves checkpoints.

---

### Task 5.2: Add Logging and Checkpointing
**Description**: Implement comprehensive logging system.

**Logging**:
- TensorBoard for metrics visualization
- Console logging for progress
- JSON file for experiment tracking

**Checkpoint Strategy**:
- Save best model (highest val accuracy)
- Save every N epochs
- Save final model
- Include optimizer state

**Success Criteria**: All logs and checkpoints saved correctly.

---

### Task 5.3: Implement Evaluation Metrics
**Description**: Add custom metrics for binary classification.

**Script**: `src/utils/metrics.py`

**Metrics**:
- Accuracy
- Precision
- Recall
- F1-Score
- Confusion Matrix
- ROC-AUC

**Success Criteria**: All metrics calculated correctly during validation.

---

### Task 5.4: Run Initial Training
**Description**: Execute first training run with baseline config.

**Command**:
```bash
python src/training/train.py \
    --config src/models/config.py \
    --experiment baseline_v1
```

**Monitor**:
- Training loss decreasing
- Validation metrics improving
- No overfitting (train vs val gap)
- GPU utilization

**Success Criteria**: Training completes, model saved, metrics logged.

---

### Task 5.5: Analyze and Tune
**Description**: Review results and adjust hyperparameters.

**Analysis**:
- Plot training curves
- Review confusion matrix
- Identify failure cases
- Adjust hyperparameters if needed

**Iterations**: Run 2-3 experiments with different configs

**Success Criteria**: Achieve >90% validation accuracy.

---

## Milestone 6: Evaluation & Testing

### Task 6.1: Implement Evaluation Script
**Description**: Create comprehensive evaluation tool.

**Script**: `src/training/evaluate.py`

**Outputs**:
- Classification report
- Confusion matrix visualization
- Per-class metrics
- ROC curve
- Precision-Recall curve

**Success Criteria**: Evaluation runs on test set, generates all reports.

---

### Task 6.2: Generate Performance Reports
**Description**: Create detailed performance analysis.

**Command**:
```bash
python src/training/evaluate.py \
    --model experiments/runs/baseline_v1/best_model.pt \
    --test-data data/splits/test \
    --output experiments/runs/baseline_v1/evaluation_report.md
```

**Success Criteria**: Complete report with visualizations generated.

---

### Task 6.3: Measure Inference Latency
**Description**: Benchmark model inference speed.

**Script**: `src/training/benchmark.py`

**Measurements**:
- Time per sample
- Throughput (samples/second)
- Memory usage
- Compare CPU vs MPS

**Target**: <500ms per 30-second chunk

**Success Criteria**: Latency meets target, documented in report.

---

### Task 6.4: Test on Held-Out Set
**Description**: Final validation on completely unseen test data.

**Process**:
1. Load best model
2. Run inference on test set
3. Calculate all metrics
4. Compare to validation performance

**Success Criteria**: Test performance within 5% of validation performance.

---

### Task 6.5: Document Model Performance
**Description**: Create final model card and documentation.

**Document**: `experiments/runs/baseline_v1/MODEL_CARD.md`

**Contents**:
- Model architecture
- Training data details
- Performance metrics
- Limitations and biases
- Intended use
- Example usage

**Success Criteria**: Complete documentation for model deployment.

---

## Milestone 7: Inference & Deployment Prep

### Task 7.1: Implement Sliding Window Inference
**Description**: Create real-time inference with overlapping windows.

**Script**: `src/training/inference.py`

**Strategy**:
- 30-second windows
- 15-second overlap (50%)
- Aggregate predictions
- Smooth predictions over time

**Success Criteria**: Can process long audio files, detect first crack events.

---

### Task 7.2: Create Real-Time Audio Script
**Description**: Process audio from file or microphone in real-time.

**Script**: `src/training/realtime_inference.py`

**Features**:
- Load audio file or stream from mic
- Buffer audio chunks
- Run inference continuously
- Display predictions with timestamps

**Success Criteria**: Can detect first crack in real-time with <2s latency.

---

### Task 7.3: Test with Live Microphone
**Description**: Validate with live audio input.

**Requirements**:
- USB microphone connected
- PyAudio or sounddevice for capture
- Real-time processing

**Success Criteria**: Successfully detects audio events from live mic.

---

### Task 7.4: Optimize Inference Speed
**Description**: Profile and optimize inference performance.

**Optimizations**:
- Model quantization (if needed)
- Batch processing
- Reduce input resolution (if acceptable)
- Cache model on GPU

**Success Criteria**: Meet <2s latency requirement consistently.

---

### Task 7.5: Save Final Model Artifacts
**Description**: Export model for production use.

**Outputs**:
- Best checkpoint
- Feature extractor config
- Preprocessing parameters
- Inference example code
- Model card

**Location**: `experiments/final_model/`

**Success Criteria**: All artifacts saved, model can be loaded independently.

---

## Milestone 8: Automation & Tooling (Optional)

### Task 8.1: Research Annotation Tools
**Description**: Survey existing audio annotation tools.

**Tools to Evaluate**:
- Audacity (with labels)
- Label Studio
- Praat
- Audio Annotation Tool (MIT)
- Custom web apps

**Criteria**:
- Easy to use
- Export to JSON
- Waveform visualization
- Support for time ranges

**Success Criteria**: Document findings, recommend tool or custom build.

---

### Task 8.2: Evaluate Tool Suitability
**Description**: Test recommended tool with sample data.

**Process**:
1. Install/setup tool
2. Load sample audio
3. Test annotation workflow
4. Export data
5. Verify compatibility with our format

**Decision**: Use existing tool OR build custom solution

**Success Criteria**: Clear decision documented.

---

### Task 8.3: Design Custom Tool (If Needed)
**Description**: Design UI/UX for custom annotation tool.

**Stack**:
- Backend: FastAPI
- Frontend: React + Wavesurfer.js
- Database: SQLite for annotations

**Features**:
- Upload audio files
- Visualize waveform
- Select time ranges
- Assign labels
- Play selected regions
- Export to JSON

**Success Criteria**: Design documented, wireframes created.

---

### Task 8.4: Implement Annotation Tool (If Needed)
**Description**: Build custom audio labeling application.

**Components**:
1. Backend API for audio management
2. Frontend UI with waveform viewer
3. Annotation storage
4. Export functionality

**Success Criteria**: Tool works end-to-end for annotation workflow.

---

### Task 8.5: Test Tool with New Recordings
**Description**: Validate tool with fresh audio data.

**Process**:
1. Record new roasting session
2. Use tool to annotate
3. Export annotations
4. Process through training pipeline

**Success Criteria**: New data successfully labeled and processed.

---

## Milestone 9: Re-annotation and Model Refinement ⚪

### Task 9.1: Update Annotation Guidelines ✅
**Description**: Revise annotation strategy from phase-based to event detection approach.

**Changes Made**:
- Updated `tools/label-studio/LABEL_STUDIO_GUIDE.md` with event detection strategy
- Updated `docs/ANNOTATION_WORKFLOW.md` with detailed event-based workflow
- Changed from 30-second chunks to individual crack events (1-3 seconds)
- Implemented sparse negative sampling (3-5 segments per pre-crack period)

**Success Criteria**: ✅ Documentation updated with clear event detection guidelines.

---

### Task 9.2: Re-annotate Existing Audio Files ⚪
**Description**: Re-annotate all 4 audio files using the new event detection approach.

**Process**:
1. Start Label Studio and open existing project
2. For each audio file:
   - Delete old phase-based annotations
   - Apply new event detection strategy:
     - **Pre-crack** (0-8 min): 3-5 sparse negative samples (~5 sec each)
     - **First crack events**: Mark each individual crack (1-3 sec each)
     - **Post-crack**: 2-3 sparse negative samples (~5 sec each)
3. Expected output per file:
   - Pre-crack negative samples: 3-5 regions
   - First crack events: 15-30 regions
   - Post-crack negative samples: 2-3 regions
   - Total: ~20-40 regions per file

**Commands**:
```bash
# Start Label Studio
./venv/bin/label-studio start

# After re-annotation, export
# Project → Export → JSON
# Save as: data/labels/project-1-event-detection-YYYYMMDD.json
```

**Reference**: See `docs/ANNOTATION_WORKFLOW.md` section 5.2 for detailed strategy.

**Success Criteria**: All 4 files re-annotated using event detection approach.

---

### Task 9.3: Export and Convert New Annotations ⚪
**Description**: Export re-annotated data and convert to our format.

**Commands**:
```bash
# Export from Label Studio (via UI)
# Then convert
./venv/bin/python src/data_prep/convert_labelstudio_export.py \
    --input data/labels/project-1-event-detection-YYYYMMDD.json \
    --output data/labels \
    --data-root data/raw

# Backup old annotations
mv data/labels/roast-*.json data/labels/archive/phase-based/

# New event-based annotations will be in data/labels/
```

**Verification**:
```bash
# Check annotation statistics
./venv/bin/python -c "
import json
from pathlib import Path

for f in sorted(Path('data/labels').glob('roast-*.json')):
    d = json.load(f.open())
    anns = d['annotations']
    fc = [a for a in anns if a['label']=='first_crack']
    nfc = [a for a in anns if a['label']=='no_first_crack']
    print(f'=== {f.name} ===')
    print(f'Total regions: {len(anns)}')
    print(f'  - first_crack (events): {len(fc)}')
    print(f'  - no_first_crack (samples): {len(nfc)}')
    if fc:
        fc_start = min(a['start_time'] for a in fc)
        avg_fc_duration = sum(a['end_time']-a['start_time'] for a in fc)/len(fc)
        print(f'First crack starts: {fc_start:.1f}s')
        print(f'Avg event duration: {avg_fc_duration:.1f}s')
    print()
"
```

**Success Criteria**: 
- 4 new annotation JSON files created
- Statistics show event-based structure (short first_crack regions, sparse no_first_crack)

---

### Task 9.4: Re-process Audio Chunks ⚪
**Description**: Re-run audio processing with new event-based annotations.

**Commands**:
```bash
# Backup old chunks
mv data/processed/first_crack data/processed/archive/first_crack_phase_based
mv data/processed/no_first_crack data/processed/archive/no_first_crack_phase_based

# Recreate directories
mkdir -p data/processed/first_crack
mkdir -p data/processed/no_first_crack

# Process new annotations
python src/data_prep/audio_processor.py --annotations data/labels/
```

**Expected Changes**:
- **first_crack chunks**: Should be 1-3 seconds each (shorter than before)
- **no_first_crack chunks**: Should be ~5 seconds each (shorter than 30-second phase chunks)
- **Total chunks**: Similar or slightly more than before
- **Class distribution**: May shift (more precise crack events, fewer background samples)

**Verification**:
```bash
# Check new chunk statistics
ls data/processed/first_crack/*.wav | wc -l
ls data/processed/no_first_crack/*.wav | wc -l

# Listen to random samples
python src/data_prep/sample_chunks.py --num-samples 10
```

**Success Criteria**: 
- New chunks created with event-based durations
- Quality check: >95% of first_crack chunks contain actual crack sounds

---

### Task 9.5: Recreate Dataset Splits ⚪
**Description**: Regenerate train/val/test splits with new chunks.

**Commands**:
```bash
# Backup old splits
mv data/splits data/splits_archive_phase_based

# Recreate split directories
mkdir -p data/splits/{train,val,test}

# Run splitter
python src/data_prep/dataset_splitter.py \
    --input data/processed \
    --output data/splits \
    --train-ratio 0.70 \
    --val-ratio 0.15 \
    --test-ratio 0.15 \
    --seed 42

# Generate new dataset report
python src/data_prep/dataset_stats.py \
    --splits-dir data/splits \
    --output data/dataset_report_event_based.md
```

**Success Criteria**: New splits created, report shows event-based statistics.

---

### Task 9.6: Update Model Configuration for Event Detection ⚪
**Description**: Adjust model and training config for shorter audio chunks.

**Changes Needed**:
1. **Input duration**: Event chunks are 1-5 seconds (vs previous 30 seconds)
2. **Model architecture**: May need to adjust for shorter sequences
3. **Batch size**: Can potentially increase (smaller inputs)
4. **Augmentation**: Review time-stretch/pitch-shift ranges for short events

**File**: `src/models/config.py`

**Update Config**:
```python
TRAINING_CONFIG = {
    # Model settings
    "model_name": "MIT/ast-finetuned-audioset-10-10-0.4593",
    "num_labels": 2,
    
    # Audio settings - UPDATED for event detection
    "sample_rate": 44100,
    "target_duration": 3.0,  # 3 seconds (was 30)
    "max_duration": 5.0,     # Max chunk length
    
    # Training hyperparameters
    "batch_size": 16,        # Increased from 8 (smaller inputs)
    "learning_rate": 5e-5,
    "num_epochs": 25,        # May need more epochs (harder task)
    "warmup_steps": 100,
    "weight_decay": 0.01,
    "max_grad_norm": 1.0,
    
    # Augmentation - UPDATED for short events
    "augmentations": {
        "time_stretch": (0.95, 1.05),  # Reduced range (was 0.9-1.1)
        "pitch_shift": 1,              # Reduced (was ±2 semitones)
        "background_noise": 0.005,     # Lower noise for short events
        "volume_range": (0.8, 1.2),
    },
    
    # Training settings
    "device": "mps",
    "seed": 42,
    "early_stopping_patience": 5,
}
```

**Review**:
- Consider if AST architecture handles very short inputs well
- May need to pad short clips to minimum duration
- Document rationale for changes

**Success Criteria**: Config updated and documented.

---

### Task 9.7: Update Data Augmentation Strategy ⚪
**Description**: Adjust augmentations for short event-based clips.

**File**: `src/data_prep/augmentations.py`

**Key Changes**:
1. **Reduced time stretch**: 0.95-1.05x (was 0.9-1.1x)
   - Reason: Don't distort short crack sounds too much
2. **Minimal pitch shift**: ±1 semitone (was ±2)
   - Reason: Preserve crack sound characteristics
3. **Lower background noise**: Reduce intensity
   - Reason: Don't mask the crack sound in short clips
4. **Add random silence padding**: For variable-length inputs

**New Augmentation**: Event-specific
```python
def augment_crack_event(audio, sr):
    """
    Augmentation specifically for crack event clips
    """
    # Random time shift within clip
    # Careful not to cut off the crack
    pass
```

**Testing**:
```bash
# Test augmentations on sample clips
python src/data_prep/test_augmentations.py \
    --input data/processed/first_crack \
    --output experiments/augmentation_samples

# Listen to augmented samples
```

**Success Criteria**: Augmentations preserve crack sound characteristics.

---

### Task 9.8: Retrain Model with Event-Based Data ⚪
**Description**: Train new model using event detection annotations.

**Commands**:
```bash
# Run training with updated config
python src/training/train.py \
    --config src/models/config.py \
    --experiment event_detection_v1 \
    --data-dir data/splits \
    --output experiments/runs/event_detection_v1

# Monitor training
tensorboard --logdir experiments/runs/event_detection_v1/logs
```

**Expected Differences from Phase-Based**:
- **Task difficulty**: Likely harder (detecting short events vs. phases)
- **Accuracy target**: May be lower initially (~85-90% vs. 95%+)
- **Class balance**: May need adjustment
- **Training time**: Potentially longer (more challenging task)

**Monitor**:
- Training/validation loss curves
- Class-wise accuracy (precision/recall per class)
- Confusion matrix patterns
- False positive rate (critical for real-time use)

**Success Criteria**: 
- Model trains without errors
- Achieves >85% validation accuracy
- False positive rate <10%

---

### Task 9.9: Analyze Model Performance and Iterate ⚪
**Description**: Evaluate event detection model and tune hyperparameters.

**Evaluation**:
```bash
# Run comprehensive evaluation
python src/training/evaluate.py \
    --model experiments/runs/event_detection_v1/best_model.pt \
    --test-data data/splits/test \
    --output experiments/runs/event_detection_v1/evaluation_report.md
```

**Analysis Questions**:
1. Is the model detecting individual crack events?
2. What's the false positive rate on background/pre-crack samples?
3. Are there specific types of cracks it misses (faint, rapid succession)?
4. How does performance compare to phase-based approach?

**Hyperparameter Tuning**:
If performance is below target, iterate on:
- Learning rate (try 3e-5 or 1e-4)
- Batch size (try 8 or 32)
- Model architecture (try different AST variants)
- Input duration (pad to 5 seconds uniform?)
- Data augmentation intensity
- Class weights (if imbalanced)

**Experiments to Try**:
```bash
# Experiment 2: Different learning rate
python src/training/train.py \
    --config src/models/config_lr3e5.py \
    --experiment event_detection_v2_lr3e5

# Experiment 3: Uniform padding to 5 seconds
python src/training/train.py \
    --config src/models/config_pad5s.py \
    --experiment event_detection_v3_pad5s
```

**Success Criteria**: 
- 2-3 training experiments completed
- Best model achieves >90% accuracy
- False positive rate <5%
- Performance documented and compared

---

### Task 9.10: Update Inference Pipeline for Event Detection ⚪
**Description**: Adapt real-time inference to detect discrete crack events.

**File**: `src/training/inference.py`

**Changes Needed**:
1. **Sliding window**: Use smaller windows (5-second with 2.5-second overlap)
2. **Event detection**: Flag windows with positive predictions as events
3. **Temporal filtering**: Avoid duplicate detections for same crack
4. **Event timestamps**: Report precise crack timing

**New Strategy**:
```python
def detect_crack_events(audio_file, model, threshold=0.5, min_gap=1.0):
    """
    Detect individual crack events in audio file
    
    Args:
        audio_file: Path to audio file
        model: Trained event detection model
        threshold: Confidence threshold for positive detection
        min_gap: Minimum seconds between events (avoid duplicates)
    
    Returns:
        List of (timestamp, confidence) tuples for detected cracks
    """
    # Sliding window inference
    # Post-process: non-maximum suppression to remove duplicates
    # Return discrete event list
    pass
```

**Testing**:
```bash
# Test on original audio files
python src/training/inference.py \
    --model experiments/runs/event_detection_v1/best_model.pt \
    --audio data/raw/roast-1-costarica-hermosa-hp-a.wav \
    --output experiments/inference_results/roast-1-events.json

# Compare detected events to ground truth annotations
python src/utils/compare_predictions.py \
    --predictions experiments/inference_results/roast-1-events.json \
    --ground-truth data/labels/roast-1-costarica-hermosa-hp-a.json
```

**Success Criteria**:
- Inference detects discrete crack events (not continuous predictions)
- Event timestamps are accurate (within ±1 second of ground truth)
- No duplicate detections for same crack

---

### Task 9.11: Document Event Detection Approach ⚪
**Description**: Create comprehensive documentation of event detection methodology.

**Documents to Create/Update**:

1. **Model Card**: `experiments/runs/event_detection_v1/MODEL_CARD.md`
   - Approach: Event detection vs. phase detection
   - Architecture and hyperparameters
   - Performance metrics
   - Limitations

2. **Training Report**: `experiments/runs/event_detection_v1/TRAINING_REPORT.md`
   - Data annotation strategy
   - Model configuration
   - Training process and iterations
   - Results comparison (event vs. phase based)

3. **Inference Guide**: `docs/INFERENCE_GUIDE.md`
   - How to use event detection model
   - Interpreting results
   - Tuning threshold for false positive/negative trade-off

**Success Criteria**: Complete documentation for event detection approach.

---

## Success Criteria Summary

### Phase 1 Complete When:
- ✅ Dataset of labeled audio chunks created from 4 recordings
- ✅ AST model fine-tuned with >95% accuracy on test set (phase-based)
- ✅ Inference latency <2 seconds for 30-second chunks
- ✅ False positive rate <5%
- ✅ Real-time inference script working with live microphone
- ✅ Complete documentation and model artifacts saved
- ✅ Reproducible training pipeline established

### Phase 1 Refinement Complete When:
- ⚪ Re-annotation with event detection approach (Milestone 9)
- ⚪ Event-based model trained with >90% accuracy
- ⚪ False positive rate <5% for event detection
- ⚪ Discrete crack event detection working in inference
- ⚪ Performance comparison documented (event vs. phase based)

---

## Risk Mitigation

### Risk: Insufficient Training Data
**Mitigation**: 
- Use aggressive data augmentation
- Consider pretrained model with minimal fine-tuning
- Collect more recordings in parallel

### Risk: MPS Compatibility Issues
**Mitigation**: 
- Test MPS early (Task 1.4)
- Have CPU fallback option
- Use Ubuntu + RTX4090 if needed

### Risk: Poor Model Performance
**Mitigation**:
- Try multiple base models
- Adjust chunk duration and overlap
- Review annotation quality
- Collect more diverse data

### Risk: Real-Time Latency Too High
**Mitigation**:
- Use smaller model variant
- Optimize preprocessing
- Consider model quantization
- Batch process windows

---

## Next Steps After Phase 1

1. **Data Collection**: Record 10+ more roasting sessions for expanded dataset
2. **Model Improvement**: Retrain with larger dataset
3. **Phase 2 Prep**: Design MCP tools architecture
4. **Integration Testing**: Test model with pyhottop library

---

## Resources & References

- [HuggingFace AST Documentation](https://huggingface.co/docs/transformers/en/model_doc/audio-spectrogram-transformer)
- [PyTorch MPS Backend](https://pytorch.org/docs/stable/notes/mps.html)
- [Audio Data Augmentation Techniques](https://pytorch.org/audio/stable/transforms.html)
- [librosa Documentation](https://librosa.org/doc/latest/index.html)

---

## Progress Tracking

**Legend**: ✅ Complete | 🟡 In Progress | ⚪ Not Started | 🔴 Blocked

Update this document as tasks are completed and new insights are gained.
