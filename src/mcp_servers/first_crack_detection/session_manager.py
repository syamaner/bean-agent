"""
DetectionSessionManager - Core session management logic.

Manages the lifecycle of first crack detection sessions including:
- Starting/stopping detection
- Querying status
- Audio source validation
- Thread safety
- Idempotency
"""
import uuid
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from .models import (
    ServerConfig,
    AudioConfig,
    SessionInfo,
    StatusInfo,
    SessionSummary,
    DetectionSession,
    ModelNotFoundError,
    FileNotFoundError as FCFileNotFoundError,
    MicrophoneNotAvailableError,
)
from .utils import get_local_timezone, to_local_time, format_elapsed_time
from .audio_devices import find_usb_microphone, find_builtin_microphone
from src.inference.first_crack_detector import FirstCrackDetector


logger = logging.getLogger(__name__)


class DetectionSessionManager:
    """
    Manages first crack detection sessions.
    
    Thread-safe singleton-style session management:
    - Only one detection session can be active at a time
    - All methods are thread-safe using locks
    - Idempotent start/stop operations
    """
    
    def __init__(self, config: ServerConfig):
        """
        Initialize session manager.
        
        Args:
            config: Server configuration
        """
        self.config = config
        self.current_session: Optional[DetectionSession] = None
        self._lock = threading.Lock()
        logger.info(f"DetectionSessionManager initialized with checkpoint: {config.model_checkpoint}")
    
    def start_session(self, audio_config: AudioConfig) -> SessionInfo:
        """
        Start a new detection session.
        
        Idempotent: If session already active, returns existing session info.
        
        Args:
            audio_config: Audio source configuration
            
        Returns:
            SessionInfo: Session information
            
        Raises:
            ModelNotFoundError: Model checkpoint not found
            FileNotFoundError: Audio file not found
            MicrophoneNotAvailableError: Microphone not available
        """
        with self._lock:
            # Check if session already running (idempotency)
            if self.current_session is not None:
                return self._get_session_info(already_running=True)
            
            # Validate model checkpoint
            self._validate_model_checkpoint()
            
            # Validate audio source
            self._validate_audio_source(audio_config)
            
            # Create detector
            detector = self._create_detector(audio_config)
            
            # Create session
            session_id = str(uuid.uuid4())
            started_at = datetime.now(timezone.utc)
            
            self.current_session = DetectionSession(
                session_id=session_id,
                detector=detector,
                started_at=started_at,
                audio_config=audio_config
            )
            
            logger.info(f"Started detection session {session_id} with {audio_config.audio_source_type}")
            
            return self._get_session_info(already_running=False)
    
    def get_status(self) -> StatusInfo:
        """
        Get current detection status.
        
        Returns:
            StatusInfo: Current status
        """
        with self._lock:
            if self.current_session is None:
                return StatusInfo(
                    session_active=False,
                    first_crack_detected=False
                )
            
            # Query detector
            result = self.current_session.detector.is_first_crack()
            
            # Build status info
            return self._build_status_info(result)
    
    def stop_session(self) -> SessionSummary:
        """
        Stop the current session.
        
        Idempotent: If no session active, returns appropriate response.
        
        Returns:
            SessionSummary: Session summary
        """
        with self._lock:
            if self.current_session is None:
                return SessionSummary(
                    session_state="no_active_session",
                    session_id=None,
                    session_summary=None
                )
            
            # Build summary before cleanup
            summary = self._build_session_summary(self.current_session)
            
            # Stop detector
            if self.current_session.detector:
                self.current_session.detector.stop()
            
            # Cleanup
            session_id = self.current_session.session_id
            self.current_session = None
            
            logger.info(f"Stopped detection session {session_id}")
            
            return summary
    
    def _validate_model_checkpoint(self) -> None:
        """
        Validate model checkpoint exists.
        
        Raises:
            ModelNotFoundError: If checkpoint doesn't exist
        """
        checkpoint_path = Path(self.config.model_checkpoint)
        if not checkpoint_path.exists():
            raise ModelNotFoundError(
                f"Model checkpoint not found: {self.config.model_checkpoint}"
            )
    
    def _validate_audio_source(self, config: AudioConfig) -> None:
        """
        Validate audio source is available.
        
        Args:
            config: Audio configuration
            
        Raises:
            FileNotFoundError: Audio file doesn't exist
            MicrophoneNotAvailableError: Microphone not available
        """
        if config.audio_source_type == "audio_file":
            # Validate file exists
            if config.audio_file_path and not Path(config.audio_file_path).exists():
                raise FCFileNotFoundError(
                    f"Audio file not found: {config.audio_file_path}"
                )
        
        elif config.audio_source_type == "usb_microphone":
            # Validate USB mic available
            device_id = find_usb_microphone()
            if device_id is None:
                raise MicrophoneNotAvailableError(
                    "USB microphone not found"
                )
        
        elif config.audio_source_type == "builtin_microphone":
            # Validate built-in mic available
            device_id = find_builtin_microphone()
            if device_id is None:
                raise MicrophoneNotAvailableError(
                    "Built-in microphone not found"
                )
    
    def _create_detector(self, audio_config: AudioConfig) -> FirstCrackDetector:
        """
        Create FirstCrackDetector instance.
        
        Args:
            audio_config: Audio configuration
            
        Returns:
            FirstCrackDetector: Detector instance
        """
        # Determine audio source for detector
        if audio_config.audio_source_type == "audio_file":
            # File-based detection
            detector = FirstCrackDetector(
                audio_file=audio_config.audio_file_path,
                checkpoint_path=self.config.model_checkpoint,
                threshold=self.config.default_threshold,
                min_pops=self.config.default_min_pops,
                confirmation_window=self.config.default_confirmation_window
            )
        else:  # usb_microphone or builtin_microphone
            # Microphone-based detection
            detector = FirstCrackDetector(
                use_microphone=True,
                checkpoint_path=self.config.model_checkpoint,
                threshold=self.config.default_threshold,
                min_pops=self.config.default_min_pops,
                confirmation_window=self.config.default_confirmation_window
            )
        
        # Start the detector
        detector.start()
        
        return detector
    
    def _get_session_info(self, already_running: bool) -> SessionInfo:
        """
        Build SessionInfo response.
        
        Args:
            already_running: Whether session was already running
            
        Returns:
            SessionInfo: Session information
        """
        if self.current_session is None:
            raise RuntimeError("No active session")
        
        session = self.current_session
        
        # Determine audio source details
        if session.audio_config.audio_source_type == "audio_file":
            audio_source_details = f"file: {session.audio_config.audio_file_path}"
        elif session.audio_config.audio_source_type == "usb_microphone":
            audio_source_details = "USB microphone (auto-detected)"
        else:
            audio_source_details = "Built-in microphone"
        
        return SessionInfo(
            session_state="already_running" if already_running else "started",
            session_id=session.session_id,
            started_at_utc=session.started_at,
            started_at_local=to_local_time(session.started_at),
            audio_source=session.audio_config.audio_source_type,
            audio_source_details=audio_source_details
        )
    
    def _build_status_info(self, result) -> StatusInfo:
        """
        Build StatusInfo from detector result.
        
        Args:
            result: Tuple of (detected: bool, time_str: Optional[str])
            
        Returns:
            StatusInfo: Status information
        """
        if self.current_session is None:
            raise RuntimeError("No active session")
        
        session = self.current_session
        
        # Handle different return types from is_first_crack()
        if isinstance(result, tuple):
            detected, time_str = result
        else:
            detected = result
            time_str = None
        
        # Calculate elapsed time
        elapsed_seconds = (datetime.now(timezone.utc) - session.started_at).total_seconds()
        elapsed_time = format_elapsed_time(elapsed_seconds)
        
        # Build base status
        status = StatusInfo(
            session_active=True,
            session_id=session.session_id,
            elapsed_time=elapsed_time,
            first_crack_detected=detected,
            started_at_utc=session.started_at,
            started_at_local=to_local_time(session.started_at),
            audio_source=session.audio_config.audio_source_type
        )
        
        # Add first crack details if detected
        if detected and time_str:
            # Parse MM:SS to get seconds offset
            parts = time_str.split(":")
            minutes = int(parts[0])
            seconds = int(parts[1])
            offset_seconds = minutes * 60 + seconds
            
            # Calculate UTC time of first crack
            from datetime import timedelta
            first_crack_utc = session.started_at + timedelta(seconds=offset_seconds)
            
            status.first_crack_time_relative = time_str
            status.first_crack_time_utc = first_crack_utc
            status.first_crack_time_local = to_local_time(first_crack_utc)
        
        return status
    
    def _build_session_summary(self, session: DetectionSession) -> SessionSummary:
        """
        Build SessionSummary for stopped session.
        
        Args:
            session: Detection session
            
        Returns:
            SessionSummary: Summary information
        """
        # Get final status
        result = session.detector.is_first_crack()
        
        # Handle different return types from is_first_crack()
        if isinstance(result, tuple):
            detected, time_str = result
        else:
            detected = result
            time_str = None
        
        # Calculate duration
        duration_seconds = (datetime.now(timezone.utc) - session.started_at).total_seconds()
        
        summary_data = {
            "duration": format_elapsed_time(duration_seconds),
            "first_crack_detected": detected,
            "audio_source": session.audio_config.audio_source_type
        }
        
        if detected and time_str:
            summary_data["first_crack_time"] = time_str
        
        return SessionSummary(
            session_state="stopped",
            session_id=session.session_id,
            session_summary=summary_data
        )
