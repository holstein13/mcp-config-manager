"""Backup information model for MCP Config Manager GUI."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class BackupType(Enum):
    """Backup types."""
    MANUAL = "manual"
    AUTO = "auto"
    SCHEDULED = "scheduled"
    PRE_CHANGE = "pre_change"
    RESTORE_POINT = "restore_point"


class BackupStatus(Enum):
    """Backup status states."""
    VALID = "valid"
    CORRUPTED = "corrupted"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class BackupMode(Enum):
    """Backup mode/source."""
    CLAUDE = "claude"
    GEMINI = "gemini"
    BOTH = "both"


@dataclass
class BackupMetadata:
    """Metadata about backup content."""
    server_count: int = 0
    enabled_count: int = 0
    disabled_count: int = 0
    preset_count: int = 0
    has_custom_presets: bool = False
    config_version: Optional[str] = None
    application_version: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "server_count": self.server_count,
            "enabled_count": self.enabled_count,
            "disabled_count": self.disabled_count,
            "preset_count": self.preset_count,
            "has_custom_presets": self.has_custom_presets,
            "config_version": self.config_version,
            "application_version": self.application_version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "BackupMetadata":
        """Create from dictionary."""
        return cls(
            server_count=data.get("server_count", 0),
            enabled_count=data.get("enabled_count", 0),
            disabled_count=data.get("disabled_count", 0),
            preset_count=data.get("preset_count", 0),
            has_custom_presets=data.get("has_custom_presets", False),
            config_version=data.get("config_version"),
            application_version=data.get("application_version"),
        )


@dataclass
class BackupInfo:
    """Represents a backup file."""
    
    # Core properties
    filename: str
    filepath: Path
    backup_type: BackupType = BackupType.MANUAL
    backup_mode: BackupMode = BackupMode.BOTH
    
    # Timestamps
    created_date: datetime = field(default_factory=datetime.now)
    modified_date: Optional[datetime] = None
    
    # Size and status
    file_size: int = 0  # in bytes
    status: BackupStatus = BackupStatus.UNKNOWN
    
    # Display properties
    name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: BackupMetadata = field(default_factory=BackupMetadata)
    
    # State properties
    is_selected: bool = False
    is_current: bool = False
    is_favorite: bool = False
    
    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    checksum: Optional[str] = None
    
    # Additional info
    notes: Optional[str] = None
    restore_count: int = 0
    last_restored: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize derived properties."""
        if not self.name:
            self.name = self._generate_name()
        if not self.description:
            self.description = self._generate_description()
        if isinstance(self.filepath, str):
            self.filepath = Path(self.filepath)
    
    def _generate_name(self) -> str:
        """Generate display name from filename."""
        # Extract timestamp from typical backup filename
        # e.g., .claude.json.backup.20240115_143022
        if ".backup." in self.filename:
            parts = self.filename.split(".backup.")
            if len(parts) > 1:
                timestamp = parts[-1]
                try:
                    # Parse YYYYMMDD_HHMMSS format
                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
        return self.filename
    
    def _generate_description(self) -> str:
        """Generate description based on backup type and metadata."""
        type_descriptions = {
            BackupType.MANUAL: "Manual backup",
            BackupType.AUTO: "Automatic backup",
            BackupType.SCHEDULED: "Scheduled backup",
            BackupType.PRE_CHANGE: "Pre-change backup",
            BackupType.RESTORE_POINT: "Restore point",
        }
        
        desc = type_descriptions.get(self.backup_type, "Backup")
        
        if self.metadata.server_count > 0:
            desc += f" ({self.metadata.server_count} servers"
            if self.metadata.enabled_count > 0:
                desc += f", {self.metadata.enabled_count} enabled"
            desc += ")"
        
        return desc
    
    def get_age_days(self) -> int:
        """Get age of backup in days."""
        age = datetime.now() - self.created_date
        return age.days
    
    def get_age_string(self) -> str:
        """Get human-readable age string."""
        days = self.get_age_days()
        
        if days == 0:
            hours = (datetime.now() - self.created_date).seconds // 3600
            if hours == 0:
                minutes = (datetime.now() - self.created_date).seconds // 60
                return f"{minutes} minutes ago" if minutes != 1 else "1 minute ago"
            return f"{hours} hours ago" if hours != 1 else "1 hour ago"
        elif days == 1:
            return "Yesterday"
        elif days < 7:
            return f"{days} days ago"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} weeks ago" if weeks != 1 else "1 week ago"
        elif days < 365:
            months = days // 30
            return f"{months} months ago" if months != 1 else "1 month ago"
        else:
            years = days // 365
            return f"{years} years ago" if years != 1 else "1 year ago"
    
    def get_size_string(self) -> str:
        """Get human-readable size string."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.2f} GB"
    
    def exists(self) -> bool:
        """Check if backup file exists."""
        return self.filepath.exists() if self.filepath else False
    
    def is_readable(self) -> bool:
        """Check if backup file is readable."""
        if not self.exists():
            return False
        try:
            return self.filepath.is_file() and self.filepath.stat().st_size > 0
        except (OSError, IOError):
            return False
    
    def validate(self) -> bool:
        """Validate backup file."""
        self.validation_errors.clear()
        self.is_valid = True
        
        # Check file existence
        if not self.exists():
            self.validation_errors.append("Backup file does not exist")
            self.status = BackupStatus.UNKNOWN
            self.is_valid = False
            return False
        
        # Check file readability
        if not self.is_readable():
            self.validation_errors.append("Backup file is not readable")
            self.status = BackupStatus.CORRUPTED
            self.is_valid = False
            return False
        
        # Check file size
        try:
            self.file_size = self.filepath.stat().st_size
            if self.file_size == 0:
                self.validation_errors.append("Backup file is empty")
                self.status = BackupStatus.CORRUPTED
                self.is_valid = False
        except (OSError, IOError) as e:
            self.validation_errors.append(f"Cannot read file size: {e}")
            self.status = BackupStatus.UNKNOWN
            self.is_valid = False
        
        # Validate based on age (warn for very old backups)
        age_days = self.get_age_days()
        if age_days > 180:
            self.validation_errors.append(f"Backup is {age_days} days old")
        
        # Set status if valid
        if self.is_valid:
            self.status = BackupStatus.VALID
        
        return self.is_valid
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the backup."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the backup."""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def has_tag(self, tag: str) -> bool:
        """Check if backup has a tag."""
        return tag in self.tags
    
    def toggle_favorite(self) -> None:
        """Toggle favorite status."""
        self.is_favorite = not self.is_favorite
    
    def mark_restored(self) -> None:
        """Mark backup as restored."""
        self.restore_count += 1
        self.last_restored = datetime.now()
    
    def matches_filter(self, filter_text: str, case_sensitive: bool = False) -> bool:
        """Check if backup matches filter text."""
        if not filter_text:
            return True
        
        search_text = filter_text if case_sensitive else filter_text.lower()
        
        # Search in name
        if self.name:
            name = self.name if case_sensitive else self.name.lower()
            if search_text in name:
                return True
        
        # Search in filename
        filename = self.filename if case_sensitive else self.filename.lower()
        if search_text in filename:
            return True
        
        # Search in description
        if self.description:
            desc = self.description if case_sensitive else self.description.lower()
            if search_text in desc:
                return True
        
        # Search in tags
        for tag in self.tags:
            tag_text = tag if case_sensitive else tag.lower()
            if search_text in tag_text:
                return True
        
        # Search in notes
        if self.notes:
            notes = self.notes if case_sensitive else self.notes.lower()
            if search_text in notes:
                return True
        
        return False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "filename": self.filename,
            "filepath": str(self.filepath),
            "backup_type": self.backup_type.value,
            "backup_mode": self.backup_mode.value,
            "created_date": self.created_date.isoformat(),
            "modified_date": self.modified_date.isoformat() if self.modified_date else None,
            "file_size": self.file_size,
            "status": self.status.value,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "metadata": self.metadata.to_dict(),
            "is_favorite": self.is_favorite,
            "checksum": self.checksum,
            "notes": self.notes,
            "restore_count": self.restore_count,
            "last_restored": self.last_restored.isoformat() if self.last_restored else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "BackupInfo":
        """Create from dictionary representation."""
        item = cls(
            filename=data.get("filename", ""),
            filepath=Path(data.get("filepath", "")),
            backup_type=BackupType(data.get("backup_type", "manual")),
            backup_mode=BackupMode(data.get("backup_mode", "both")),
            file_size=data.get("file_size", 0),
            status=BackupStatus(data.get("status", "unknown")),
            name=data.get("name"),
            description=data.get("description"),
            tags=data.get("tags", []),
            is_favorite=data.get("is_favorite", False),
            checksum=data.get("checksum"),
            notes=data.get("notes"),
            restore_count=data.get("restore_count", 0),
        )
        
        # Parse dates
        if data.get("created_date"):
            item.created_date = datetime.fromisoformat(data["created_date"])
        if data.get("modified_date"):
            item.modified_date = datetime.fromisoformat(data["modified_date"])
        if data.get("last_restored"):
            item.last_restored = datetime.fromisoformat(data["last_restored"])
        
        # Parse metadata
        if data.get("metadata"):
            item.metadata = BackupMetadata.from_dict(data["metadata"])
        
        return item
    
    @classmethod
    def from_file(cls, filepath: Path, backup_type: BackupType = BackupType.MANUAL) -> "BackupInfo":
        """Create BackupInfo from file path."""
        if not filepath.exists():
            raise FileNotFoundError(f"Backup file not found: {filepath}")
        
        stat = filepath.stat()
        
        # Determine backup mode from filename
        backup_mode = BackupMode.BOTH
        if "claude" in filepath.name.lower():
            backup_mode = BackupMode.CLAUDE
        elif "gemini" in filepath.name.lower():
            backup_mode = BackupMode.GEMINI
        
        item = cls(
            filename=filepath.name,
            filepath=filepath,
            backup_type=backup_type,
            backup_mode=backup_mode,
            created_date=datetime.fromtimestamp(stat.st_ctime),
            modified_date=datetime.fromtimestamp(stat.st_mtime),
            file_size=stat.st_size,
        )
        
        item.validate()
        return item
    
    def __eq__(self, other) -> bool:
        """Check equality based on filepath."""
        if not isinstance(other, BackupInfo):
            return False
        return self.filepath == other.filepath
    
    def __hash__(self) -> int:
        """Hash based on filepath."""
        return hash(self.filepath)
    
    def __str__(self) -> str:
        """String representation."""
        return f"BackupInfo(name='{self.name}', type={self.backup_type.value}, size={self.get_size_string()})"
    
    def __repr__(self) -> str:
        """Developer representation."""
        return self.__str__()