"""
Pydantic data models for First Crack Detection MCP Server.

Models define the structure and validation for:
- Configuration (audio, detection, server)
- Request/response data (session info, status, summary)
- Internal state (detection session)
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator


class AudioConfig(BaseModel):
    """Audio source configuration."""
    
    audio_source_type: Literal["audio_file", "usb_microphone", "builtin_microphone"]
    audio_file_path: Optional[str] = None
    
    @field_validator("audio_file_path")
    @classmethod
    def validate_file_path(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that audio_file_path is provided when audio_source_type is 'audio_file'."""
        if info.data.get("audio_source_type") == "audio_file" and not v:
            raise ValueError("audio_file_path is required when audio_source_type is 'audio_file'")
        return v


class DetectionConfig(BaseModel):
    """Detection parameters."""
    
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    min_pops: int = Field(default=3, ge=1)
    confirmation_window: float = Field(default=30.0, ge=1.0)


class SessionInfo(BaseModel):
    """Information about a started detection session."""
    
    session_state: Literal["started", "already_running"]
    session_id: str
    started_at_utc: datetime
    started_at_local: datetime
    audio_source: str
    audio_source_details: str


class StatusInfo(BaseModel):
    """Current detection status."""
    
    session_active: bool
    session_id: Optional[str] = None
    elapsed_time: Optional[str] = None  # MM:SS format
    first_crack_detected: bool = False
    first_crack_time_relative: Optional[str] = None  # MM:SS format
    first_crack_time_utc: Optional[datetime] = None
    first_crack_time_local: Optional[datetime] = None
    confidence: Optional[Dict[str, Any]] = None
    started_at_utc: Optional[datetime] = None
    started_at_local: Optional[datetime] = None
    audio_source: Optional[str] = None


class SessionSummary(BaseModel):
    """Summary after session stop."""
    
    session_state: Literal["stopped", "no_active_session"]
    session_id: Optional[str] = None
    session_summary: Optional[Dict[str, Any]] = None


class ServerConfig(BaseModel):
    """Server configuration."""
    
    model_checkpoint: str
    default_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    default_min_pops: int = Field(default=3, ge=1)
    default_confirmation_window: float = Field(default=30.0, ge=1.0)
    log_level: str = "INFO"


@dataclass
class DetectionSession:
    """Represents an active detection session (internal state)."""
    
    session_id: str
    detector: Any  # FirstCrackDetector instance
    started_at: datetime
    audio_config: Any  # AudioConfig instance
    thread_exception: Optional[Exception] = None
    windows_processed: int = 0


# =============================================================================
# Custom Exceptions
# =============================================================================

class DetectionError(Exception):
    """Base exception for detection errors."""
    
    error_code: str = "DETECTION_ERROR"
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.error_code}, message={str(self)})"


class ModelNotFoundError(DetectionError):
    """Model checkpoint not found."""
    error_code = "MODEL_NOT_FOUND"


class MicrophoneNotAvailableError(DetectionError):
    """Microphone device not available."""
    error_code = "MICROPHONE_NOT_AVAILABLE"


class FileNotFoundError(DetectionError):
    """Audio file not found."""
    error_code = "FILE_NOT_FOUND"


class SessionAlreadyActiveError(DetectionError):
    """Cannot start session, one already active."""
    error_code = "SESSION_ALREADY_ACTIVE"


class ThreadCrashError(DetectionError):
    """Detection thread crashed."""
    error_code = "DETECTION_THREAD_CRASHED"


class InvalidAudioSourceError(DetectionError):
    """Invalid audio source type."""
    error_code = "INVALID_AUDIO_SOURCE"
