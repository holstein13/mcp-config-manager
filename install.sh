#!/bin/bash

# MCP Config Manager - One-Click Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/yourusername/mcp-config-manager/main/install.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Installation settings
REPO_URL="https://github.com/yourusername/mcp-config-manager.git"
APP_NAME="mcp-config-manager"
DEFAULT_INSTALL_DIR="$HOME/bin"
VENV_NAME="venv"

# Print formatted messages
print_header() {
    echo -e "\n${PURPLE}================================================================${NC}"
    echo -e "${WHITE}  🔧 MCP Config Manager - One-Click Installer${NC}"
    echo -e "${PURPLE}================================================================${NC}\n"
}

print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC}  $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ️${NC}  $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
check_requirements() {
    print_step "Checking system requirements..."

    # Check Python
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed. Please install Python 3.8+ and try again."
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        print_success "Python $PYTHON_VERSION detected"
    else
        print_error "Python 3.8+ is required, but you have Python $PYTHON_VERSION"
        exit 1
    fi

    # Check pip
    if ! command_exists pip3; then
        print_error "pip3 is required but not installed. Please install pip and try again."
        exit 1
    fi
    print_success "pip3 detected"

    # Check git
    if ! command_exists git; then
        print_error "git is required but not installed. Please install git and try again."
        exit 1
    fi
    print_success "git detected"

    # Check for curl or wget
    if ! command_exists curl && ! command_exists wget; then
        print_error "Either curl or wget is required but neither is installed."
        exit 1
    fi
    print_success "Download tools available"
}

# Get installation directory from user
get_install_directory() {
    print_step "Selecting installation directory..."

    echo -e "\nWhere would you like to install MCP Config Manager?"
    echo -e "1) ${GREEN}$HOME/bin${NC} (recommended - user-local installation)"
    echo -e "2) ${YELLOW}$HOME/.local/bin${NC} (XDG standard location)"
    echo -e "3) ${YELLOW}/usr/local/bin${NC} (system-wide installation - requires sudo)"
    echo -e "4) ${CYAN}Custom directory${NC}"
    echo ""

    while true; do
        read -p "Enter your choice (1-4): " choice
        case $choice in
            1)
                INSTALL_DIR="$HOME/bin"
                break
                ;;
            2)
                INSTALL_DIR="$HOME/.local/bin"
                break
                ;;
            3)
                INSTALL_DIR="/usr/local/bin"
                NEED_SUDO=true
                break
                ;;
            4)
                read -p "Enter custom directory path: " custom_dir
                if [[ "$custom_dir" = /* ]]; then
                    INSTALL_DIR="$custom_dir"
                else
                    INSTALL_DIR="$PWD/$custom_dir"
                fi
                break
                ;;
            *)
                echo "Invalid choice. Please enter 1, 2, 3, or 4."
                ;;
        esac
    done

    APP_DIR="$INSTALL_DIR/$APP_NAME"
    print_success "Installation directory: $APP_DIR"
}

# Create installation directory
create_install_directory() {
    print_step "Creating installation directory..."

    if [[ "$NEED_SUDO" == "true" ]]; then
        sudo mkdir -p "$INSTALL_DIR"
        sudo chown "$USER:$(id -gn)" "$INSTALL_DIR"
    else
        mkdir -p "$INSTALL_DIR"
    fi

    print_success "Directory created: $INSTALL_DIR"
}

# Download and install application
install_application() {
    print_step "Downloading MCP Config Manager..."

    # Remove existing installation if it exists
    if [ -d "$APP_DIR" ]; then
        print_warning "Existing installation found. Removing..."
        rm -rf "$APP_DIR"
    fi

    # Clone repository
    git clone "$REPO_URL" "$APP_DIR" --quiet
    cd "$APP_DIR"

    print_success "Application downloaded"

    print_step "Setting up Python virtual environment..."
    python3 -m venv "$VENV_NAME"
    source "$VENV_NAME/bin/activate"

    print_step "Installing dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet -e .

    # Try to install PyQt6 for better GUI experience
    print_step "Installing optional GUI dependencies..."
    if pip install --quiet PyQt6 2>/dev/null; then
        print_success "PyQt6 installed - enhanced GUI available"
    else
        print_warning "PyQt6 installation failed - will use tkinter fallback"
    fi

    print_success "Application installed successfully"
}

# Create launcher script
create_launcher() {
    print_step "Creating launcher script..."

    LAUNCHER_PATH="$INSTALL_DIR/mcp"

    cat > "$LAUNCHER_PATH" << EOF
#!/bin/bash
# MCP Config Manager Launcher
# Generated by installer on $(date)

INSTALL_DIR="$APP_DIR"
VENV_PATH="\$INSTALL_DIR/$VENV_NAME"

# Check if installation exists
if [ ! -d "\$INSTALL_DIR" ]; then
    echo "❌ MCP Config Manager installation not found at \$INSTALL_DIR"
    echo "   Please reinstall using: curl -fsSL https://raw.githubusercontent.com/yourusername/mcp-config-manager/main/install.sh | bash"
    exit 1
fi

# Activate virtual environment
if [ -f "\$VENV_PATH/bin/activate" ]; then
    source "\$VENV_PATH/bin/activate"
else
    echo "❌ Virtual environment not found. Installation may be corrupted."
    exit 1
fi

# Change to app directory
cd "\$INSTALL_DIR"

# Run the application with passed arguments
exec mcp-config-manager "\$@"
EOF

    chmod +x "$LAUNCHER_PATH"
    print_success "Launcher created: $LAUNCHER_PATH"
}

# Add to shell configuration
setup_shell_integration() {
    print_step "Setting up shell integration..."

    echo ""
    echo "Would you like to add the 'mcp' command to your shell PATH?"
    echo "This will allow you to run 'mcp' from anywhere in your terminal."
    echo ""

    read -p "Add to shell PATH? (y/n): " add_to_path

    if [[ "$add_to_path" =~ ^[Yy]$ ]]; then
        # Detect shell and add to appropriate config file
        SHELL_NAME=$(basename "$SHELL")
        case "$SHELL_NAME" in
            bash)
                SHELL_CONFIG="$HOME/.bashrc"
                if [[ -f "$HOME/.bash_profile" ]]; then
                    SHELL_CONFIG="$HOME/.bash_profile"
                fi
                ;;
            zsh)
                SHELL_CONFIG="$HOME/.zshrc"
                ;;
            fish)
                SHELL_CONFIG="$HOME/.config/fish/config.fish"
                ;;
            *)
                SHELL_CONFIG="$HOME/.profile"
                ;;
        esac

        # Add to PATH if not already there
        PATH_EXPORT="export PATH=\"$INSTALL_DIR:\$PATH\""

        if ! grep -q "$INSTALL_DIR" "$SHELL_CONFIG" 2>/dev/null; then
            echo "" >> "$SHELL_CONFIG"
            echo "# Added by MCP Config Manager installer" >> "$SHELL_CONFIG"
            echo "$PATH_EXPORT" >> "$SHELL_CONFIG"
            print_success "Added to $SHELL_CONFIG"
        else
            print_info "Already in PATH configuration"
        fi

        # Create alias for convenience
        ALIAS_LINE="alias mcp-gui='mcp gui'"
        if ! grep -q "mcp-gui" "$SHELL_CONFIG" 2>/dev/null; then
            echo "alias mcp-gui='mcp gui'" >> "$SHELL_CONFIG"
            print_success "Added 'mcp-gui' alias"
        fi

        export PATH="$INSTALL_DIR:$PATH"
        print_success "Shell integration complete"
    else
        print_info "Skipping shell integration"
        echo "You can manually run: $INSTALL_DIR/mcp"
    fi
}

# Check for CLI tools
check_cli_tools() {
    print_step "Checking for supported CLI tools..."

    CLI_FOUND=false

    if command_exists claude; then
        print_success "Claude CLI detected"
        CLI_FOUND=true
    else
        print_warning "Claude CLI not found"
    fi

    if command_exists gemini; then
        print_success "Gemini CLI detected"
        CLI_FOUND=true
    elif command_exists "google-gemini-cli"; then
        print_success "Google Gemini CLI detected"
        CLI_FOUND=true
    else
        print_warning "Gemini CLI not found"
    fi

    # Check for various codex/openai implementations
    if command_exists codex || command_exists openai || command_exists "openai-cli"; then
        print_success "OpenAI/Codex CLI detected"
        CLI_FOUND=true
    else
        print_warning "OpenAI/Codex CLI not found"
    fi

    if [[ "$CLI_FOUND" == "false" ]]; then
        print_warning "No supported CLI tools found"
        echo "  MCP Config Manager will still work, but you'll need to install CLI tools to use them."
        echo "  Supported tools: Claude CLI, Gemini CLI, OpenAI CLI"
    fi
}

# Create desktop entry (Linux only)
create_desktop_entry() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_step "Creating desktop entry..."

        DESKTOP_DIR="$HOME/.local/share/applications"
        mkdir -p "$DESKTOP_DIR"

        cat > "$DESKTOP_DIR/mcp-config-manager.desktop" << EOF
[Desktop Entry]
Name=MCP Config Manager
Comment=Manage your AI CLI configurations
Exec=$INSTALL_DIR/mcp gui
Icon=$APP_DIR/assets/icon.png
Terminal=false
Type=Application
Categories=Development;Utility;
StartupWMClass=mcp-config-manager
EOF

        print_success "Desktop entry created"
    fi
}

# Print final instructions
print_final_instructions() {
    echo ""
    echo -e "${GREEN}================================================================${NC}"
    echo -e "${WHITE}  🎉 Installation Complete!${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo ""
    echo -e "${WHITE}MCP Config Manager has been successfully installed!${NC}"
    echo ""
    echo -e "${CYAN}📍 Installation Location:${NC} $APP_DIR"
    echo -e "${CYAN}🚀 Launcher Script:${NC} $INSTALL_DIR/mcp"
    echo ""
    echo -e "${WHITE}Quick Start:${NC}"

    if command_exists mcp 2>/dev/null || [[ ":$PATH:" == *":$INSTALL_DIR:"* ]]; then
        echo -e "  ${GREEN}mcp gui${NC}          # Launch GUI interface"
        echo -e "  ${GREEN}mcp interactive${NC}  # Launch interactive CLI"
        echo -e "  ${GREEN}mcp status${NC}       # Show configuration status"
        echo -e "  ${GREEN}mcp --help${NC}       # Show all commands"
        echo ""
        echo -e "  ${GREEN}mcp-gui${NC}          # Quick alias for GUI mode"
    else
        echo -e "  ${GREEN}$INSTALL_DIR/mcp gui${NC}          # Launch GUI interface"
        echo -e "  ${GREEN}$INSTALL_DIR/mcp interactive${NC}  # Launch interactive CLI"
        echo -e "  ${GREEN}$INSTALL_DIR/mcp status${NC}       # Show configuration status"
        echo ""
        echo -e "${YELLOW}💡 Restart your terminal or run:${NC} source ~/.bashrc"
        echo -e "   ${YELLOW}Then you can use 'mcp' command directly${NC}"
    fi

    echo ""
    echo -e "${WHITE}What's New:${NC}"
    echo -e "  ✨ Enhanced dark theme support with automatic system detection"
    echo -e "  🎨 Improved accessibility with WCAG AA compliance"
    echo -e "  🖥️  Cross-platform GUI (PyQt6 + tkinter fallback)"
    echo -e "  ⚡ Faster startup and better error handling"
    echo ""
    echo -e "${WHITE}Need Help?${NC}"
    echo -e "  📖 Documentation: https://github.com/yourusername/mcp-config-manager"
    echo -e "  🐛 Report Issues: https://github.com/yourusername/mcp-config-manager/issues"
    echo ""
    echo -e "${WHITE}Uninstall:${NC}"
    echo -e "  Run: ${CYAN}$INSTALL_DIR/mcp uninstall${NC}"
    echo ""
}

# Create uninstaller
create_uninstaller() {
    print_step "Creating uninstaller..."

    cat > "$APP_DIR/uninstall.sh" << 'EOF'
#!/bin/bash
# MCP Config Manager Uninstaller

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_step() {
    echo -e "${CYAN}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC}  $1"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(dirname "$SCRIPT_DIR")"
LAUNCHER_PATH="$INSTALL_DIR/mcp"

echo ""
echo -e "${RED}🗑️  MCP Config Manager Uninstaller${NC}"
echo ""
echo "This will remove MCP Config Manager from your system."
echo -e "Installation directory: ${YELLOW}$SCRIPT_DIR${NC}"
echo ""

read -p "Are you sure you want to uninstall? (y/N): " confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

print_step "Removing application files..."
if [ -f "$LAUNCHER_PATH" ]; then
    rm -f "$LAUNCHER_PATH"
    print_success "Removed launcher script"
fi

print_step "Removing desktop entry..."
if [ -f "$HOME/.local/share/applications/mcp-config-manager.desktop" ]; then
    rm -f "$HOME/.local/share/applications/mcp-config-manager.desktop"
    print_success "Removed desktop entry"
fi

print_step "Removing shell integration..."
for config_file in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile"; do
    if [ -f "$config_file" ]; then
        if grep -q "MCP Config Manager installer" "$config_file" 2>/dev/null; then
            # Remove the installer lines
            sed -i.bak '/# Added by MCP Config Manager installer/,+2d' "$config_file" 2>/dev/null || true
            print_success "Cleaned $config_file"
        fi
    fi
done

print_step "Removing application directory..."
cd "$HOME"
rm -rf "$SCRIPT_DIR"
print_success "Application removed"

echo ""
echo -e "${GREEN}✅ MCP Config Manager has been successfully uninstalled!${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} Please restart your terminal to complete the removal."
echo ""
EOF

    chmod +x "$APP_DIR/uninstall.sh"

    # Add uninstall command to main launcher
    cat >> "$LAUNCHER_PATH" << 'EOF'

# Handle uninstall command
if [ "$1" = "uninstall" ]; then
    exec "$INSTALL_DIR/$APP_NAME/uninstall.sh"
fi
EOF

    print_success "Uninstaller created"
}

# Main installation flow
main() {
    print_header

    # Check if we're running as root (not recommended)
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root is not recommended. Install as a regular user instead."
        read -p "Continue anyway? (y/N): " continue_root
        if [[ ! "$continue_root" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    check_requirements
    get_install_directory
    create_install_directory
    install_application
    create_launcher
    create_uninstaller
    setup_shell_integration
    check_cli_tools
    create_desktop_entry
    print_final_instructions
}

# Handle interruption gracefully
trap 'echo -e "\n${RED}Installation interrupted${NC}"; exit 1' INT

# Run main installation
main "$@"