#!/bin/bash

# Create icon.icns from a 1024x1024 PNG file
# Usage: ./create_icon.sh icon_1024x1024.png

if [ ! -f "$1" ]; then
    echo "Please provide a 1024x1024 PNG file as argument"
    echo "Usage: ./create_icon.sh icon_1024x1024.png"
    exit 1
fi

SOURCE_PNG="$1"
ICONSET_DIR="MCPIcon.iconset"

echo "Creating iconset directory..."
mkdir -p "$ICONSET_DIR"

echo "Generating icon sizes..."
# Generate all required sizes from the 1024x1024 source
sips -z 16 16     "$SOURCE_PNG" --out "$ICONSET_DIR/icon_16x16.png"
sips -z 32 32     "$SOURCE_PNG" --out "$ICONSET_DIR/icon_16x16@2x.png"
sips -z 32 32     "$SOURCE_PNG" --out "$ICONSET_DIR/icon_32x32.png"
sips -z 64 64     "$SOURCE_PNG" --out "$ICONSET_DIR/icon_32x32@2x.png"
sips -z 128 128   "$SOURCE_PNG" --out "$ICONSET_DIR/icon_128x128.png"
sips -z 256 256   "$SOURCE_PNG" --out "$ICONSET_DIR/icon_128x128@2x.png"
sips -z 256 256   "$SOURCE_PNG" --out "$ICONSET_DIR/icon_256x256.png"
sips -z 512 512   "$SOURCE_PNG" --out "$ICONSET_DIR/icon_256x256@2x.png"
sips -z 512 512   "$SOURCE_PNG" --out "$ICONSET_DIR/icon_512x512.png"
cp "$SOURCE_PNG" "$ICONSET_DIR/icon_512x512@2x.png"

echo "Creating icns file..."
iconutil -c icns "$ICONSET_DIR" -o icon.icns

echo "Cleaning up..."
rm -r "$ICONSET_DIR"

echo "✅ Created icon.icns successfully!"
echo "Now update setup_app.py to use this icon."