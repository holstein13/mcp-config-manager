# Rebuilding the macOS .app Bundle

This document explains how to rebuild the native macOS application bundle after making code changes.

## Prerequisites

- Python 3.8 or higher
- Virtual environment with dependencies installed

## Initial Setup (One-time)

If you haven't already set up the build environment:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install py2app
pip install -e .
pip install PyQt6
```

## Rebuilding the App

After making code changes, rebuild the .app bundle:

```bash
# Activate virtual environment
source venv/bin/activate

# Clean previous build artifacts
rm -rf build artifacts/dist

# Build the .app bundle
./build_app.sh

# Install to Applications folder
cp -r "artifacts/dist/MCP Config Manager.app" /Applications/
```

## What Gets Built

The build process creates a self-contained macOS application bundle that includes:
- Python interpreter
- All Python dependencies (PyQt6, requests, etc.)
- Your application code
- Resources and configuration

The resulting app can be launched like any native macOS application without requiring Python or any dependencies to be installed on the system.

## Build Location

- Built app: `artifacts/dist/MCP Config Manager.app`
- Installed app: `/Applications/MCP Config Manager.app`

## Troubleshooting

If the build fails:

1. Make sure you're in the virtual environment (`source venv/bin/activate`)
2. Check that all dependencies are installed (`pip list`)
3. Clean build artifacts and try again (`rm -rf build artifacts/dist`)

If the app crashes on launch:
- Run from terminal to see error messages: `/Applications/MCP\ Config\ Manager.app/Contents/MacOS/MCP\ Config\ Manager`
- Check that PyQt6 is properly installed in the venv
