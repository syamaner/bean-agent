"""
Mock First Crack Detector for demos.

Triggers FC based on configured parameters instead of audio analysis.
"""
import threading
import time
from datetime import datetime
from typing import Optional, Callable


class MockFirstCrackDetector:
    """
    Mock FC detector that triggers based on scenario timing.
    
    For demo mode - no audio processing, auto-triggers at configured time.
    """
    
    def __init__(self, fc_trigger_time: float = 90.0):
        """
        Initialize mock detector.
        
        Args:
            fc_trigger_time: Seconds after start to trigger FC
        """
        self.fc_trigger_time = fc_trigger_time
        self.is_running = False
        self.first_crack_detected = False
        self.first_crack_time: Optional[datetime] = None
        self.detection_callback: Optional[Callable] = None
        self._start_time: Optional[float] = None
        
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def start(self, callback: Optional[Callable] = None):
        """
        Start mock detection.
        
        Args:
            callback: Optional callback to invoke when FC detected
        """
        if self.is_running:
            return
        
        self.is_running = True
        self.first_crack_detected = False
        self.first_crack_time = None
        self.detection_callback = callback
        self._start_time = time.time()
        
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop(self) -> dict:
        """
        Stop mock detection and return summary.
        
        Returns:
            dict: Detection summary
        """
        self.is_running = False
        self._stop_event.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        
        return {
            "first_crack_detected": self.first_crack_detected,
            "first_crack_time": self.first_crack_time.isoformat() if self.first_crack_time else None,
            "mock_mode": True
        }
    
    def trigger_first_crack(self):
        """
        Externally trigger first crack detection.
        
        This would be called by the demo roaster hardware when it reaches FC point.
        """
        if not self.first_crack_detected:
            self.first_crack_detected = True
            self.first_crack_time = datetime.now()
            
            if self.detection_callback:
                self.detection_callback(self.first_crack_time)
    
    def get_status(self) -> dict:
        """Get current detection status."""
        return {
            "is_running": self.is_running,
            "first_crack_detected": self.first_crack_detected,
            "first_crack_time": self.first_crack_time.isoformat() if self.first_crack_time else None,
            "mock_mode": True
        }
    
    def _monitor_loop(self):
        """
        Monitor loop - auto-triggers FC at configured time.
        
        Checks elapsed time and triggers FC when threshold is reached.
        """
        while not self._stop_event.is_set() and self.is_running:
            if not self.first_crack_detected and self._start_time:
                elapsed = time.time() - self._start_time
                
                if elapsed >= self.fc_trigger_time:
                    # Auto-trigger first crack
                    self.trigger_first_crack()
            
            time.sleep(0.5)
