# Update Control System

MCP Config Manager includes a comprehensive update control system that allows users and administrators to manage updates according to their needs.

## 🔧 Quick Start

### Check Current Settings
```bash
mcp config get                    # Show all settings
mcp config get updates.enabled   # Check if updates are enabled
```

### Disable Updates (Enterprise/Production)
```bash
mcp config set updates.enabled false
```

### Enable Updates
```bash
mcp config set updates.enabled true
```

### Change Update Channel
```bash
mcp config set updates.channel stable  # Default, most stable
mcp config set updates.channel beta    # Beta features, tested
mcp config set updates.channel dev     # Latest development
```

## 📋 Configuration Options

| Setting | Values | Description |
|---------|--------|-------------|
| `updates.enabled` | `true`/`false` | Enable/disable all updates |
| `updates.auto_check` | `true`/`false` | Check for updates on startup (future) |
| `updates.channel` | `stable`/`beta`/`dev` | Update release channel |

## 🏢 Environment-Specific Defaults

The installer automatically detects your environment and sets appropriate defaults:

### Enterprise/CI/Container Environments
**Updates: DISABLED by default**
- Detected in: CI/CD pipelines, Kubernetes clusters, Docker containers
- Rationale: Controlled environments need predictable software versions
- Override: `mcp config set updates.enabled true`

### Remote SSH Environments
**Updates: ENABLED, Auto-check: DISABLED**
- Detected in: SSH connections, remote servers
- Rationale: Manual update control preferred on servers
- Override: `mcp config set updates.auto_check true`

### Standard Desktop Environments
**Updates: ENABLED, Auto-check: ENABLED**
- Detected in: Local desktop/laptop installations
- Rationale: Individual users benefit from automatic updates

## 🔄 Update Commands

### Check for Updates
```bash
mcp update-status    # Check if updates are available
# Output:
# 🔍 Checking for updates...
# 📡 Update channel: stable
# 🔧 Updates enabled: true
# 🌿 Current branch: main
# ✅ You have the latest version!
```

### Perform Update
```bash
mcp update          # Update if enabled
# Output:
# 🔄 Updating MCP Config Manager...
# 📡 Update channel: stable
# 💾 Creating backup: /path/to/backup
# 📦 Updates available! Installing...
# ✅ Update completed successfully!
```

### Update When Disabled
```bash
mcp update
# Output:
# ❌ Updates are disabled for this installation
# 💡 To enable updates, run: mcp config set updates.enabled true
```

## 🎯 Update Channels Explained

### Stable Channel (Default)
- **Branch**: `main`
- **Frequency**: Monthly releases
- **Content**: Fully tested features, bug fixes
- **Recommended for**: Production use, enterprise environments
- **Stability**: ⭐⭐⭐⭐⭐

### Beta Channel
- **Branch**: `beta`
- **Frequency**: Bi-weekly releases
- **Content**: New features in testing, recent bug fixes
- **Recommended for**: Power users, testing environments
- **Stability**: ⭐⭐⭐⭐☆

### Dev Channel
- **Branch**: `develop`
- **Frequency**: Daily/weekly commits
- **Content**: Latest features, experimental changes
- **Recommended for**: Developers, contributors
- **Stability**: ⭐⭐⭐☆☆

## 💼 Enterprise Use Cases

### Scenario 1: Corporate Environment
```bash
# Disable updates for all corporate machines
mcp config set updates.enabled false

# Centrally manage updates through IT department
# Updates done manually during maintenance windows
```

### Scenario 2: Development Team
```bash
# Use beta channel for latest features
mcp config set updates.channel beta
mcp config set updates.enabled true

# Developers get new features quickly
# But still stable enough for development work
```

### Scenario 3: CI/CD Pipeline
```bash
# Updates automatically disabled on detection
# Ensures consistent builds
# Manual override available if needed:
mcp config set updates.enabled true
```

## 🔒 Security Considerations

### Update Verification
- All updates pulled from official GitHub repository
- Git signature verification (when available)
- Automatic backup before updates
- Rollback capability via backup restoration

### Network Requirements
- Updates require internet access to GitHub
- Uses HTTPS for all communications
- No telemetry or tracking data sent

### Permissions
- Updates only modify the installation directory
- No system-wide changes required
- User-level permissions sufficient

## 🛠️ Advanced Configuration

### Manual Configuration File
Location: `<installation-dir>/.mcp_update_config`

```bash
# MCP Config Manager Update Configuration
# Generated on 2024-01-15

# Enable/disable updates completely
UPDATES_ENABLED=true

# Check for updates on startup (future feature)
AUTO_CHECK_UPDATES=true

# Update channel: stable, beta, dev
UPDATE_CHANNEL="stable"

# Environment detection (informational)
DETECTED_ENVIRONMENT="standard"
```

### Environment Variables
Override config file settings:
```bash
export MCP_UPDATES_ENABLED=false
export MCP_UPDATE_CHANNEL=beta
mcp update  # Uses environment variable values
```

### Backup Management
Automatic backups are created before updates:
```bash
# Backup location pattern:
<installation-dir>.backup.YYYYMMDD_HHMMSS

# Restore from backup:
rm -rf <installation-dir>
mv <installation-dir>.backup.20240115_143022 <installation-dir>
```

## 🔍 Troubleshooting

### Updates Not Working
1. **Check if enabled**: `mcp config get updates.enabled`
2. **Check git repository**: `cd <install-dir> && git status`
3. **Check network**: `curl -s https://github.com`
4. **Force reinstall**: Re-run installer script

### Wrong Update Channel
```bash
# Check current channel
mcp config get updates.channel

# Switch channel
mcp config set updates.channel stable
mcp update  # Will switch to appropriate branch
```

### Reset Configuration
```bash
# Reset all settings to defaults
mcp config reset

# Or manually delete config file
rm <installation-dir>/.mcp_update_config
```

## 📈 Future Features

Planned enhancements for the update system:

- **Auto-update notifications**: Desktop notifications when updates are available
- **Scheduled updates**: Automatic updates at specified times
- **Update rollback**: Easy rollback to previous versions
- **Update logs**: Detailed logging of update history
- **Proxy support**: Updates through corporate proxies
- **Offline updates**: Update from downloaded packages

## 🤝 Contributing

To contribute to the update system:

1. Test update scenarios in different environments
2. Report issues with environment detection
3. Suggest improvements for enterprise use cases
4. Help with documentation and examples

## 📞 Support

If you encounter issues with updates:

1. Check this documentation first
2. Run `mcp config get` to see current settings
3. Try `mcp update-status` to diagnose issues
4. Report bugs with environment details and config settings

---

**Remember**: You always have complete control over when and how updates are applied to your MCP Config Manager installation!