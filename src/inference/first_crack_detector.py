#!/usr/bin/env python3
"""
First Crack Detector for MCP Server Integration.

Provides a unified interface for detecting first crack from either:
- Audio file input
- Live USB microphone input

Designed to be called from an MCP server with simple start/stop lifecycle.
"""
import threading
import time
from pathlib import Path
from typing import Optional, Tuple, Union
from datetime import timedelta
from collections import deque
import sys

import torch
import librosa
import numpy as np
import sounddevice as sd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.ast_model import FirstCrackClassifier, ModelInitConfig


class FirstCrackDetector:
    """
    First crack detector for coffee roasting with file or microphone input.
    
    Supports both:
    - File-based inference (processes entire audio file)
    - Live microphone streaming (processes audio in real-time)
    
    Usage:
        # File input
        detector = FirstCrackDetector(audio_file="roast.wav")
        detector.start()
        # ... check is_first_crack() periodically
        detector.stop()
        
        # Microphone input
        detector = FirstCrackDetector(use_microphone=True)
        detector.start()
        # ... check is_first_crack() periodically
        detector.stop()
    """
    
    def __init__(
        self,
        audio_file: Optional[Union[str, Path]] = None,
        use_microphone: bool = False,
        checkpoint_path: Optional[Union[str, Path]] = None,
        model_config: Optional[ModelInitConfig] = None,
        window_size: float = 10.0,
        overlap: float = 0.7,
        threshold: float = 0.5,
        sample_rate: int = 16000,
        min_pops: int = 3,
        confirmation_window: float = 30.0,
    ):
        """
        Initialize the first crack detector.
        
        Args:
            audio_file: Path to audio file (mutually exclusive with use_microphone)
            use_microphone: Use USB microphone for live input (default: False)
            checkpoint_path: Path to model checkpoint (required if using trained model)
            model_config: Model configuration (optional, defaults to standard config)
            window_size: Size of sliding window in seconds (default: 10.0)
            overlap: Overlap ratio for sliding windows (default: 0.7)
            threshold: Classification threshold (default: 0.5)
            sample_rate: Audio sample rate in Hz (default: 16000)
            min_pops: Minimum positive detections to confirm first crack (default: 3)
            confirmation_window: Time window for pop counting in seconds (default: 30.0)
        """
        if audio_file and use_microphone:
            raise ValueError("Cannot specify both audio_file and use_microphone")
        
        if not audio_file and not use_microphone:
            raise ValueError("Must specify either audio_file or use_microphone")
        
        # Input configuration
        self.audio_file = Path(audio_file) if audio_file else None
        self.use_microphone = use_microphone
        
        # Model parameters
        self.window_size = window_size
        self.overlap = overlap
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.min_pops = min_pops
        self.confirmation_window = confirmation_window
        
        # Computed parameters
        self.window_samples = int(window_size * sample_rate)
        self.hop_samples = int(self.window_samples * (1 - overlap))
        
        # State management
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._first_crack_detected = False
        self._first_crack_time: Optional[float] = None
        self._start_time: Optional[float] = None
        
        # Streaming state (for microphone)
        self._audio_buffer = deque(maxlen=int(sample_rate * 60))  # 60 second buffer
        self._detection_history = deque(maxlen=100)  # Last 100 detection results
        self._lock = threading.Lock()
        
        # Load model
        if model_config is None:
            device = 'mps' if torch.backends.mps.is_available() else 'cpu'
            model_config = ModelInitConfig(device=device)
        
        self.model = FirstCrackClassifier(model_config)
        
        # Load checkpoint if provided
        if checkpoint_path:
            checkpoint_path = Path(checkpoint_path)
            if not checkpoint_path.exists():
                raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
            
            checkpoint = torch.load(checkpoint_path, map_location=model_config.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            print(f"Loaded model from checkpoint: {checkpoint_path}")
        
        self.model.eval()
    
    def start(self) -> None:
        """
        Start the detection process.
        
        For file input: Processes the entire file in a background thread
        For microphone: Starts streaming audio and processing in real-time
        """
        if self._running:
            raise RuntimeError("Detector is already running")
        
        self._running = True
        self._start_time = time.time()
        self._first_crack_detected = False
        self._first_crack_time = None
        
        if self.use_microphone:
            self._thread = threading.Thread(target=self._microphone_loop, daemon=True)
        else:
            self._thread = threading.Thread(target=self._file_processing_loop, daemon=True)
        
        self._thread.start()
        print(f"Started first crack detection ({'microphone' if self.use_microphone else 'file'})")
    
    def stop(self) -> None:
        """
        Stop the detection process and clean up resources.
        """
        if not self._running:
            return
        
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        
        self._audio_buffer.clear()
        self._detection_history.clear()
        
        print("Stopped first crack detection")
    
    def is_first_crack(self) -> Union[bool, Tuple[bool, str]]:
        """
        Check if first crack has been detected.
        
        Returns:
            False: If first crack has not been detected yet
            (True, "MM:SS"): If first crack detected, with timestamp in MM:SS format
        """
        with self._lock:
            if not self._first_crack_detected:
                return False
            
            if self._first_crack_time is not None:
                # Format as MM:SS
                timestamp_str = self._format_time(self._first_crack_time)
                return True, timestamp_str
            
            return False
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        td = timedelta(seconds=int(seconds))
        # Extract minutes and seconds
        total_seconds = int(td.total_seconds())
        minutes = total_seconds // 60
        secs = total_seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    
    def _file_processing_loop(self) -> None:
        """Process audio file in background thread."""
        try:
            # Load audio
            print(f"Loading audio file: {self.audio_file}")
            audio, sr = librosa.load(self.audio_file, sr=self.sample_rate, mono=True)
            duration = len(audio) / sr
            print(f"Audio duration: {duration:.2f}s")
            
            # Process in windows
            start = 0
            window_index = 0
            
            while self._running and start + self.window_samples <= len(audio):
                window = audio[start:start + self.window_samples]
                current_time = start / self.sample_rate
                
                # Run inference
                prob = self._predict_window(window)
                
                # Update detection state
                self._update_detection_state(prob, current_time, window_index)
                
                start += self.hop_samples
                window_index += 1
                
                # Simulate real-time processing pace (optional)
                time.sleep(0.1)
            
            print("File processing complete")
            
        except Exception as e:
            print(f"Error in file processing: {e}")
            self._running = False
    
    def _microphone_loop(self) -> None:
        """Stream audio from microphone and process in real-time."""
        try:
            def audio_callback(indata, frames, time_info, status):
                """Callback for audio stream."""
                if status:
                    print(f"Audio stream status: {status}")
                
                # Add to buffer (flatten to 1D and normalize)
                audio_data = indata[:, 0] if indata.ndim > 1 else indata
                with self._lock:
                    self._audio_buffer.extend(audio_data)
            
            # Start audio stream
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=audio_callback,
                blocksize=int(self.sample_rate * 0.5),  # 0.5 second blocks
            ):
                print(f"Microphone stream started (sample rate: {self.sample_rate} Hz)")
                window_index = 0
                
                while self._running:
                    # Wait for buffer to have enough samples
                    with self._lock:
                        buffer_size = len(self._audio_buffer)
                    
                    if buffer_size >= self.window_samples:
                        # Extract window
                        with self._lock:
                            window = np.array(list(self._audio_buffer)[-self.window_samples:])
                        
                        current_time = time.time() - self._start_time
                        
                        # Run inference
                        prob = self._predict_window(window)
                        
                        # Update detection state
                        self._update_detection_state(prob, current_time, window_index)
                        
                        window_index += 1
                    
                    # Small sleep to avoid tight loop
                    time.sleep(0.5)
        
        except Exception as e:
            print(f"Error in microphone loop: {e}")
            self._running = False
    
    @torch.inference_mode()
    def _predict_window(self, window: np.ndarray) -> float:
        """
        Run inference on a single audio window.
        
        Args:
            window: Audio samples of length window_samples
        
        Returns:
            First crack probability (0-1)
        """
        # Convert to tensor
        audio_tensor = torch.FloatTensor(window).unsqueeze(0)
        
        # Forward pass
        logits = self.model(audio_tensor)
        probs = torch.softmax(logits, dim=-1)
        
        # Get first_crack probability (class index 1)
        first_crack_prob = probs[0, 1].item()
        
        return first_crack_prob
    
    def _update_detection_state(
        self,
        prob: float,
        current_time: float,
        window_index: int
    ) -> None:
        """
        Update detection state based on new prediction.
        
        Uses moving window of positive detections to confirm first crack.
        """
        with self._lock:
            # Add to history
            is_positive = prob >= self.threshold
            self._detection_history.append((current_time, is_positive, prob))
            
            # Count recent positives within confirmation window
            recent_positives = 0
            cutoff_time = current_time - self.confirmation_window
            
            for t, positive, _ in self._detection_history:
                if t >= cutoff_time and positive:
                    recent_positives += 1
            
            # Check if we should declare first crack
            if not self._first_crack_detected and recent_positives >= self.min_pops:
                self._first_crack_detected = True
                # Use the earliest positive detection in the window as the timestamp
                for t, positive, _ in self._detection_history:
                    if positive and t >= cutoff_time:
                        self._first_crack_time = t
                        break
                
                print(f"🔥 FIRST CRACK DETECTED at {self._format_time(self._first_crack_time)} "
                      f"(confidence: {recent_positives} pops)")
    
    @property
    def is_running(self) -> bool:
        """Check if detector is currently running."""
        return self._running
    
    def get_elapsed_time(self) -> Optional[str]:
        """Get elapsed time since start in MM:SS format."""
        if self._start_time is None:
            return None
        
        elapsed = time.time() - self._start_time
        return self._format_time(elapsed)


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="First Crack Detector Demo")
    parser.add_argument("--audio", type=str, help="Path to audio file")
    parser.add_argument("--microphone", action="store_true", help="Use microphone input")
    parser.add_argument("--checkpoint", type=str, help="Path to model checkpoint")
    args = parser.parse_args()
    
    # Create detector
    if args.microphone:
        detector = FirstCrackDetector(
            use_microphone=True,
            checkpoint_path=args.checkpoint
        )
    elif args.audio:
        detector = FirstCrackDetector(
            audio_file=args.audio,
            checkpoint_path=args.checkpoint
        )
    else:
        print("Must specify either --audio or --microphone")
        sys.exit(1)
    
    # Start detection
    detector.start()
    
    try:
        # Monitor for first crack
        while detector.is_running:
            result = detector.is_first_crack()
            elapsed = detector.get_elapsed_time()
            
            if result is False:
                print(f"[{elapsed}] No first crack detected yet...")
            else:
                detected, timestamp = result
                print(f"[{elapsed}] First crack detected at {timestamp}!")
            
            time.sleep(2)
    
    except KeyboardInterrupt:
        print("\nStopping...")
    
    finally:
        detector.stop()
