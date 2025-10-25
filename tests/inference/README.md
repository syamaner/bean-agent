# Inference Tests

Tests for the FirstCrackDetector inference pipeline.

## Test Scripts

### test_detector.py
Tests file-based inference with pre-recorded audio files.

**Usage:**
```bash
./venv/bin/python tests/inference/test_detector.py
```

**What it tests:**
- Loading audio files
- Model initialization and checkpoint loading
- File-based detection pipeline
- Background thread processing
- Detection timing and formatting

### test_microphone.py
Tests real-time microphone streaming with USB audio device.

**Usage:**
```bash
./venv/bin/python tests/inference/test_microphone.py
```

**What it tests:**
- USB microphone connectivity
- Real-time audio streaming
- Live inference processing
- Thread-safe buffer management
- Detection in streaming mode

## Running Tests

From project root:

```bash
# Test with audio file
./venv/bin/python tests/inference/test_detector.py

# Test with microphone (USB PnP Audio Device)
./venv/bin/python tests/inference/test_microphone.py
```

## Expected Results

### test_detector.py
- Should detect first crack around 08:30 in the test audio file
- Demonstrates successful file processing

### test_microphone.py
- Will run for 30 seconds listening to microphone
- May detect false positives from ambient noise (documented in MODEL_IMPROVEMENTS.md)
- Verifies microphone streaming is working correctly

## Notes

- Both tests use the model checkpoint at `experiments/final_model/model.pt`
- Tests require sounddevice package: `pip install sounddevice>=0.4.6`
- See `src/inference/README.md` for API documentation
