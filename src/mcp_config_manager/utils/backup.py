"""
Backup functionality for MCP configurations
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


def create_backup(config_path: Path, backup_suffix: str = None) -> Path:
    """Create a timestamped backup of a config file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    if backup_suffix is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_suffix = f"backup.{timestamp}"
    
    backup_path = config_path.parent / f"{config_path.name}.{backup_suffix}"
    shutil.copy2(config_path, backup_path)
    return backup_path


def backup_all_configs(claude_path: Path, gemini_path: Path) -> List[Tuple[str, Path]]:
    """Create timestamped backups of all config files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = []
    
    # Backup Claude config
    if claude_path.exists():
        claude_backup = create_backup(claude_path, f"backup.{timestamp}")
        backups.append(('Claude', claude_backup))
    
    # Backup Gemini config
    if gemini_path.exists():
        gemini_backup = create_backup(gemini_path, f"backup.{timestamp}")
        backups.append(('Gemini', gemini_backup))
    
    return backups


def list_backups(config_path: Path) -> List[Path]:
    """List all backup files for a given config."""
    backup_pattern = f"{config_path.name}.backup.*"
    return sorted(config_path.parent.glob(backup_pattern), reverse=True)


def restore_backup(backup_path: Path, target_path: Path) -> None:
    """Restore a config from backup."""
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    shutil.copy2(backup_path, target_path)
