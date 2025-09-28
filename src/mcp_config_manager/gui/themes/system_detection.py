"""System theme detection for cross-platform GUI applications."""

import platform
import sys
from typing import Optional

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QPalette, QColor
    from PyQt6.QtCore import QSettings
    USING_QT = True
except ImportError:
    QApplication = None
    QPalette = None
    QColor = None
    QSettings = None
    USING_QT = False


def detect_system_theme() -> str:
    """Detect the current system theme.

    Returns:
        'dark', 'light', or 'unknown'
    """
    system = platform.system().lower()

    if system == "darwin":  # macOS
        return _detect_macos_theme()
    elif system == "windows":
        return _detect_windows_theme()
    elif system == "linux":
        return _detect_linux_theme()
    else:
        return "unknown"


def _detect_macos_theme() -> str:
    """Detect macOS theme using system preferences."""
    try:
        # Method 1: Use PyQt6 palette detection if available
        if USING_QT and QApplication.instance():
            app = QApplication.instance()
            palette = app.palette()

            # Check if window background is dark
            bg_color = palette.color(QPalette.ColorRole.Window)
            # If the background lightness is less than 128, it's likely dark mode
            if bg_color.lightness() < 128:
                return "dark"
            else:
                return "light"

        # Method 2: Use subprocess to check system defaults
        import subprocess
        result = subprocess.run([
            "defaults", "read", "-g", "AppleInterfaceStyle"
        ], capture_output=True, text=True)

        if result.returncode == 0 and "Dark" in result.stdout:
            return "dark"
        else:
            return "light"

    except (FileNotFoundError, subprocess.SubprocessError, Exception):
        # Fallback: try checking NSUserDefaults if available
        try:
            import objc
            from Foundation import NSUserDefaults

            defaults = NSUserDefaults.standardUserDefaults()
            interface_style = defaults.stringForKey_("AppleInterfaceStyle")

            if interface_style and "Dark" in interface_style:
                return "dark"
            else:
                return "light"
        except ImportError:
            return "unknown"


def _detect_windows_theme() -> str:
    """Detect Windows theme using registry."""
    try:
        import winreg

        # Check Windows 10/11 theme setting
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        ) as key:
            apps_use_light_theme = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
            return "light" if apps_use_light_theme else "dark"

    except (ImportError, OSError, FileNotFoundError):
        # Fallback: use Qt palette if available
        if USING_QT and QApplication.instance():
            app = QApplication.instance()
            palette = app.palette()
            bg_color = palette.color(QPalette.ColorRole.Window)
            return "dark" if bg_color.lightness() < 128 else "light"

        return "unknown"


def _detect_linux_theme() -> str:
    """Detect Linux theme using various desktop environment methods."""
    try:
        # Method 1: Check GTK theme
        import subprocess
        result = subprocess.run([
            "gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            theme_name = result.stdout.strip().lower()
            if "dark" in theme_name:
                return "dark"
            elif "light" in theme_name:
                return "light"

        # Method 2: Check KDE theme
        result = subprocess.run([
            "kreadconfig5", "--group", "Colors:Window", "--key", "BackgroundNormal"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            # Parse color value and check if it's dark
            color_value = result.stdout.strip()
            if color_value:
                # Simple heuristic: if color looks dark, it's dark theme
                if "0,0,0" in color_value or color_value.startswith("0,"):
                    return "dark"
                else:
                    return "light"

        # Method 3: Use Qt palette if available
        if USING_QT and QApplication.instance():
            app = QApplication.instance()
            palette = app.palette()
            bg_color = palette.color(QPalette.ColorRole.Window)
            return "dark" if bg_color.lightness() < 128 else "light"

    except (FileNotFoundError, subprocess.SubprocessError, ImportError):
        pass

    return "unknown"


def monitor_theme_changes(callback: callable) -> bool:
    """Monitor system theme changes and call callback when theme changes.

    Args:
        callback: Function to call when theme changes, receives new theme as argument

    Returns:
        True if monitoring is supported and started, False otherwise
    """
    system = platform.system().lower()

    if system == "darwin":
        return _monitor_macos_theme_changes(callback)
    elif system == "windows":
        return _monitor_windows_theme_changes(callback)
    else:
        return False  # Not implemented for Linux yet


def _monitor_macos_theme_changes(callback: callable) -> bool:
    """Monitor macOS theme changes using distributed notifications."""
    try:
        import objc
        from Foundation import NSDistributedNotificationCenter, NSObject

        class ThemeObserver(NSObject):
            def themeChanged_(self, notification):
                new_theme = detect_system_theme()
                callback(new_theme)

        observer = ThemeObserver.alloc().init()
        center = NSDistributedNotificationCenter.defaultCenter()
        center.addObserver_selector_name_object_(
            observer,
            objc.selector(observer.themeChanged_, signature=b"v@:@"),
            "AppleInterfaceThemeChangedNotification",
            None
        )

        return True

    except ImportError:
        return False


def _monitor_windows_theme_changes(callback: callable) -> bool:
    """Monitor Windows theme changes using registry notifications."""
    try:
        import winreg
        import threading
        import time

        def monitor_registry():
            """Monitor registry for theme changes."""
            last_theme = detect_system_theme()

            while True:
                time.sleep(1)  # Check every second
                current_theme = detect_system_theme()
                if current_theme != last_theme and current_theme != "unknown":
                    callback(current_theme)
                    last_theme = current_theme

        # Start monitoring in background thread
        thread = threading.Thread(target=monitor_registry, daemon=True)
        thread.start()

        return True

    except ImportError:
        return False