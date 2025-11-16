# Coffee Roasting

AI-assisted, autonomous coffee roasting with real-time first crack detection and hardware control for the Hottop KN8828B-2K+. This repository contains the ML model, MCP servers, and orchestration pieces needed to monitor a roast, adjust controls, and finish at a target development profile.

- First crack detection: Audio model (AST-based) that spots first crack in near real-time and reports the timestamp.
- Roaster control: MCP server that reads temperatures and adjusts heat/fan on a Hottop roaster (via serial/pyhottop).
- Agent/orchestration: Scripts and docs for running an autonomous agent and integrating with an orchestrator (e.g., .NET Aspire).

---

## Project status (high level)

- Phase 1 – Model training: complete; test accuracy ≈93% with 100% recall on first crack (limited data). See docs.
- Phase 2 – MCP servers (first-crack + roaster control): complete; ready for integration.
- Phase 3 – Agent/orchestration: complete; end-to-end flow documented.

For live microphone detection, see src/inference/README.md and src/inference/first_crack_detector.py.

Detailed phase docs live under docs/ (links below).
 
---

## What’s in this repo

- src/
  - data_prep/: dataset tools (converters, splitters, checks)
  - models/: AST wrapper and training config
  - training/: train/evaluate/inference/packaging scripts
  - inference/: streaming detector for file or microphone input
  - utils/: metrics and helpers
- experiments/
  - final_model/: packaged checkpoint and docs
- docs/
  - Phase overviews and architecture, setup, and testing guides

See docs/README.md for the full documentation index.

---

## Requirements (summary)

- Hardware: Hottop KN8828B-2K+ roaster; USB connection; external mic recommended.
- OS/Runtime: Python 3.11; PyTorch with MPS (Apple) or CUDA (NVIDIA) support.
- Audio: mono, 16 kHz–44.1 kHz WAV works; model code defaults to 16 kHz windows.

---

## How it works (short)

- Microphone audio is windowed (sliding), transformed to mel spectrograms, and scored by an AST classifier.
- The detector aggregates consecutive positives to confirm first crack and emits a timestamp.
- A roaster-control MCP server reads bean/chamber temps and adjusts heat/fan.
- An agent/orchestrator uses these signals to manage development time and decide the drop.

---

## Useful links

- Hottop KN8828B-2K+: https://www.hottopamericas.com/KN-8828B-2Kplus.html
- pyhottop library: https://github.com/splitkeycoffee/pyhottop
- Audio Spectrogram Transformer docs: https://huggingface.co/docs/transformers/en/model_doc/audio-spectrogram-transformer

Additional, deeper guides are in docs/: setup, testing, architecture, and per‑phase write‑ups.

---

## Safety and responsibility

This software can control a real coffee roaster. Use at your own risk. Always supervise roasts and be prepared to stop the process. Verify all configuration and hardware connections before enabling autonomous control.
