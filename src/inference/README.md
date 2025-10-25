# First Crack Detector - MCP Server Integration

The `FirstCrackDetector` class provides a simple interface for detecting first crack events in coffee roasting, designed to be called from an MCP server.

## Features

- **Dual Input Modes:**
  - Audio file processing (for testing/validation)
  - Live USB microphone streaming (for real-time roasting)

- **Simple Lifecycle:**
  - `start()` - Begin detection
  - `stop()` - End detection and cleanup
  - `is_first_crack()` - Check detection status

- **Thread-safe:** All operations are thread-safe for MCP server integration

## Installation

Install the additional dependency for microphone support:

```bash
pip install sounddevice>=0.4.6
```

Or install from requirements:

```bash
pip install -r requirements.txt
```

## Usage

### File-based Detection

```python
from src.inference import FirstCrackDetector

# Initialize with audio file
detector = FirstCrackDetector(
    audio_file="data/roast_session.wav",
    checkpoint_path="path/to/model_checkpoint.pt"
)

# Start detection
detector.start()

# Check status periodically
result = detector.is_first_crack()
if result is False:
    print("No first crack detected yet")
else:
    detected, timestamp = result
    print(f"First crack detected at {timestamp}")

# Stop when done
detector.stop()
```

### Microphone-based Detection (Real-time)

```python
from src.inference import FirstCrackDetector

# Initialize with microphone
detector = FirstCrackDetector(
    use_microphone=True,
    checkpoint_path="path/to/model_checkpoint.pt",
    sample_rate=16000  # Match your microphone settings
)

# Start streaming detection
detector.start()

# In your MCP server loop
while roasting:
    result = detector.is_first_crack()
    
    if result is False:
        # First crack not detected yet
        continue
    else:
        detected, timestamp = result
        # Take action: adjust heat, fan, etc.
        print(f"🔥 First crack at {timestamp}")
        break
    
    time.sleep(1)  # Poll every second

# Stop when roast is done
detector.stop()
```

## MCP Server Integration Example

```python
from typing import Optional, Tuple
from src.inference import FirstCrackDetector

class RoastingMCPServer:
    def __init__(self):
        self.detector: Optional[FirstCrackDetector] = None
    
    def tool_start_detection(
        self,
        use_microphone: bool = True,
        checkpoint_path: str = "models/best_model.pt"
    ) -> dict:
        """MCP tool to start first crack detection."""
        try:
            self.detector = FirstCrackDetector(
                use_microphone=use_microphone,
                checkpoint_path=checkpoint_path
            )
            self.detector.start()
            return {"status": "started", "mode": "microphone" if use_microphone else "file"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def tool_check_first_crack(self) -> dict:
        """MCP tool to check if first crack has been detected."""
        if self.detector is None:
            return {"status": "error", "message": "Detector not initialized"}
        
        result = self.detector.is_first_crack()
        
        if result is False:
            return {
                "first_crack_detected": False,
                "elapsed_time": self.detector.get_elapsed_time()
            }
        else:
            detected, timestamp = result
            return {
                "first_crack_detected": True,
                "timestamp": timestamp,
                "elapsed_time": self.detector.get_elapsed_time()
            }
    
    def tool_stop_detection(self) -> dict:
        """MCP tool to stop first crack detection."""
        if self.detector is None:
            return {"status": "error", "message": "Detector not initialized"}
        
        self.detector.stop()
        self.detector = None
        return {"status": "stopped"}
```

## API Reference

### Constructor

```python
FirstCrackDetector(
    audio_file: Optional[str] = None,
    use_microphone: bool = False,
    checkpoint_path: Optional[str] = None,
    model_config: Optional[ModelInitConfig] = None,
    window_size: float = 10.0,
    overlap: float = 0.5,
    threshold: float = 0.5,
    sample_rate: int = 16000,
    min_pops: int = 3,
    confirmation_window: float = 30.0,
)
```

**Parameters:**
- `audio_file` - Path to audio file (mutually exclusive with `use_microphone`)
- `use_microphone` - Use USB microphone for live input
- `checkpoint_path` - Path to trained model checkpoint
- `window_size` - Sliding window size in seconds (default: 10.0)
- `overlap` - Window overlap ratio 0-1 (default: 0.5)
- `threshold` - Classification threshold (default: 0.5)
- `sample_rate` - Audio sample rate in Hz (default: 16000)
- `min_pops` - Minimum positive detections to confirm first crack (default: 3)
- `confirmation_window` - Time window for counting pops in seconds (default: 30.0)

### Methods

#### `start() -> None`
Start the detection process. Runs in a background thread.

#### `stop() -> None`
Stop detection and clean up resources.

#### `is_first_crack() -> Union[bool, Tuple[bool, str]]`
Check if first crack has been detected.

**Returns:**
- `False` - If first crack has not been detected yet
- `(True, "MM:SS")` - If detected, with timestamp in MM:SS format

#### `get_elapsed_time() -> Optional[str]`
Get elapsed time since start in MM:SS format.

**Returns:**
- `"MM:SS"` - Formatted elapsed time
- `None` - If not started

### Properties

#### `is_running -> bool`
Check if detector is currently running.

## Configuration Tips

### For Real-time Roasting:
- Use `sample_rate=16000` (balances quality and performance)
- `min_pops=3` ensures reliable detection
- `confirmation_window=30.0` allows for typical first crack duration
- `threshold=0.5` is a good starting point (tune based on your model)

### For Testing with Files:
- Process faster by reducing `time.sleep()` in `_file_processing_loop`
- Use same parameters as real-time for consistency

## Troubleshooting

### Microphone Not Found
```bash
# List available audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### Model Not Loading
- Ensure checkpoint path is correct
- Verify checkpoint was saved with same model architecture
- Check device compatibility (MPS for Mac M1/M2/M3)

### No Detection
- Verify microphone is working and positioned correctly
- Check threshold value (try lowering to 0.3)
- Ensure model is trained on similar audio
- Verify `min_pops` isn't too high
