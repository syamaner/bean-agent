# Model Improvement Roadmap

## Current Issues

### False Positive Detection (2025-10-18)

**Observation:**
During microphone testing with the `FirstCrackDetector` class, the model detected "first crack" at 00:12 when no coffee roasting was occurring. This indicates the model is picking up ambient sounds (voices, typing, background noise) as first crack events.

**Impact:**
- False positives during actual roasting could lead to incorrect timing decisions
- Premature adjustment of roast parameters (heat/fan)
- Suboptimal roast development time

**Root Cause:**
The current model (trained on limited data) may not sufficiently distinguish between:
- Actual first crack popping sounds (rapid, sharp, popcorn-like)
- Ambient environmental sounds (voices, keyboard, room noise)
- Other non-roasting audio events

## Recommended Improvements

### 1. Expand Training Dataset

**Priority: HIGH**

- Collect more labeled roast sessions with clear first crack annotations
- Include negative examples:
  - Pre-roast ambient sounds (microphone near roaster but not roasting)
  - Room noise, conversations, equipment sounds
  - Post-first-crack sounds (second crack, cooling phase)
- Aim for balanced dataset:
  - 50% first crack samples
  - 50% negative samples (no first crack, ambient noise, other roast phases)

**Action Items:**
- [ ] Record 10+ additional roast sessions
- [ ] Record 5+ "noise only" sessions (microphone positioned as during roast, but no roasting)
- [ ] Label existing data more precisely
- [ ] Create dedicated "false positive" training category

### 2. Feature Engineering

**Priority: MEDIUM**

- Enhance audio features to better capture first crack characteristics:
  - Temporal patterns (rapid succession of pops)
  - Frequency characteristics (sharp, high-frequency transients)
  - Intensity patterns (distinctive volume/energy profile)
- Consider additional input features:
  - Bean temperature (from roaster sensor) - first crack typically occurs 190-205°C
  - Time since roast start - first crack unlikely before 6-8 minutes
  - Rate of rise - temperature change patterns

### 3. Multi-Modal Approach

**Priority: MEDIUM**

Combine audio detection with contextual data:
```python
detection_confidence = (
    audio_model_confidence * 0.6 +
    temperature_in_range * 0.2 +  # 190-205°C
    time_window_check * 0.2        # 6-12 min since start
)
```

This would require integration with roaster sensor data (already planned for MCP architecture).

### 4. Adjust Detection Thresholds

**Priority: LOW** (Quick fix, but doesn't address root cause)

Current settings:
- `threshold = 0.5` (classification threshold)
- `min_pops = 3` (minimum positive windows)
- `confirmation_window = 30.0s` (time window for counting pops)

Consider more conservative settings:
- `threshold = 0.7` (higher confidence required)
- `min_pops = 5` (more confirmations needed)
- `confirmation_window = 20.0s` (tighter time window)

**Trade-off:** May increase false negatives (missed first crack)

### 5. Add Confidence Levels

**Priority: MEDIUM**

Instead of binary detection, provide confidence levels:
- **High confidence** (>0.8): Very likely first crack
- **Medium confidence** (0.5-0.8): Possible first crack, monitor closely
- **Low confidence** (<0.5): Unlikely first crack

This allows the orchestrator/MCP server to make more nuanced decisions.

### 6. Post-Processing Filters

**Priority: MEDIUM**

Add additional validation logic:
```python
def validate_detection(timestamp, bean_temp, time_since_start, audio_pattern):
    """Additional checks before confirming first crack."""
    
    # Must be within typical first crack temperature range
    if not (190 <= bean_temp <= 210):
        return False
    
    # Must be after minimum roast time
    if time_since_start < 360:  # 6 minutes
        return False
    
    # Must show sustained pattern (not single spike)
    if audio_pattern.duration < 10:  # seconds
        return False
    
    return True
```

## Implementation Plan

### Phase 1: Immediate (This Week)
- [ ] Document current false positive rate
- [ ] Test with different threshold settings
- [ ] Record ambient "noise only" samples

### Phase 2: Short-term (Next 2 Weeks)
- [ ] Collect 5+ new roast sessions with careful labeling
- [ ] Retrain model with expanded dataset
- [ ] Implement confidence levels in detector

### Phase 3: Medium-term (Next Month)
- [ ] Integrate temperature/time contextual data
- [ ] Implement multi-modal detection approach
- [ ] Build comprehensive validation pipeline

### Phase 4: Long-term (Future)
- [ ] Explore advanced architectures (temporal models, attention mechanisms)
- [ ] Build automated evaluation pipeline
- [ ] Continuous model improvement based on production data

## Evaluation Metrics

Track these metrics for each model version:

- **Precision**: What % of detections are true first crack? (Target: >95%)
- **Recall**: What % of actual first cracks are detected? (Target: >98%)
- **False Positive Rate**: Detections when not roasting (Target: <2%)
- **Detection Latency**: Time from actual first crack to detection (Target: <10s)

## Testing Protocol

Before deploying any model update:

1. **Ambient Noise Test** (like today's test)
   - Run detector for 5 minutes with no roasting
   - Should have ZERO detections

2. **Historical Data Test**
   - Test on all labeled roast sessions
   - Verify detection timing matches labels

3. **Live Roast Test**
   - Use during actual roast with manual observation
   - Compare detection time to manual observation

## Notes

- Current model checkpoint: `experiments/final_model/model.pt`
- Training data: 4 roast sessions from Costa Rica Hermosa HP-A
- Model architecture: Audio Spectrogram Transformer (AST)
- Sample rate: 16kHz

## Related Files

- Model implementation: `src/models/ast_model.py`
- Inference pipeline: `src/inference/first_crack_detector.py`
- Training script: `src/training/train.py`
- Evaluation: `src/training/evaluate.py`
