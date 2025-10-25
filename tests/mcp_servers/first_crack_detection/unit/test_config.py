"""
Tests for configuration loading and management.

Following TDD approach:
1. Write tests first (RED) - ensure they fail for the RIGHT reason
2. Implement configuration manager (GREEN)
3. Refactor (REFACTOR)
"""
import pytest
import json
import tempfile
import os
from pathlib import Path


def test_load_config_from_json_file():
    """Test loading configuration from JSON file."""
    from src.mcp_servers.first_crack_detection.config import load_config
    
    # Create temp config file
    config_data = {
        "model_checkpoint": "/path/to/model.pt",
        "log_level": "DEBUG"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        config = load_config(temp_path)
        
        assert config.model_checkpoint == "/path/to/model.pt"
        assert config.log_level == "DEBUG"
    finally:
        os.unlink(temp_path)


def test_load_config_with_defaults():
    """Test loading configuration uses defaults when file not provided."""
    from src.mcp_servers.first_crack_detection.config import load_config
    
    config = load_config()
    
    # Should have sensible defaults
    assert config.model_checkpoint is not None
    assert config.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]


def test_load_config_env_var_override():
    """Test environment variables override config file."""
    from src.mcp_servers.first_crack_detection.config import load_config
    
    # Create temp config file
    config_data = {
        "model_checkpoint": "/path/from/file.pt",
        "log_level": "INFO"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        # Set environment variable
        os.environ['FIRST_CRACK_MODEL_CHECKPOINT'] = '/path/from/env.pt'
        os.environ['FIRST_CRACK_LOG_LEVEL'] = 'DEBUG'
        
        config = load_config(temp_path)
        
        # Env vars should override file
        assert config.model_checkpoint == "/path/from/env.pt"
        assert config.log_level == "DEBUG"
    finally:
        os.unlink(temp_path)
        os.environ.pop('FIRST_CRACK_MODEL_CHECKPOINT', None)
        os.environ.pop('FIRST_CRACK_LOG_LEVEL', None)


def test_load_config_missing_file_raises_error():
    """Test loading non-existent config file raises error."""
    from src.mcp_servers.first_crack_detection.config import load_config
    
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/config.json")


def test_load_config_invalid_json_raises_error():
    """Test loading invalid JSON raises error."""
    from src.mcp_servers.first_crack_detection.config import load_config
    
    # Create temp file with invalid JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            load_config(temp_path)
    finally:
        os.unlink(temp_path)


def test_load_config_partial_overrides():
    """Test partial configuration with defaults for missing fields."""
    from src.mcp_servers.first_crack_detection.config import load_config
    
    # Only specify model checkpoint
    config_data = {
        "model_checkpoint": "/path/to/model.pt"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        config = load_config(temp_path)
        
        # Should have model from file
        assert config.model_checkpoint == "/path/to/model.pt"
        
        # Should have defaults for others
        assert config.default_threshold == 0.5
        assert config.default_min_pops == 3
        assert config.default_confirmation_window == 30.0
        assert config.log_level == "INFO"
    finally:
        os.unlink(temp_path)


def test_load_config_validation_error():
    """Test configuration validation catches invalid values."""
    from src.mcp_servers.first_crack_detection.config import load_config
    from pydantic import ValidationError
    
    # Create config with invalid threshold (out of range)
    config_data = {
        "model_checkpoint": "/path/to/model.pt",
        "default_threshold": 1.5  # Invalid - should be 0.0-1.0
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        with pytest.raises(ValidationError):
            load_config(temp_path)
    finally:
        os.unlink(temp_path)


def test_load_config_with_full_config():
    """Test loading complete configuration with all fields."""
    from src.mcp_servers.first_crack_detection.config import load_config
    
    config_data = {
        "model_checkpoint": "/experiments/final_model/model.pt",
        "detection_defaults": {
            "threshold": 0.6,
            "min_pops": 5,
            "confirmation_window": 45.0
        },
        "audio": {
            "sample_rate": 16000,
            "window_size": 10.0,
            "overlap": 0.8
        },
        "log_level": "WARNING"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        config = load_config(temp_path)
        
        assert config.model_checkpoint == "/experiments/final_model/model.pt"
        # ServerConfig uses flat structure
        assert config.default_threshold == 0.6
        assert config.default_min_pops == 5
        assert config.default_confirmation_window == 45.0
        # Audio fields not currently in ServerConfig
        assert config.log_level == "WARNING"
    finally:
        os.unlink(temp_path)




def test_load_config_env_var_partial_override():
    """Test environment variable overrides specific field only."""
    from src.mcp_servers.first_crack_detection.config import load_config
    
    config_data = {
        "model_checkpoint": "/path/from/file.pt",
        "log_level": "INFO"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        # Override only log level
        os.environ['FIRST_CRACK_LOG_LEVEL'] = 'ERROR'
        
        config = load_config(temp_path)
        
        # Model from file unchanged
        assert config.model_checkpoint == "/path/from/file.pt"
        # Log level from env var
        assert config.log_level == "ERROR"
    finally:
        os.unlink(temp_path)
        os.environ.pop('FIRST_CRACK_LOG_LEVEL', None)


def test_config_to_dict():
    """Test ServerConfig can be converted to dictionary."""
    from src.mcp_servers.first_crack_detection.config import load_config
    
    config_data = {
        "model_checkpoint": "/path/to/model.pt",
        "log_level": "INFO"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        config = load_config(temp_path)
        config_dict = config.model_dump()
        
        assert isinstance(config_dict, dict)
        assert config_dict['model_checkpoint'] == "/path/to/model.pt"
        assert config_dict['log_level'] == "INFO"
    finally:
        os.unlink(temp_path)


def test_get_default_config_path():
    """Test get_default_config_path returns sensible default."""
    from src.mcp_servers.first_crack_detection.config import get_default_config_path
    
    path = get_default_config_path()
    
    # Should return a Path object
    assert isinstance(path, Path)
    # Should point to config directory
    assert "config" in str(path).lower()
