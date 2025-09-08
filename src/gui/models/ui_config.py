"""UI configuration model for MCP Config Manager GUI."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple


class Theme(Enum):
    """UI theme options."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class IconSet(Enum):
    """Icon set options."""
    DEFAULT = "default"
    MATERIAL = "material"
    FLUENT = "fluent"


@dataclass
class WindowGeometry:
    """Window position and size."""
    x: int = 100
    y: int = 100
    width: int = 800
    height: int = 600
    maximized: bool = False
    
    def to_tuple(self) -> Tuple[int, int, int, int]:
        """Return geometry as tuple (x, y, width, height)."""
        return (self.x, self.y, self.width, self.height)
    
    def from_tuple(self, geometry: Tuple[int, int, int, int]) -> None:
        """Set geometry from tuple."""
        self.x, self.y, self.width, self.height = geometry


@dataclass
class UIConfiguration:
    """UI configuration and preferences."""
    
    # Theme settings
    theme: Theme = Theme.SYSTEM
    icon_set: IconSet = IconSet.DEFAULT
    custom_colors: Dict[str, str] = field(default_factory=dict)
    
    # Window settings
    window_geometry: WindowGeometry = field(default_factory=WindowGeometry)
    remember_window_position: bool = True
    start_maximized: bool = False
    always_on_top: bool = False
    
    # Layout settings
    show_toolbar: bool = True
    show_statusbar: bool = True
    show_sidebar: bool = False
    sidebar_width: int = 200
    server_list_view_mode: str = "list"  # "list", "grid", "compact"
    
    # Display settings
    font_family: str = "System"
    font_size: int = 10
    show_server_icons: bool = True
    show_server_descriptions: bool = True
    compact_mode: bool = False
    
    # Behavior settings
    confirm_before_save: bool = False
    confirm_before_delete: bool = True
    auto_save: bool = False
    auto_save_interval: int = 300  # seconds
    restore_last_session: bool = True
    
    # Animation settings
    enable_animations: bool = True
    animation_speed: float = 1.0  # 0.5 = slow, 1.0 = normal, 2.0 = fast
    
    # Keyboard shortcuts
    shortcuts: Dict[str, str] = field(default_factory=lambda: {
        "save": "Ctrl+S",
        "quit": "Ctrl+Q",
        "toggle_server": "Space",
        "select_all": "Ctrl+A",
        "deselect_all": "Ctrl+D",
        "enable_all": "Ctrl+E",
        "disable_all": "Ctrl+Shift+E",
        "add_server": "Ctrl+N",
        "remove_server": "Delete",
        "search": "Ctrl+F",
        "preset_manager": "Ctrl+P",
        "backup_restore": "Ctrl+B",
        "settings": "Ctrl+,",
        "refresh": "F5",
        "mode_claude": "Ctrl+1",
        "mode_gemini": "Ctrl+2",
        "mode_both": "Ctrl+3",
    })
    
    # Search settings
    search_case_sensitive: bool = False
    search_regex: bool = False
    search_highlight: bool = True
    
    # Notification settings
    show_notifications: bool = True
    notification_position: str = "bottom-right"  # "top-left", "top-right", "bottom-left", "bottom-right"
    notification_duration: int = 3000  # milliseconds
    
    # Advanced settings
    debug_mode: bool = False
    log_level: str = "INFO"
    check_for_updates: bool = True
    telemetry_enabled: bool = False
    
    def apply_theme(self, theme: Theme) -> None:
        """Apply a theme to the configuration."""
        self.theme = theme
        if theme == Theme.DARK:
            self.custom_colors = {
                "background": "#1e1e1e",
                "foreground": "#cccccc",
                "accent": "#007acc",
                "success": "#4caf50",
                "warning": "#ff9800",
                "error": "#f44336",
                "border": "#3c3c3c",
                "selection": "#2d2d30",
            }
        elif theme == Theme.LIGHT:
            self.custom_colors = {
                "background": "#ffffff",
                "foreground": "#000000",
                "accent": "#0078d4",
                "success": "#107c10",
                "warning": "#ff8c00",
                "error": "#e81123",
                "border": "#e0e0e0",
                "selection": "#e8f4fd",
            }
    
    def get_color(self, color_key: str, default: str = "#000000") -> str:
        """Get a custom color value."""
        return self.custom_colors.get(color_key, default)
    
    def set_color(self, color_key: str, color_value: str) -> None:
        """Set a custom color value."""
        self.custom_colors[color_key] = color_value
    
    def reset_colors(self) -> None:
        """Reset colors to theme defaults."""
        self.apply_theme(self.theme)
    
    def get_shortcut(self, action: str) -> Optional[str]:
        """Get keyboard shortcut for an action."""
        return self.shortcuts.get(action)
    
    def set_shortcut(self, action: str, shortcut: str) -> None:
        """Set keyboard shortcut for an action."""
        self.shortcuts[action] = shortcut
    
    def reset_shortcuts(self) -> None:
        """Reset shortcuts to defaults."""
        self.shortcuts = {
            "save": "Ctrl+S",
            "quit": "Ctrl+Q",
            "toggle_server": "Space",
            "select_all": "Ctrl+A",
            "deselect_all": "Ctrl+D",
            "enable_all": "Ctrl+E",
            "disable_all": "Ctrl+Shift+E",
            "add_server": "Ctrl+N",
            "remove_server": "Delete",
            "search": "Ctrl+F",
            "preset_manager": "Ctrl+P",
            "backup_restore": "Ctrl+B",
            "settings": "Ctrl+,",
            "refresh": "F5",
            "mode_claude": "Ctrl+1",
            "mode_gemini": "Ctrl+2",
            "mode_both": "Ctrl+3",
        }
    
    def save_window_geometry(self, x: int, y: int, width: int, height: int, maximized: bool = False) -> None:
        """Save window geometry."""
        if self.remember_window_position:
            self.window_geometry.x = x
            self.window_geometry.y = y
            self.window_geometry.width = width
            self.window_geometry.height = height
            self.window_geometry.maximized = maximized
    
    def get_window_geometry(self) -> Tuple[int, int, int, int]:
        """Get window geometry as tuple."""
        return self.window_geometry.to_tuple()
    
    def is_compact_mode(self) -> bool:
        """Check if compact mode is enabled."""
        return self.compact_mode
    
    def toggle_compact_mode(self) -> None:
        """Toggle compact mode."""
        self.compact_mode = not self.compact_mode
        if self.compact_mode:
            self.show_server_descriptions = False
            self.server_list_view_mode = "compact"
        else:
            self.show_server_descriptions = True
            self.server_list_view_mode = "list"
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        valid = True
        
        # Validate font size
        if not 6 <= self.font_size <= 24:
            self.font_size = 10
            valid = False
        
        # Validate animation speed
        if not 0.1 <= self.animation_speed <= 5.0:
            self.animation_speed = 1.0
            valid = False
        
        # Validate auto-save interval
        if self.auto_save and self.auto_save_interval < 30:
            self.auto_save_interval = 300
            valid = False
        
        # Validate notification duration
        if not 1000 <= self.notification_duration <= 10000:
            self.notification_duration = 3000
            valid = False
        
        # Validate sidebar width
        if not 100 <= self.sidebar_width <= 500:
            self.sidebar_width = 200
            valid = False
        
        return valid
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            "theme": self.theme.value,
            "icon_set": self.icon_set.value,
            "custom_colors": self.custom_colors,
            "window_geometry": {
                "x": self.window_geometry.x,
                "y": self.window_geometry.y,
                "width": self.window_geometry.width,
                "height": self.window_geometry.height,
                "maximized": self.window_geometry.maximized,
            },
            "remember_window_position": self.remember_window_position,
            "start_maximized": self.start_maximized,
            "always_on_top": self.always_on_top,
            "show_toolbar": self.show_toolbar,
            "show_statusbar": self.show_statusbar,
            "show_sidebar": self.show_sidebar,
            "sidebar_width": self.sidebar_width,
            "server_list_view_mode": self.server_list_view_mode,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "show_server_icons": self.show_server_icons,
            "show_server_descriptions": self.show_server_descriptions,
            "compact_mode": self.compact_mode,
            "confirm_before_save": self.confirm_before_save,
            "confirm_before_delete": self.confirm_before_delete,
            "auto_save": self.auto_save,
            "auto_save_interval": self.auto_save_interval,
            "restore_last_session": self.restore_last_session,
            "enable_animations": self.enable_animations,
            "animation_speed": self.animation_speed,
            "shortcuts": self.shortcuts,
            "search_case_sensitive": self.search_case_sensitive,
            "search_regex": self.search_regex,
            "search_highlight": self.search_highlight,
            "show_notifications": self.show_notifications,
            "notification_position": self.notification_position,
            "notification_duration": self.notification_duration,
            "debug_mode": self.debug_mode,
            "log_level": self.log_level,
            "check_for_updates": self.check_for_updates,
            "telemetry_enabled": self.telemetry_enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "UIConfiguration":
        """Create configuration from dictionary."""
        config = cls()
        
        if "theme" in data:
            config.theme = Theme(data["theme"])
        if "icon_set" in data:
            config.icon_set = IconSet(data["icon_set"])
        if "custom_colors" in data:
            config.custom_colors = data["custom_colors"]
        
        if "window_geometry" in data:
            geom = data["window_geometry"]
            config.window_geometry = WindowGeometry(
                x=geom.get("x", 100),
                y=geom.get("y", 100),
                width=geom.get("width", 800),
                height=geom.get("height", 600),
                maximized=geom.get("maximized", False),
            )
        
        # Copy all other settings
        for key in ["remember_window_position", "start_maximized", "always_on_top",
                    "show_toolbar", "show_statusbar", "show_sidebar", "sidebar_width",
                    "server_list_view_mode", "font_family", "font_size",
                    "show_server_icons", "show_server_descriptions", "compact_mode",
                    "confirm_before_save", "confirm_before_delete", "auto_save",
                    "auto_save_interval", "restore_last_session", "enable_animations",
                    "animation_speed", "shortcuts", "search_case_sensitive",
                    "search_regex", "search_highlight", "show_notifications",
                    "notification_position", "notification_duration", "debug_mode",
                    "log_level", "check_for_updates", "telemetry_enabled"]:
            if key in data:
                setattr(config, key, data[key])
        
        config.validate()
        return config