#!/usr/bin/env python3
"""Test to detect theme styling anomalies and hardcoded colors."""

import re
from pathlib import Path
from typing import List, Dict, Tuple

def find_hardcoded_colors(file_path: Path) -> List[Tuple[int, str, str]]:
    """Find hardcoded color values in files."""
    anomalies = []

    if not file_path.exists():
        return anomalies

    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')

        # Patterns for hardcoded colors
        color_patterns = [
            r'#[0-9a-fA-F]{6}',  # Hex colors like #f0f0f0
            r'#[0-9a-fA-F]{3}',   # Short hex colors like #fff
            r'rgb\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)',  # rgb(255, 255, 255)
            r'rgba\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)',  # rgba(255, 255, 255, 0.5)
            r'background-color:\s*[^{};]+',  # CSS background-color
            r'color:\s*[^{};]+',  # CSS color
        ]

        for line_num, line in enumerate(lines, 1):
            for pattern in color_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    # Skip if it's using theme system variables
                    if '{colors[' not in line and '{colors.' not in line:
                        # Skip common acceptable patterns
                        if not any(skip in match.lower() for skip in [
                            'transparent', 'inherit', 'none', 'auto', 'initial',
                            'currentcolor', 'unset'
                        ]):
                            anomalies.append((line_num, match, line.strip()))

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return anomalies

def find_missing_theme_integration(file_path: Path) -> List[Tuple[int, str]]:
    """Find components that should use theme system but don't."""
    issues = []

    if not file_path.exists():
        return issues

    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')

        # Look for Qt styling without theme integration
        for line_num, line in enumerate(lines, 1):
            # Check for setStyleSheet without theme variables
            if 'setStyleSheet' in line and 'f"""' not in line and '{colors' not in line:
                if any(color_indicator in line.lower() for color_indicator in [
                    '#', 'rgb', 'background-color', 'color:', 'border:'
                ]):
                    issues.append((line_num, line.strip()))

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return issues

def check_theme_consistency() -> Dict[str, List]:
    """Check for theme styling consistency across the application."""
    src_path = Path("src/mcp_config_manager/gui")

    results = {
        "hardcoded_colors": {},
        "missing_theme_integration": {},
        "summary": {}
    }

    if not src_path.exists():
        print("❌ GUI source directory not found")
        return results

    # Find all Python files in GUI directory
    python_files = list(src_path.rglob("*.py"))

    total_hardcoded = 0
    total_missing_integration = 0

    for py_file in python_files:
        # Skip theme system files themselves
        if 'themes/' in str(py_file):
            continue

        try:
            relative_path = str(py_file.relative_to(Path.cwd()))
        except ValueError:
            relative_path = str(py_file)

        # Check for hardcoded colors
        hardcoded = find_hardcoded_colors(py_file)
        if hardcoded:
            results["hardcoded_colors"][relative_path] = hardcoded
            total_hardcoded += len(hardcoded)

        # Check for missing theme integration
        missing_integration = find_missing_theme_integration(py_file)
        if missing_integration:
            results["missing_theme_integration"][relative_path] = missing_integration
            total_missing_integration += len(missing_integration)

    results["summary"] = {
        "files_checked": len(python_files),
        "total_hardcoded_colors": total_hardcoded,
        "total_missing_integration": total_missing_integration,
        "files_with_issues": len(results["hardcoded_colors"]) + len(results["missing_theme_integration"])
    }

    return results

def print_results(results: Dict):
    """Print the analysis results."""
    print("Theme Styling Anomaly Detection")
    print("=" * 50)

    summary = results["summary"]
    print(f"Files checked: {summary['files_checked']}")
    print(f"Hardcoded colors found: {summary['total_hardcoded_colors']}")
    print(f"Missing theme integration: {summary['total_missing_integration']}")
    print(f"Files with issues: {summary['files_with_issues']}")

    if summary['total_hardcoded_colors'] == 0 and summary['total_missing_integration'] == 0:
        print("\n🎉 No theme styling anomalies detected!")
        return True

    # Report hardcoded colors
    if results["hardcoded_colors"]:
        print("\n🚨 Hardcoded Colors Found:")
        print("-" * 30)
        for file_path, anomalies in results["hardcoded_colors"].items():
            print(f"\n📁 {file_path}")
            for line_num, color, line in anomalies:
                print(f"  Line {line_num}: {color}")
                print(f"    {line}")

    # Report missing theme integration
    if results["missing_theme_integration"]:
        print("\n⚠️  Missing Theme Integration:")
        print("-" * 30)
        for file_path, issues in results["missing_theme_integration"].items():
            print(f"\n📁 {file_path}")
            for line_num, line in issues:
                print(f"  Line {line_num}: {line}")

    print("\n💡 Recommendations:")
    if results["hardcoded_colors"]:
        print("  • Replace hardcoded colors with theme system variables")
        print("  • Use {colors.control_bg} instead of #f0f0f0")
        print("  • Use {colors.text_primary} instead of #000000")

    if results["missing_theme_integration"]:
        print("  • Update setStyleSheet calls to use theme-aware styling")
        print("  • Import theme manager: from ..themes import get_theme_manager")
        print("  • Apply dynamic styling with f-strings and color variables")

    return False

def check_specific_components():
    """Check specific components known to have styling issues."""
    print("\nSpecific Component Checks:")
    print("=" * 30)

    # Check toolbar styling
    server_list_path = Path("src/mcp_config_manager/gui/widgets/server_list.py")
    if server_list_path.exists():
        content = server_list_path.read_text()

        # Check if toolbar uses theme system
        if 'get_theme_manager()' in content and 'QToolBar {' in content:
            print("✅ Toolbar: Using theme system")
        else:
            print("❌ Toolbar: Not using theme system")

        # Check if hardcoded colors exist in toolbar
        if '#f0f0f0' in content or '#d0d0d0' in content:
            print("❌ Toolbar: Contains hardcoded colors")
        else:
            print("✅ Toolbar: No hardcoded colors detected")

    # Check main window styling
    main_window_path = Path("src/mcp_config_manager/gui/main_window.py")
    if main_window_path.exists():
        content = main_window_path.read_text()

        if '_setup_theme_system' in content and 'get_theme_manager' in content:
            print("✅ Main Window: Theme system integrated")
        else:
            print("❌ Main Window: Missing theme system integration")

def main():
    """Run all theme styling anomaly checks."""
    print("Theme Styling Anomaly Detection Tool")
    print("=" * 50)

    # Run general consistency check
    results = check_theme_consistency()
    success = print_results(results)

    # Run specific component checks
    check_specific_components()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All theme styling checks passed!")
        exit(0)
    else:
        print("⚠️  Theme styling issues detected. See details above.")
        exit(1)

if __name__ == "__main__":
    main()