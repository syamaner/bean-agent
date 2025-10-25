"""
Tests for audio device discovery and validation.

Following TDD approach:
1. Write tests first (RED) - ensure they fail for the RIGHT reason
2. Implement audio device functions (GREEN)
3. Refactor (REFACTOR)
"""
import pytest
from unittest.mock import Mock, patch


def test_list_audio_devices_returns_list():
    """Test list_audio_devices returns a list of devices."""
    from src.mcp_servers.first_crack_detection.audio_devices import list_audio_devices
    
    with patch('sounddevice.query_devices') as mock_query:
        # Mock return value
        mock_query.return_value = [
            {"name": "Built-in Microphone", "max_input_channels": 2},
            {"name": "USB Audio Device", "max_input_channels": 2},
            {"name": "Built-in Output", "max_input_channels": 0}  # Output only
        ]
        
        devices = list_audio_devices()
        
        assert isinstance(devices, list)
        assert len(devices) == 2  # Only input devices
        assert all("name" in dev for dev in devices)
        assert all("channels" in dev for dev in devices)


def test_list_audio_devices_filters_output_only():
    """Test that output-only devices are filtered out."""
    from src.mcp_servers.first_crack_detection.audio_devices import list_audio_devices
    
    with patch('sounddevice.query_devices') as mock_query:
        mock_query.return_value = [
            {"name": "Microphone", "max_input_channels": 1},
            {"name": "Speaker", "max_input_channels": 0}
        ]
        
        devices = list_audio_devices()
        
        assert len(devices) == 1
        assert devices[0]["name"] == "Microphone"


def test_find_usb_microphone_returns_index():
    """Test find_usb_microphone returns device index for USB mic."""
    from src.mcp_servers.first_crack_detection.audio_devices import find_usb_microphone
    
    with patch('src.mcp_servers.first_crack_detection.audio_devices.list_audio_devices') as mock_list:
        mock_list.return_value = [
            {"index": 0, "name": "Built-in Microphone", "default": True},
            {"index": 1, "name": "USB Audio Device", "default": False},
        ]
        
        result = find_usb_microphone()
        
        assert result == 1
        assert isinstance(result, int)


def test_find_usb_microphone_case_insensitive():
    """Test USB detection is case-insensitive."""
    from src.mcp_servers.first_crack_detection.audio_devices import find_usb_microphone
    
    with patch('src.mcp_servers.first_crack_detection.audio_devices.list_audio_devices') as mock_list:
        mock_list.return_value = [
            {"index": 0, "name": "usb microphone", "default": False},
        ]
        
        result = find_usb_microphone()
        assert result == 0


def test_find_usb_microphone_returns_none_if_not_found():
    """Test find_usb_microphone returns None when no USB mic exists."""
    from src.mcp_servers.first_crack_detection.audio_devices import find_usb_microphone
    
    with patch('src.mcp_servers.first_crack_detection.audio_devices.list_audio_devices') as mock_list:
        mock_list.return_value = [
            {"index": 0, "name": "Built-in Microphone", "default": True},
        ]
        
        result = find_usb_microphone()
        assert result is None


def test_find_usb_microphone_skips_default_device():
    """Test USB detection skips default device (usually built-in)."""
    from src.mcp_servers.first_crack_detection.audio_devices import find_usb_microphone
    
    with patch('src.mcp_servers.first_crack_detection.audio_devices.list_audio_devices') as mock_list:
        mock_list.return_value = [
            {"index": 0, "name": "USB Audio (default)", "default": True},  # Skip this
            {"index": 1, "name": "USB Microphone", "default": False},
        ]
        
        result = find_usb_microphone()
        assert result == 1  # Should return the non-default USB device


def test_find_builtin_microphone_returns_default():
    """Test find_builtin_microphone returns default input device."""
    from src.mcp_servers.first_crack_detection.audio_devices import find_builtin_microphone
    
    with patch('sounddevice.default.device', [2, 5]):  # [input, output]
        result = find_builtin_microphone()
        assert result == 2


def test_find_builtin_microphone_returns_none_on_error():
    """Test find_builtin_microphone returns None if no default exists."""
    from src.mcp_servers.first_crack_detection.audio_devices import find_builtin_microphone
    
    with patch('sounddevice.default') as mock_default:
        # Simulate exception when accessing device attribute
        type(mock_default).device = property(lambda self: (_ for _ in ()).throw(Exception("No default")))
        
        result = find_builtin_microphone()
        assert result is None


def test_get_device_info_returns_details():
    """Test get_device_info returns device details."""
    from src.mcp_servers.first_crack_detection.audio_devices import get_device_info
    
    with patch('sounddevice.query_devices') as mock_query:
        mock_query.return_value = {
            "name": "Test Device",
            "max_input_channels": 2,
            "default_samplerate": 44100
        }
        
        info = get_device_info(1)
        
        assert info["name"] == "Test Device"
        assert info["max_input_channels"] == 2
        mock_query.assert_called_once_with(1)


def test_validate_audio_source_audio_file_valid():
    """Test validate_audio_source with valid audio file."""
    from src.mcp_servers.first_crack_detection.audio_devices import validate_audio_source
    from src.mcp_servers.first_crack_detection.models import AudioConfig
    
    config = AudioConfig(
        audio_source_type="audio_file",
        audio_file_path="/path/to/test.wav"
    )
    
    with patch('pathlib.Path.exists', return_value=True):
        is_valid, details = validate_audio_source(config)
        
        assert is_valid is True
        assert "/path/to/test.wav" in details


def test_validate_audio_source_audio_file_not_found():
    """Test validate_audio_source with missing audio file."""
    from src.mcp_servers.first_crack_detection.audio_devices import validate_audio_source
    from src.mcp_servers.first_crack_detection.models import AudioConfig
    
    config = AudioConfig(
        audio_source_type="audio_file",
        audio_file_path="/nonexistent/file.wav"
    )
    
    with patch('pathlib.Path.exists', return_value=False):
        is_valid, details = validate_audio_source(config)
        
        assert is_valid is False
        assert "not found" in details.lower() or "nonexistent" in details


def test_validate_audio_source_usb_microphone_found():
    """Test validate_audio_source with available USB microphone."""
    from src.mcp_servers.first_crack_detection.audio_devices import validate_audio_source
    from src.mcp_servers.first_crack_detection.models import AudioConfig
    
    config = AudioConfig(audio_source_type="usb_microphone")
    
    with patch('src.mcp_servers.first_crack_detection.audio_devices.find_usb_microphone', return_value=1):
        with patch('src.mcp_servers.first_crack_detection.audio_devices.get_device_info') as mock_info:
            mock_info.return_value = {"name": "USB Audio Device"}
            
            is_valid, details = validate_audio_source(config)
            
            assert is_valid is True
            assert "USB Audio Device" in details


def test_validate_audio_source_usb_microphone_not_found():
    """Test validate_audio_source when USB microphone is not available."""
    from src.mcp_servers.first_crack_detection.audio_devices import validate_audio_source
    from src.mcp_servers.first_crack_detection.models import AudioConfig
    
    config = AudioConfig(audio_source_type="usb_microphone")
    
    with patch('src.mcp_servers.first_crack_detection.audio_devices.find_usb_microphone', return_value=None):
        is_valid, details = validate_audio_source(config)
        
        assert is_valid is False
        assert "usb" in details.lower() or "not found" in details.lower()


def test_validate_audio_source_builtin_microphone_found():
    """Test validate_audio_source with built-in microphone."""
    from src.mcp_servers.first_crack_detection.audio_devices import validate_audio_source
    from src.mcp_servers.first_crack_detection.models import AudioConfig
    
    config = AudioConfig(audio_source_type="builtin_microphone")
    
    with patch('src.mcp_servers.first_crack_detection.audio_devices.find_builtin_microphone', return_value=0):
        with patch('src.mcp_servers.first_crack_detection.audio_devices.get_device_info') as mock_info:
            mock_info.return_value = {"name": "Built-in Microphone"}
            
            is_valid, details = validate_audio_source(config)
            
            assert is_valid is True
            assert "Built-in Microphone" in details


def test_validate_audio_source_builtin_microphone_not_found():
    """Test validate_audio_source when built-in microphone is not available."""
    from src.mcp_servers.first_crack_detection.audio_devices import validate_audio_source
    from src.mcp_servers.first_crack_detection.models import AudioConfig
    
    config = AudioConfig(audio_source_type="builtin_microphone")
    
    with patch('src.mcp_servers.first_crack_detection.audio_devices.find_builtin_microphone', return_value=None):
        is_valid, details = validate_audio_source(config)
        
        assert is_valid is False
        assert "built-in" in details.lower() or "not found" in details.lower()


def test_validate_audio_source_invalid_type():
    """Test validate_audio_source with invalid audio source type."""
    from src.mcp_servers.first_crack_detection.audio_devices import validate_audio_source
    from unittest.mock import Mock
    
    # Create a mock config with invalid type (bypassing Pydantic validation for this test)
    config = Mock()
    config.audio_source_type = "invalid_type"
    
    is_valid, details = validate_audio_source(config)
    
    assert is_valid is False
    assert "invalid" in details.lower()
