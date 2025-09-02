"""
Configuration management for NuttX builds.
"""

import yaml
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    """Manages NuttX build configurations."""
    
    def __init__(self):
        self.config = {}
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        return self.config
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def validate_config(self) -> bool:
        """Validate configuration."""
        # TODO: Implement configuration validation
        return True
