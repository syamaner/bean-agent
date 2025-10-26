"""
Tests for DetectionSessionManager.

Following TDD approach - comprehensive test coverage for:
- Session lifecycle (start, status, stop)
- Thread safety
- Idempotency
- Error handling
- Validation
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import time


@pytest.fixture
def server_config():
    """Server configuration fixture."""
    from src.mcp_servers.first_crack_detection.models import ServerConfig
    return ServerConfig(
        model_checkpoint="test_model.pt",
        log_level="INFO"
    )


@pytest.fixture
def audio_config_file():
    """Audio file configuration fixture."""
    from src.mcp_servers.first_crack_detection.models import AudioConfig
    return AudioConfig(
        audio_source_type="audio_file",
        audio_file_path="test_audio.wav"
    )


@pytest.fixture
def audio_config_usb():
    """USB microphone configuration fixture."""
    from src.mcp_servers.first_crack_detection.models import AudioConfig
    return AudioConfig(
        audio_source_type="usb_microphone"
    )


def test_session_manager_initialization(server_config):
    """Test SessionManager initializes correctly."""
    from src.mcp_servers.first_crack_detection.session_manager import DetectionSessionManager
    
    manager = DetectionSessionManager(server_config)
    
    assert manager.config == server_config
    assert manager.current_session is None


def test_start_session_creates_new_session(server_config, audio_config_file):
    """Test starting a new detection session."""
    from src.mcp_servers.first_crack_detection.session_manager import DetectionSessionManager
    
    with patch('src.mcp_servers.first_crack_detection.session_manager.Path.exists', return_value=True):
        with patch('src.mcp_servers.first_crack_detection.session_manager.FirstCrackDetector') as mock_detector_class:
            mock_detector = Mock()
            mock_detector_class.return_value = mock_detector
            
            manager = DetectionSessionManager(server_config)
            result = manager.start_session(audio_config_file)
            
            assert result.session_state == "started"
            assert result.session_id is not None
            assert result.audio_source == "audio_file"
            assert manager.current_session is not None


def test_start_session_idempotent_when_already_running(server_config, audio_config_file):
    """Test starting session when one is already active returns already_running."""
    from src.mcp_servers.first_crack_detection.session_manager import DetectionSessionManager
    
    with patch('src.mcp_servers.first_crack_detection.session_manager.Path.exists', return_value=True):
        with patch('src.mcp_servers.first_crack_detection.session_manager.FirstCrackDetector') as mock_detector_class:
            mock_detector = Mock()
            mock_detector_class.return_value = mock_detector
            
            manager = DetectionSessionManager(server_config)
            
            # Start first session
            result1 = manager.start_session(audio_config_file)
            session_id1 = result1.session_id
            
            # Try to start second session
            result2 = manager.start_session(audio_config_file)
            
            assert result2.session_state == "already_running"
            assert result2.session_id == session_id1


def test_start_session_validates_model_checkpoint(server_config, audio_config_file):
    """Test start_session raises error if model checkpoint doesn't exist."""
    from src.mcp_servers.first_crack_detection.session_manager import DetectionSessionManager
    from src.mcp_servers.first_crack_detection.models import ModelNotFoundError
    
    with patch('src.mcp_servers.first_crack_detection.session_manager.Path.exists', return_value=False):
        manager = DetectionSessionManager(server_config)
        
        with pytest.raises(ModelNotFoundError):
            manager.start_session(audio_config_file)


def test_start_session_validates_audio_file(server_config):
    """Test start_session raises error if audio file doesn't exist."""
    from src.mcp_servers.first_crack_detection.session_manager import DetectionSessionManager
    from src.mcp_servers.first_crack_detection.models import AudioConfig, FileNotFoundError as FCFileNotFoundError
    
    audio_config = AudioConfig(
        audio_source_type="audio_file",
        audio_file_path="/nonexistent/file.wav"
    )
    
    with patch('src.mcp_servers.first_crack_detection.session_manager.Path.exists', side_effect=[True, False]):
        manager = DetectionSessionManager(server_config)
        
        with pytest.raises(FCFileNotFoundError):
            manager.start_session(audio_config)


def test_get_status_no_active_session(server_config):
    """Test get_status when no session is active."""
    from src.mcp_servers.first_crack_detection.session_manager import DetectionSessionManager
    
    manager = DetectionSessionManager(server_config)
    status = manager.get_status()
    
    assert status.session_active is False
    assert status.session_id is None
    assert status.first_crack_detected is False


def test_get_status_with_active_session(server_config, audio_config_file):
    """Test get_status with active session."""
    from src.mcp_servers.first_crack_detection.session_manager import DetectionSessionManager
    
    with patch('src.mcp_servers.first_crack_detection.session_manager.Path.exists', return_value=True):
        with patch('src.mcp_servers.first_crack_detection.session_manager.FirstCrackDetector') as mock_detector_class:
            mock_detector = Mock()
            mock_detector.is_first_crack.return_value = (False, None)
            mock_detector_class.return_value = mock_detector
            
            manager = DetectionSessionManager(server_config)
            session_info = manager.start_session(audio_config_file)
            
            time.sleep(0.1)  # Small delay
            
            status = manager.get_status()
            
            assert status.session_active is True
            assert status.session_id == session_info.session_id
            assert status.elapsed_time is not None
            assert status.first_crack_detected is False


def test_get_status_with_first_crack_detected(server_config, audio_config_file):
    """Test get_status when first crack is detected."""
    from src.mcp_servers.first_crack_detection.session_manager import DetectionSessionManager
    
    with patch('src.mcp_servers.first_crack_detection.session_manager.Path.exists', return_value=True):
        with patch('src.mcp_servers.first_crack_detection.session_manager.FirstCrackDetector') as mock_detector_class:
            mock_detector = Mock()
            mock_detector.is_first_crack.return_value = (True, "05:30")
            mock_detector_class.return_value = mock_detector
            
            manager = DetectionSessionManager(server_config)
            manager.start_session(audio_config_file)
            
            status = manager.get_status()
            
            assert status.session_active is True
            assert status.first_crack_detected is True
            assert status.first_crack_time_relative == "05:30"
            assert status.first_crack_time_utc is not None


def test_stop_session_stops_active_session(server_config, audio_config_file):
    """Test stop_session stops active session."""
    from src.mcp_servers.first_crack_detection.session_manager import DetectionSessionManager
    
    with patch('src.mcp_servers.first_crack_detection.session_manager.Path.exists', return_value=True):
        with patch('src.mcp_servers.first_crack_detection.session_manager.FirstCrackDetector') as mock_detector_class:
            mock_detector = Mock()
            mock_detector.is_first_crack.return_value = (False, None)
            mock_detector_class.return_value = mock_detector
            
            manager = DetectionSessionManager(server_config)
            session_info = manager.start_session(audio_config_file)
            
            summary = manager.stop_session()
            
            assert summary.session_state == "stopped"
            assert summary.session_id == session_info.session_id
            assert summary.session_summary is not None
            assert manager.current_session is None


def test_stop_session_idempotent_when_no_session(server_config):
    """Test stop_session when no session is active."""
    from src.mcp_servers.first_crack_detection.session_manager import DetectionSessionManager
    
    manager = DetectionSessionManager(server_config)
    summary = manager.stop_session()
    
    assert summary.session_state == "no_active_session"
    assert summary.session_id is None


def test_session_manager_thread_safe(server_config, audio_config_file):
    """Test session manager is thread-safe."""
    from src.mcp_servers.first_crack_detection.session_manager import DetectionSessionManager
    import threading
    
    with patch('src.mcp_servers.first_crack_detection.session_manager.Path.exists', return_value=True):
        with patch('src.mcp_servers.first_crack_detection.session_manager.FirstCrackDetector') as mock_detector_class:
            mock_detector = Mock()
            mock_detector_class.return_value = mock_detector
            
            manager = DetectionSessionManager(server_config)
            results = []
            
            def start_session():
                result = manager.start_session(audio_config_file)
                results.append(result)
            
            # Try to start multiple sessions concurrently
            threads = [threading.Thread(target=start_session) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            # Only one should be "started", others "already_running"
            started_count = sum(1 for r in results if r.session_state == "started")
            assert started_count == 1


def test_validate_audio_source_usb_microphone(server_config, audio_config_usb):
    """Test validation of USB microphone availability."""
    from src.mcp_servers.first_crack_detection.session_manager import DetectionSessionManager
    from src.mcp_servers.first_crack_detection.models import MicrophoneNotAvailableError
    
    with patch('src.mcp_servers.first_crack_detection.session_manager.Path.exists', return_value=True):
        with patch('src.mcp_servers.first_crack_detection.session_manager.find_usb_microphone', return_value=None):
            manager = DetectionSessionManager(server_config)
            
            with pytest.raises(MicrophoneNotAvailableError):
                manager.start_session(audio_config_usb)


def test_session_timestamps_in_utc_and_local(server_config, audio_config_file):
    """Test session timestamps are provided in both UTC and local time."""
    from src.mcp_servers.first_crack_detection.session_manager import DetectionSessionManager
    
    with patch('src.mcp_servers.first_crack_detection.session_manager.Path.exists', return_value=True):
        with patch('src.mcp_servers.first_crack_detection.session_manager.FirstCrackDetector') as mock_detector_class:
            mock_detector = Mock()
            mock_detector_class.return_value = mock_detector
            
            manager = DetectionSessionManager(server_config)
            result = manager.start_session(audio_config_file)
            
            assert result.started_at_utc is not None
            assert result.started_at_local is not None
            assert result.started_at_utc.tzinfo == timezone.utc
            # Local time should have different timezone than UTC (unless system is UTC)
            assert result.started_at_local.tzinfo is not None
