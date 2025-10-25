# Deployment Instructions

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install torch transformers librosa numpy
   ```

2. **Copy required files**:
   - `model.pt` - Model checkpoint
   - `config.json` - Configuration
   - Your inference code or `example_inference.py`

3. **Run inference**:
   ```bash
   python example_inference.py --checkpoint model.pt --audio sample.wav
   ```

## Integration with Roasting System

To integrate with the roasting control system:

1. Load model once at startup (cache in memory)
2. Process audio in real-time using sliding windows
3. Detect first crack event when consecutive windows show positive predictions
4. Trigger roasting control adjustments based on detection

## Performance Optimization

- Use MPS (Metal) on Mac M-series chips for GPU acceleration
- Process in batches if handling multiple streams
- Consider model quantization for CPU-only deployment
- Cache the model in memory, don't reload per inference

## Monitoring

- Log detection timestamps and confidence scores
- Track false positive/negative rates during actual roasts
- Collect feedback to improve model with additional training data
