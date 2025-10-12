#!/bin/bash
# Convenience script to build the macOS app
# The actual build scripts are in scripts/build/

echo "Building MCP Config Manager.app..."
echo "Using build script at scripts/build/setup_app.py"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Using virtual environment"
else
    echo "⚠️  Warning: No virtual environment found at venv/"
    echo "   Using system Python"
fi

# Run the build script from the project root
python3 scripts/build/setup_app.py py2app --dist-dir artifacts/dist

if [ $? -eq 0 ]; then
    # Copy icon to app bundle (py2app doesn't always copy it correctly)
    if [ -f "resources/icon.icns" ]; then
        cp "resources/icon.icns" "artifacts/dist/MCP Config Manager.app/Contents/Resources/icon.icns"
        echo "✅ Icon copied to app bundle"
    fi

    # Code sign the application (ad-hoc signature for local use)
    echo "🔐 Signing application..."
    codesign --force --deep --sign - "artifacts/dist/MCP Config Manager.app"

    if [ $? -eq 0 ]; then
        echo "✅ Application signed successfully"
    else
        echo "⚠️  Warning: Code signing failed, app may not run on macOS 10.15+"
    fi

    echo ""
    echo "✅ Build successful!"
    echo "App location: artifacts/dist/MCP Config Manager.app"
    echo ""
    echo "To run the app:"
    echo "  open \"artifacts/dist/MCP Config Manager.app\""
else
    echo "❌ Build failed"
    exit 1
fi