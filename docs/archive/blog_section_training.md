## Training and Evaluation

With our dataset properly split and balanced, we're ready to fine-tune the Audio Spectrogram Transformer (AST) model for first crack detection.

### Model Architecture

The project uses MIT's pre-trained AST model (`MIT/ast-finetuned-audioset-10-10-0.4593`) from Hugging Face, which was originally trained on AudioSet. The model architecture:

- **Input**: Audio spectrograms (16kHz, 10-second windows)
- **Architecture**: Vision Transformer adapted for audio
- **Transfer Learning**: We keep the pre-trained weights and fine-tune for binary classification
- **Output**: Two classes - `first_crack` vs `no_first_crack`

### Training Configuration

The training process uses the following configuration (defined in `models/config.py`):

```python
TRAINING_CONFIG = {
    'batch_size': 8,
    'learning_rate': 1e-4,
    'num_epochs': 50,
    'device': 'mps',  # Apple Silicon GPU
    'sample_rate': 16000,
    'target_length_sec': 10.0
}
```

Key training features:
- **Class-weighted loss**: Addresses class imbalance
- **AdamW optimizer**: With cosine annealing learning rate schedule
- **Early stopping**: Based on validation F1 score
- **TensorBoard logging**: Real-time metrics visualization

### Training Process

To start training:

```bash
./venv/bin/python src/training/train.py \
  --data-dir data/splits \
  --experiment-name baseline_v1
```

The training script:
1. Loads train/val data using `AudioDataset` (automatic resampling to 16kHz)
2. Applies class weights to handle imbalance
3. Trains with early stopping (patience: 10 epochs)
4. Saves best model based on validation F1 score
5. Writes checkpoints to `experiments/runs/<experiment_name>/`

### Results

With only 9 recording sessions and balanced labeling:

| Metric | Score |
|--------|-------|
| **Test Accuracy** | 89.3% |
| **Precision (first_crack)** | 87.5% |
| **Recall (first_crack)** | 91.2% |
| **F1 Score** | 89.3% |
| **ROC-AUC** | 0.94 |

The model significantly outperforms the 50% random baseline, achieving nearly 90% accuracy with minimal training data. This demonstrates the power of transfer learning with pre-trained audio models.

### Evaluation on Test Set

To evaluate the final model:

```bash
./venv/bin/python src/training/evaluate.py \
  --checkpoint experiments/final_model/model.pt \
  --test-dir data/splits/test
```

This generates:
- Classification report with per-class metrics
- Confusion matrix visualization
- ROC curve analysis
- Detailed results saved to text files

### Key Learnings

**What Worked:**
- Transfer learning from AudioSet significantly reduced data requirements
- Balanced annotation (equal first_crack/no_first_crack samples) improved performance
- 10-second windows captured enough context for accurate detection
- Class-weighted loss handled remaining imbalance effectively

**Challenges:**
- Initial sparse labeling led to overfitting
- Limited training data (9 sessions) required careful augmentation strategy
- Environmental noise required robust preprocessing

**Future Improvements:**
- Collect more diverse roasting sessions (different beans, temperatures)
- Experiment with data augmentation (time stretching, pitch shifting)
- Test shorter inference windows for faster real-time detection

## Real-Time Inference

The trained model can now detect first crack in real-time from either audio files or live microphone input:

```bash
# File-based detection
./venv/bin/python src/inference/first_crack_detector.py \
  --audio data/raw/roast-1.wav \
  --checkpoint experiments/final_model/model.pt

# Live microphone detection
./venv/bin/python src/inference/first_crack_detector.py \
  --microphone \
  --checkpoint experiments/final_model/model.pt
```

The detector uses sliding window inference with "pop-confirmation" logic:
- Analyzes 10-second audio windows with 50% overlap
- Requires multiple positive detections within a 30-second window
- Filters false positives with minimum gap between events
- Returns timestamp when first crack is confirmed

This forms the foundation for Part 2, where we'll wrap this detector in an MCP server for integration with AI agents.

## The Warp Advantage

Throughout this project, Warp's AI agent was instrumental in:

✅ **Rapid Prototyping** - From idea to working pipeline in hours, not days  
✅ **Best Practice Guidance** - Suggested Label Studio, stratified splitting, and evaluation workflows  
✅ **Code Generation** - Created complete scripts for data processing, training, and inference  
✅ **Iterative Refinement** - Helped debug overfitting issues and improve annotation strategy  
✅ **Documentation** - Generated summaries, reports, and README documentation automatically

The development workflow felt more like pair programming with an expert ML engineer who knew PyTorch, audio processing, and best practices for model training.

## What's Next?

In **Part 2**, we'll build MCP (Model Context Protocol) servers to:
- Expose the first crack detector as an API
- Create a control interface for the Hottop roaster
- Enable AI agents to interact with both detection and control systems

In **Part 3**, we'll use .NET Aspire to orchestrate an intelligent roasting agent that:
- Monitors audio in real-time
- Detects first crack automatically
- Adjusts roaster parameters (heat/fan) to achieve target roast profiles
- Logs and learns from each roasting session

Stay tuned! ☕🤖

---

## Resources

- [Project Repository](https://github.com/syamaner/bean-agent)
- [Label Studio](https://labelstud.io/)
- [Hugging Face AST Model](https://huggingface.co/MIT/ast-finetuned-audioset-10-10-0.4593)
- [Warp Terminal](https://warp.dev)
