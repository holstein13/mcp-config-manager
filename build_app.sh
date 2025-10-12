#!/bin/bash
# Convenience script to build the macOS app
# The actual build scripts are in scripts/build/

echo "Building MCP Config Manager.app..."
echo "Using build script at scripts/build/setup_app.py"

# Run the build script from the project root
python3 scripts/build/setup_app.py py2app --dist-dir artifacts/dist

if [ $? -eq 0 ]; then
    # Copy icon to app bundle (py2app doesn't always copy it correctly)
    if [ -f "resources/icon.icns" ]; then
        cp "resources/icon.icns" "artifacts/dist/MCP Config Manager.app/Contents/Resources/icon.icns"
        echo "✅ Icon copied to app bundle"
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