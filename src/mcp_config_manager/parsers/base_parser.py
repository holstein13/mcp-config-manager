"""
Base class for configuration file parsers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path


class BaseConfigParser(ABC):
    """Abstract base class for configuration parsers"""
    
    @abstractmethod
    def parse(self, config_path: Path) -> Dict[str, Any]:
        """Parse configuration file and return normalized format"""
        pass
    
    @abstractmethod
    def write(self, config: Dict[str, Any], output_path: Path) -> None:
        """Write configuration to file in the appropriate format"""
        pass
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure"""
        pass
