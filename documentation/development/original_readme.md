# MCP Server Toggle for Claude Code CLI

A Python script to manage MCP (Model Context Protocol) servers in Claude Code CLI, allowing you to quickly enable/disable servers to reduce context usage and switch between project configurations.

## Problem This Solves

Claude Code CLI loads all MCP servers defined in `~/.claude.json` at startup, which can consume significant context. This script allows you to:
- Instantly disable unnecessary servers to maximize available context
- Switch between project-specific configurations (different Supabase projects, Clerk API keys, etc.)
- Preserve server configurations when disabled (like commenting out code)
- Manage project presets in a separate, easy-to-edit file

## Prerequisites

- Python 3 installed (`python3 --version` to check)
- Claude Code CLI installed
- `~/.claude.json` configuration file

## Installation

1. Save the `mcp_toggle.py` script to a convenient location:
```bash
# Create a directory for Claude management tools
mkdir -p ~/claude_manager
cd ~/claude_manager

# Save the script here as mcp_toggle.py
```

2. Create the presets file at `~/.mcp_presets.json`:
```bash
# Create an initial presets file
cat > ~/.mcp_presets.json << 'EOF'
{
  "presets": {},
  "defaults": {
    "minimal": ["context7", "browsermcp"],
    "webdev": ["context7", "browsermcp", "playwright"],
    "fullstack": ["context7", "browsermcp", "playwright", "supabase", "clerk", "railway"]
  }
}
EOF
```

3. Make the script executable (optional):
```bash
chmod +x mcp_toggle.py
```

## File Structure

The system uses two files:

1. **`~/.claude.json`** - Claude's main config (modified by the script)
2. **`~/.mcp_presets.json`** - Your project presets (easy to edit directly)

## Core Features

### 1. Quick Server Management
- **Disable ALL** (`n`) - Instant maximum context for Claude
- **Minimal mode** (`m`) - Only essential servers (context7 + browsermcp)
- **Web dev mode** (`w`) - Adds playwright for web development
- **Toggle individual servers** - Type server number to enable/disable

### 2. Add New MCP Servers (`+`)
Easily add any new MCP server by pasting its JSON configuration:

```
Action: +
```

Then paste the JSON from any MCP server's documentation:
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem"]
}
```

The script accepts multiple formats and will guide you through the process. Server is added and activated immediately!

### 3. Project Presets (`p`)
Save and load different configurations for different projects:
- Each project can have its own Supabase ID, Clerk API key, etc.
- Switch between clients instantly
- Edit presets directly in `~/.mcp_presets.json`

## Usage

### Basic Launch

```bash
python3 mcp_toggle.py
```

### Understanding the Interface

When you launch the script, you'll see:

```
📊 Current Status:
------------------------------

✅ ACTIVE servers:
  [1] supabase
  [2] context7
  [3] browsermcp
  [4] playwright

❌ INACTIVE servers:
  [i1] sentry
  [i2] clerk

📋 Actions:
  [1-N]  Deactivate active server
  [i1-N] Reactivate inactive server
  [a]    Activate ALL
  [n]    Deactivate ALL
  [m]    Minimal (context7 + browsermcp)
  [w]    Web dev (+ playwright)
  [p]    📁 Project presets →
  [s]    Save and exit
  [q]    Quit without saving
```

### Key Actions

#### Quick Context Reduction
- Type `n` → Disables ALL servers (maximum context for Claude)
- Type `m` → Minimal mode (only context7 + browsermcp)
- Type `w` → Web dev mode (adds playwright)

#### Toggle Individual Servers
- Type `1` → Deactivates server #1 
- Type `i1` → Reactivates inactive server #1

#### Project Presets (Type `p`)
Opens the preset manager where you can:
- View all saved presets with descriptions
- Load a preset by typing its number
- Save current configuration as a new preset
- Edit the presets file directly
- Reload after external edits

## Project Presets

### Understanding Presets

Presets save your project-specific server configurations in `~/.mcp_presets.json`. This file is human-readable and easy to edit directly.

### Editing Presets Directly

Open `~/.mcp_presets.json` in any text editor:

```json
{
  "presets": {
    "acme-corp": {
      "description": "Acme Corporation main project",
      "servers": {
        "supabase": {
          "project_ref": "ubodishzdgjbyqabrsgn",
          "url": "https://ubodishzdgjbyqabrsgn.supabase.co"
        },
        "clerk": {
          "api_key": "clerk_test_abc123xyz"
        },
        "sentry": {
          "auth_token": "sntryu_6db85c8c...",
          "org": "acme-corp"
        }
      }
    },
    "personal-blog": {
      "description": "My personal website",
      "servers": {
        "supabase": {
          "project_ref": "personalxyz123"
        }
      }
    }
  },
  "defaults": {
    "minimal": ["context7", "browsermcp"],
    "webdev": ["context7", "browsermcp", "playwright"]
  }
}
```

### Using Presets in the Script

1. **View presets**: Type `p` to enter preset manager
2. **Load a preset**: Type the preset number (1, 2, etc.)
3. **Edit presets file**: Type `e` to open in your system editor
4. **Reload changes**: Type `r` after editing externally

### Common Workflows

#### Starting a Minimal Session
```
1. Launch: python3 mcp_toggle.py
2. Type: m (for minimal mode)
3. Type: s (save and exit)
4. Restart Claude Code CLI
```

#### Switching Between Projects
```
1. Launch: python3 mcp_toggle.py
2. Type: p (opens preset manager)
3. Type: 1 (loads preset #1)
4. Type: s (save and exit)
5. Restart Claude Code CLI
```

#### Adding a New Project Preset
Option 1 - Edit the file directly:
```bash
# Open in your favorite editor
code ~/.mcp_presets.json
# or
nano ~/.mcp_presets.json
```

Option 2 - Through the script:
```
1. Configure your servers as needed
2. Type: p (preset manager)
3. Type: s (save current as preset)
4. Enter name and description
```

#### Quick Project Switch Example
```
Monday (Client A): python3 mcp_toggle.py → p → 1 → s → restart
Tuesday (Client B): python3 mcp_toggle.py → p → 2 → s → restart
Wednesday (Client A): python3 mcp_toggle.py → p → 1 → s → restart
```

## Adding New MCP Servers

### Through the Script (Easiest)

1. Run `python3 mcp_toggle.py`
2. Type `+` to add a new server
3. Paste your JSON configuration
4. Press Enter twice
5. The server is added and activated

### JSON Formats Supported

The script accepts various JSON formats:

#### Format 1: Complete with name
```json
"filesystem": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem"]
}
```

#### Format 2: Just the configuration (script will ask for name)
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem"]
}
```

#### Format 3: Multiple servers at once
```json
{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem"]
  },
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"]
  }
}
```

### Real Examples

#### Adding Filesystem MCP Server
1. Type `+`
2. Paste:
```json
"filesystem": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/yourusername/projects"]
}
```
3. Press Enter twice
4. Done! Server is added and active

#### Adding GitHub MCP Server
1. Type `+` 
2. Paste:
```json
"github": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"
  }
}
```

#### Adding Python-based MCP Server
1. Type `+`
2. Paste:
```json
"weather": {
  "command": "uv",
  "args": ["tool", "run", "weather-server", "--api-key", "your_key"]
}
```

### Where to Find MCP Server Configurations

Most MCP servers provide their configuration in their README. Look for:
- NPM packages: Usually start with `@modelcontextprotocol/` or similar
- Installation instructions that mention Claude Desktop or MCP
- JSON configuration examples in the documentation

Common places to find MCP servers:
- [MCP Servers GitHub](https://github.com/modelcontextprotocol)
- NPM packages tagged with 'mcp'
- Community MCP server lists

## How It Works

The script manages two sections in `~/.claude.json`:
- **`mcpServers`** - Active servers that will run
- **`_inactiveMcpServers`** - Preserved but inactive (won't run)

When you "disable" a server, it moves to `_inactiveMcpServers`, preserving all configuration. This is necessary because Claude Code CLI ignores the `"enabled": false` field.

## Configurable Servers

These servers typically need project-specific parameters:

| Server | Parameter | Use Case |
|--------|-----------|----------|
| supabase | `project_ref` | Different Supabase projects |
| sentry | `auth_token` | Different Sentry organizations |
| clerk | `api_key` | Different Clerk applications |
| railway | `project_id` | Different Railway projects |

## Important Notes

1. **Always restart Claude Code CLI** after making changes for them to take effect

2. **Backups are automatic** - The script creates timestamped backups of `.claude.json` before any changes

3. **Presets file is separate** - You can edit `~/.mcp_presets.json` directly without running the script

4. **Version control friendly** - Add `.mcp_presets.json` to git to track your project configurations

## Troubleshooting

### Changes don't take effect
- Make sure you saved (type `s`, not `q`)
- Fully quit and restart Claude Code CLI
- Check if processes are still running: `ps aux | grep -i mcp`

### Server still shows as connected
```bash
# Kill all MCP processes
pkill -f mcp
pkill -f "npm exec"

# Then restart Claude Code CLI
```

### Can't find files
```bash
# Find the script
find ~ -name "mcp_toggle.py" 2>/dev/null

# Check if presets file exists
ls -la ~/.mcp_presets.json

# Create presets file if missing
echo '{"presets": {}, "defaults": {"minimal": ["context7", "browsermcp"]}}' > ~/.mcp_presets.json
```

### Want to reset everything
```bash
# Restore from backup
ls ~/.claude.json.backup.*  # List backups
cp ~/.claude.json.backup.YYYYMMDD_HHMMSS ~/.claude.json  # Restore one
```

## Tips

- **For maximum context**: Use `n` to disable all servers
- **For quick work**: Use `m` for minimal mode
- **For web development**: Use `w` for web dev mode
- **Edit presets directly**: It's just a JSON file - use your favorite editor
- **Share configurations**: Copy `.mcp_presets.json` between machines
- **Track changes**: Add `.mcp_presets.json` to version control

## File Locations

- **Main config**: `~/.claude.json`
- **Presets file**: `~/.mcp_presets.json`
- **Backups**: `~/.claude.json.backup.YYYYMMDD_HHMMSS`
- **Script**: `~/claude_manager/mcp_toggle.py` (or wherever you saved it)

## Example: Setting Up Multiple Client Projects

1. **Create your presets file** with all clients:
```json
{
  "presets": {
    "client-abc": {
      "description": "ABC Corp - Production",
      "servers": {
        "supabase": {"project_ref": "abc123prod"},
        "clerk": {"api_key": "clerk_prod_abc"}
      }
    },
    "client-xyz": {
      "description": "XYZ Industries - Development", 
      "servers": {
        "supabase": {"project_ref": "xyz789dev"},
        "sentry": {"auth_token": "sntryu_xyz..."}
      }
    }
  }
}
```

2. **Switch between clients instantly**:
   - Working on ABC: `python3 mcp_toggle.py` → `p` → `1` → `s`
   - Switch to XYZ: `python3 mcp_toggle.py` → `p` → `2` → `s`

The presets make it seamless to work across multiple projects with different configurations!