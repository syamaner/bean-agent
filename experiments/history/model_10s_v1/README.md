# First Crack Detection Model - Deployment Package

**Version**: 1.0.0  
**Created**: 2025-10-18  
**Base Model**: MIT Audio Spectrogram Transformer

## Model Description

This model detects first crack events in coffee roasting audio. It's a fine-tuned
Audio Spectrogram Transformer (AST) trained on coffee roasting sound recordings.

## Performance

- **Test Accuracy**: 92.86%
- **Test F1 Score**: 85.71%
- **Test Recall (first_crack)**: 100% ✨
- **Inference Speed**: ~87x real-time on M3 Max (MPS)

## Input Format

- **Sample Rate**: 16000 Hz
- **Audio Length**: 10 seconds per window
- **Channels**: Mono
- **Format**: WAV (recommended)

## Output Format

- **Classes**: 
  - 0: no_first_crack
  - 1: first_crack
- **Output**: Logits [batch, 2] or probabilities after softmax

## Files in This Package

- `model.pt`: Model checkpoint with trained weights
- `config.json`: Training configuration
- `model_info.json`: Model metadata
- `README.md`: This file
- `example_inference.py`: Example inference script (if included)

## Usage

### Basic Inference

```python
import torch
from pathlib import Path

# Load checkpoint
checkpoint = torch.load('model.pt', map_location='cpu')
config = checkpoint['config']

# Create model (requires FirstCrackClassifier class)
from models.ast_model import FirstCrackClassifier, ModelInitConfig

device = 'mps' if torch.backends.mps.is_available() else 'cpu'
model_config = ModelInitConfig(device=device)
model = FirstCrackClassifier(model_config)
model.load_state_dict(checkpoint['model_state_dict'])
model.to(device)
model.eval()

# Process audio (10s window at 16kHz)
import librosa
audio, sr = librosa.load('audio.wav', sr=16000, mono=True)

# Pad/truncate to 10 seconds
target_length = 16000 * 10
if len(audio) < target_length:
    audio = np.pad(audio, (0, target_length - len(audio)))
else:
    audio = audio[:target_length]

# Run inference
with torch.inference_mode():
    audio_tensor = torch.FloatTensor(audio).unsqueeze(0).to(device)
    logits = model(audio_tensor)
    probs = torch.softmax(logits, dim=-1)
    prediction = torch.argmax(probs, dim=-1)
    
    print(f"Prediction: {prediction.item()}")  # 0 or 1
    print(f"Confidence: {probs[0, prediction].item():.3f}")
```

### Sliding Window Inference

For processing long audio files (full roasting sessions):

```bash
python inference.py \
    --checkpoint model.pt \
    --audio roast-session.wav \
    --window-size 10.0 \
    --overlap 0.5 \
    --threshold 0.5
```

This will process the audio with overlapping windows and detect first crack events.

## Requirements

```
torch>=2.1.0
transformers>=4.35.0
librosa>=0.10.0
numpy>=1.24.0
```

## Model Architecture

- **Base**: Audio Spectrogram Transformer (AST)
- **Parameters**: ~86M
- **Input**: Mel spectrogram (extracted by ASTFeatureExtractor)
- **Output**: Binary classification logits

## Training Details

- **Dataset**: 87 samples (14 first_crack, 73 no_first_crack)
- **Training samples**: 60 (9/51 split)
- **Validation samples**: 13 (2/11 split)
- **Test samples**: 14 (3/11 split)
- **Epochs**: 2 (early stopping)
- **Optimizer**: AdamW
- **Learning rate**: 5e-5
- **Batch size**: 8
- **Class weights**: [0.59, 3.33] to handle imbalance

## Limitations

- Trained on limited dataset (87 samples from 4 roasting sessions)
- All training data from same coffee origin (Costa Rica Hermosa HP)
- May not generalize well to different roaster types or environments
- Best performance with similar audio conditions as training data

## Recommended Use

1. Use sliding window inference for full roasting sessions
2. Apply 50% overlap between windows for better temporal resolution
3. Aggregate consecutive positive predictions for robust detection
4. Consider using threshold tuning based on your false positive tolerance

## License

Model weights are provided for research and development purposes.

## Contact

For questions or issues, refer to the project documentation.
