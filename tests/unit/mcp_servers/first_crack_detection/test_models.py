"""
Tests for Pydantic data models.

Following TDD approach:
1. Write tests first (RED)
2. Implement models to pass tests (GREEN)
3. Refactor (REFACTOR)
"""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError


def test_audio_config_audio_file():
    """Test AudioConfig with audio file source."""
    from src.mcp_servers.first_crack_detection.models import AudioConfig
    
    # Valid audio file config
    config = AudioConfig(
        audio_source_type="audio_file",
        audio_file_path="/path/to/audio.wav"
    )
    assert config.audio_source_type == "audio_file"
    assert config.audio_file_path == "/path/to/audio.wav"


def test_audio_config_audio_file_missing_path():
    """Test AudioConfig validates file path is required for audio_file type."""
    from src.mcp_servers.first_crack_detection.models import AudioConfig
    
    # Should raise validation error when audio_file_path is missing
    with pytest.raises(ValidationError) as exc_info:
        AudioConfig(
            audio_source_type="audio_file",
            audio_file_path=None
        )
    
    assert "audio_file_path" in str(exc_info.value)


def test_audio_config_usb_microphone():
    """Test AudioConfig with USB microphone."""
    from src.mcp_servers.first_crack_detection.models import AudioConfig
    
    config = AudioConfig(audio_source_type="usb_microphone")
    assert config.audio_source_type == "usb_microphone"
    assert config.audio_file_path is None


def test_audio_config_builtin_microphone():
    """Test AudioConfig with built-in microphone."""
    from src.mcp_servers.first_crack_detection.models import AudioConfig
    
    config = AudioConfig(audio_source_type="builtin_microphone")
    assert config.audio_source_type == "builtin_microphone"
    assert config.audio_file_path is None


def test_audio_config_invalid_type():
    """Test AudioConfig rejects invalid audio source type."""
    from src.mcp_servers.first_crack_detection.models import AudioConfig
    
    with pytest.raises(ValidationError):
        AudioConfig(audio_source_type="invalid_type")


def test_detection_config_defaults():
    """Test DetectionConfig default values."""
    from src.mcp_servers.first_crack_detection.models import DetectionConfig
    
    config = DetectionConfig()
    assert config.threshold == 0.5
    assert config.min_pops == 3
    assert config.confirmation_window == 30.0


def test_detection_config_custom_values():
    """Test DetectionConfig with custom values."""
    from src.mcp_servers.first_crack_detection.models import DetectionConfig
    
    config = DetectionConfig(
        threshold=0.7,
        min_pops=5,
        confirmation_window=60.0
    )
    assert config.threshold == 0.7
    assert config.min_pops == 5
    assert config.confirmation_window == 60.0


def test_detection_config_threshold_validation():
    """Test DetectionConfig validates threshold range (0-1)."""
    from src.mcp_servers.first_crack_detection.models import DetectionConfig
    
    # Valid range
    DetectionConfig(threshold=0.0)
    DetectionConfig(threshold=1.0)
    
    # Invalid range
    with pytest.raises(ValidationError):
        DetectionConfig(threshold=-0.1)
    
    with pytest.raises(ValidationError):
        DetectionConfig(threshold=1.1)


def test_detection_config_min_pops_validation():
    """Test DetectionConfig validates min_pops is positive."""
    from src.mcp_servers.first_crack_detection.models import DetectionConfig
    
    # Valid
    DetectionConfig(min_pops=1)
    
    # Invalid
    with pytest.raises(ValidationError):
        DetectionConfig(min_pops=0)


def test_session_info_structure():
    """Test SessionInfo model structure."""
    from src.mcp_servers.first_crack_detection.models import SessionInfo
    
    started_at_utc = datetime.now(timezone.utc)
    started_at_local = datetime.now()
    
    info = SessionInfo(
        session_state="started",
        session_id="test-session-123",
        started_at_utc=started_at_utc,
        started_at_local=started_at_local,
        audio_source="usb_microphone",
        audio_source_details="USB Audio Device"
    )
    
    assert info.session_state == "started"
    assert info.session_id == "test-session-123"
    assert info.audio_source == "usb_microphone"


def test_session_info_already_running():
    """Test SessionInfo with already_running state."""
    from src.mcp_servers.first_crack_detection.models import SessionInfo
    
    info = SessionInfo(
        session_state="already_running",
        session_id="existing-session",
        started_at_utc=datetime.now(timezone.utc),
        started_at_local=datetime.now(),
        audio_source="audio_file",
        audio_source_details="/path/to/file.wav"
    )
    
    assert info.session_state == "already_running"


def test_status_info_no_session():
    """Test StatusInfo when no session is active."""
    from src.mcp_servers.first_crack_detection.models import StatusInfo
    
    status = StatusInfo(session_active=False)
    assert status.session_active is False
    assert status.session_id is None
    assert status.first_crack_detected is False


def test_status_info_active_no_detection():
    """Test StatusInfo with active session, no detection."""
    from src.mcp_servers.first_crack_detection.models import StatusInfo
    
    status = StatusInfo(
        session_active=True,
        session_id="test-session",
        elapsed_time="05:30",
        first_crack_detected=False,
        started_at_utc=datetime.now(timezone.utc),
        started_at_local=datetime.now(),
        audio_source="usb_microphone"
    )
    
    assert status.session_active is True
    assert status.first_crack_detected is False
    assert status.first_crack_time_relative is None


def test_status_info_with_detection():
    """Test StatusInfo with first crack detected."""
    from src.mcp_servers.first_crack_detection.models import StatusInfo
    
    status = StatusInfo(
        session_active=True,
        session_id="test-session",
        elapsed_time="08:45",
        first_crack_detected=True,
        first_crack_time_relative="07:30",
        first_crack_time_utc=datetime.now(timezone.utc),
        first_crack_time_local=datetime.now(),
        confidence={"pop_count": 5, "confirmation_window": 30.0},
        started_at_utc=datetime.now(timezone.utc),
        started_at_local=datetime.now(),
        audio_source="usb_microphone"
    )
    
    assert status.first_crack_detected is True
    assert status.first_crack_time_relative == "07:30"
    assert status.confidence["pop_count"] == 5


def test_session_summary_stopped():
    """Test SessionSummary when session stopped normally."""
    from src.mcp_servers.first_crack_detection.models import SessionSummary
    
    summary = SessionSummary(
        session_state="stopped",
        session_id="test-session",
        session_summary={
            "duration": "10:23",
            "first_crack_detected": True,
            "first_crack_time_relative": "07:30",
            "first_crack_time_local": "2025-01-25T10:37:30-05:00",
            "total_windows_processed": 123
        }
    )
    
    assert summary.session_state == "stopped"
    assert summary.session_summary["duration"] == "10:23"


def test_session_summary_no_active_session():
    """Test SessionSummary when no session to stop."""
    from src.mcp_servers.first_crack_detection.models import SessionSummary
    
    summary = SessionSummary(
        session_state="no_active_session",
        session_id=None,
        session_summary=None
    )
    
    assert summary.session_state == "no_active_session"
    assert summary.session_id is None


def test_server_config():
    """Test ServerConfig model."""
    from src.mcp_servers.first_crack_detection.models import ServerConfig
    
    config = ServerConfig(
        model_checkpoint="experiments/final_model/model.pt",
        default_threshold=0.6,
        default_min_pops=4,
        default_confirmation_window=45.0,
        log_level="DEBUG"
    )
    
    assert config.model_checkpoint == "experiments/final_model/model.pt"
    assert config.default_threshold == 0.6
    assert config.log_level == "DEBUG"


def test_server_config_defaults():
    """Test ServerConfig default values."""
    from src.mcp_servers.first_crack_detection.models import ServerConfig
    
    config = ServerConfig(model_checkpoint="/path/to/model.pt")
    assert config.default_threshold == 0.5
    assert config.default_min_pops == 3
    assert config.default_confirmation_window == 30.0
    assert config.log_level == "INFO"


def test_detection_session_dataclass():
    """Test DetectionSession dataclass."""
    from src.mcp_servers.first_crack_detection.models import DetectionSession
    from unittest.mock import Mock
    
    mock_detector = Mock()
    audio_config = Mock()
    
    session = DetectionSession(
        session_id="test-123",
        detector=mock_detector,
        started_at=datetime.now(timezone.utc),
        audio_config=audio_config
    )
    
    assert session.session_id == "test-123"
    assert session.detector == mock_detector
    assert session.thread_exception is None
    assert session.windows_processed == 0
