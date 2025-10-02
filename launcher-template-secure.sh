#!/bin/bash
# MCP Config Manager Launcher - Secure Version
# Auto-generated - Do not edit manually

set -euo pipefail
IFS=$'\n\t'

# Installation paths (replaced during install)
readonly INSTALL_DIR="{{APP_DIR}}"
readonly VENV_PATH="$INSTALL_DIR/{{VENV_NAME}}"
readonly UPDATE_TIMEOUT=60
readonly FETCH_TIMEOUT=30

# Verify installation exists and is not compromised
if [ ! -d "$INSTALL_DIR" ]; then
    echo "❌ MCP Config Manager not found at $INSTALL_DIR" >&2
    echo "   Please reinstall from: https://github.com/holstein13/mcp-config-manager" >&2
    exit 1
fi

# Check virtual environment
if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo "❌ Virtual environment not found or corrupted" >&2
    exit 1
fi

# Activate virtual environment
# shellcheck source=/dev/null
source "$VENV_PATH/bin/activate"

# Change to app directory
cd "$INSTALL_DIR" || exit 1

# Secure helper functions
get_timeout_cmd() {
    if command -v timeout >/dev/null 2>&1; then
        echo "timeout"
    elif command -v gtimeout >/dev/null 2>&1; then
        echo "gtimeout"
    else
        echo "none"
    fi
}

run_with_timeout() {
    local duration="${1:-30}"
    shift
    local timeout_cmd=$(get_timeout_cmd)

    if [ "$timeout_cmd" = "none" ]; then
        # Fallback with proper cleanup
        "$@" &
        local pid=$!
        local count=0

        while [ $count -lt "$duration" ]; do
            if ! kill -0 $pid 2>/dev/null; then
                wait $pid
                return $?
            fi
            sleep 1
            ((count++))
        done

        # Graceful shutdown
        kill -TERM $pid 2>/dev/null || true
        sleep 2
        kill -KILL $pid 2>/dev/null || true
        return 124
    else
        $timeout_cmd --signal=TERM --kill-after=5 "$duration" "$@"
    fi
}

read_config_value() {
    local config_file="$1"
    local key="$2"
    local default="$3"

    if [ -f "$config_file" ] && [ -r "$config_file" ]; then
        grep "^${key}=" "$config_file" 2>/dev/null | \
            head -n1 | cut -d'=' -f2- | tr -d '"' || echo "$default"
    else
        echo "$default"
    fi
}

safe_sed_replace() {
    local file="$1"
    local pattern="$2"
    local replacement="$3"
    local temp_file=""

    [ ! -f "$file" ] && return 1

    # Create temp file and ensure cleanup
    temp_file=$(mktemp) || return 1
    trap "rm -f '$temp_file'" RETURN

    if sed "s/${pattern}/${replacement}/" "$file" > "$temp_file" 2>/dev/null; then
        if [ -s "$file" ] && [ ! -s "$temp_file" ]; then
            return 1
        fi
        # Preserve permissions with secure fallback
        if ! chmod --reference="$file" "$temp_file" 2>/dev/null; then
            if [[ "$file" == *config* ]]; then
                chmod 600 "$temp_file"
            else
                chmod 644 "$temp_file"
            fi
        fi
        mv -f "$temp_file" "$file"
        return 0
    fi
    return 1
}

# Handle commands
case "${1:-}" in
    update|upgrade)
        echo "🔄 Checking for updates..."
        cd "$INSTALL_DIR" || exit 1

        # Read config securely
        UPDATE_CONFIG="$INSTALL_DIR/.mcp_update_config"
        UPDATES_ENABLED=$(read_config_value "$UPDATE_CONFIG" "UPDATES_ENABLED" "true")

        if [ "$UPDATES_ENABLED" != "true" ]; then
            echo "❌ Updates are disabled"
            echo "   Enable with: mcp config set updates.enabled true"
            exit 1
        fi

        if [ ! -d ".git" ]; then
            echo "❌ Not a git repository. Please reinstall for update support."
            exit 1
        fi

        # Verify repository with strict matching
        REMOTE_URL=$(git config --get remote.origin.url 2>/dev/null)
        EXPECTED_HTTPS="https://github.com/holstein13/mcp-config-manager.git"
        EXPECTED_HTTPS_NO_GIT="https://github.com/holstein13/mcp-config-manager"
        EXPECTED_SSH="git@github.com:holstein13/mcp-config-manager.git"

        if [[ "$REMOTE_URL" != "$EXPECTED_HTTPS" ]] &&
           [[ "$REMOTE_URL" != "$EXPECTED_HTTPS_NO_GIT" ]] &&
           [[ "$REMOTE_URL" != "$EXPECTED_SSH" ]]; then
            echo "❌ Repository verification failed"
            echo "   Expected: github.com/holstein13/mcp-config-manager"
            echo "   Got: $REMOTE_URL"
            exit 1
        fi

        # Fetch with timeout
        echo "📡 Checking for updates..."
        if ! run_with_timeout "$FETCH_TIMEOUT" git fetch origin; then
            echo "❌ Failed to check for updates (timeout/network issue)"
            exit 1
        fi

        LOCAL=$(git rev-parse HEAD)
        REMOTE=$(git rev-parse origin/master)

        if [ "$LOCAL" = "$REMOTE" ]; then
            echo "✅ Already up to date!"
            exit 0
        fi

        echo "📦 Installing updates..."

        # Backup (exclude large dirs)
        BACKUP_DIR="$INSTALL_DIR.backup.$(date +%Y%m%d_%H%M%S)"
        echo "💾 Creating backup: $BACKUP_DIR"

        if command -v rsync >/dev/null 2>&1; then
            rsync -a --exclude=venv --exclude=.git "$INSTALL_DIR/" "$BACKUP_DIR/"
        else
            mkdir -p "$BACKUP_DIR"
            find "$INSTALL_DIR" -type d \( -name venv -o -name .git \) -prune -o \
                -print | cpio -pdm "$BACKUP_DIR" 2>/dev/null
        fi

        # Update with verification
        if ! run_with_timeout "$UPDATE_TIMEOUT" git pull origin master; then
            echo "❌ Update failed"
            echo "💾 Restoring from backup..."
            rm -rf "$INSTALL_DIR"
            mv "$BACKUP_DIR" "$INSTALL_DIR"
            exit 1
        fi

        # Verify update
        NEW_LOCAL=$(git rev-parse HEAD)
        if [ "$LOCAL" = "$NEW_LOCAL" ]; then
            echo "❌ Update verification failed"
            rm -rf "$INSTALL_DIR"
            mv "$BACKUP_DIR" "$INSTALL_DIR"
            exit 1
        fi

        # Reinstall dependencies
        source "$VENV_PATH/bin/activate"
        pip install --quiet --upgrade pip
        pip install --quiet -e .

        # Clean backup on success
        rm -rf "$BACKUP_DIR"

        echo "✅ Update completed successfully!"
        exit 0
        ;;

    check-updates|update-status)
        cd "$INSTALL_DIR" || exit 1

        UPDATE_CONFIG="$INSTALL_DIR/.mcp_update_config"
        UPDATES_ENABLED=$(read_config_value "$UPDATE_CONFIG" "UPDATES_ENABLED" "true")

        echo "🔧 Updates enabled: $UPDATES_ENABLED"

        if [ "$UPDATES_ENABLED" != "true" ]; then
            exit 0
        fi

        if [ -d ".git" ]; then
            if run_with_timeout "$FETCH_TIMEOUT" git fetch origin --quiet; then
                LOCAL=$(git rev-parse HEAD)
                REMOTE=$(git rev-parse origin/master)

                if [ "$LOCAL" = "$REMOTE" ]; then
                    echo "✅ You have the latest version!"
                else
                    echo "📦 Updates available!"
                    echo "   Run 'mcp update' to install"
                fi
            else
                echo "❌ Failed to check for updates"
            fi
        fi
        exit 0
        ;;

    uninstall)
        exec "$INSTALL_DIR/uninstall.sh"
        ;;

    version|--version|-v)
        cd "$INSTALL_DIR" || exit 1
        python -c "import mcp_config_manager; print(f'v{mcp_config_manager.__version__}')" 2>/dev/null || \
            echo "MCP Config Manager (version unknown)"
        exit 0
        ;;

    config)
        UPDATE_CONFIG="$INSTALL_DIR/.mcp_update_config"

        case "${2:-}" in
            get)
                if [ -z "${3:-}" ]; then
                    echo "📋 Configuration:"
                    echo "  updates.enabled: $(read_config_value "$UPDATE_CONFIG" "UPDATES_ENABLED" "true")"
                    echo "  updates.channel: $(read_config_value "$UPDATE_CONFIG" "UPDATE_CHANNEL" "stable")"
                else
                    case "$3" in
                        updates.enabled)
                            read_config_value "$UPDATE_CONFIG" "UPDATES_ENABLED" "true"
                            ;;
                        updates.channel)
                            read_config_value "$UPDATE_CONFIG" "UPDATE_CHANNEL" "stable"
                            ;;
                        *)
                            echo "❌ Unknown setting: $3" >&2
                            exit 1
                            ;;
                    esac
                fi
                ;;

            set)
                [ ! -f "$UPDATE_CONFIG" ] && {
                    echo "❌ Config file not found" >&2
                    exit 1
                }

                case "${3:-}" in
                    updates.enabled)
                        if [[ "${4:-}" =~ ^(true|false)$ ]]; then
                            safe_sed_replace "$UPDATE_CONFIG" \
                                "UPDATES_ENABLED=.*" "UPDATES_ENABLED=$4"
                            echo "✅ Set updates.enabled = $4"
                        else
                            echo "❌ Value must be 'true' or 'false'" >&2
                            exit 1
                        fi
                        ;;
                    updates.channel)
                        if [[ "${4:-}" =~ ^(stable|beta|dev)$ ]]; then
                            safe_sed_replace "$UPDATE_CONFIG" \
                                "UPDATE_CHANNEL=.*" "UPDATE_CHANNEL=\"$4\""
                            echo "✅ Set updates.channel = $4"
                        else
                            echo "❌ Channel must be 'stable', 'beta', or 'dev'" >&2
                            exit 1
                        fi
                        ;;
                    *)
                        echo "❌ Unknown setting: ${3:-}" >&2
                        exit 1
                        ;;
                esac
                ;;

            *)
                echo "Usage: mcp config [get|set] [setting] [value]"
                echo "Settings: updates.enabled, updates.channel"
                exit 1
                ;;
        esac
        exit 0
        ;;

    help|--help|-h)
        echo "MCP Config Manager"
        echo ""
        echo "Usage: mcp [command] [options]"
        echo ""
        echo "Commands:"
        echo "  gui            Launch GUI (default)"
        echo "  interactive    Interactive CLI mode"
        echo "  status         Show status"
        echo "  update         Update to latest version"
        echo "  check-updates  Check for updates"
        echo "  config         Manage settings"
        echo "  uninstall      Remove application"
        echo "  version        Show version"
        echo "  help           Show this help"
        exit 0
        ;;

    "")
        # Default to GUI
        set -- gui
        ;;
esac

# Execute main application
exec mcp-config-manager "$@"