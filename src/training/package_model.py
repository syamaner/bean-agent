#!/usr/bin/env python3
"""
Package final model artifacts for deployment.

Creates a deployment-ready package with model, config, and documentation.
"""
import argparse
import shutil
import json
from pathlib import Path
from datetime import datetime

import torch


def package_model(
    checkpoint_path: Path,
    output_dir: Path,
    include_examples: bool = True
):
    """
    Package model for deployment.
    
    Creates a directory with:
    - Model checkpoint
    - Configuration
    - README with usage instructions
    - Example inference script
    """
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print("PACKAGING MODEL FOR DEPLOYMENT")
    print(f"{'='*70}\n")
    
    # Load checkpoint to extract config
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    config = checkpoint['config']
    
    print(f"Source checkpoint: {checkpoint_path}")
    print(f"Epoch: {checkpoint['epoch']}")
    print(f"Best val F1: {checkpoint.get('best_val_f1', 'N/A'):.4f}")
    print(f"Output directory: {output_dir}\n")
    
    # 1. Copy model checkpoint
    model_dest = output_dir / "model.pt"
    shutil.copy(checkpoint_path, model_dest)
    print(f"✅ Copied model checkpoint to {model_dest.name}")
    
    # 2. Save configuration as JSON
    config_dest = output_dir / "config.json"
    with open(config_dest, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✅ Saved configuration to {config_dest.name}")
    
    # 3. Create model info file
    info = {
        'model_name': 'FirstCrackDetector',
        'version': '1.0.0',
        'base_model': 'MIT/ast-finetuned-audioset-10-10-0.4593',
        'task': 'Binary classification (first_crack vs no_first_crack)',
        'training_date': datetime.now().isoformat(),
        'checkpoint_epoch': checkpoint['epoch'],
        'best_val_f1': float(checkpoint.get('best_val_f1', 0)),
        'best_val_accuracy': float(checkpoint.get('best_val_accuracy', 0)),
        'input_format': {
            'sample_rate': config['sample_rate'],
            'duration': f"{config['target_length_sec']}s",
            'channels': 'mono'
        },
        'output_format': {
            'num_classes': 2,
            'classes': ['no_first_crack', 'first_crack']
        }
    }
    
    info_dest = output_dir / "model_info.json"
    with open(info_dest, 'w') as f:
        json.dump(info, f, indent=2)
    print(f"✅ Saved model info to {info_dest.name}")
    
    # 4. Create README
    readme_content = f"""# First Crack Detection Model - Deployment Package

**Version**: 1.0.0  
**Created**: {datetime.now().strftime('%Y-%m-%d')}  
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

- **Sample Rate**: {config['sample_rate']} Hz
- **Audio Length**: {config['target_length_sec']} seconds per window
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
audio, sr = librosa.load('audio.wav', sr={config['sample_rate']}, mono=True)

# Pad/truncate to 10 seconds
target_length = {config['sample_rate']} * {config['target_length_sec']}
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
    
    print(f"Prediction: {{prediction.item()}}")  # 0 or 1
    print(f"Confidence: {{probs[0, prediction].item():.3f}}")
```

### Sliding Window Inference

For processing long audio files (full roasting sessions):

```bash
python inference.py \\
    --checkpoint model.pt \\
    --audio roast-session.wav \\
    --window-size 10.0 \\
    --overlap 0.5 \\
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
"""
    
    readme_dest = output_dir / "README.md"
    with open(readme_dest, 'w') as f:
        f.write(readme_content)
    print(f"✅ Created README.md")
    
    # 5. Copy example inference script if requested
    if include_examples:
        src_inference = Path(__file__).parent / "inference.py"
        if src_inference.exists():
            example_dest = output_dir / "example_inference.py"
            shutil.copy(src_inference, example_dest)
            print(f"✅ Copied example inference script")
    
    # Create deployment instructions
    deploy_instructions = """# Deployment Instructions

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
"""
    
    deploy_dest = output_dir / "DEPLOYMENT.md"
    with open(deploy_dest, 'w') as f:
        f.write(deploy_instructions)
    print(f"✅ Created DEPLOYMENT.md")
    
    print(f"\n{'='*70}")
    print("✅ PACKAGING COMPLETE!")
    print(f"{'='*70}")
    print(f"\nDeployment package created at: {output_dir}")
    print(f"\nPackage contents:")
    for item in sorted(output_dir.iterdir()):
        size = item.stat().st_size
        size_str = f"{size/1024/1024:.1f}MB" if size > 1024*1024 else f"{size/1024:.1f}KB"
        print(f"  - {item.name:<30} ({size_str})")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Package model artifacts for deployment"
    )
    parser.add_argument('--checkpoint', type=str, required=True,
                        help='Path to best model checkpoint')
    parser.add_argument('--output-dir', type=str, default='deployment_package',
                        help='Output directory for packaged model')
    parser.add_argument('--no-examples', action='store_true',
                        help='Skip including example scripts')
    
    args = parser.parse_args()
    
    checkpoint_path = Path(args.checkpoint)
    output_dir = Path(args.output_dir)
    
    if not checkpoint_path.exists():
        print(f"❌ Checkpoint not found: {checkpoint_path}")
        return 1
    
    package_model(
        checkpoint_path=checkpoint_path,
        output_dir=output_dir,
        include_examples=not args.no_examples
    )
    
    return 0


if __name__ == '__main__':
    exit(main())
