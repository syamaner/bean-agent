# Tests Directory

This directory contains test scripts for validating implementation tasks and testing code functionality.

## Purpose

This directory focuses on:
- **Task validation**: Verifying that Phase 1 implementation tasks are completed correctly
- **Unit tests**: Testing individual functions and classes
- **Integration tests**: Testing component interactions
- **Pipeline tests**: Verifying data processing workflows

**Note:** For model performance evaluation, see the `evaluation/` directory at the project root.

## Structure

```
tests/
├── validation/          # Validation tests for Phase 1 tasks
│   ├── test_mps.py     # Verify MPS (Apple Silicon GPU) support
│   └── test_audio.py   # Test audio loading with librosa
├── VALIDATION.md        # Task validation guide
└── README.md           # This file
```

## Task Validation

Validation tests verify that each milestone task has been completed correctly. See `VALIDATION.md` for detailed instructions on running these tests.

### Quick Start

Run all validation tests for Milestone 1:
```bash
./venv/bin/python tests/validation/test_mps.py
./venv/bin/python tests/validation/test_audio.py
```

## Future Tests

As the project progresses, additional test categories will be added:

- **Unit tests** - Test individual functions and classes
- **Integration tests** - Test component interactions
- **Model tests** - Validate model training and inference
- **Pipeline tests** - End-to-end workflow validation
