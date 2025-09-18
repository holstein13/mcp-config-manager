"""
Backup functionality for MCP configurations
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from .file_utils import get_disabled_servers_path, get_project_backups_dir


def create_backup(config_path: Path, backup_suffix: str = None, backup_dir: Path = None) -> Path:
    """Create a timestamped backup of a config file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    if backup_suffix is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_suffix = f"backup.{timestamp}"
    
    # Use provided backup directory or default to same directory as source
    if backup_dir is None:
        backup_dir = config_path.parent
    
    # Ensure backup directory exists
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    backup_path = backup_dir / f"{config_path.name}.{backup_suffix}"
    shutil.copy(config_path, backup_path)  # Use copy instead of copy2 to get current timestamps
    return backup_path


def backup_all_configs(claude_path: Path, gemini_path: Path, codex_path: Path = None) -> List[Tuple[str, Path]]:
    """Create simple-named backups of all config files in the project backups directory.

    Args:
        codex_path: Optional path to Codex config.toml file for three-way backup
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backups_dir = get_project_backups_dir()
    backups_dir.mkdir(parents=True, exist_ok=True)
    backups = []
    
    # Backup Claude config with simple naming
    if claude_path.exists():
        claude_backup = backups_dir / f"claude-backup-{timestamp}.json"
        shutil.copy(claude_path, claude_backup)  # Use copy instead of copy2 to get current timestamps
        backups.append(('Claude', claude_backup))

    # Backup Gemini config with simple naming
    if gemini_path.exists():
        gemini_backup = backups_dir / f"gemini-backup-{timestamp}.json"
        shutil.copy(gemini_path, gemini_backup)  # Use copy instead of copy2 to get current timestamps
        backups.append(('Gemini', gemini_backup))

    # Backup Codex config with simple naming (TOML format)
    if codex_path and codex_path.exists():
        codex_backup = backups_dir / f"codex-backup-{timestamp}.toml"
        shutil.copy(codex_path, codex_backup)  # Use copy instead of copy2 to get current timestamps
        backups.append(('Codex', codex_backup))

    # Backup disabled servers file with simple naming
    disabled_path = get_disabled_servers_path()
    if disabled_path.exists():
        disabled_backup = backups_dir / f"disabled-backup-{timestamp}.json"
        shutil.copy(disabled_path, disabled_backup)  # Use copy instead of copy2 to get current timestamps
        backups.append(('Disabled Servers', disabled_backup))
    
    return backups


def list_backups(config_type: str = 'all') -> List[Path]:
    """List backup files of specified type from the backups directory.
    
    Args:
        config_type: 'claude', 'gemini', 'codex', 'disabled', or 'all'
    """
    backups_dir = get_project_backups_dir()
    if not backups_dir.exists():
        return []
    
    if config_type == 'claude':
        pattern = "claude-backup-*.json"
    elif config_type == 'gemini':
        pattern = "gemini-backup-*.json"
    elif config_type == 'codex':
        pattern = "codex-backup-*.toml"
    elif config_type == 'disabled':
        pattern = "disabled-backup-*.json"
    else:  # 'all'
        claude_backups = sorted(backups_dir.glob("claude-backup-*.json"), reverse=True)
        gemini_backups = sorted(backups_dir.glob("gemini-backup-*.json"), reverse=True)
        codex_backups = sorted(backups_dir.glob("codex-backup-*.toml"), reverse=True)
        disabled_backups = sorted(backups_dir.glob("disabled-backup-*.json"), reverse=True)
        return claude_backups + gemini_backups + codex_backups + disabled_backups
    
    return sorted(backups_dir.glob(pattern), reverse=True)


def restore_backup(backup_path: Path, target_path: Path) -> None:
    """Restore a config from backup.

    Supports both JSON and TOML backup files.
    """
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    # Validate backup format matches target
    backup_ext = backup_path.suffix.lower()
    target_ext = target_path.suffix.lower()

    if backup_ext != target_ext:
        # Allow restoring TOML to TOML and JSON to JSON only
        raise ValueError(f"Cannot restore {backup_ext} backup to {target_ext} config")

    shutil.copy(backup_path, target_path)  # Use copy instead of copy2 to get current timestamps


def restore_from_backup(backup_path: Path, claude_path: Path = None,
                       gemini_path: Path = None, codex_path: Path = None) -> List[Tuple[str, Path]]:
    """Restore configs from a backup file based on its naming convention.

    Automatically detects the backup type and restores to the appropriate location.

    Returns:
        List of tuples (config_type, restored_path) for each restored config
    """
    restored = []
    backup_name = backup_path.name

    if backup_name.startswith("claude-backup-") and backup_name.endswith(".json"):
        if claude_path:
            restore_backup(backup_path, claude_path)
            restored.append(('Claude', claude_path))
    elif backup_name.startswith("gemini-backup-") and backup_name.endswith(".json"):
        if gemini_path:
            restore_backup(backup_path, gemini_path)
            restored.append(('Gemini', gemini_path))
    elif backup_name.startswith("codex-backup-") and backup_name.endswith(".toml"):
        if codex_path:
            restore_backup(backup_path, codex_path)
            restored.append(('Codex', codex_path))
    elif backup_name.startswith("disabled-backup-") and backup_name.endswith(".json"):
        disabled_path = get_disabled_servers_path()
        restore_backup(backup_path, disabled_path)
        restored.append(('Disabled Servers', disabled_path))
    else:
        raise ValueError(f"Unknown backup type: {backup_name}")

    return restored


def validate_backup(backup_path: Path) -> Tuple[bool, str]:
    """Validate a backup file.

    Returns:
        tuple: (is_valid, error_message or backup_type)
    """
    if not backup_path.exists():
        return False, "Backup file does not exist"

    backup_name = backup_path.name

    # Check file naming and extension
    if backup_name.startswith("claude-backup-"):
        if not backup_name.endswith(".json"):
            return False, "Claude backup should be JSON format"
        return True, "claude"
    elif backup_name.startswith("gemini-backup-"):
        if not backup_name.endswith(".json"):
            return False, "Gemini backup should be JSON format"
        return True, "gemini"
    elif backup_name.startswith("codex-backup-"):
        if not backup_name.endswith(".toml"):
            return False, "Codex backup should be TOML format"
        # Try to validate TOML format
        try:
            import toml
            with backup_path.open('r', encoding='utf-8') as f:
                toml.load(f)
            return True, "codex"
        except Exception as e:
            return False, f"Invalid TOML format: {e}"
    elif backup_name.startswith("disabled-backup-"):
        if not backup_name.endswith(".json"):
            return False, "Disabled servers backup should be JSON format"
        return True, "disabled"
    else:
        return False, "Unknown backup type"
