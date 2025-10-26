"""
Tests for custom exception classes.

Following TDD approach:
1. Write tests first (RED)
2. Implement exceptions to pass tests (GREEN)
3. Refactor (REFACTOR)
"""
import pytest


def test_detection_error_base():
    """Test base DetectionError exception."""
    from src.mcp_servers.first_crack_detection.models import DetectionError
    
    error = DetectionError("Test error message")
    assert str(error) == "Test error message"
    assert isinstance(error, Exception)


def test_model_not_found_error():
    """Test ModelNotFoundError exception."""
    from src.mcp_servers.first_crack_detection.models import ModelNotFoundError
    
    error = ModelNotFoundError("Model checkpoint not found")
    assert error.error_code == "MODEL_NOT_FOUND"
    assert "Model checkpoint not found" in str(error)


def test_microphone_not_available_error():
    """Test MicrophoneNotAvailableError exception."""
    from src.mcp_servers.first_crack_detection.models import MicrophoneNotAvailableError
    
    error = MicrophoneNotAvailableError("USB microphone not detected")
    assert error.error_code == "MICROPHONE_NOT_AVAILABLE"
    assert "USB microphone not detected" in str(error)


def test_file_not_found_error():
    """Test FileNotFoundError exception."""
    from src.mcp_servers.first_crack_detection.models import FileNotFoundError
    
    error = FileNotFoundError("Audio file does not exist")
    assert error.error_code == "FILE_NOT_FOUND"
    assert "Audio file does not exist" in str(error)


def test_session_already_active_error():
    """Test SessionAlreadyActiveError exception."""
    from src.mcp_servers.first_crack_detection.models import SessionAlreadyActiveError
    
    error = SessionAlreadyActiveError("Session already running")
    assert error.error_code == "SESSION_ALREADY_ACTIVE"
    assert "Session already running" in str(error)


def test_thread_crash_error():
    """Test ThreadCrashError exception."""
    from src.mcp_servers.first_crack_detection.models import ThreadCrashError
    
    error = ThreadCrashError("Detection thread crashed")
    assert error.error_code == "DETECTION_THREAD_CRASHED"
    assert "Detection thread crashed" in str(error)


def test_invalid_audio_source_error():
    """Test InvalidAudioSourceError exception."""
    from src.mcp_servers.first_crack_detection.models import InvalidAudioSourceError
    
    error = InvalidAudioSourceError("Unknown audio source type")
    assert error.error_code == "INVALID_AUDIO_SOURCE"
    assert "Unknown audio source type" in str(error)


def test_exception_with_details():
    """Test exception can carry additional details."""
    from src.mcp_servers.first_crack_detection.models import ModelNotFoundError
    
    error = ModelNotFoundError(
        "Model not found",
        details={"path": "/path/to/model.pt", "checked_locations": ["/a", "/b"]}
    )
    assert error.error_code == "MODEL_NOT_FOUND"
    assert error.details["path"] == "/path/to/model.pt"
    assert len(error.details["checked_locations"]) == 2


def test_exception_without_details():
    """Test exception works without details dict."""
    from src.mcp_servers.first_crack_detection.models import FileNotFoundError
    
    error = FileNotFoundError("File not found")
    assert error.error_code == "FILE_NOT_FOUND"
    assert hasattr(error, "details")
    assert error.details == {}


def test_exception_inheritance():
    """Test all custom exceptions inherit from DetectionError."""
    from src.mcp_servers.first_crack_detection.models import (
        DetectionError,
        ModelNotFoundError,
        MicrophoneNotAvailableError,
        FileNotFoundError,
        SessionAlreadyActiveError,
        ThreadCrashError,
        InvalidAudioSourceError
    )
    
    # All should be instances of DetectionError
    assert issubclass(ModelNotFoundError, DetectionError)
    assert issubclass(MicrophoneNotAvailableError, DetectionError)
    assert issubclass(FileNotFoundError, DetectionError)
    assert issubclass(SessionAlreadyActiveError, DetectionError)
    assert issubclass(ThreadCrashError, DetectionError)
    assert issubclass(InvalidAudioSourceError, DetectionError)


def test_exception_can_be_caught_as_detection_error():
    """Test that specific exceptions can be caught as DetectionError."""
    from src.mcp_servers.first_crack_detection.models import (
        DetectionError,
        ModelNotFoundError
    )
    
    try:
        raise ModelNotFoundError("Test")
    except DetectionError as e:
        assert e.error_code == "MODEL_NOT_FOUND"
        assert True  # Successfully caught
    except Exception:
        pytest.fail("Should have been caught as DetectionError")


def test_exception_repr():
    """Test exception __repr__ is helpful."""
    from src.mcp_servers.first_crack_detection.models import ModelNotFoundError
    
    error = ModelNotFoundError("Test message")
    repr_str = repr(error)
    assert "ModelNotFoundError" in repr_str
    assert "MODEL_NOT_FOUND" in repr_str
