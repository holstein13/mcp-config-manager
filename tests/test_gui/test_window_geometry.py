#!/usr/bin/env python3
"""Test window geometry changes."""

from pathlib import Path
import re

def test_qt_window_geometry():
    """Test Qt window geometry settings."""
    main_window_path = Path("src/mcp_config_manager/gui/main_window.py")

    print("Window Geometry Test")
    print("=" * 30)

    assert main_window_path.exists(), "Main window file not found"

    content = main_window_path.read_text()

    # Check for improved window sizing
    has_larger_default = "1400, 900" in content
    has_minimum_size = "setMinimumSize(1200, 800)" in content
    has_tk_larger_default = "1400x900" in content
    has_tk_minimum = "minsize(1200, 800)" in content

    print("Qt Window Settings:")
    print(f"  Larger default size (1400x900): {'✅ Yes' if has_larger_default else '❌ No'}")
    print(f"  Minimum size constraint (1200x800): {'✅ Yes' if has_minimum_size else '❌ No'}")

    print("Tkinter Window Settings:")
    print(f"  Larger default size (1400x900): {'✅ Yes' if has_tk_larger_default else '❌ No'}")
    print(f"  Minimum size constraint (1200x800): {'✅ Yes' if has_tk_minimum else '❌ No'}")

    assert has_larger_default and has_minimum_size and has_tk_larger_default and has_tk_minimum, "Window geometry settings not properly configured"

def test_theme_font_sizing():
    """Test that custom font sizing has been removed from headers."""
    theme_manager_path = Path("src/mcp_config_manager/gui/themes/theme_manager.py")

    print("\nTheme Header Font Test")
    print("=" * 30)

    assert theme_manager_path.exists(), "Theme manager file not found"

    content = theme_manager_path.read_text()

    # Check that custom font-size has been removed
    has_custom_font_size = "font-size: 14px" in content
    # Check specifically for header font-weight, not button font-weight
    has_header_font_weight = "QTreeWidget QHeaderView::section" in content and "font-weight:" in content.split("QTreeWidget QHeaderView::section")[1].split("}}")[0]

    print("Header Font Customization:")
    print(f"  Custom font-size removed: {'✅ Yes' if not has_custom_font_size else '❌ No'}")
    print(f"  Header font-weight removed: {'✅ Yes' if not has_header_font_weight else '❌ No'}")

    assert not has_custom_font_size and not has_header_font_weight, "Custom font sizing should be removed from headers"

def main():
    """Run all geometry and styling tests."""
    print("Window Geometry and Font Sizing Validation")
    print("=" * 50)

    geometry_ok = test_qt_window_geometry()
    font_ok = test_theme_font_sizing()

    print("\n" + "=" * 50)
    if geometry_ok and font_ok:
        print("🎉 All window geometry and font fixes validated!")
        print("\nExpected improvements:")
        print("  • Application opens with larger default size (1400x900)")
        print("  • Window cannot be resized smaller than 1200x800")
        print("  • Header checkboxes use default system font size")
        print("  • All UI elements remain visible and accessible")
        return True
    else:
        print("⚠️  Some issues detected:")
        print(f"  Window geometry: {'✅ OK' if geometry_ok else '❌ Issues'}")
        print(f"  Font sizing: {'✅ OK' if font_ok else '❌ Issues'}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)