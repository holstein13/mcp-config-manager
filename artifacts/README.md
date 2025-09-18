# Build Artifacts Directory

This directory contains build outputs and generated files from the MCP Config Manager project.

## Directory Structure

### `build/`
Contains intermediate build files from the py2app build process. These are generated when building the macOS application bundle.

### `dist/`
Contains final distribution packages and built applications ready for deployment.

### `macos/`
Contains macOS-specific build configuration and utility scripts:
- `setup_app.py` - Basic macOS app setup script
- `setup_py2app.py` - py2app configuration for building .app bundle
- `create_icon.sh` - Script to generate application icon
- `launch_gui.py` - GUI launcher script
- `icon.icns` - macOS application icon file

## Usage

To build the macOS application:
```bash
cd artifacts/macos
./create_icon.sh  # Generate icon if needed
python setup_py2app.py py2app
```

The built application will appear in `dist/`.

## Note

All files in this directory are generated artifacts and can be safely deleted. They will be regenerated when needed by the build process.