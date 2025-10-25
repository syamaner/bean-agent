# AST Base Model Selection

We evaluated candidate pretrained AST models for binary first-crack detection.

## Candidates
- MIT/ast-finetuned-audioset-10-10-0.4593
- MIT/ast-finetuned-speech-commands-v2

## Selection Criteria
- Pretrained on diverse, non-speech environmental sounds
- Strong transfer potential for non-verbal acoustic events (pops/cracks)
- Compatibility with 16 kHz sampling rate and 10s segments
- Availability in Hugging Face Transformers with ASTFeatureExtractor

## Decision
- Selected: MIT/ast-finetuned-audioset-10-10-0.4593
  - Trained on AudioSet (broad, environmental audio)
  - Good generalization to impulsive non-speech events similar to first crack
  - Seamless integration with Transformers API

## Initial Configuration
- Sampling rate: 16 kHz (feature extractor default)
- Input length: 10 seconds per sample (padded/truncated)
- Labels: {0: no_first_crack, 1: first_crack}

## Next Steps
- Validate baseline with small training run
- If overfitting or poor recall on first_crack, try alternative base models and/or stronger augmentation
