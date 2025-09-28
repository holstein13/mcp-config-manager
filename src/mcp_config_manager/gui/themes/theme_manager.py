"""Theme manager for coordinating application-wide theming."""

from typing import Optional, Dict, Callable, Any
import logging

try:
    from PyQt6.QtCore import QObject, pyqtSignal
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QPalette
    USING_QT = True
except ImportError:
    QObject = object
    pyqtSignal = lambda *args: None
    QApplication = None
    QPalette = None
    USING_QT = False

from .semantic_colors import SemanticColors, MacOSColors, validate_contrast, ContrastLevel, calculate_contrast_ratio
from .system_detection import detect_system_theme, monitor_theme_changes
from ..models.ui_config import Theme, UIConfiguration

logger = logging.getLogger(__name__)


class ThemeManager(QObject if USING_QT else object):
    """Manages application themes and color schemes."""

    if USING_QT:
        theme_changed = pyqtSignal(str)  # Emitted when theme changes
        colors_changed = pyqtSignal(dict)  # Emitted when colors update

    def __init__(self):
        """Initialize the theme manager."""
        if USING_QT:
            super().__init__()

        self._current_theme: str = "light"  # 'light', 'dark', or 'system'
        self._system_theme: str = "light"   # Detected system theme
        self._colors: SemanticColors = MacOSColors.light_theme()
        self._ui_config: Optional[UIConfiguration] = None
        self._theme_callbacks: Dict[str, Callable] = {}
        self._monitoring_started: bool = False

    def initialize(self, ui_config: UIConfiguration) -> None:
        """Initialize with UI configuration."""
        self._ui_config = ui_config
        self._current_theme = ui_config.theme.value

        # Detect system theme
        self._system_theme = detect_system_theme()
        logger.info(f"Detected system theme: {self._system_theme}")

        # Apply initial theme
        self._update_colors()

        # Start monitoring system changes if theme is set to system
        if self._current_theme == "system" and not self._monitoring_started:
            self._start_theme_monitoring()

    def set_theme(self, theme: str) -> None:
        """Set the application theme.

        Args:
            theme: 'light', 'dark', or 'system'
        """
        if theme not in ['light', 'dark', 'system']:
            logger.warning(f"Invalid theme: {theme}, using 'light'")
            theme = 'light'

        old_theme = self._current_theme
        self._current_theme = theme

        # Update UI config if available
        if self._ui_config:
            self._ui_config.theme = Theme(theme)

        # Start/stop system monitoring based on theme setting
        if theme == "system" and not self._monitoring_started:
            self._start_theme_monitoring()
        elif theme != "system" and self._monitoring_started:
            self._stop_theme_monitoring()

        # Update colors
        self._update_colors()

        if old_theme != theme:
            logger.info(f"Theme changed from {old_theme} to {theme}")
            if USING_QT:
                self.theme_changed.emit(theme)

            # Notify registered callbacks
            for callback in self._theme_callbacks.values():
                try:
                    callback(theme, self._colors)
                except Exception as e:
                    logger.error(f"Error in theme callback: {e}")

    def get_current_theme(self) -> str:
        """Get the current theme name."""
        return self._current_theme

    def get_effective_theme(self) -> str:
        """Get the effective theme (resolves 'system' to actual theme)."""
        if self._current_theme == "system":
            return self._system_theme if self._system_theme != "unknown" else "light"
        return self._current_theme

    def get_colors(self) -> SemanticColors:
        """Get current semantic colors."""
        return self._colors

    def get_color(self, color_name: str) -> str:
        """Get a specific color value."""
        color_dict = self._colors.to_dict()
        return color_dict.get(color_name, "#000000")

    def register_theme_callback(self, name: str, callback: Callable[[str, SemanticColors], None]) -> None:
        """Register a callback for theme changes.

        Args:
            name: Unique name for the callback
            callback: Function called with (theme_name, colors) when theme changes
        """
        self._theme_callbacks[name] = callback

    def unregister_theme_callback(self, name: str) -> None:
        """Unregister a theme callback."""
        self._theme_callbacks.pop(name, None)

    def generate_stylesheet(self) -> str:
        """Generate QSS stylesheet based on current theme."""
        colors = self._colors.to_dict()

        return f"""
        /* MCP Config Manager - {self.get_effective_theme().title()} Theme */

        QMainWindow {{
            background-color: {colors['bg_primary']};
            color: {colors['text_primary']};
        }}

        QWidget {{
            background-color: {colors['bg_primary']};
            color: {colors['text_primary']};
        }}

        /* Lists and Trees */
        QListWidget, QTreeWidget {{
            background-color: {colors['list_bg']};
            border: 1px solid {colors['border_primary']};
            border-radius: 4px;
            padding: 2px;
            color: {colors['text_primary']};
            selection-background-color: {colors['selection_bg']};
            selection-color: {colors['text_inverse']};
        }}

        QListWidget::item, QTreeWidget::item {{
            padding: 6px;
            border-bottom: 1px solid {colors['separator']};
            color: {colors['text_primary']};
        }}

        QListWidget::item:alternate, QTreeWidget::item:alternate {{
            background-color: {colors['list_alternate']};
        }}

        QListWidget::item:selected, QTreeWidget::item:selected {{
            background-color: {colors['selection_bg']};
            color: {colors['text_inverse']};
        }}

        QListWidget::item:hover, QTreeWidget::item:hover {{
            background-color: {colors['control_hover']};
        }}

        /* Buttons */
        QPushButton {{
            background-color: {colors['control_bg']};
            color: {colors['text_primary']};
            border: 1px solid {colors['control_border']};
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: 500;
        }}

        QPushButton:hover {{
            background-color: {colors['control_hover']};
            border-color: {colors['accent_primary']};
        }}

        QPushButton:pressed {{
            background-color: {colors['control_pressed']};
        }}

        QPushButton:disabled {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_disabled']};
            border-color: {colors['border_secondary']};
        }}

        QPushButton:focus {{
            border: 2px solid {colors['control_focus']};
        }}

        /* Primary/Accent Buttons */
        QPushButton.primary {{
            background-color: {colors['accent_primary']};
            color: {colors['text_inverse']};
            border-color: {colors['accent_primary']};
        }}

        QPushButton.primary:hover {{
            background-color: {colors['accent_secondary']};
        }}

        /* Text Inputs */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {colors['control_bg']};
            border: 1px solid {colors['control_border']};
            border-radius: 4px;
            padding: 4px 8px;
            color: {colors['text_primary']};
            selection-background-color: {colors['selection_bg']};
            selection-color: {colors['text_inverse']};
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid {colors['control_focus']};
            background-color: {colors['control_bg']};
        }}

        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_disabled']};
        }}

        QLineEdit::placeholder {{
            color: {colors['text_secondary']};
        }}

        /* Labels */
        QLabel {{
            color: {colors['text_primary']};
            background: transparent;  /* Prevent odd background blocks */
        }}

        QLabel:disabled {{
            color: {colors['text_disabled']};
            background: transparent;
        }}

        /* Menu Bar */
        QMenuBar {{
            background-color: {colors['toolbar_bg']};
            border-bottom: 1px solid {colors['border_primary']};
            color: {colors['text_primary']};
        }}

        QMenuBar::item {{
            background-color: transparent;
            padding: 4px 8px;
        }}

        QMenuBar::item:selected {{
            background-color: {colors['control_hover']};
        }}

        QMenuBar::item:pressed {{
            background-color: {colors['control_pressed']};
        }}

        /* Menus */
        QMenu {{
            background-color: {colors['bg_tertiary']};
            border: 1px solid {colors['border_primary']};
            border-radius: 4px;
            padding: 4px;
            color: {colors['text_primary']};
        }}

        QMenu::item {{
            padding: 6px 20px;
            border-radius: 2px;
        }}

        QMenu::item:selected {{
            background-color: {colors['selection_bg']};
            color: {colors['text_inverse']};
        }}

        QMenu::separator {{
            height: 1px;
            background-color: {colors['separator']};
            margin: 4px 0px;
        }}

        /* Status Bar */
        QStatusBar {{
            background-color: {colors['toolbar_bg']};
            border-top: 1px solid {colors['border_primary']};
            color: {colors['text_primary']};
        }}

        /* Tool Bar */
        QToolBar {{
            background-color: {colors['toolbar_bg']};
            border: 1px solid {colors['border_primary']};
            padding: 2px;
            spacing: 2px;
        }}

        QToolBar::separator {{
            background-color: {colors['separator']};
            width: 1px;
            margin: 4px 2px;
        }}

        /* Combo Boxes */
        QComboBox {{
            background-color: {colors['control_bg']};
            border: 1px solid {colors['control_border']};
            border-radius: 4px;
            padding: 4px 8px;
            color: {colors['text_primary']};
            selection-background-color: {colors['selection_bg']};
            selection-color: {colors['text_inverse']};
            /* Use native dropdown arrow - simpler and more reliable */
        }}

        QComboBox:hover {{
            border-color: {colors['accent_primary']};
            background-color: {colors['control_hover']};
        }}

        QComboBox:focus {{
            border: 2px solid {colors['control_focus']};
            background-color: {colors['control_bg']};
        }}

        QComboBox:on {{
            background-color: {colors['control_pressed']};
        }}

        QComboBox QAbstractItemView {{
            background-color: {colors['bg_tertiary']};
            border: 1px solid {colors['border_primary']};
            border-radius: 4px;
            selection-background-color: {colors['selection_bg']};
            selection-color: {colors['text_inverse']};
            color: {colors['text_primary']};
        }}

        QComboBox QAbstractItemView::item {{
            padding: 4px 8px;
            color: {colors['text_primary']};
        }}

        QComboBox QAbstractItemView::item:selected {{
            background-color: {colors['selection_bg']};
            color: {colors['text_inverse']};
        }}

        /* Check Boxes */
        QCheckBox {{
            color: {colors['text_primary']};
            background: transparent;
            spacing: 8px;
        }}

        /* Scroll Bars */
        QScrollBar:vertical {{
            background-color: {colors['bg_secondary']};
            width: 12px;
            border: none;
        }}

        QScrollBar::handle:vertical {{
            background-color: {colors['border_primary']};
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {colors['text_secondary']};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
            background: transparent;  /* Fix scroll arrow backgrounds */
        }}

        QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
            background: transparent;  /* Fix arrow backgrounds */
            border: none;
        }}

        QScrollBar:horizontal {{
            background-color: {colors['bg_secondary']};
            height: 12px;
            border: none;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {colors['border_primary']};
            border-radius: 6px;
            min-width: 20px;
            margin: 2px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {colors['text_secondary']};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
            background: transparent;  /* Fix scroll arrow backgrounds */
        }}

        QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {{
            background: transparent;  /* Fix arrow backgrounds */
            border: none;
        }}

        /* Fix tree widget scroll indicators and corner widgets */
        QTreeWidget::corner {{
            background: transparent;
            border: none;
        }}

        QAbstractScrollArea::corner {{
            background: transparent;
            border: none;
        }}

        /* Hide or fix scroll area corner widget that might show >> */
        QScrollArea::corner {{
            background: transparent;
            border: none;
        }}

        /* Progress Bars */
        QProgressBar {{
            background-color: {colors['bg_secondary']};
            border: 1px solid {colors['border_primary']};
            border-radius: 4px;
            text-align: center;
            color: {colors['text_primary']};
        }}

        QProgressBar::chunk {{
            background-color: {colors['accent_primary']};
            border-radius: 3px;
        }}

        /* Splitters */
        QSplitter::handle {{
            background-color: {colors['border_primary']};
        }}

        QSplitter::handle:horizontal {{
            width: 1px;
        }}

        QSplitter::handle:vertical {{
            height: 1px;
        }}

        /* Tab Widgets */
        QTabWidget::pane {{
            border: 1px solid {colors['border_primary']};
            background-color: {colors['bg_primary']};
        }}

        QTabBar::tab {{
            background-color: {colors['bg_secondary']};
            border: 1px solid {colors['border_primary']};
            padding: 6px 12px;
            color: {colors['text_primary']};
        }}

        QTabBar::tab:selected {{
            background-color: {colors['bg_primary']};
            border-bottom-color: {colors['bg_primary']};
        }}

        QTabBar::tab:hover {{
            background-color: {colors['control_hover']};
        }}

        /* Headers */
        QHeaderView::section {{
            background-color: {colors['bg_secondary']};
            border: 1px solid {colors['border_primary']};
            padding: 4px 8px;
            color: {colors['text_primary']};
        }}

        QHeaderView::section:hover {{
            background-color: {colors['control_hover']};
        }}

        /* Fix header view scroll indicators */
        QHeaderView::up-arrow, QHeaderView::down-arrow {{
            background: transparent;
            border: none;
        }}

        QHeaderView::left-arrow, QHeaderView::right-arrow {{
            background: transparent;
            border: none;
        }}

        /* Tree Widget Header Checkboxes */
        QTreeWidget QHeaderView::section {{
            background-color: {colors['bg_secondary']};
            border: 1px solid {colors['border_primary']};
            padding: 6px 8px;
            color: {colors['text_primary']};
            min-height: 24px;
        }}
        """

    def validate_theme_contrast(self) -> Dict[str, Any]:
        """Validate contrast ratios in current theme."""
        colors = self._colors
        results = {
            "theme": self.get_effective_theme(),
            "passes_aa": True,
            "passes_aaa": True,
            "checks": []
        }

        # Define critical color combinations to check
        checks = [
            ("Primary text on background", colors.text_primary, colors.bg_primary, ContrastLevel.AA_NORMAL),
            ("Secondary text on background", colors.text_secondary, colors.bg_primary, ContrastLevel.AA_NORMAL),
            ("Button text on button background", colors.text_primary, colors.control_bg, ContrastLevel.AA_NORMAL),
            ("Selection text on selection background", colors.text_inverse, colors.selection_bg, ContrastLevel.AA_NORMAL),
            ("Accent text accessibility", colors.text_inverse, colors.accent_primary, ContrastLevel.AA_NORMAL),
            ("Border visibility", colors.border_primary, colors.bg_primary, ContrastLevel.AA_LARGE),
            ("Disabled text contrast", colors.text_disabled, colors.bg_primary, ContrastLevel.AA_LARGE),
        ]

        for name, fg_color, bg_color, level in checks:
            ratio = calculate_contrast_ratio(fg_color, bg_color)
            passes_aa = ratio >= ContrastLevel.AA_NORMAL.value
            passes_aaa = ratio >= ContrastLevel.AAA_NORMAL.value

            if not passes_aa:
                results["passes_aa"] = False
            if not passes_aaa:
                results["passes_aaa"] = False

            results["checks"].append({
                "name": name,
                "foreground": fg_color,
                "background": bg_color,
                "ratio": round(ratio, 2),
                "required": level.value,
                "passes_aa": passes_aa,
                "passes_aaa": passes_aaa
            })

        return results

    def _update_colors(self) -> None:
        """Update color scheme based on current theme."""
        effective_theme = self.get_effective_theme()

        if effective_theme == "dark":
            self._colors = MacOSColors.dark_theme()
        else:
            self._colors = MacOSColors.light_theme()

        # Apply custom colors from UI config if available
        if self._ui_config and self._ui_config.custom_colors:
            color_dict = self._colors.to_dict()
            color_dict.update(self._ui_config.custom_colors)
            # Update colors object with custom values
            for key, value in self._ui_config.custom_colors.items():
                if hasattr(self._colors, key):
                    setattr(self._colors, key, value)

        logger.debug(f"Updated colors for {effective_theme} theme")
        if USING_QT:
            self.colors_changed.emit(self._colors.to_dict())

    def _start_theme_monitoring(self) -> None:
        """Start monitoring system theme changes."""
        if monitor_theme_changes(self._on_system_theme_changed):
            self._monitoring_started = True
            logger.info("Started monitoring system theme changes")
        else:
            logger.warning("System theme monitoring not supported on this platform")

    def _stop_theme_monitoring(self) -> None:
        """Stop monitoring system theme changes."""
        # Note: This is a placeholder. Actual implementation would need
        # to store monitoring handles and properly stop them.
        self._monitoring_started = False
        logger.info("Stopped monitoring system theme changes")

    def _on_system_theme_changed(self, new_theme: str) -> None:
        """Handle system theme change."""
        if new_theme != self._system_theme:
            logger.info(f"System theme changed from {self._system_theme} to {new_theme}")
            self._system_theme = new_theme

            # Update colors if we're following system theme
            if self._current_theme == "system":
                self._update_colors()

                # Notify callbacks
                for callback in self._theme_callbacks.values():
                    try:
                        callback(self._current_theme, self._colors)
                    except Exception as e:
                        logger.error(f"Error in system theme change callback: {e}")


# Global theme manager instance
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager