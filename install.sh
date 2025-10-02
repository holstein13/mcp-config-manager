#!/bin/bash

# MCP Config Manager - One-Click Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/holstein13/mcp-config-manager/main/install.sh | bash

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
REPO_URL="https://github.com/holstein13/mcp-config-manager.git"
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

# Safe config reader - avoids sourcing user-controlled files
read_config_value() {
    local config_file="$1"
    local key="$2"
    local default="$3"

    if [ -f "$config_file" ]; then
        local value=$(grep "^$key=" "$config_file" 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "$default")
        echo "${value:-$default}"
    else
        echo "$default"
    fi
}

# Platform-safe sed replacement
safe_sed_replace() {
    local file="$1"
    local pattern="$2"
    local replacement="$3"

    # Create temp file for platform compatibility
    local temp_file="${file}.tmp$$"

    if sed "s/$pattern/$replacement/" "$file" > "$temp_file"; then
        mv "$temp_file" "$file"
    else
        rm -f "$temp_file"
        return 1
    fi
}

# Check for timeout command or use alternative
get_timeout_cmd() {
    if command -v timeout >/dev/null 2>&1; then
        echo "timeout"
    elif command -v gtimeout >/dev/null 2>&1; then
        # macOS with coreutils installed
        echo "gtimeout"
    else
        # No timeout available, use background job with sleep
        echo "none"
    fi
}

# Run command with timeout
run_with_timeout() {
    local duration="$1"
    shift
    local timeout_cmd=$(get_timeout_cmd)

    if [ "$timeout_cmd" = "none" ]; then
        # Fallback: run in background and kill after timeout
        "$@" &
        local pid=$!
        ( sleep "$duration" && kill -9 $pid 2>/dev/null ) &
        local sleep_pid=$!
        if wait $pid 2>/dev/null; then
            kill $sleep_pid 2>/dev/null
            return 0
        else
            return 1
        fi
    else
        $timeout_cmd "$duration" "$@"
    fi
}

# Check disk space (needs at least 100MB)
check_disk_space() {
    local required_mb=100
    local install_dir="$1"

    # Get available space in MB
    local available_mb
    if command -v df >/dev/null 2>&1; then
        available_mb=$(df -m "$(dirname "$install_dir")" 2>/dev/null | awk 'NR==2 {print $4}')
        if [ -n "$available_mb" ] && [ "$available_mb" -lt "$required_mb" ]; then
            print_error "Insufficient disk space. Need at least ${required_mb}MB, but only ${available_mb}MB available."
            return 1
        fi
    fi
    return 0
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

# Cleanup on failure
cleanup_on_failure() {
    if [ -n "$APP_DIR" ] && [ -d "$APP_DIR" ]; then
        print_warning "Cleaning up partial installation..."
        rm -rf "$APP_DIR"
    fi
    if [ -n "$LAUNCHER_PATH" ] && [ -f "$LAUNCHER_PATH" ]; then
        rm -f "$LAUNCHER_PATH"
    fi
}

# Set trap for cleanup
trap 'cleanup_on_failure' ERR

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

    # Check disk space
    if ! check_disk_space "$APP_DIR"; then
        exit 1
    fi

    print_success "Installation directory: $APP_DIR"
}

# Create installation directory with race condition protection
create_install_directory() {
    print_step "Creating installation directory..."

    if [[ "$NEED_SUDO" == "true" ]]; then
        sudo mkdir -p "$INSTALL_DIR"
        sudo chown "$USER:$(id -gn)" "$INSTALL_DIR"
    else
        mkdir -p "$INSTALL_DIR" 2>/dev/null || true
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

    # Clone repository with shallow clone for performance
    print_info "Downloading from $REPO_URL..."
    if ! git clone --depth 1 "$REPO_URL" "$APP_DIR" --quiet; then
        print_error "Failed to download repository"
        cleanup_on_failure
        exit 1
    fi

    cd "$APP_DIR"

    # Verify git clone succeeded
    if [ ! -d ".git" ]; then
        print_error "Repository clone verification failed"
        exit 1
    fi

    print_success "Application downloaded"

    print_step "Setting up Python virtual environment..."
    python3 -m venv "$VENV_NAME"
    source "$VENV_NAME/bin/activate"

    print_step "Installing dependencies..."
    if ! pip install --quiet --upgrade pip; then
        print_error "Failed to upgrade pip"
        exit 1
    fi

    if ! pip install --quiet -e .; then
        print_error "Failed to install application dependencies"
        exit 1
    fi

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

    # Enhanced CI detection - check multiple CI environments
    if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ] || [ -n "$JENKINS_URL" ] || \
       [ -n "$GITLAB_CI" ] || [ -n "$CIRCLECI" ] || [ -n "$TRAVIS" ] || \
       [ -n "$BUILDKITE" ] || [ -n "$TEAMCITY_VERSION" ]; then
        DEFAULT_UPDATES="false"
        DEFAULT_AUTO_CHECK="false"
        print_info "Detected CI environment - updates disabled by default"
    else
        DEFAULT_UPDATES="true"
        DEFAULT_AUTO_CHECK="true"
    fi

    cat > "$UPDATE_CONFIG" << EOF
# MCP Config Manager Update Configuration
# Generated on $(date)

# Enable/disable updates completely
UPDATES_ENABLED=$DEFAULT_UPDATES

# Check for updates on startup (future feature)
AUTO_CHECK_UPDATES=$DEFAULT_AUTO_CHECK

# Update channel: stable, beta, dev
UPDATE_CHANNEL="stable"

# Installation paths (for uninstaller)
INSTALL_DIR="$INSTALL_DIR"
APP_DIR="$APP_DIR"
EOF

    print_success "Update configuration created"
    if [ "$DEFAULT_UPDATES" = "false" ]; then
        print_warning "Updates are disabled by default in CI environment"
        print_info "To enable: mcp config set updates.enabled true"
    fi
}

# Create launcher script
create_launcher() {
    print_step "Creating launcher script..."

    LAUNCHER_PATH="$INSTALL_DIR/mcp"

    cat > "$LAUNCHER_PATH" << 'EOF'
#!/bin/bash
# MCP Config Manager Launcher
# Generated by installer on '$(date)'

EOF

    # Add actual paths
    cat >> "$LAUNCHER_PATH" << EOF
INSTALL_DIR="$APP_DIR"
VENV_PATH="\$INSTALL_DIR/$VENV_NAME"

EOF

    # Add the rest of the launcher script
    cat >> "$LAUNCHER_PATH" << 'EOF'
# Check if installation exists
if [ ! -d "$INSTALL_DIR" ]; then
    echo "❌ MCP Config Manager installation not found at $INSTALL_DIR"
    echo "   Please reinstall using: curl -fsSL https://raw.githubusercontent.com/holstein13/mcp-config-manager/main/install.sh | bash"
    exit 1
fi

# Activate virtual environment
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
else
    echo "❌ Virtual environment not found. Installation may be corrupted."
    exit 1
fi

# Change to app directory
cd "$INSTALL_DIR"

# Check for timeout command or use alternative
get_timeout_cmd() {
    if command -v timeout >/dev/null 2>&1; then
        echo "timeout"
    elif command -v gtimeout >/dev/null 2>&1; then
        # macOS with coreutils installed
        echo "gtimeout"
    else
        # No timeout available
        echo "none"
    fi
}

# Run command with timeout
run_with_timeout() {
    local duration="$1"
    shift
    local timeout_cmd=$(get_timeout_cmd)

    if [ "$timeout_cmd" = "none" ]; then
        # Fallback: run in background and kill after timeout
        "$@" &
        local pid=$!
        ( sleep "$duration" && kill -9 $pid 2>/dev/null ) &
        local sleep_pid=$!
        if wait $pid 2>/dev/null; then
            kill $sleep_pid 2>/dev/null
            return 0
        else
            return 1
        fi
    else
        $timeout_cmd "$duration" "$@"
    fi
}

# Safe config reader function
read_config_value() {
    local config_file="$1"
    local key="$2"
    local default="$3"

    if [ -f "$config_file" ]; then
        local value=$(grep "^$key=" "$config_file" 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "$default")
        echo "${value:-$default}"
    else
        echo "$default"
    fi
}

# Platform-safe sed replacement
safe_sed_replace() {
    local file="$1"
    local pattern="$2"
    local replacement="$3"

    local temp_file="${file}.tmp$$"

    if sed "s/$pattern/$replacement/" "$file" > "$temp_file"; then
        mv "$temp_file" "$file"
    else
        rm -f "$temp_file"
        return 1
    fi
}

# Handle special commands first
case "$1" in
    update|upgrade)
        echo "🔄 Updating MCP Config Manager..."
        cd "$INSTALL_DIR"

        # Check update settings using safe config reader
        UPDATE_CONFIG="$INSTALL_DIR/.mcp_update_config"
        UPDATES_ENABLED=$(read_config_value "$UPDATE_CONFIG" "UPDATES_ENABLED" "true")
        AUTO_CHECK_UPDATES=$(read_config_value "$UPDATE_CONFIG" "AUTO_CHECK_UPDATES" "true")
        UPDATE_CHANNEL=$(read_config_value "$UPDATE_CONFIG" "UPDATE_CHANNEL" "stable")

        # Check if updates are disabled
        if [ "$UPDATES_ENABLED" != "true" ]; then
            echo "❌ Updates are disabled for this installation"
            echo "💡 To enable updates, run: mcp config set updates.enabled true"
            echo "   Or edit: $UPDATE_CONFIG"
            exit 1
        fi

        # Check if we have git repository
        if [ -d ".git" ]; then
            # Save current branch/state
            CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "master")

            # Fetch latest changes with timeout
            echo "📡 Checking for updates..."
            if ! run_with_timeout 30 git fetch origin; then
                echo "❌ Failed to check for updates (network timeout or authentication issue)"
                exit 1
            fi

            # Check if updates are available
            LOCAL=$(git rev-parse HEAD)
            REMOTE=$(git rev-parse origin/$CURRENT_BRANCH)

            if [ "$LOCAL" = "$REMOTE" ]; then
                echo "✅ Already up to date!"
                exit 0
            fi

            echo "📦 Updates available! Installing..."
            echo "📡 Update channel: $UPDATE_CHANNEL"

            # Backup current installation (lighter backup - exclude venv)
            BACKUP_DIR="$INSTALL_DIR.backup.$(date +%Y%m%d_%H%M%S)"
            echo "💾 Creating backup: $BACKUP_DIR"
            if command -v rsync >/dev/null 2>&1; then
                rsync -a --exclude=venv --exclude=.git "$INSTALL_DIR/" "$BACKUP_DIR/"
            else
                # Fallback: use find and cpio to exclude directories
                mkdir -p "$BACKUP_DIR"
                (cd "$INSTALL_DIR" && find . -type d \( -name venv -o -name .git \) -prune -o -print | cpio -pdm "$BACKUP_DIR" 2>/dev/null)
            fi

            # Determine branch based on update channel
            TARGET_BRANCH="$CURRENT_BRANCH"
            case "$UPDATE_CHANNEL" in
                "stable")
                    TARGET_BRANCH="master"
                    ;;
                "beta")
                    TARGET_BRANCH="beta"
                    ;;
                "dev")
                    TARGET_BRANCH="develop"
                    ;;
            esac

            # Switch to appropriate branch if needed
            if [ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ]; then
                echo "🔄 Switching to $UPDATE_CHANNEL channel (branch: $TARGET_BRANCH)"
                git checkout $TARGET_BRANCH 2>/dev/null || {
                    echo "⚠️  Branch $TARGET_BRANCH not found, staying on $CURRENT_BRANCH"
                    TARGET_BRANCH="$CURRENT_BRANCH"
                }
            fi

            # Update repository with timeout
            if ! run_with_timeout 60 git pull origin $TARGET_BRANCH; then
                echo "❌ Failed to pull updates (timeout or merge conflict)"
                echo "💡 Restoring from backup..."
                rm -rf "$INSTALL_DIR"
                mv "$BACKUP_DIR" "$INSTALL_DIR"
                exit 1
            fi

            # Verify update succeeded
            NEW_LOCAL=$(git rev-parse HEAD)
            if [ "$LOCAL" = "$NEW_LOCAL" ]; then
                echo "❌ Update verification failed - no changes applied"
                echo "💡 Restoring from backup..."
                rm -rf "$INSTALL_DIR"
                mv "$BACKUP_DIR" "$INSTALL_DIR"
                exit 1
            fi

            # Reinstall dependencies
            source "$VENV_PATH/bin/activate"
            if ! pip install --quiet --upgrade pip; then
                print_warning "Failed to upgrade pip during update"
            fi

            if ! pip install --quiet -e .; then
                print_error "Failed to reinstall dependencies"
                echo "💡 Restoring from backup..."
                rm -rf "$INSTALL_DIR"
                mv "$BACKUP_DIR" "$INSTALL_DIR"
                exit 1
            fi

            # Try to update PyQt6
            pip install --quiet --upgrade PyQt6 2>/dev/null || true

            echo "✅ Update completed successfully!"
            echo "💡 Run 'mcp --version' to see the new version"
        else
            echo "❌ Cannot update: Installation not git-enabled"
            echo "💡 Re-run the installer to get the latest version:"
            echo "   curl -fsSL https://raw.githubusercontent.com/holstein13/mcp-config-manager/main/install.sh | bash"
        fi
        exit 0
        ;;
    update-status|check-updates)
        echo "🔍 Checking for updates..."
        cd "$INSTALL_DIR"

        # Check update settings using safe config reader
        UPDATE_CONFIG="$INSTALL_DIR/.mcp_update_config"
        UPDATES_ENABLED=$(read_config_value "$UPDATE_CONFIG" "UPDATES_ENABLED" "true")
        UPDATE_CHANNEL=$(read_config_value "$UPDATE_CONFIG" "UPDATE_CHANNEL" "stable")

        echo "📡 Update channel: $UPDATE_CHANNEL"
        echo "🔧 Updates enabled: $UPDATES_ENABLED"

        if [ "$UPDATES_ENABLED" != "true" ]; then
            echo "❌ Updates are disabled for this installation"
            exit 0
        fi

        if [ -d ".git" ]; then
            CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "master")
            echo "🌿 Current branch: $CURRENT_BRANCH"

            # Determine target branch
            TARGET_BRANCH="$CURRENT_BRANCH"
            case "$UPDATE_CHANNEL" in
                "stable") TARGET_BRANCH="master" ;;
                "beta") TARGET_BRANCH="beta" ;;
                "dev") TARGET_BRANCH="develop" ;;
            esac

            if run_with_timeout 30 git fetch origin --quiet; then
                LOCAL=$(git rev-parse HEAD)
                REMOTE=$(git rev-parse origin/$TARGET_BRANCH 2>/dev/null || git rev-parse origin/$CURRENT_BRANCH)

                if [ "$LOCAL" = "$REMOTE" ]; then
                    echo "✅ You have the latest version!"
                else
                    echo "📦 Updates are available!"
                    echo "💡 Run 'mcp update' to install updates"

                    # Show commit summary
                    COMMIT_COUNT=$(git rev-list --count HEAD..origin/$TARGET_BRANCH 2>/dev/null || echo "unknown")
                    if [ "$COMMIT_COUNT" != "unknown" ] && [ "$COMMIT_COUNT" -gt 0 ]; then
                        echo "📊 $COMMIT_COUNT new commit(s) available"
                    fi
                fi
            else
                echo "❌ Failed to check for updates (network timeout)"
            fi
        else
            echo "❌ Cannot check for updates: Installation not git-enabled"
            echo "💡 Re-run the installer to get a git-enabled installation"
        fi
        exit 0
        ;;
    uninstall)
        exec "$INSTALL_DIR/uninstall.sh"
        ;;
    --version|-v|version)
        cd "$INSTALL_DIR"
        source "$VENV_PATH/bin/activate"
        python -c "import mcp_config_manager; print(f'MCP Config Manager v{mcp_config_manager.__version__}')" 2>/dev/null || echo "MCP Config Manager (version unknown)"
        exit 0
        ;;
    config)
        # Configuration management
        UPDATE_CONFIG="$INSTALL_DIR/.mcp_update_config"

        case "$2" in
            "get")
                if [ -n "$3" ]; then
                    # Get specific setting using safe reader
                    case "$3" in
                        "updates.enabled")
                            read_config_value "$UPDATE_CONFIG" "UPDATES_ENABLED" "true"
                            ;;
                        "updates.auto_check")
                            read_config_value "$UPDATE_CONFIG" "AUTO_CHECK_UPDATES" "true"
                            ;;
                        "updates.channel")
                            read_config_value "$UPDATE_CONFIG" "UPDATE_CHANNEL" "stable"
                            ;;
                        *)
                            echo "❌ Unknown setting: $3"
                            echo "Available settings: updates.enabled, updates.auto_check, updates.channel"
                            exit 1
                            ;;
                    esac
                else
                    echo "📋 Current update configuration:"
                    echo "  updates.enabled: $(read_config_value "$UPDATE_CONFIG" "UPDATES_ENABLED" "true")"
                    echo "  updates.auto_check: $(read_config_value "$UPDATE_CONFIG" "AUTO_CHECK_UPDATES" "true")"
                    echo "  updates.channel: $(read_config_value "$UPDATE_CONFIG" "UPDATE_CHANNEL" "stable")"
                fi
                ;;
            "set")
                # Create config file if it doesn't exist
                if [ ! -f "$UPDATE_CONFIG" ]; then
                    cat > "$UPDATE_CONFIG" << 'CONFIG_EOF'
# MCP Config Manager Update Configuration
# Generated on $(date)

# Enable/disable updates completely
UPDATES_ENABLED=true

# Check for updates on startup (future feature)
AUTO_CHECK_UPDATES=true

# Update channel: stable, beta, dev
UPDATE_CHANNEL="stable"
CONFIG_EOF
                fi

                case "$3" in
                    "updates.enabled")
                        if [ "$4" = "true" ] || [ "$4" = "false" ]; then
                            safe_sed_replace "$UPDATE_CONFIG" "UPDATES_ENABLED=.*" "UPDATES_ENABLED=$4"
                            echo "✅ Set updates.enabled = $4"
                        else
                            echo "❌ Value must be 'true' or 'false'"
                            exit 1
                        fi
                        ;;
                    "updates.auto_check")
                        if [ "$4" = "true" ] || [ "$4" = "false" ]; then
                            safe_sed_replace "$UPDATE_CONFIG" "AUTO_CHECK_UPDATES=.*" "AUTO_CHECK_UPDATES=$4"
                            echo "✅ Set updates.auto_check = $4"
                        else
                            echo "❌ Value must be 'true' or 'false'"
                            exit 1
                        fi
                        ;;
                    "updates.channel")
                        if [ "$4" = "stable" ] || [ "$4" = "beta" ] || [ "$4" = "dev" ]; then
                            safe_sed_replace "$UPDATE_CONFIG" "UPDATE_CHANNEL=.*" "UPDATE_CHANNEL=\"$4\""
                            echo "✅ Set updates.channel = $4"
                        else
                            echo "❌ Channel must be 'stable', 'beta', or 'dev'"
                            exit 1
                        fi
                        ;;
                    *)
                        echo "❌ Unknown setting: $3"
                        echo "Available settings: updates.enabled, updates.auto_check, updates.channel"
                        exit 1
                        ;;
                esac
                ;;
            "reset")
                rm -f "$UPDATE_CONFIG"
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
        echo "  gui            Launch GUI interface (default)"
        echo "  interactive    Launch interactive CLI mode"
        echo "  status         Show configuration status"
        echo "  update         Update to latest version"
        echo "  update-status  Check for available updates"
        echo "  config         Manage update preferences"
        echo "  uninstall      Remove MCP Config Manager"
        echo "  version        Show version information"
        echo "  help           Show this help message"
        echo ""
        echo "Configuration:"
        echo "  mcp config get                       # Show all settings"
        echo "  mcp config set updates.enabled false # Disable updates"
        echo "  mcp config set updates.channel beta  # Use beta channel"
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
exec mcp-config-manager "$@"
EOF

    chmod +x "$LAUNCHER_PATH"
    print_success "Launcher created: $LAUNCHER_PATH"

    # Create default update configuration
    create_update_config
}

# Add to shell configuration with PATH deduplication
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

        # Check if already in PATH to avoid duplicates
        PATH_EXPORT="export PATH=\"$INSTALL_DIR:\$PATH\""

        # Safe shell config modification
        if [ -f "$SHELL_CONFIG" ]; then
            # Create backup first
            cp "$SHELL_CONFIG" "${SHELL_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

            # Remove old entries safely
            TEMP_FILE="${SHELL_CONFIG}.tmp.$$"
            grep -v "# Added by MCP Config Manager installer" "$SHELL_CONFIG" | \
            grep -v "$INSTALL_DIR" | \
            grep -v "mcp-gui" > "$TEMP_FILE" || echo -n "" > "$TEMP_FILE"

            # Verify temp file is not empty (unless original was empty)
            if [ -s "$SHELL_CONFIG" ] && [ ! -s "$TEMP_FILE" ]; then
                print_error "Failed to process shell config safely. Backup saved as ${SHELL_CONFIG}.backup.*"
                rm -f "$TEMP_FILE"
                exit 1
            fi

            mv "$TEMP_FILE" "$SHELL_CONFIG"
        fi

        # Add new PATH entry based on shell type
        echo "" >> "$SHELL_CONFIG"
        echo "# Added by MCP Config Manager installer" >> "$SHELL_CONFIG"

        if [ "$SHELL_NAME" = "fish" ]; then
            # Fish shell uses different syntax
            echo "set -gx PATH $INSTALL_DIR \$PATH" >> "$SHELL_CONFIG"
        else
            echo "$PATH_EXPORT" >> "$SHELL_CONFIG"
        fi

        print_success "Added to $SHELL_CONFIG"

        # Create alias for convenience (except Fish which uses functions)
        if [ "$SHELL_NAME" != "fish" ]; then
            ALIAS_LINE="alias mcp-gui='mcp gui'"
            if ! grep -q "mcp-gui" "$SHELL_CONFIG" 2>/dev/null; then
                echo "alias mcp-gui='mcp gui'" >> "$SHELL_CONFIG"
                print_success "Added 'mcp-gui' alias"
            fi
        else
            # Fish uses functions instead of aliases
            echo "function mcp-gui; mcp gui; end" >> "$SHELL_CONFIG"
            print_success "Added 'mcp-gui' function for Fish"
        fi

        export PATH="$INSTALL_DIR:$PATH"
        print_success "Shell integration complete"
    else
        print_info "Skipping shell integration"
        echo "You can manually run: $INSTALL_DIR/mcp"
    fi
}

# Create uninstaller with correct path handling
create_uninstaller() {
    print_step "Creating uninstaller..."

    cat > "$APP_DIR/uninstall.sh" << 'UNINSTALL_EOF'
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

# Get paths from config or use defaults
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPDATE_CONFIG="$SCRIPT_DIR/.mcp_update_config"

# Try to read paths from config
if [ -f "$UPDATE_CONFIG" ]; then
    INSTALL_DIR=$(grep "^INSTALL_DIR=" "$UPDATE_CONFIG" 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "")
    APP_DIR=$(grep "^APP_DIR=" "$UPDATE_CONFIG" 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "")
fi

# Fallback to computed paths
if [ -z "$INSTALL_DIR" ] || [ -z "$APP_DIR" ]; then
    APP_DIR="$SCRIPT_DIR"
    # Try to determine INSTALL_DIR from launcher location
    FOUND_LAUNCHER=false
    for check_dir in "$HOME/bin" "$HOME/.local/bin" "/usr/local/bin"; do
        if [ -f "$check_dir/mcp" ]; then
            # Verify this launcher points to our installation
            if grep -q "$SCRIPT_DIR" "$check_dir/mcp" 2>/dev/null; then
                INSTALL_DIR="$check_dir"
                FOUND_LAUNCHER=true
                break
            fi
        fi
    done

    if [ "$FOUND_LAUNCHER" = false ]; then
        # Last resort: assume parent directory
        INSTALL_DIR="$(dirname "$APP_DIR")"
        echo "⚠️  Warning: Could not determine original install directory."
        echo "   Assuming: $INSTALL_DIR"
        echo "   If this is incorrect, please manually remove:"
        echo "   - The installation directory"
        echo "   - The launcher script from your PATH"
    fi
fi

LAUNCHER_PATH="$INSTALL_DIR/mcp"

echo ""
echo -e "${RED}🗑️  MCP Config Manager Uninstaller${NC}"
echo ""
echo "This will remove MCP Config Manager from your system."
echo -e "Installation directory: ${YELLOW}$APP_DIR${NC}"
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

print_step "Removing shell integration..."
for config_file in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile" "$HOME/.config/fish/config.fish"; do
    if [ -f "$config_file" ]; then
        if grep -q "MCP Config Manager installer" "$config_file" 2>/dev/null; then
            # Create backup
            cp "$config_file" "${config_file}.uninstall.backup"

            # Remove the installer lines safely
            TEMP_FILE="${config_file}.tmp.$$"
            grep -v "# Added by MCP Config Manager installer" "$config_file" | \
            grep -v "$INSTALL_DIR" | \
            grep -v "mcp-gui" > "$TEMP_FILE" || echo -n "" > "$TEMP_FILE"

            # Only replace if we have a valid file
            if [ -s "$config_file" ] && [ ! -s "$TEMP_FILE" ]; then
                print_warning "Skipped $config_file - backup saved as ${config_file}.uninstall.backup"
                rm -f "$TEMP_FILE"
            else
                mv "$TEMP_FILE" "$config_file"
                print_success "Cleaned $config_file"
            fi
        fi
    fi
done

print_step "Removing application directory..."
cd "$HOME"
rm -rf "$APP_DIR"
print_success "Application removed"

echo ""
echo -e "${GREEN}✅ MCP Config Manager has been successfully uninstalled!${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} Please restart your terminal to complete the removal."
echo ""
UNINSTALL_EOF

    chmod +x "$APP_DIR/uninstall.sh"
    print_success "Uninstaller created"
}

# Print final instructions
print_final_instructions() {
    echo ""
    echo -e "${GREEN}🎉 Installation Complete!${NC}"
    echo ""
    echo -e "${WHITE}MCP Config Manager installed to:${NC} $APP_DIR"
    echo ""
    echo -e "${WHITE}Quick Start:${NC}"
    if command_exists mcp 2>/dev/null || [[ ":$PATH:" == *":$INSTALL_DIR:"* ]]; then
        echo -e "  ${GREEN}mcp${NC}              # Launch GUI (default)"
        echo -e "  ${GREEN}mcp interactive${NC}  # Interactive CLI"
        echo -e "  ${GREEN}mcp --help${NC}       # Show all commands"
    else
        echo -e "  ${GREEN}$INSTALL_DIR/mcp${NC}         # Launch GUI"
        echo -e "  ${YELLOW}Restart terminal or run: source ~/.bashrc${NC}"
    fi
    echo ""
    echo -e "${WHITE}Documentation:${NC} https://github.com/holstein13/mcp-config-manager"
    echo -e "${WHITE}Uninstall:${NC} ${CYAN}$INSTALL_DIR/mcp uninstall${NC}"
    echo ""
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
    print_final_instructions
}

# Handle interruption gracefully
trap 'echo -e "\n${RED}Installation interrupted${NC}"; exit 1' INT

# Run main installation
main "$@"