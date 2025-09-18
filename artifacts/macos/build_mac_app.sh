#!/bin/bash
# Build macOS app for MCP Config Manager

echo "🔨 Building MCP Config Manager macOS app..."

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only"
    exit 1
fi

# Check if icon exists, if not create it
if [ ! -f "artifacts/macos/icon.icns" ]; then
    echo "📦 Creating app icon..."
    cd artifacts/macos && ./create_icon.sh && cd ../..
fi

# Copy icon to root temporarily for build
cp artifacts/macos/icon.icns icon.icns

# Run py2app build
echo "🏗️ Running py2app build..."
python3 artifacts/macos/setup_py2app.py py2app

# Move built app to artifacts/dist
if [ -d "py2app_dist/MCP Config Manager.app" ]; then
    echo "✅ Build successful!"
    mv py2app_dist/* artifacts/dist/ 2>/dev/null
    rmdir py2app_dist
    echo "📁 App location: artifacts/dist/MCP Config Manager.app"
else
    echo "❌ Build failed"
fi

# Clean up temporary icon
rm -f icon.icns

echo "✨ Done!"
