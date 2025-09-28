# Update Control

MCP Config Manager allows you to control when and how updates are applied.

## Quick Commands

### Check Update Status
```bash
mcp config get updates.enabled   # Check if updates are enabled
```

### Enable Updates
```bash
mcp config set updates.enabled true
```

### Disable Updates
```bash
mcp config set updates.enabled false
```

### Update Application
```bash
mcp update                       # Update if enabled
mcp update-status               # Check for available updates
```

## Settings

| Setting | Values | Description |
|---------|--------|-------------|
| `updates.enabled` | `true`/`false` | Enable or disable updates |

## Environment Defaults

- **CI/CD environments**: Updates disabled by default
- **Standard installations**: Updates enabled by default

You can always override the default by using `mcp config set updates.enabled true/false`.

## Examples

### Disable Updates for Production
```bash
mcp config set updates.enabled false
```

### Enable Updates for Development
```bash
mcp config set updates.enabled true
mcp update
```

### Check Current Configuration
```bash
mcp config get
```

That's it! Simple update control for your MCP Config Manager installation.