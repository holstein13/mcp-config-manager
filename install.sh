#!/bin/bash

# MCP Config Manager - Secure One-Click Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/holstein13/mcp-config-manager/main/install.sh | bash

set -euo pipefail  # Exit on error, undefined vars, pipe failures
IFS=$'\n\t'        # Set secure Internal Field Separator

# Security: Define constants at the top
readonly REPO_URL="https://github.com/holstein13/mcp-config-manager.git"
readonly REPO_FINGERPRINT="github.com/holstein13/mcp-config-manager"
readonly APP_NAME="mcp-config-manager"
readonly DEFAULT_INSTALL_DIR="$HOME/bin"
readonly VENV_NAME="venv"
readonly MIN_DISK_MB=100
readonly DEFAULT_TIMEOUT=30
readonly UPDATE_TIMEOUT=60
readonly CONFIG_PERMS=600

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly NC='\033[0m' # No Color

# Global variables for cleanup
APP_DIR=""
LAUNCHER_PATH=""
TEMP_FILES=()

# Print formatted messages
print_header() {
    echo -e "\n${PURPLE}================================================================${NC}"
    echo -e "${WHITE}  🔧 MCP Config Manager - Secure Installer${NC}"
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
    echo -e "${RED}❌${NC} $1" >&2
}

print_info() {
    echo -e "${CYAN}ℹ️${NC}  $1"
}

# Cleanup function for any failure
cleanup_on_failure() {
    local exit_code=$?

    if [ $exit_code -ne 0 ]; then
        print_error "Installation failed with exit code: $exit_code"

        # Clean up temp files
        for temp_file in "${TEMP_FILES[@]}"; do
            [ -f "$temp_file" ] && rm -f "$temp_file"
        done

        # Clean up partial installation
        if [ -n "$APP_DIR" ] && [ -d "$APP_DIR" ]; then
            print_warning "Cleaning up partial installation..."
            rm -rf "$APP_DIR"
        fi

        if [ -n "$LAUNCHER_PATH" ] && [ -f "$LAUNCHER_PATH" ]; then
            rm -f "$LAUNCHER_PATH"
        fi
    fi
}

# Set comprehensive error trap
trap cleanup_on_failure EXIT ERR INT TERM

# Security: Validate input to prevent injection
validate_path_input() {
    local input="$1"
    local path_type="${2:-directory}"

    # Check for dangerous characters and patterns
    if [[ "$input" =~ [;&|<>$\`\\] ]]; then
        print_error "Invalid $path_type path: contains shell metacharacters"
        return 1
    fi

    # Check for directory traversal attempts
    if [[ "$input" =~ \.\. ]]; then
        print_error "Invalid $path_type path: contains directory traversal"
        return 1
    fi

    # Ensure path doesn't contain wildcards
    if [[ "$input" =~ [*?[\]] ]]; then
        print_error "Invalid $path_type path: contains wildcards"
        return 1
    fi

    return 0
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Secure timeout implementation with proper cleanup
get_timeout_cmd() {
    if command_exists timeout; then
        echo "timeout"
    elif command_exists gtimeout; then
        echo "gtimeout"
    else
        echo "none"
    fi
}

# Run command with timeout and proper cleanup
run_with_timeout() {
    local duration="${1:-$DEFAULT_TIMEOUT}"
    shift
    local timeout_cmd=$(get_timeout_cmd)

    if [ "$timeout_cmd" = "none" ]; then
        # Improved fallback with proper signal handling
        local tmpfile=$(mktemp)
        TEMP_FILES+=("$tmpfile")

        # Run command in background
        "$@" &
        local pid=$!

        # Monitor with timeout
        local count=0
        while [ $count -lt "$duration" ]; do
            if ! kill -0 $pid 2>/dev/null; then
                wait $pid
                local exit_code=$?
                rm -f "$tmpfile"
                return $exit_code
            fi
            sleep 1
            ((count++))
        done

        # Timeout reached - graceful shutdown first
        kill -TERM $pid 2>/dev/null || true
        sleep 2

        # Force kill if still running
        if kill -0 $pid 2>/dev/null; then
            kill -KILL $pid 2>/dev/null || true
        fi

        rm -f "$tmpfile"
        return 124  # Standard timeout exit code
    else
        $timeout_cmd --signal=TERM --kill-after=5 "$duration" "$@"
    fi
}

# Check disk space
check_disk_space() {
    local install_dir="$1"
    local parent_dir=$(dirname "$install_dir")

    # Find a directory that exists to check
    while [ ! -d "$parent_dir" ] && [ "$parent_dir" != "/" ]; do
        parent_dir=$(dirname "$parent_dir")
    done

    if command_exists df; then
        local available_mb=$(df -m "$parent_dir" 2>/dev/null | awk 'NR==2 {print $4}')
        if [ -n "$available_mb" ] && [ "$available_mb" -lt "$MIN_DISK_MB" ]; then
            print_error "Insufficient disk space. Need at least ${MIN_DISK_MB}MB, but only ${available_mb}MB available."
            return 1
        fi
    fi
    return 0
}

# Safe config reader - avoids sourcing user-controlled files
read_config_value() {
    local config_file="$1"
    local key="$2"
    local default="$3"

    if [ -f "$config_file" ]; then
        local value=$(grep "^${key}=" "$config_file" 2>/dev/null | head -n1 | cut -d'=' -f2- | tr -d '"' || echo "$default")
        echo "${value:-$default}"
    else
        echo "$default"
    fi
}

# Platform-safe sed replacement with validation
safe_sed_replace() {
    local file="$1"
    local pattern="$2"
    local replacement="$3"

    # Validate inputs
    if [ ! -f "$file" ]; then
        return 1
    fi

    # Create secure temp file
    local temp_file=$(mktemp "${file}.XXXXXX")
    TEMP_FILES+=("$temp_file")

    # Perform replacement
    if sed "s/${pattern}/${replacement}/" "$file" > "$temp_file" 2>/dev/null; then
        # Verify temp file is not empty if original wasn't
        if [ -s "$file" ] && [ ! -s "$temp_file" ]; then
            rm -f "$temp_file"
            return 1
        fi

        # Preserve permissions (secure fallback based on file type)
        if ! chmod --reference="$file" "$temp_file" 2>/dev/null; then
            # Determine appropriate permissions
            if [[ "$file" == *.sh ]] || [[ -x "$file" ]]; then
                chmod 755 "$temp_file"
            elif [[ "$file" == *config* ]] || [[ "$file" == *rc ]]; then
                chmod 600 "$temp_file"  # Restrictive for config files
            else
                chmod 644 "$temp_file"  # Default for regular files
            fi
        fi

        # Atomic replace
        mv -f "$temp_file" "$file"
        return 0
    else
        rm -f "$temp_file"
        return 1
    fi
}

# Check system requirements
check_requirements() {
    print_step "Checking system requirements..."

    # Check for root (not recommended)
    if [[ $EUID -eq 0 ]]; then
        print_error "Running as root is not recommended for security reasons."
        print_info "Please run as a regular user. The installer will use sudo if needed."
        exit 1
    fi

    # Check Python
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed. Please install Python 3.8+ and try again."
        exit 1
    fi

    local python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        print_error "Python 3.8+ is required, but you have Python $python_version"
        exit 1
    fi
    print_success "Python $python_version detected"

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

# Get installation directory from user with validation
get_install_directory() {
    print_step "Selecting installation directory..."

    echo -e "\nWhere would you like to install MCP Config Manager?"
    echo -e "1) ${GREEN}$HOME/bin${NC} (recommended - user-local installation)"
    echo -e "2) ${YELLOW}$HOME/.local/bin${NC} (XDG standard location)"
    echo -e "3) ${YELLOW}/usr/local/bin${NC} (system-wide installation - requires sudo)"
    echo -e "4) ${CYAN}Custom directory${NC}"
    echo ""

    local install_dir=""
    while true; do
        read -rp "Enter your choice (1-4): " choice
        case "$choice" in
            1)
                install_dir="$HOME/bin"
                break
                ;;
            2)
                install_dir="$HOME/.local/bin"
                break
                ;;
            3)
                install_dir="/usr/local/bin"
                NEED_SUDO=true
                break
                ;;
            4)
                read -rp "Enter custom directory path: " custom_dir

                # Validate custom directory input
                if ! validate_path_input "$custom_dir"; then
                    continue
                fi

                # Resolve path safely
                if [[ "$custom_dir" = /* ]]; then
                    # Absolute path
                    install_dir="$custom_dir"
                else
                    # Relative path - safely combine
                    install_dir="$(pwd)/$custom_dir"
                fi

                # Canonicalize path safely (portable)
                if command_exists realpath; then
                    install_dir=$(realpath -m "$install_dir" 2>/dev/null) || install_dir="$install_dir"
                elif command_exists readlink && readlink -f /dev/null >/dev/null 2>&1; then
                    # macOS readlink doesn't have -m, use -f for existing paths
                    install_dir=$(cd "$(dirname "$install_dir")" 2>/dev/null && pwd)/$(basename "$install_dir") || install_dir="$install_dir"
                else
                    # Fallback: just use the path as-is
                    install_dir="$install_dir"
                fi
                break
                ;;
            *)
                echo "Invalid choice. Please enter 1, 2, 3, or 4."
                ;;
        esac
    done

    INSTALL_DIR="$install_dir"
    APP_DIR="$INSTALL_DIR/$APP_NAME"

    # Check disk space
    if ! check_disk_space "$APP_DIR"; then
        exit 1
    fi

    print_success "Installation directory: $APP_DIR"
}

# Create installation directory securely
create_install_directory() {
    print_step "Creating installation directory..."

    # Check if directory exists and is not a symlink
    if [ -e "$INSTALL_DIR" ]; then
        if [ -L "$INSTALL_DIR" ]; then
            print_error "Target directory is a symlink. Please choose a different location."
            exit 1
        fi
    fi

    # Create directory with explicit permissions
    if [[ "${NEED_SUDO:-false}" == "true" ]]; then
        sudo mkdir -p -m 755 "$INSTALL_DIR"
        sudo chown "$USER:$(id -gn)" "$INSTALL_DIR"
    else
        # Use umask to ensure secure permissions
        (umask 022 && mkdir -p "$INSTALL_DIR")
    fi

    # Verify directory was created and we own it
    if [ ! -d "$INSTALL_DIR" ]; then
        print_error "Failed to create installation directory"
        exit 1
    fi

    if [ ! -w "$INSTALL_DIR" ]; then
        print_error "No write permission for installation directory"
        exit 1
    fi

    print_success "Directory created: $INSTALL_DIR"
}

# Verify repository authenticity
verify_repository() {
    local repo_dir="$1"

    # Check git remote URL
    local remote_url=$(cd "$repo_dir" && git config --get remote.origin.url 2>/dev/null)

    # Strict repository URL verification (no wildcards)
    local expected_https="https://${REPO_FINGERPRINT}.git"
    local expected_ssh="git@${REPO_FINGERPRINT}.git"
    local expected_https_no_git="https://${REPO_FINGERPRINT}"

    if [[ "$remote_url" != "$expected_https" ]] &&
       [[ "$remote_url" != "$expected_ssh" ]] &&
       [[ "$remote_url" != "$expected_https_no_git" ]]; then
        print_error "Repository verification failed: unexpected remote URL"
        print_error "Expected: $REPO_FINGERPRINT"
        print_error "Got: $remote_url"
        return 1
    fi

    # Could add GPG signature verification here if commits are signed
    # git verify-commit HEAD 2>/dev/null || print_warning "Commit signature not verified"

    return 0
}

# Download and install application
install_application() {
    print_step "Downloading MCP Config Manager..."

    # Remove existing installation if it exists
    if [ -d "$APP_DIR" ]; then
        print_warning "Existing installation found. Removing..."
        rm -rf "$APP_DIR"
    fi

    # Clone repository with verification
    print_info "Cloning from $REPO_URL..."

    # Clone with explicit error handling
    local git_log=$(mktemp)
    TEMP_FILES+=("$git_log")

    if ! git clone --depth 1 "$REPO_URL" "$APP_DIR" 2>&1 | tee "$git_log"; then
        print_error "Failed to download repository. Check $git_log for details"
        exit 1
    fi

    cd "$APP_DIR" || exit 1

    # Verify repository
    if ! verify_repository "$APP_DIR"; then
        print_error "Repository verification failed"
        cd ..
        rm -rf "$APP_DIR"
        exit 1
    fi

    # Verify git clone succeeded
    if [ ! -d ".git" ]; then
        print_error "Repository clone verification failed"
        exit 1
    fi

    print_success "Application downloaded and verified"

    print_step "Setting up Python virtual environment..."
    python3 -m venv "$VENV_NAME"

    # shellcheck source=/dev/null
    source "$VENV_NAME/bin/activate"

    print_step "Installing dependencies..."

    # Upgrade pip with output for debugging
    local pip_upgrade_log=$(mktemp)
    TEMP_FILES+=("$pip_upgrade_log")

    if ! pip install --upgrade pip 2>&1 | tee "$pip_upgrade_log"; then
        print_error "Failed to upgrade pip. Check $pip_upgrade_log for details"
        exit 1
    fi

    # Install application with visible output for error detection
    print_info "Installing application (this may take a moment)..."
    local pip_install_log=$(mktemp)
    TEMP_FILES+=("$pip_install_log")

    if ! pip install -e . 2>&1 | tee "$pip_install_log"; then
        print_error "Failed to install application dependencies"
        print_error "Check $pip_install_log for details"
        exit 1
    fi

    # Try to install PyQt6 for better GUI experience
    print_step "Installing optional GUI dependencies..."
    if pip install PyQt6 2>/dev/null; then
        print_success "PyQt6 installed - enhanced GUI available"
    else
        print_warning "PyQt6 installation failed - will use tkinter fallback"
    fi

    print_success "Application installed successfully"
}

# Create default update configuration with secure permissions
create_update_config() {
    print_step "Creating update configuration..."

    local UPDATE_CONFIG="$APP_DIR/.mcp_update_config"

    # Enhanced CI detection
    local is_ci=false
    if [ -n "${CI:-}" ] || [ -n "${GITHUB_ACTIONS:-}" ] || [ -n "${JENKINS_URL:-}" ] || \
       [ -n "${GITLAB_CI:-}" ] || [ -n "${CIRCLECI:-}" ] || [ -n "${TRAVIS:-}" ] || \
       [ -n "${BUILDKITE:-}" ] || [ -n "${TEAMCITY_VERSION:-}" ] || \
       [ -n "${DRONE:-}" ] || [ -n "${SEMAPHORE:-}" ]; then
        is_ci=true
    fi

    local default_updates="true"
    local default_auto_check="true"

    if [ "$is_ci" = true ]; then
        default_updates="false"
        default_auto_check="false"
        print_info "Detected CI environment - updates disabled by default"
    fi

    # Create config with secure permissions
    (umask 077 && cat > "$UPDATE_CONFIG" << EOF
# MCP Config Manager Update Configuration
# Generated on $(date -Iseconds)

# Enable/disable updates completely
UPDATES_ENABLED=$default_updates

# Check for updates on startup
AUTO_CHECK_UPDATES=$default_auto_check

# Update channel: stable, beta, dev
UPDATE_CHANNEL="stable"

# Installation paths (for uninstaller)
INSTALL_DIR="$INSTALL_DIR"
APP_DIR="$APP_DIR"
EOF
    )

    # Set explicit permissions
    chmod $CONFIG_PERMS "$UPDATE_CONFIG"

    print_success "Update configuration created"
    if [ "$default_updates" = "false" ]; then
        print_warning "Updates are disabled by default in CI environment"
        print_info "To enable: mcp config set updates.enabled true"
    fi
}

# Create launcher script with consistent permissions
create_launcher() {
    print_step "Creating launcher script..."

    LAUNCHER_PATH="$INSTALL_DIR/mcp"

    # Create complete launcher in one operation for consistent permissions
    cat > "$LAUNCHER_PATH" << EOF
#!/bin/bash
# MCP Config Manager Launcher
# Auto-generated - Do not edit
# Security: This launcher validates installation integrity before execution

set -euo pipefail
IFS=\$'\\n\\t'

# Installation paths
readonly INSTALL_DIR="$APP_DIR"
readonly VENV_PATH="\$INSTALL_DIR/$VENV_NAME"

# Verify installation integrity
if [ ! -d "\$INSTALL_DIR" ]; then
    echo "❌ MCP Config Manager installation not found at \$INSTALL_DIR" >&2
    echo "   Please reinstall from: https://github.com/holstein13/mcp-config-manager" >&2
    exit 1
fi

if [ ! -f "\$VENV_PATH/bin/activate" ]; then
    echo "❌ Virtual environment not found or corrupted" >&2
    echo "   Please reinstall from: https://github.com/holstein13/mcp-config-manager" >&2
    exit 1
fi

# Verify no symlink attacks
if [ -L "\$INSTALL_DIR" ] || [ -L "\$VENV_PATH" ]; then
    echo "❌ Security warning: Installation directory contains symlinks" >&2
    exit 1
fi

# Activate virtual environment
# shellcheck source=/dev/null
source "\$VENV_PATH/bin/activate"

# Change to app directory
cd "\$INSTALL_DIR" || exit 1

# Execute application with all arguments (no string expansion)
exec mcp-config-manager "\$@"
EOF

    # Set secure permissions after creation
    chmod 755 "$LAUNCHER_PATH"
    print_success "Launcher created: $LAUNCHER_PATH"
}

# Setup shell integration with PATH validation
setup_shell_integration() {
    print_step "Setting up shell integration..."

    echo ""
    echo "Would you like to add the 'mcp' command to your shell PATH?"
    echo "This will allow you to run 'mcp' from anywhere in your terminal."
    echo ""

    read -rp "Add to shell PATH? (y/n): " add_to_path

    if [[ ! "$add_to_path" =~ ^[Yy]$ ]]; then
        print_info "Skipping shell integration"
        echo "You can manually run: $LAUNCHER_PATH"
        return
    fi

    # Detect shell
    local shell_name=$(basename "${SHELL:-/bin/bash}")
    local shell_config=""

    case "$shell_name" in
        bash)
            shell_config="$HOME/.bashrc"
            [ -f "$HOME/.bash_profile" ] && shell_config="$HOME/.bash_profile"
            ;;
        zsh)
            shell_config="$HOME/.zshrc"
            ;;
        fish)
            shell_config="$HOME/.config/fish/config.fish"
            ;;
        *)
            shell_config="$HOME/.profile"
            ;;
    esac

    # Validate INSTALL_DIR doesn't contain dangerous chars
    if ! validate_path_input "$INSTALL_DIR" "PATH"; then
        print_error "Cannot add to PATH: installation directory contains unsafe characters"
        return
    fi

    # Backup shell config
    if [ -f "$shell_config" ]; then
        cp "$shell_config" "${shell_config}.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # Safe modification of shell config
    if [ -f "$shell_config" ]; then
        local temp_file=$(mktemp)
        TEMP_FILES+=("$temp_file")

        # Remove old entries
        grep -v "# Added by MCP Config Manager installer" "$shell_config" | \
        grep -v "$INSTALL_DIR" > "$temp_file" || true

        # Validate temp file
        if [ -s "$shell_config" ] && [ ! -s "$temp_file" ]; then
            print_error "Failed to process shell config safely"
            rm -f "$temp_file"
            return
        fi

        mv "$temp_file" "$shell_config"
    fi

    # Add PATH based on shell type
    {
        echo ""
        echo "# Added by MCP Config Manager installer"
        if [ "$shell_name" = "fish" ]; then
            echo "set -gx PATH $INSTALL_DIR \$PATH"
        else
            echo "export PATH=\"$INSTALL_DIR:\$PATH\""
        fi
    } >> "$shell_config"

    print_success "Added to $shell_config"

    # Add convenience alias (except Fish)
    if [ "$shell_name" != "fish" ]; then
        echo "alias mcp-gui='mcp gui'" >> "$shell_config"
    else
        echo "function mcp-gui; mcp gui; end" >> "$shell_config"
    fi

    print_success "Shell integration complete"
}

# Create uninstaller
create_uninstaller() {
    print_step "Creating uninstaller..."

    cat > "$APP_DIR/uninstall.sh" << 'UNINSTALL_EOF'
#!/bin/bash
# MCP Config Manager Uninstaller

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}🗑️  MCP Config Manager Uninstaller${NC}"
echo ""

# Get paths from config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPDATE_CONFIG="$SCRIPT_DIR/.mcp_update_config"

if [ -f "$UPDATE_CONFIG" ]; then
    # shellcheck source=/dev/null
    INSTALL_DIR=$(grep "^INSTALL_DIR=" "$UPDATE_CONFIG" 2>/dev/null | cut -d'=' -f2- | tr -d '"')
    APP_DIR=$(grep "^APP_DIR=" "$UPDATE_CONFIG" 2>/dev/null | cut -d'=' -f2- | tr -d '"')
fi

# Fallback
: "${APP_DIR:=$SCRIPT_DIR}"
: "${INSTALL_DIR:=$(dirname "$APP_DIR")}"

echo "This will remove MCP Config Manager from: $APP_DIR"
read -rp "Are you sure? (y/N): " confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Remove launcher
[ -f "$INSTALL_DIR/mcp" ] && rm -f "$INSTALL_DIR/mcp"

# Clean shell configs
for config in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile" "$HOME/.config/fish/config.fish"; do
    if [ -f "$config" ] && grep -q "MCP Config Manager installer" "$config"; then
        cp "$config" "${config}.uninstall.backup"
        grep -v "# Added by MCP Config Manager installer" "$config" | \
        grep -v "$INSTALL_DIR" | \
        grep -v "mcp-gui" > "$config.tmp" || true
        mv "$config.tmp" "$config"
    fi
done

# Remove application
rm -rf "$APP_DIR"

echo -e "${GREEN}✅ Uninstalled successfully${NC}"
UNINSTALL_EOF

    chmod 755 "$APP_DIR/uninstall.sh"
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

    if [[ ":$PATH:" == *":$INSTALL_DIR:"* ]]; then
        echo -e "  ${GREEN}mcp${NC}              # Launch GUI"
        echo -e "  ${GREEN}mcp interactive${NC}  # Interactive CLI"
        echo -e "  ${GREEN}mcp --help${NC}       # Show all commands"
    else
        echo -e "  ${GREEN}$LAUNCHER_PATH${NC}         # Launch GUI"
        echo -e "  ${YELLOW}Restart terminal or run: source ~/.bashrc${NC}"
    fi

    echo ""
    echo -e "${WHITE}Documentation:${NC} https://github.com/holstein13/mcp-config-manager"
    echo -e "${WHITE}Uninstall:${NC} ${CYAN}$LAUNCHER_PATH uninstall${NC}"
    echo ""
}

# Main installation flow
main() {
    print_header

    check_requirements
    get_install_directory
    create_install_directory
    install_application
    create_update_config
    create_launcher
    create_uninstaller
    setup_shell_integration
    print_final_instructions

    # Success - disable cleanup trap
    trap - EXIT
}

# Run main installation
main "$@"