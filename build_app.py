#!/usr/bin/env python3
"""
Build script to create a macOS .app bundle for MCP Config Manager.
The app bundle will always launch the currently installed version.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def create_app_bundle():
    """Create a macOS .app bundle for MCP Config Manager."""

    app_name = "MCP Config Manager"
    bundle_name = f"{app_name}.app"

    # Define paths
    current_dir = Path(__file__).parent
    build_dir = current_dir / "dist"
    app_path = build_dir / bundle_name
    contents_path = app_path / "Contents"
    macos_path = contents_path / "MacOS"
    resources_path = contents_path / "Resources"

    # Remove existing app if it exists
    if app_path.exists():
        shutil.rmtree(app_path)

    # Create directory structure
    macos_path.mkdir(parents=True, exist_ok=True)
    resources_path.mkdir(parents=True, exist_ok=True)

    # Create launcher script
    launcher_path = macos_path / "launcher"
    launcher_content = """#!/bin/bash

# MCP Config Manager GUI Launcher
# This script launches the MCP Config Manager GUI

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to find mcp-config-manager
find_mcp_command() {
    # First check if it's in PATH
    if command -v mcp-config-manager &> /dev/null; then
        echo "mcp-config-manager"
        return 0
    fi

    # Check system-wide locations
    if [ -x "/usr/local/bin/mcp-config-manager" ]; then
        echo "/usr/local/bin/mcp-config-manager"
        return 0
    fi

    # Check user Python installations (macOS specific paths)
    for version in 3.8 3.9 3.10 3.11 3.12 3.13; do
        USER_BIN="$HOME/Library/Python/$version/bin/mcp-config-manager"
        if [ -x "$USER_BIN" ]; then
            echo "$USER_BIN"
            return 0
        fi
    done

    # Check Linux/Unix user paths
    if [ -x "$HOME/.local/bin/mcp-config-manager" ]; then
        echo "$HOME/.local/bin/mcp-config-manager"
        return 0
    fi

    # Check if installed with pipx
    if [ -x "$HOME/.local/pipx/venvs/mcp-config-manager/bin/mcp-config-manager" ]; then
        echo "$HOME/.local/pipx/venvs/mcp-config-manager/bin/mcp-config-manager"
        return 0
    fi

    # Check Homebrew Python paths
    if [ -x "/opt/homebrew/bin/mcp-config-manager" ]; then
        echo "/opt/homebrew/bin/mcp-config-manager"
        return 0
    fi

    # Not found
    return 1
}

# Find the mcp-config-manager command
MCP_CMD=$(find_mcp_command)

# Check if we found the command
if [ -z "$MCP_CMD" ]; then
    osascript -e 'display alert "MCP Config Manager Not Found" message "Please install MCP Config Manager using pip install -e . from the project directory." as critical'
    exit 1
fi

# Launch the GUI
exec "$MCP_CMD" gui
"""

    launcher_path.write_text(launcher_content)
    launcher_path.chmod(0o755)

    # Create Info.plist
    info_plist_path = contents_path / "Info.plist"
    info_plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIdentifier</key>
    <string>com.mcpconfig.manager</string>
    <key>CFBundleName</key>
    <string>{app_name}</string>
    <key>CFBundleDisplayName</key>
    <string>{app_name}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
"""

    info_plist_path.write_text(info_plist_content)

    # Create a simple icon file (optional - placeholder for now)
    icon_path = resources_path / "icon.icns"
    # For now, we'll skip creating an actual icon
    # You can add your own icon.icns file later

    print(f"✅ Successfully created {bundle_name} in dist/")
    print(f"📍 Location: {app_path}")
    print("\nYou can now:")
    print("  1. Double-click the app to launch the GUI")
    print("  2. Drag it to /Applications for system-wide access")
    print("  3. Add it to your Dock for quick access")

    # Offer to open the dist folder (only in interactive mode)
    if sys.stdin.isatty():
        try:
            response = input("\nOpen dist folder in Finder? (y/n): ").lower()
            if response == 'y':
                subprocess.run(['open', str(build_dir)])
        except (EOFError, KeyboardInterrupt):
            pass  # Running non-interactively or user cancelled

    return app_path


def main():
    """Main entry point."""
    try:
        # Check if we're on macOS
        if sys.platform != 'darwin':
            print("❌ This script is for macOS only.")
            sys.exit(1)

        # Check if the package is installed
        result = subprocess.run(['which', 'mcp-config-manager'],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️  Warning: mcp-config-manager not found in PATH.")
            print("   Please run 'pip install -e .' first to install the package.")
            if sys.stdin.isatty():
                try:
                    response = input("Continue anyway? (y/n): ").lower()
                    if response != 'y':
                        sys.exit(1)
                except (EOFError, KeyboardInterrupt):
                    print("\n   Continuing with app bundle creation...")
            else:
                print("   Continuing with app bundle creation...")

        app_path = create_app_bundle()

    except Exception as e:
        print(f"❌ Error creating app bundle: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()