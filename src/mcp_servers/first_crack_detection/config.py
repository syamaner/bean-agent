"""
Configuration loading and management.
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from .models import ServerConfig


def load_config(config_path: Optional[str] = None) -> ServerConfig:
    """
    Load configuration from file and environment variables.
    
    Priority: env vars > config file > defaults
    
    Args:
        config_path: Path to JSON config file (optional)
        
    Returns:
        ServerConfig: Validated configuration
        
    Raises:
        FileNotFoundError: If config_path provided but doesn't exist
        ValueError: If config file contains invalid JSON
    """
    config_data: Dict[str, Any] = {}
    
    # Step 1: Load from file if provided
    if config_path is not None:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with open(path, 'r') as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
    
    # Step 2: Apply environment variable overrides
    # Model checkpoint
    if 'FIRST_CRACK_MODEL_CHECKPOINT' in os.environ:
        config_data['model_checkpoint'] = os.environ['FIRST_CRACK_MODEL_CHECKPOINT']
    
    # Log level
    if 'FIRST_CRACK_LOG_LEVEL' in os.environ:
        config_data['log_level'] = os.environ['FIRST_CRACK_LOG_LEVEL']
    
    # Step 3: Flatten nested config if present
    # Handle detection_defaults nesting
    if 'detection_defaults' in config_data:
        defaults = config_data.pop('detection_defaults')
        if 'threshold' in defaults:
            config_data['default_threshold'] = defaults['threshold']
        if 'min_pops' in defaults:
            config_data['default_min_pops'] = defaults['min_pops']
        if 'confirmation_window' in defaults:
            config_data['default_confirmation_window'] = defaults['confirmation_window']
    
    # Handle audio nesting (for future use - currently ServerConfig doesn't have these fields)
    if 'audio' in config_data:
        # For now, just remove it since ServerConfig doesn't have audio fields
        config_data.pop('audio')
    
    # Step 3: Set defaults if not provided
    if 'model_checkpoint' not in config_data:
        # Default to most recent best model
        config_data['model_checkpoint'] = 'experiments/runs/10s_70overlap_v1/checkpoints/best_model.pt'
    
    if 'log_level' not in config_data:
        config_data['log_level'] = 'INFO'
    
    # Step 5: Validate and create ServerConfig
    # Pydantic will validate and raise ValidationError if invalid
    return ServerConfig(**config_data)


def get_default_config_path() -> Path:
    """
    Get the default configuration file path.
    
    Returns:
        Path: Default config path
    """
    # Return path relative to project root
    # Assume config is at config/first_crack_detection/config.json
    return Path('config/first_crack_detection/config.json')
