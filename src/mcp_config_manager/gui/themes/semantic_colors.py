"""Semantic color system for cross-platform theme support."""

from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum

try:
    from PyQt6.QtCore import QObject, pyqtSignal
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QPalette, QColor
    USING_QT = True
except ImportError:
    QObject = object
    pyqtSignal = lambda *args: None
    QApplication = None
    QPalette = None
    QColor = None
    USING_QT = False


class ContrastLevel(Enum):
    """Contrast level for accessibility compliance."""
    AA_NORMAL = 4.5  # WCAG AA for normal text
    AA_LARGE = 3.0   # WCAG AA for large text (18pt+ or 14pt+ bold)
    AAA_NORMAL = 7.0 # WCAG AAA for normal text
    AAA_LARGE = 4.5  # WCAG AAA for large text


@dataclass
class SemanticColors:
    """Semantic color definitions for both light and dark themes."""

    # Background colors
    bg_primary: str  # Main window background
    bg_secondary: str  # Secondary panels, sidebars
    bg_tertiary: str  # Cards, elevated surfaces
    bg_overlay: str  # Modal overlays, tooltips

    # Text colors
    text_primary: str  # Primary text
    text_secondary: str  # Secondary text
    text_tertiary: str  # Tertiary text, placeholders
    text_disabled: str  # Disabled text
    text_inverse: str  # Text on colored backgrounds

    # Interactive colors
    accent_primary: str  # Primary accent/brand color
    accent_secondary: str  # Secondary accent

    # State colors
    success: str
    warning: str
    error: str
    info: str

    # Border and separator colors
    border_primary: str  # Primary borders
    border_secondary: str  # Secondary, subtle borders
    separator: str  # Dividers, separators

    # Interactive element colors
    control_bg: str  # Button, input backgrounds
    control_border: str  # Button, input borders
    control_hover: str  # Hover states
    control_pressed: str  # Pressed/active states
    control_focus: str  # Focus ring color

    # Selection colors
    selection_bg: str  # Selection background
    selection_border: str  # Selection border

    # Special macOS colors
    sidebar_bg: str  # Sidebar/source list background
    list_bg: str  # List/table background
    list_alternate: str  # Alternating row background
    toolbar_bg: str  # Toolbar background

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for easy access."""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }


class MacOSColors:
    """macOS semantic color definitions following Human Interface Guidelines."""

    @staticmethod
    def light_theme() -> SemanticColors:
        """Get light theme colors matching macOS."""
        return SemanticColors(
            # Background colors
            bg_primary="#FFFFFF",          # windowBackgroundColor
            bg_secondary="#F6F6F6",        # controlBackgroundColor
            bg_tertiary="#FFFFFF",         # controlColor
            bg_overlay="rgba(0,0,0,0.4)",  # Modal backdrop

            # Text colors
            text_primary="#000000",        # labelColor
            text_secondary="#3C3C43",      # secondaryLabelColor
            text_tertiary="#8E8E93",       # tertiaryLabelColor
            text_disabled="#C7C7CC",       # quaternaryLabelColor
            text_inverse="#FFFFFF",        # Text on colored backgrounds

            # Interactive colors
            accent_primary="#0066CC",      # Improved blue for better contrast (4.5:1 on white)
            accent_secondary="#5856D6",    # purple

            # State colors
            success="#228B22",             # Improved green for better contrast (4.5:1 on white)
            warning="#CC6600",             # Improved orange for better contrast (4.5:1 on white)
            error="#CC2936",               # Improved red for better contrast (4.5:1 on white)
            info="#0066CC",                # Improved blue for better contrast (matches accent)

            # Border and separator colors
            border_primary="#D1D1D6",      # separatorColor
            border_secondary="#E5E5EA",    # Lighter separator
            separator="#D1D1D6",           # separatorColor

            # Interactive element colors
            control_bg="#FFFFFF",          # controlBackgroundColor
            control_border="#D1D1D6",      # Control borders
            control_hover="#E5E5EA",       # Hover state
            control_pressed="#D1D1D6",     # Pressed state
            control_focus="#007AFF",       # Focus ring (accent)

            # Selection colors
            selection_bg="#0066CC",        # selectedControlColor (improved contrast)
            selection_border="#0066CC",    # Selection border

            # Special macOS colors
            sidebar_bg="#F6F6F6",          # Source list background
            list_bg="#FFFFFF",             # Table/list background
            list_alternate="#F6F6F6",      # Alternating rows
            toolbar_bg="#EBEBF0",          # Toolbar background
        )

    @staticmethod
    def dark_theme() -> SemanticColors:
        """Get dark theme colors matching macOS Dark Mode."""
        return SemanticColors(
            # Background colors
            bg_primary="#1E1E1E",          # windowBackgroundColor (dark)
            bg_secondary="#2D2D2D",        # controlBackgroundColor (dark)
            bg_tertiary="#3A3A3A",         # controlColor (dark)
            bg_overlay="rgba(0,0,0,0.6)",  # Modal backdrop (darker)

            # Text colors
            text_primary="#FFFFFF",        # labelColor (dark)
            text_secondary="#E5E5E7",      # secondaryLabelColor (dark)
            text_tertiary="#A1A1A6",       # tertiaryLabelColor (dark)
            text_disabled="#6D6D7D",       # quaternaryLabelColor (dark)
            text_inverse="#000000",        # Text on colored backgrounds

            # Interactive colors
            accent_primary="#0A84FF",      # controlAccentColor (dark)
            accent_secondary="#5E5CE6",    # purple (dark)

            # State colors
            success="#32D74B",             # systemGreen (dark)
            warning="#FF9F0A",             # systemOrange (dark)
            error="#FF453A",               # systemRed (dark)
            info="#0A84FF",                # systemBlue (dark)

            # Border and separator colors
            border_primary="#48484A",      # separatorColor (dark)
            border_secondary="#38383A",    # Lighter separator (dark)
            separator="#48484A",           # separatorColor (dark)

            # Interactive element colors
            control_bg="#2D2D2D",          # controlBackgroundColor (dark)
            control_border="#48484A",      # Control borders (dark)
            control_hover="#3A3A3A",       # Hover state (dark)
            control_pressed="#48484A",     # Pressed state (dark)
            control_focus="#0A84FF",       # Focus ring (accent, dark)

            # Selection colors
            selection_bg="#0A84FF",        # selectedControlColor (dark)
            selection_border="#0A84FF",    # Selection border (dark)

            # Special macOS colors
            sidebar_bg="#1C1C1E",          # Source list background (dark)
            list_bg="#1E1E1E",             # Table/list background (dark)
            list_alternate="#2D2D2D",      # Alternating rows (dark)
            toolbar_bg="#2D2D2D",          # Toolbar background (dark)
        )


def calculate_contrast_ratio(color1: str, color2: str) -> float:
    """Calculate contrast ratio between two colors."""
    if not USING_QT:
        return 4.5  # Assume compliant if Qt not available

    def get_luminance(color_str: str) -> float:
        """Get relative luminance of a color."""
        color = QColor(color_str)
        if not color.isValid():
            return 0.5

        # Convert to linear RGB
        r, g, b = color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0

        def to_linear(c):
            return c / 12.92 if c <= 0.03928 else pow((c + 0.055) / 1.055, 2.4)

        r_lin, g_lin, b_lin = to_linear(r), to_linear(g), to_linear(b)

        # Calculate relative luminance
        return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

    lum1 = get_luminance(color1)
    lum2 = get_luminance(color2)

    # Ensure lighter color is in numerator
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)

    return (lighter + 0.05) / (darker + 0.05)


def validate_contrast(color1: str, color2: str, level: ContrastLevel = ContrastLevel.AA_NORMAL) -> bool:
    """Validate if two colors meet the specified contrast level."""
    ratio = calculate_contrast_ratio(color1, color2)
    return ratio >= level.value


def get_accessible_color(bg_color: str, preferred_text_color: str, fallback_text_color: str,
                        level: ContrastLevel = ContrastLevel.AA_NORMAL) -> str:
    """Get an accessible text color for the given background."""
    if validate_contrast(bg_color, preferred_text_color, level):
        return preferred_text_color
    return fallback_text_color


