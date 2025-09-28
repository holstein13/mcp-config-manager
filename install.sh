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

# Create default update configuration
create_update_config() {
    print_step "Creating update configuration..."

    UPDATE_CONFIG="$APP_DIR/.mcp_update_config"

    # Detect environment type
    DETECTED_ENV="standard"
    if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ] || [ -n "$JENKINS_URL" ]; then
        DETECTED_ENV="ci"
    elif [ -d "/etc/kubernetes" ] || [ -n "$KUBERNETES_SERVICE_HOST" ]; then
        DETECTED_ENV="enterprise"
    elif [ -f "/.dockerenv" ] || [ -n "$DOCKER_CONTAINER" ]; then
        DETECTED_ENV="container"
    elif [ -n "$SSH_CONNECTION" ] || [ -n "$SSH_CLIENT" ]; then
        DETECTED_ENV="remote"
    fi

    # Set defaults based on environment
    case "$DETECTED_ENV" in
        "ci"|"enterprise"|"container")
            DEFAULT_UPDATES="false"
            DEFAULT_AUTO_CHECK="false"
            print_info "Detected $DETECTED_ENV environment - updates disabled by default"
            ;;
        "remote")
            DEFAULT_UPDATES="true"
            DEFAULT_AUTO_CHECK="false"
            print_info "Detected remote environment - auto-check disabled by default"
            ;;
        *)
            DEFAULT_UPDATES="true"
            DEFAULT_AUTO_CHECK="true"
            ;;
    esac

    cat > "$UPDATE_CONFIG" << EOF
# MCP Config Manager Update Configuration
# Generated on $(date)
# Detected environment: $DETECTED_ENV

# Enable/disable updates completely
UPDATES_ENABLED=$DEFAULT_UPDATES

# Check for updates on startup (future feature)
AUTO_CHECK_UPDATES=$DEFAULT_AUTO_CHECK

# Update channel: stable, beta, dev
UPDATE_CHANNEL="stable"

# Environment detection (informational)
DETECTED_ENVIRONMENT="$DETECTED_ENV"
EOF

    print_success "Update configuration created with environment-specific defaults"
    if [ "$DEFAULT_UPDATES" = "false" ]; then
        print_warning "Updates are disabled by default in this environment"
        print_info "To enable: mcp config set updates.enabled true"
    fi
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

# Handle special commands first
case "\$1" in
    update|upgrade)
        echo "🔄 Updating MCP Config Manager..."
        cd "\$INSTALL_DIR"

        # Check update settings
        UPDATE_CONFIG="\$INSTALL_DIR/.mcp_update_config"
        if [ -f "\$UPDATE_CONFIG" ]; then
            source "\$UPDATE_CONFIG"
        else
            # Default settings
            UPDATES_ENABLED=true
            AUTO_CHECK_UPDATES=true
            UPDATE_CHANNEL="stable"
        fi

        # Check if updates are disabled
        if [ "\$UPDATES_ENABLED" != "true" ]; then
            echo "❌ Updates are disabled for this installation"
            echo "💡 To enable updates, run: mcp config set updates.enabled true"
            echo "   Or edit: \$UPDATE_CONFIG"
            exit 1
        fi

        # Check if we have git repository
        if [ -d ".git" ]; then
            # Save current branch/state
            CURRENT_BRANCH=\$(git branch --show-current 2>/dev/null || echo "main")

            # Fetch latest changes
            echo "📡 Checking for updates..."
            git fetch origin

            # Check if updates are available
            LOCAL=\$(git rev-parse HEAD)
            REMOTE=\$(git rev-parse origin/\$CURRENT_BRANCH)

            if [ "\$LOCAL" = "\$REMOTE" ]; then
                echo "✅ Already up to date!"
                exit 0
            fi

            echo "📦 Updates available! Installing..."
            echo "📡 Update channel: \$UPDATE_CHANNEL"

            # Backup current installation
            BACKUP_DIR="\$INSTALL_DIR.backup.\$(date +%Y%m%d_%H%M%S)"
            echo "💾 Creating backup: \$BACKUP_DIR"
            cp -r "\$INSTALL_DIR" "\$BACKUP_DIR"

            # Determine branch based on update channel
            TARGET_BRANCH="\$CURRENT_BRANCH"
            case "\$UPDATE_CHANNEL" in
                "stable")
                    TARGET_BRANCH="main"
                    ;;
                "beta")
                    TARGET_BRANCH="beta"
                    ;;
                "dev")
                    TARGET_BRANCH="develop"
                    ;;
            esac

            # Switch to appropriate branch if needed
            if [ "\$CURRENT_BRANCH" != "\$TARGET_BRANCH" ]; then
                echo "🔄 Switching to \$UPDATE_CHANNEL channel (branch: \$TARGET_BRANCH)"
                git checkout \$TARGET_BRANCH 2>/dev/null || {
                    echo "⚠️  Branch \$TARGET_BRANCH not found, staying on \$CURRENT_BRANCH"
                    TARGET_BRANCH="\$CURRENT_BRANCH"
                }
            fi

            # Update repository
            git pull origin \$TARGET_BRANCH

            # Reinstall dependencies
            source "\$VENV_PATH/bin/activate"
            pip install --quiet --upgrade pip
            pip install --quiet -e .

            # Try to update PyQt6
            pip install --quiet --upgrade PyQt6 2>/dev/null || true

            echo "✅ Update completed successfully!"
            echo "💡 Run 'mcp --version' to see the new version"
        else
            echo "❌ Cannot update: Installation not git-enabled"
            echo "💡 Re-run the installer to get the latest version:"
            echo "   curl -fsSL https://raw.githubusercontent.com/yourusername/mcp-config-manager/main/install.sh | bash"
        fi
        exit 0
        ;;
    update-status|check-updates)
        echo "🔍 Checking for updates..."
        cd "\$INSTALL_DIR"

        # Check update settings
        UPDATE_CONFIG="\$INSTALL_DIR/.mcp_update_config"
        if [ -f "\$UPDATE_CONFIG" ]; then
            source "\$UPDATE_CONFIG"
        else
            UPDATES_ENABLED=true
            UPDATE_CHANNEL="stable"
        fi

        echo "📡 Update channel: \$UPDATE_CHANNEL"
        echo "🔧 Updates enabled: \$UPDATES_ENABLED"

        if [ "\$UPDATES_ENABLED" != "true" ]; then
            echo "❌ Updates are disabled for this installation"
            exit 0
        fi

        if [ -d ".git" ]; then
            CURRENT_BRANCH=\$(git branch --show-current 2>/dev/null || echo "main")
            echo "🌿 Current branch: \$CURRENT_BRANCH"

            # Determine target branch
            TARGET_BRANCH="\$CURRENT_BRANCH"
            case "\$UPDATE_CHANNEL" in
                "stable") TARGET_BRANCH="main" ;;
                "beta") TARGET_BRANCH="beta" ;;
                "dev") TARGET_BRANCH="develop" ;;
            esac

            git fetch origin --quiet

            LOCAL=\$(git rev-parse HEAD)
            REMOTE=\$(git rev-parse origin/\$TARGET_BRANCH 2>/dev/null || git rev-parse origin/\$CURRENT_BRANCH)

            if [ "\$LOCAL" = "\$REMOTE" ]; then
                echo "✅ You have the latest version!"
            else
                echo "📦 Updates are available!"
                echo "💡 Run 'mcp update' to install updates"

                # Show commit summary
                COMMIT_COUNT=\$(git rev-list --count HEAD..origin/\$TARGET_BRANCH 2>/dev/null || echo "unknown")
                if [ "\$COMMIT_COUNT" != "unknown" ] && [ "\$COMMIT_COUNT" -gt 0 ]; then
                    echo "📊 \$COMMIT_COUNT new commit(s) available"
                fi
            fi
        else
            echo "❌ Cannot check for updates: Installation not git-enabled"
            echo "💡 Re-run the installer to get a git-enabled installation"
        fi
        exit 0
        ;;
    uninstall)
        exec "\$INSTALL_DIR/uninstall.sh"
        ;;
    --version|-v)
        cd "\$INSTALL_DIR"
        source "\$VENV_PATH/bin/activate"
        python -c "import mcp_config_manager; print(f'MCP Config Manager v{mcp_config_manager.__version__}')" 2>/dev/null || echo "MCP Config Manager (version unknown)"
        exit 0
        ;;
    config)
        # Configuration management
        UPDATE_CONFIG="\$INSTALL_DIR/.mcp_update_config"

        case "\$2" in
            "get")
                if [ -f "\$UPDATE_CONFIG" ]; then
                    if [ -n "\$3" ]; then
                        # Get specific setting
                        case "\$3" in
                            "updates.enabled")
                                source "\$UPDATE_CONFIG" && echo "\$UPDATES_ENABLED"
                                ;;
                            "updates.auto_check")
                                source "\$UPDATE_CONFIG" && echo "\$AUTO_CHECK_UPDATES"
                                ;;
                            "updates.channel")
                                source "\$UPDATE_CONFIG" && echo "\$UPDATE_CHANNEL"
                                ;;
                            *)
                                echo "❌ Unknown setting: \$3"
                                echo "Available settings: updates.enabled, updates.auto_check, updates.channel"
                                exit 1
                                ;;
                        esac
                    else
                        echo "📋 Current update configuration:"
                        source "\$UPDATE_CONFIG"
                        echo "  updates.enabled: \$UPDATES_ENABLED"
                        echo "  updates.auto_check: \$AUTO_CHECK_UPDATES"
                        echo "  updates.channel: \$UPDATE_CHANNEL"
                    fi
                else
                    echo "📋 Default update configuration:"
                    echo "  updates.enabled: true"
                    echo "  updates.auto_check: true"
                    echo "  updates.channel: stable"
                fi
                ;;
            "set")
                # Create config file if it doesn't exist
                if [ ! -f "\$UPDATE_CONFIG" ]; then
                    cat > "\$UPDATE_CONFIG" << 'CONFIG_EOF'
# MCP Config Manager Update Configuration
# Generated on \$(date)

# Enable/disable updates completely
UPDATES_ENABLED=true

# Check for updates on startup (future feature)
AUTO_CHECK_UPDATES=true

# Update channel: stable, beta, dev
UPDATE_CHANNEL="stable"
CONFIG_EOF
                fi

                case "\$3" in
                    "updates.enabled")
                        if [ "\$4" = "true" ] || [ "\$4" = "false" ]; then
                            sed -i.bak "s/UPDATES_ENABLED=.*/UPDATES_ENABLED=\$4/" "\$UPDATE_CONFIG"
                            echo "✅ Set updates.enabled = \$4"
                        else
                            echo "❌ Value must be 'true' or 'false'"
                            exit 1
                        fi
                        ;;
                    "updates.auto_check")
                        if [ "\$4" = "true" ] || [ "\$4" = "false" ]; then
                            sed -i.bak "s/AUTO_CHECK_UPDATES=.*/AUTO_CHECK_UPDATES=\$4/" "\$UPDATE_CONFIG"
                            echo "✅ Set updates.auto_check = \$4"
                        else
                            echo "❌ Value must be 'true' or 'false'"
                            exit 1
                        fi
                        ;;
                    "updates.channel")
                        if [ "\$4" = "stable" ] || [ "\$4" = "beta" ] || [ "\$4" = "dev" ]; then
                            sed -i.bak "s/UPDATE_CHANNEL=.*/UPDATE_CHANNEL=\"\$4\"/" "\$UPDATE_CONFIG"
                            echo "✅ Set updates.channel = \$4"
                        else
                            echo "❌ Channel must be 'stable', 'beta', or 'dev'"
                            exit 1
                        fi
                        ;;
                    *)
                        echo "❌ Unknown setting: \$3"
                        echo "Available settings: updates.enabled, updates.auto_check, updates.channel"
                        exit 1
                        ;;
                esac
                ;;
            "reset")
                rm -f "\$UPDATE_CONFIG"
                echo "✅ Reset to default update configuration"
                ;;
            *)
                echo "Usage: mcp config [get|set|reset] [setting] [value]"
                echo ""
                echo "Settings:"
                echo "  updates.enabled     Enable/disable updates (true/false)"
                echo "  updates.auto_check  Check for updates on startup (true/false)"
                echo "  updates.channel     Update channel (stable/beta/dev)"
                echo ""
                echo "Examples:"
                echo "  mcp config get                    # Show all settings"
                echo "  mcp config get updates.enabled   # Show specific setting"
                echo "  mcp config set updates.enabled false  # Disable updates"
                echo "  mcp config set updates.channel beta   # Use beta channel"
                echo "  mcp config reset                 # Reset to defaults"
                exit 1
                ;;
        esac
        exit 0
        ;;
    --help|-h|help)
        echo "MCP Config Manager - AI CLI Configuration Management"
        echo ""
        echo "Usage: mcp [command] [options]"
        echo ""
        echo "Commands:"
        echo "  gui              Launch GUI interface (default)"
        echo "  interactive      Launch interactive CLI mode"
        echo "  status          Show configuration status"
        echo "  update          Update to latest version"
        echo "  update-status   Check for available updates"
        echo "  config          Manage update preferences"
        echo "  uninstall       Remove MCP Config Manager"
        echo "  --version       Show version information"
        echo "  --help          Show this help message"
        echo ""
        echo "Configuration:"
        echo "  mcp config get                    # Show all settings"
        echo "  mcp config set updates.enabled false  # Disable updates"
        echo "  mcp config set updates.channel beta   # Use beta channel"
        echo ""
        echo "Examples:"
        echo "  mcp             # Launch GUI (default)"
        echo "  mcp gui         # Launch GUI explicitly"
        echo "  mcp interactive # Launch CLI mode"
        echo "  mcp status      # Show status"
        echo "  mcp update      # Update application"
        echo ""
        exit 0
        ;;
    "")
        # No arguments provided - default to GUI
        set -- gui
        ;;
esac

# Run the application with arguments
exec mcp-config-manager "\$@"
EOF

    chmod +x "$LAUNCHER_PATH"
    print_success "Launcher created: $LAUNCHER_PATH"

    # Create default update configuration
    create_update_config
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
        echo -e "  ${GREEN}mcp${NC}              # Launch GUI interface (default)"
        echo -e "  ${GREEN}mcp interactive${NC}  # Launch interactive CLI"
        echo -e "  ${GREEN}mcp status${NC}       # Show configuration status"
        echo -e "  ${GREEN}mcp update${NC}       # Update to latest version"
        echo -e "  ${GREEN}mcp config get${NC}   # Show update preferences"
        echo -e "  ${GREEN}mcp --help${NC}       # Show all commands"
        echo ""
        echo -e "  ${GREEN}mcp-gui${NC}          # Quick alias for GUI mode"
    else
        echo -e "  ${GREEN}$INSTALL_DIR/mcp${NC}              # Launch GUI interface (default)"
        echo -e "  ${GREEN}$INSTALL_DIR/mcp interactive${NC}  # Launch interactive CLI"
        echo -e "  ${GREEN}$INSTALL_DIR/mcp update${NC}       # Update to latest version"
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