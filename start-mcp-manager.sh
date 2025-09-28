#!/bin/bash

# MCP Config Manager Startup Script
# This script provides an easy way to start the MCP Config Manager

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory
cd "$SCRIPT_DIR"

# Activate the virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Please run: python3 -m venv venv && source venv/bin/activate && pip install -e ."
    exit 1
fi

# Check if the package is installed
if ! command -v mcp-config-manager &> /dev/null; then
    echo "❌ MCP Config Manager not installed. Installing now..."
    pip install -e .
fi

# Display available options
echo ""
echo "🔧 MCP Config Manager - Quick Start"
echo "======================================"
echo ""
echo "✨ NEW: Enhanced dark theme support for better visibility!"
echo ""
echo "Choose how to launch the application:"
echo ""
echo "1) GUI Mode (Recommended) - Visual interface with automatic theme detection"
echo "2) Interactive CLI Mode - Command-line interactive interface"
echo "3) Status Check - Show current configuration status"
echo "4) Help - Show all available commands"
echo ""

# Get user choice
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "🖥️  Launching GUI Mode..."
        mcp-config-manager gui
        ;;
    2)
        echo "💻 Launching Interactive CLI Mode..."
        mcp-config-manager interactive
        ;;
    3)
        echo "📊 Showing Status..."
        mcp-config-manager status
        ;;
    4)
        echo "📋 Available Commands:"
        mcp-config-manager --help
        ;;
    *)
        echo "❌ Invalid choice. Launching GUI Mode by default..."
        mcp-config-manager gui
        ;;
esac