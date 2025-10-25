# Phase 1: Model Training

Training an audio classification model to detect coffee first crack.

## Overview

Phase 1 focused on building and training a neural network to detect the "first crack" event during coffee roasting from audio recordings.

**Status**: ✅ COMPLETE

## Results

- **Model**: Audio Spectrogram Transformer (AST)
- **Accuracy**: 93% on test set
- **Checkpoint**: `experiments/runs/10s_70overlap_v1/checkpoints/best_model.pt`
- **Real-world validation**: Successfully detected first crack at 08:06 in test roast

## Documentation

- [Model Selection](model-selection.md) - Why we chose AST
- [Model Improvements](model-improvements.md) - Optimization journey
- [Data Preparation](data-preparation.md) - Dataset creation workflow
- [Annotation Workflow](annotation-workflow.md) - Label Studio setup

## Key Achievements

1. ✅ Collected and labeled roasting audio dataset
2. ✅ Fine-tuned AST model on first crack sounds
3. ✅ Built inference pipeline with sliding window detection
4. ✅ Implemented pop-confirmation logic (min 3 pops in 30s window)
5. ✅ Packaged model for deployment

---

**Completed**: October 2025  
**Next Phase**: [Phase 2 - MCP Servers](../02-phase-2/)
