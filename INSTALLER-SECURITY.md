# MCP Config Manager Installer Security Documentation

## Security Model

The MCP Config Manager installer implements defense-in-depth security with multiple layers of protection against common installation vulnerabilities.

## Security Features

### 1. Input Validation

All user inputs are validated before use:

- **Path Validation**: Blocks shell metacharacters (`; & | < > $ \` \\`), directory traversal (`..`), and wildcards (`* ? [ ]`)
- **Custom Directory**: User-provided paths are sanitized and canonicalized
- **Repository URL**: Strict matching against known-good patterns (no wildcards)

### 2. Process Security

- **Strict Bash Mode**: `set -euo pipefail` ensures immediate exit on errors
- **Secure IFS**: `IFS=$'\n\t'` prevents word splitting exploits
- **No Root Execution**: Installer refuses to run as root for security
- **Cleanup on Failure**: Comprehensive trap handlers clean up partial installs

### 3. File System Security

- **TOCTOU Prevention**: Checks for symlinks before directory operations
- **Atomic Operations**: Uses temp files with atomic moves
- **Secure Permissions**:
  - Config files: 600 (owner read/write only)
  - Scripts: 755 (executable)
  - Regular files: 644 (world readable)
- **umask Protection**: Directory creation uses `umask 022`

### 4. Network Security

- **Repository Verification**: Validates git remote URLs against fingerprint
- **Timeout Protection**: All network operations have timeouts (30-60 seconds)
- **Graceful Degradation**: Falls back safely if network operations fail

### 5. Code Execution Prevention

- **No Sourcing User Files**: Never executes user-controlled configuration files
- **Safe Config Reading**: Uses `grep` and `cut` instead of `source`
- **Command Injection Prevention**: All variables properly quoted

## Threat Model

The installer defends against:

1. **Shell Injection**: Malicious input in custom directories
2. **Path Traversal**: Attempts to install outside intended directories
3. **TOCTOU Attacks**: Race conditions during directory creation
4. **Symlink Attacks**: Malicious symlinks to sensitive locations
5. **Repository Hijacking**: Installing from malicious repositories
6. **Privilege Escalation**: Unsafe operations as root
7. **Information Disclosure**: Logs stored with secure permissions

## Recovery Procedures

### Installation Failure

If installation fails:
1. Automatic cleanup removes partial installation
2. Temp files are cleaned up via trap handlers
3. Error logs are preserved for debugging

### Update Failure

If update fails:
1. Automatic rollback from backup
2. Original installation is preserved
3. User notified with recovery instructions

### Uninstall Safety

The uninstaller:
1. Backs up shell configs before modification
2. Only removes known installation files
3. Preserves user data and configurations

## Update Channels

Three update channels are supported:

- **stable** (default): Production-ready releases
- **beta**: Pre-release testing versions
- **dev**: Development builds (use with caution)

Channel configuration is stored in `.mcp_update_config` with restricted permissions.

## Platform Compatibility

### Timeout Commands
- Linux: `timeout` (coreutils)
- macOS: `gtimeout` (requires `brew install coreutils`)
- Fallback: Background job with signal handling

### Path Canonicalization
- Linux: `realpath -m` or `readlink -m`
- macOS: Manual canonicalization with `cd` and `pwd`
- Fallback: Use path as-is

### Shell Support
- Bash: Full support
- Zsh: Full support
- Fish: Custom syntax for PATH and functions
- Other: Basic POSIX support via `.profile`

## CI/CD Integration

The installer detects CI environments and automatically:
- Disables auto-updates
- Suppresses interactive prompts
- Uses restrictive permissions

Detected CI systems:
- GitHub Actions
- GitLab CI
- CircleCI
- Travis CI
- Jenkins
- BuildKite
- TeamCity
- Drone CI
- Semaphore
- Generic `CI` environment variable

## Security Best Practices

### For Users

1. **Verify Source**: Only install from official repository
2. **Check Permissions**: Ensure installer has correct permissions (755)
3. **Avoid Root**: Never run installer as root unless absolutely necessary
4. **Review Logs**: Check installation logs for any warnings

### For Developers

1. **Input Validation**: Always validate user input before use
2. **Error Handling**: Use proper error codes and cleanup
3. **Logging**: Log security-relevant events
4. **Testing**: Test installation on multiple platforms
5. **Updates**: Keep dependencies and base images updated

## Vulnerability Reporting

Report security vulnerabilities to: security@mcp-config-manager.org

Please include:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Audit Trail

All security-relevant operations are logged:
- Installation location and time
- Update operations with version changes
- Configuration modifications
- Error conditions with context

Logs are stored with restrictive permissions (600) to prevent information disclosure.

## Compliance

The installer follows security best practices from:
- OWASP Secure Coding Practices
- CIS Security Benchmarks
- NIST Guidelines for secure software

## Version History

- v2.0.0: Complete security rewrite
  - Input validation for all user inputs
  - TOCTOU prevention
  - Secure temp file handling
  - Repository verification
  - Comprehensive error handling

- v1.0.0: Initial release (deprecated)