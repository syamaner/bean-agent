"""
Audio device discovery and validation.

Functions for:
- Listing available audio input devices
- Finding USB and built-in microphones  
- Validating audio sources before use
"""
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import sounddevice as sd


def list_audio_devices() -> List[Dict[str, Any]]:
    """
    List all available audio input devices.
    
    Returns:
        List of device dicts with keys: index, name, channels, default
    """
    devices = sd.query_devices()
    input_devices = []
    
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            input_devices.append({
                "index": i,
                "name": dev["name"],
                "channels": dev["max_input_channels"],
                "default": i == sd.default.device[0] if hasattr(sd.default, 'device') else False
            })
    
    return input_devices


def find_usb_microphone() -> Optional[int]:
    """
    Find first USB audio input device.
    
    Uses heuristic: device name contains "USB" (case-insensitive)
    and is not the default device (usually built-in).
    
    Returns:
        Device index if found, None otherwise
    """
    devices = list_audio_devices()
    
    for dev in devices:
        name_lower = dev["name"].lower()
        # USB device that's not the default (skip built-in that might have USB in name)
        if "usb" in name_lower and not dev["default"]:
            return dev["index"]
    
    return None


def find_builtin_microphone() -> Optional[int]:
    """
    Find built-in (default) microphone.
    
    Returns:
        Default input device index if available, None otherwise
    """
    try:
        default_input = sd.default.device[0]  # [input_device, output_device]
        return default_input
    except Exception:
        return None


def get_device_info(device_index: int) -> Dict[str, Any]:
    """
    Get detailed device information.
    
    Args:
        device_index: Device index to query
        
    Returns:
        Device information dict
    """
    return sd.query_devices(device_index)


def validate_audio_source(config) -> Tuple[bool, str]:
    """
    Validate audio source is available.
    
    Args:
        config: AudioConfig instance
        
    Returns:
        (is_valid, device_name_or_error_message)
    """
    audio_type = config.audio_source_type
    
    if audio_type == "audio_file":
        file_path = Path(config.audio_file_path)
        if file_path.exists():
            return True, str(file_path)
        else:
            return False, f"File not found: {config.audio_file_path}"
    
    elif audio_type == "usb_microphone":
        device_index = find_usb_microphone()
        if device_index is not None:
            device_info = get_device_info(device_index)
            return True, device_info["name"]
        else:
            return False, "No USB microphone found"
    
    elif audio_type == "builtin_microphone":
        device_index = find_builtin_microphone()
        if device_index is not None:
            device_info = get_device_info(device_index)
            return True, device_info["name"]
        else:
            return False, "No built-in microphone found"
    
    else:
        return False, f"Invalid audio source type: {audio_type}"
