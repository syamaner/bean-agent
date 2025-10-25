#!/usr/bin/env python3
"""
Sliding window inference for first crack detection on continuous audio.

Processes long audio files with overlapping windows to detect first crack events.
"""
import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
from datetime import timedelta

import torch
import librosa
import numpy as np
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.ast_model import FirstCrackClassifier, ModelInitConfig


@dataclass
class DetectionEvent:
    """Represents a detected first crack event."""
    start_time: float  # seconds
    end_time: float  # seconds
    confidence: float  # probability
    window_index: int


class SlidingWindowInference:
    """
    Sliding window inference for first crack detection.
    
    Processes long audio files by splitting into overlapping windows
    and aggregating predictions.
    """
    
    def __init__(
        self,
        model: FirstCrackClassifier,
        window_size: float = 10.0,  # seconds
        overlap: float = 0.7,  # 70% overlap for better responsiveness
        threshold: float = 0.5,  # classification threshold
        sample_rate: int = 16000
    ):
        self.model = model
        self.window_size = window_size
        self.overlap = overlap
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.window_samples = int(window_size * sample_rate)
        self.hop_samples = int(self.window_samples * (1 - overlap))
        
        self.model.eval()
    
    def load_audio(self, audio_path: Path) -> Tuple[np.ndarray, float]:
        """Load audio file and return waveform and duration."""
        print(f"Loading audio from: {audio_path}")
        audio, sr = librosa.load(audio_path, sr=self.sample_rate, mono=True)
        duration = len(audio) / sr
        print(f"  Duration: {duration:.2f}s ({timedelta(seconds=int(duration))})")
        print(f"  Sample rate: {sr} Hz")
        print(f"  Samples: {len(audio):,}")
        return audio, duration
    
    def create_windows(self, audio: np.ndarray) -> List[Tuple[int, np.ndarray]]:
        """
        Split audio into overlapping windows.
        
        Returns:
            List of (start_sample, window_audio) tuples
        """
        windows = []
        start = 0
        
        while start + self.window_samples <= len(audio):
            window = audio[start:start + self.window_samples]
            windows.append((start, window))
            start += self.hop_samples
        
        # Handle last window if there's remaining audio
        if start < len(audio):
            # Pad the last window
            remaining = audio[start:]
            if len(remaining) > self.window_samples * 0.5:  # Only if >50% of window
                padded = np.pad(remaining, (0, self.window_samples - len(remaining)))
                windows.append((start, padded))
        
        return windows
    
    @torch.inference_mode()
    def predict_windows(
        self, 
        windows: List[Tuple[int, np.ndarray]]
    ) -> List[Tuple[int, float, np.ndarray]]:
        """
        Run inference on all windows.
        
        Returns:
            List of (start_sample, first_crack_prob, logits) tuples
        """
        predictions = []
        
        print(f"\nProcessing {len(windows)} windows...")
        for start_sample, window in tqdm(windows, desc="Inference"):
            # Convert to tensor and add batch dimension
            audio_tensor = torch.FloatTensor(window).unsqueeze(0)
            
            # Forward pass
            logits = self.model(audio_tensor)
            probs = torch.softmax(logits, dim=-1)
            
            # Get first_crack probability (class index 1)
            first_crack_prob = probs[0, 1].item()
            
            predictions.append((start_sample, first_crack_prob, probs[0].cpu().numpy()))
        
        return predictions
    
    def aggregate_predictions(
        self,
        predictions: List[Tuple[int, float, np.ndarray]],
        min_duration: float = 2.0,  # seconds
        min_pops: int = 3,
        confirmation_window: float = 30.0,  # seconds
        min_gap: float = 10.0  # seconds
    ) -> List[DetectionEvent]:
        """
        Aggregate overlapping predictions into detection events with pop confirmation.
        
        Args:
            predictions: List of (start_sample, probability, logits)
            min_duration: Minimum duration for a valid detection event
            min_pops: Minimum number of positive windows required for confirmation
            confirmation_window: Time window over which pops are counted
            min_gap: Merge events separated by gaps shorter than this
        
        Returns:
            List of DetectionEvent objects
        """
        if not predictions:
            return []
        
        # Build arrays of times and probabilities
        starts = np.array([s for s, _, _ in predictions], dtype=np.int64)
        probs = np.array([p for _, p, _ in predictions], dtype=np.float32)
        starts_sec = starts / float(self.sample_rate)
        ends_sec = starts_sec + self.window_size
        
        # Binary decision per window
        pos = (probs >= self.threshold).astype(np.int32)
        
        # Compute moving sum of positives across confirmation window
        hop_sec = self.hop_samples / float(self.sample_rate)
        k = max(1, int(np.ceil(confirmation_window / hop_sec)))
        kernel = np.ones(k, dtype=np.int32)
        # same-length moving sum; handles edges gracefully
        mov_sum = np.convolve(pos, kernel, mode='same')
        active = mov_sum >= int(min_pops)
        
        # Form contiguous active regions
        events: List[DetectionEvent] = []
        n = len(active)
        i = 0
        while i < n:
            if not active[i]:
                i += 1
                continue
            j = i
            max_conf = probs[i]
            while j + 1 < n and active[j + 1]:
                j += 1
                if probs[j] > max_conf:
                    max_conf = probs[j]
            # Create tentative event
            start_time = starts_sec[i]
            end_time = ends_sec[j]
            events.append(DetectionEvent(start_time, end_time, float(max_conf), i))
            i = j + 1
        
        if not events:
            return []
        
        # Merge events separated by small gaps (min_gap)
        merged: List[DetectionEvent] = []
        current = events[0]
        for e in events[1:]:
            gap = e.start_time - current.end_time
            if gap <= min_gap:
                current.end_time = max(current.end_time, e.end_time)
                current.confidence = max(current.confidence, e.confidence)
            else:
                merged.append(current)
                current = e
        merged.append(current)
        
        # Enforce minimum duration
        final_events: List[DetectionEvent] = []
        for ev in merged:
            if (ev.end_time - ev.start_time) >= min_duration:
                final_events.append(ev)
        
        return final_events
    
    def process_audio(
        self,
        audio_path: Path,
        min_event_duration: float = 2.0,
        min_pops: int = 3,
        confirmation_window: float = 30.0,
        min_gap: float = 10.0,
    ) -> Tuple[List[DetectionEvent], List[Tuple[int, float, np.ndarray]]]:
        """
        Process complete audio file and detect first crack events.
        
        Args:
            audio_path: Path to audio file
            min_event_duration: Minimum duration for valid event
        
        Returns:
            (events, all_predictions) tuple
        """
        # Load audio
        audio, duration = self.load_audio(audio_path)
        
        # Create windows
        windows = self.create_windows(audio)
        print(f"Created {len(windows)} overlapping windows "
              f"(window={self.window_size}s, overlap={self.overlap*100:.0f}%)")
        
        # Run inference
        predictions = self.predict_windows(windows)
        
        # Aggregate predictions
        events = self.aggregate_predictions(
            predictions,
            min_duration=min_event_duration,
            min_pops=min_pops,
            confirmation_window=confirmation_window,
            min_gap=min_gap,
        )
        
        return events, predictions
    
    def format_time(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        return str(timedelta(seconds=int(seconds)))[2:]  # Remove hours


def print_results(
    audio_path: Path,
    events: List[DetectionEvent],
    predictions: List[Tuple[int, float, np.ndarray]],
    sample_rate: int,
    threshold: float,
    window_size: float,
    overlap: float,
    min_duration: float,
    min_pops: int,
    confirmation_window: float,
    min_gap: float,
):
    """Print detection results in a formatted way."""
    print("\n" + "="*70)
    print(f"FIRST CRACK DETECTION RESULTS")
    print("="*70)
    print(f"Audio file: {audio_path.name}")
    print(f"Total windows analyzed: {len(predictions)}")
    print(f"Detection threshold: {threshold}")
    print(f"Window: {window_size}s, Overlap: {overlap*100:.0f}%")
    print(f"Min event duration: {min_duration}s")
    print(f"Pop confirmation: at least {min_pops} pops within {confirmation_window}s; min gap merge {min_gap}s")
    
    if events:
        print(f"\n🔥 DETECTED {len(events)} FIRST CRACK EVENT(S):")
        print("-"*70)
        for i, event in enumerate(events, 1):
            duration = event.end_time - event.start_time
            print(f"\nEvent {i}:")
            print(f"  Start:      {str(timedelta(seconds=int(event.start_time)))} "
                  f"({event.start_time:.1f}s)")
            print(f"  End:        {str(timedelta(seconds=int(event.end_time)))} "
                  f"({event.end_time:.1f}s)")
            print(f"  Duration:   {duration:.1f}s")
            print(f"  Confidence: {event.confidence:.3f}")
    else:
        print("\n❌ No first crack events detected")
    
    # Statistics
    probs = [p[1] for p in predictions]
    print(f"\n" + "-"*70)
    print(f"Prediction Statistics:")
    print(f"  Mean confidence:   {np.mean(probs):.3f}")
    print(f"  Max confidence:    {np.max(probs):.3f}")
    print(f"  Min confidence:    {np.min(probs):.3f}")
    print(f"  Windows >0.5:      {sum(1 for p in probs if p > 0.5)} "
          f"({sum(1 for p in probs if p > 0.5)/len(probs)*100:.1f}%)")
    print("="*70 + "\n")


def save_results(
    output_path: Path,
    audio_path: Path,
    events: List[DetectionEvent],
    predictions: List[Tuple[int, float, np.ndarray]],
    sample_rate: int,
    threshold: float,
    window_size: float,
    overlap: float,
    min_duration: float,
    min_pops: int,
    confirmation_window: float,
    min_gap: float,
):
    """Save detection results to file."""
    with open(output_path, 'w') as f:
        f.write(f"First Crack Detection Results\n")
        f.write(f"="*70 + "\n\n")
        f.write(f"Audio file: {audio_path}\n")
        f.write(f"Total windows: {len(predictions)}\n")
        f.write(f"Threshold: {threshold}\n")
        f.write(f"Window: {window_size}s, Overlap: {overlap*100:.0f}%\n")
        f.write(f"Min event duration: {min_duration}s\n")
        f.write(f"Pop confirmation: at least {min_pops} pops within {confirmation_window}s; min gap merge {min_gap}s\n\n")
        
        if events:
            f.write(f"Detected Events: {len(events)}\n")
            f.write("-"*70 + "\n\n")
            for i, event in enumerate(events, 1):
                duration = event.end_time - event.start_time
                f.write(f"Event {i}:\n")
                f.write(f"  Start: {event.start_time:.2f}s\n")
                f.write(f"  End: {event.end_time:.2f}s\n")
                f.write(f"  Duration: {duration:.2f}s\n")
                f.write(f"  Confidence: {event.confidence:.4f}\n\n")
        else:
            f.write("No events detected\n\n")
        
        # All predictions
        f.write("\n" + "="*70 + "\n")
        f.write("All Window Predictions:\n")
        f.write("-"*70 + "\n")
        for i, (start_sample, prob, _) in enumerate(predictions):
            start_time = start_sample / sample_rate
            f.write(f"Window {i:3d}: {start_time:7.2f}s - "
                   f"{start_time + 10:7.2f}s | Prob: {prob:.4f}\n")
    
    print(f"Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Sliding window inference for first crack detection"
    )
    parser.add_argument('--checkpoint', type=str, required=True,
                        help='Path to model checkpoint')
    parser.add_argument('--audio', type=str, required=True,
                        help='Path to audio file')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file for results (default: audio_name_results.txt)')
    parser.add_argument('--window-size', type=float, default=10.0,
                        help='Window size in seconds (default: 10.0)')
    parser.add_argument('--overlap', type=float, default=0.7,
                        help='Window overlap ratio 0-1 (default: 0.7)')
    parser.add_argument('--threshold', type=float, default=0.5,
                        help='Detection threshold (default: 0.5)')
    parser.add_argument('--min-duration', type=float, default=2.0,
                        help='Minimum event duration in seconds (default: 2.0)')
    parser.add_argument('--min-pops', type=int, default=3,
                        help='Minimum positive windows within confirmation window to confirm an event (default: 3)')
    parser.add_argument('--confirmation-window', type=float, default=30.0,
                        help='Seconds over which to count pops for confirmation (default: 30.0)')
    parser.add_argument('--min-gap', type=float, default=10.0,
                        help='Merge events separated by gaps shorter than this (default: 10.0)')
    
    args = parser.parse_args()
    
    # Load checkpoint
    checkpoint_path = Path(args.checkpoint)
    if not checkpoint_path.exists():
        print(f"❌ Checkpoint not found: {checkpoint_path}")
        sys.exit(1)
    
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    config = checkpoint['config']
    
    print("="*70)
    print("FIRST CRACK DETECTION - SLIDING WINDOW INFERENCE")
    print("="*70)
    print(f"\nLoading model from: {checkpoint_path}")
    print(f"Checkpoint epoch: {checkpoint['epoch']}")
    print(f"Best val F1: {checkpoint.get('best_val_f1', 'N/A'):.4f}")
    
    # Check audio file
    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"❌ Audio file not found: {audio_path}")
        sys.exit(1)
    
    # Setup output
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(f"{audio_path.stem}_inference_results.txt")
    
    # Create model
    device = config.get('device', 'mps' if torch.backends.mps.is_available() else 'cpu')
    model_config = ModelInitConfig(device=device)
    model = FirstCrackClassifier(model_config)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    
    print(f"Model device: {device}")
    print(f"\nInference parameters:")
    print(f"  Window size: {args.window_size}s")
    print(f"  Overlap: {args.overlap*100:.0f}%")
    print(f"  Threshold: {args.threshold}")
    print(f"  Min event duration: {args.min_duration}s")
    print(f"  Min pops: {args.min_pops}")
    print(f"  Confirmation window: {args.confirmation_window}s")
    print(f"  Min gap: {args.min_gap}s")
    
    # Create inference engine
    inference = SlidingWindowInference(
        model=model,
        window_size=args.window_size,
        overlap=args.overlap,
        threshold=args.threshold,
        sample_rate=config['sample_rate']
    )
    
    # Process audio
    events, predictions = inference.process_audio(
        audio_path,
        min_event_duration=args.min_duration,
        min_pops=args.min_pops,
        confirmation_window=args.confirmation_window,
        min_gap=args.min_gap,
    )
    
    # Print results
    print_results(
        audio_path,
        events,
        predictions,
        config['sample_rate'],
        args.threshold,
        args.window_size,
        args.overlap,
        args.min_duration,
        args.min_pops,
        args.confirmation_window,
        args.min_gap,
    )
    
    # Save results
    save_results(
        output_path,
        audio_path,
        events,
        predictions,
        config['sample_rate'],
        args.threshold,
        args.window_size,
        args.overlap,
        args.min_duration,
        args.min_pops,
        args.confirmation_window,
        args.min_gap,
    )


if __name__ == '__main__':
    main()
