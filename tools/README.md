# Tools Directory

This directory contains tools, configurations, and research documentation for the coffee-roasting project.

## Structure

```
tools/
├── label-studio/                   # Label Studio audio annotation tool
│   ├── LABEL_STUDIO_GUIDE.md      # Complete guide for using Label Studio
│   ├── label-studio-config.xml    # Annotation interface configuration
│   └── import-tasks.json          # Pre-configured import file for 4 audio files
├── create_eval_version.py         # Create versioned evaluation directories
├── update_performance_history.py  # Update performance history CSV
├── ANNOTATION_TOOLS_RESEARCH.md   # Research on audio annotation tools
└── README.md                      # This file
```

## Label Studio

Label Studio is our chosen tool for annotating audio files to identify first crack events.

### Quick Start

```bash
# Start Label Studio
./venv/bin/label-studio start
```

Then follow the guide in `label-studio/LABEL_STUDIO_GUIDE.md`.

### Files

- **LABEL_STUDIO_GUIDE.md**: Complete walkthrough including:
  - Setup instructions
  - Annotation workflow
  - Export process
  - Keyboard shortcuts
  - Troubleshooting

- **label-studio-config.xml**: Labeling interface configuration
  - Defines audio player with waveform
  - Sets up two labels: `first_crack` (red) and `no_first_crack` (blue)
  - Enables zoom and speed controls

- **import-tasks.json**: Pre-configured JSON for importing all 4 audio files
  - Contains absolute paths to WAV files
  - Ready to upload in Label Studio

## Evaluation Versioning

Tools for tracking evaluation results across model iterations.

### create_eval_version.py

Create a new versioned directory for evaluation results with metadata tracking.

```bash
python tools/create_eval_version.py \
    --name "hp_tuning_lr_001" \
    --model-path "experiments/runs/v2" \
    --changes "Reduced learning rate to 0.001" \
    --hp-changes "lr: 0.01 → 0.001" \
    --training-samples 8
```

Creates: `evaluation/results/YYYYMMDD_name/metadata.json`

**Tracks:**
- Model architecture changes
- Hyperparameter modifications
- Data additions (new recordings, annotations)
- Git commit hash
- What changed from previous version

### update_performance_history.py

Append evaluation metrics to the historical performance CSV.

```bash
python tools/update_performance_history.py \
    --version 20251019_hp_tuning_lr_001 \
    --accuracy 0.97 \
    --precision 0.96 \
    --recall 0.98 \
    --f1 0.97 \
    --training-samples 8 \
    --notes "Improved recall"
```

See `evaluation/WORKFLOW.md` for complete workflow.

## Annotation Tools Research

See `ANNOTATION_TOOLS_RESEARCH.md` for:
- Comparison of 7 audio annotation tools
- Evaluation criteria and scoring
- Decision rationale for choosing Label Studio
- Alternative approaches for future use

## Future Tools

As the project progresses, additional tools may be added:
- Custom preprocessing scripts
- Data augmentation utilities
- Model deployment tools
- Monitoring and logging utilities
- Performance comparison visualizations

---

**Last Updated**: 2025-10-18
