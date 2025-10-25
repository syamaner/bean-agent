# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Quick commands

- Setup (Python 3.11 venv)
  - python3.11 -m venv venv
  - source venv/bin/activate
  - pip install --upgrade pip && pip install -r requirements.txt
- Verify environment
  - ./venv/bin/python --version  # expect 3.11.x
  - ./venv/bin/python tests/validation/test_mps.py  # check MPS on Apple Silicon
- Data preparation
  - Split dataset (stratified): ./venv/bin/python src/data_prep/dataset_splitter.py --input data/processed --output data/splits --train 0.7 --val 0.15 --test 0.15 --seed 42
  - Verify random chunks: ./venv/bin/python src/data_prep/verify_chunks.py --data data/processed --samples 10
  - Convert Label Studio export: ./venv/bin/python src/data_prep/convert_labelstudio_export.py --input data/labels/project-1-at-2025-10-18-20-44-9bc9cd1d.json --output data/labels --data-root data/raw
- Training
  - Single run (uses models/config.py defaults): ./venv/bin/python src/training/train.py --data-dir data/splits --experiment-name baseline_v1
  - Resume: ./venv/bin/python src/training/train.py --data-dir data/splits --resume experiments/runs/<exp>/checkpoints/best_model.pt
- Inference (offline, sliding window)
  - Single file: ./venv/bin/python src/training/inference.py --checkpoint experiments/final_model/model.pt --audio data/raw/roast-1-costarica-hermosa-hp-a.wav --window-size 10.0 --overlap 0.5 --threshold 0.5 --min-pops 3 --confirmation-window 30.0 --min-gap 10.0
  - Batch directory: ./venv/bin/python src/training/batch_inference.py --checkpoint experiments/final_model/model.pt --audio-dir data/raw --output-dir results
- Inference (streaming / MCP-oriented)
  - File-based detector: ./venv/bin/python src/inference/first_crack_detector.py --audio data/raw/roast-1-costarica-hermosa-hp-a.wav --checkpoint experiments/final_model/model.pt
  - Microphone detector: ./venv/bin/python src/inference/first_crack_detector.py --microphone --checkpoint experiments/final_model/model.pt
  - List audio devices: ./venv/bin/python -c "import sounddevice as sd; print(sd.query_devices())"
- Evaluation and packaging
  - Evaluate on test set: ./venv/bin/python src/training/evaluate.py --checkpoint experiments/final_model/model.pt --test-dir data/splits/test
  - Package deployment bundle: ./venv/bin/python src/training/package_model.py --checkpoint experiments/final_model/model.pt --output-dir experiments/final_model
- Tests
  - Run validation: ./venv/bin/python tests/validation/test_mps.py && ./venv/bin/python tests/validation/test_audio.py
  - Inference tests: ./venv/bin/python tests/inference/test_detector.py
  - Single “test”: run any script directly, e.g., ./venv/bin/python tests/validation/test_audio.py
- Lint/format
  - None configured in this repo.

## Codebase architecture (big picture)

- Data preparation (src/data_prep)
  - convert_labelstudio_export.py: Converts Label Studio export into per-file JSON annotations (preserves local filenames, computes durations at 44.1kHz).
  - dataset_splitter.py: Stratified split of labeled chunks into train/val/test under data/splits/(first_crack|no_first_crack).
  - audio_dataset.py: PyTorch Dataset that loads 16kHz mono, 10s windows; pads/truncates; exposes class weights and stats; create_dataloaders(...) builds torch DataLoaders.
  - verify_chunks.py: Random quality checks (duration, silence, clipping) across processed chunks.
- Model (src/models)
  - ast_model.py: FirstCrackClassifier wraps Hugging Face AST (MIT/ast-finetuned-audioset-10-10-0.4593). Uses ASTFeatureExtractor, returns logits; auto-selects device (MPS→CUDA→CPU). ModelInitConfig threads config through to set device and num_labels.
  - config.py: TRAINING_CONFIG defaults (batch size, LR, device='mps', sample_rate=16000, target_length_sec=10).
- Training and packaging (src/training)
  - train.py: Trainer orchestrates loop with class-weighted CrossEntropyLoss, AdamW, CosineAnnealingLR; logs to TensorBoard; early-stop by F1; writes checkpoints and config.json under experiments/runs/<exp>.
  - inference.py: SlidingWindowInference splits long audio into overlapping windows, scores with the model, and aggregates into DetectionEvent(s) using “pop-confirmation” logic (min_pops within a confirmation_window, gap merge, min duration). Prints and saves per-window probabilities and events.
  - batch_inference.py: Batch wrapper for inference.py across a directory; computes per-file and aggregate RTF; writes a JSON summary.
  - evaluate.py: Runs test-set evaluation with MetricsCalculator (accuracy/precision/recall/F1/ROC-AUC), prints classification report, saves confusion matrix plot and text results.
  - package_model.py: Builds deployment bundle (model.pt, config.json, model_info.json, README.md, DEPLOYMENT.md) into experiments/final_model/.
- Inference API for MCP (src/inference)
  - first_crack_detector.py: Threaded detector for either file-based or live microphone input using sounddevice. Sliding window over stream, pop-confirmation counter, is_first_crack() returns (True, "MM:SS") once confirmed. Designed to be owned by an MCP server process.
  - __init__.py: Exposes FirstCrackDetector.
- Utilities (src/utils)
  - metrics.py: Batches metric accumulation and reporting (per-class metrics, confusion matrix, ROC-AUC) and a quick batch accuracy helper.
- Experiments and evaluation
  - experiments/final_model/: Final packaged checkpoint and docs (README.md, DEPLOYMENT.md, example_inference.py).
  - evaluation/: Workflow and versioning docs; results/ and history/ for tracking metrics across runs.

## Pointers to key docs

- Project overview and setup: README.md (environment, phases, goals, known issues).
- Dev environment details: docs/DEVELOPMENT.md (venv usage, dependency workflow, troubleshooting).
- Sliding-window detector API and MCP usage: src/inference/README.md.
- Final model usage and deployment: experiments/final_model/README.md and DEPLOYMENT.md.
- Evaluation workflow and versioning: evaluation/WORKFLOW.md; tools/README.md for helper scripts.
