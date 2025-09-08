# Quickstart: MCP Config Manager GUI

**Time to First Success**: 5 minutes

## Prerequisites

- Python 3.11+ installed
- MCP Config Manager installed (`pip install mcp-config-manager`)
- At least one AI system (Claude or Gemini) configured

## Installation

### Option 1: With GUI Support (Recommended)
```bash
pip install mcp-config-manager[gui]
```

### Option 2: Lightweight (tkinter fallback)
```bash
pip install mcp-config-manager
# GUI will use tkinter if PyQt6 not available
```

## First Launch

1. **Start the GUI**
   ```bash
   mcp-config-manager gui
   ```
   Or from the command line:
   ```bash
   python -m mcp_config_manager.gui
   ```

2. **Initial Setup**
   - The GUI will detect your existing configurations
   - If no configs found, it offers to create defaults
   - Select your primary mode: Claude, Gemini, or Both

## Core Workflows

### 1. Toggle a Server (Most Common Task)
**Goal**: Enable/disable a server without losing configuration

1. Launch the GUI
2. Find the server in the list
3. Click the toggle switch
4. Click "Save" or press Ctrl+S (Cmd+S on Mac)

✅ **Success**: Server state changed, configuration preserved

### 2. Apply a Preset
**Goal**: Switch to a minimal configuration for better performance

1. Click "Presets" in the toolbar
2. Select "Minimal" from the list
3. Click "Apply"
4. Confirm the changes

✅ **Success**: Only essential servers remain enabled

### 3. Add a New Server
**Goal**: Add a new MCP server from JSON

1. Click "Add Server" button (+ icon)
2. Paste your server JSON:
   ```json
   {
     "name": "my-server",
     "command": "node",
     "args": ["server.js"],
     "env": {"API_KEY": "..."}
   }
   ```
3. Click "Validate" then "Add"

✅ **Success**: New server appears in the list

### 4. Save a Project Preset
**Goal**: Save current configuration for a specific project

1. Configure servers for your project
2. Click "Presets" → "Save Current"
3. Name it (e.g., "ClientA Project")
4. Add description (optional)
5. Click "Save"

✅ **Success**: Preset saved and available for quick switching

### 5. Restore from Backup
**Goal**: Recover from a configuration error

1. Click "Tools" → "Backup & Restore"
2. Select a backup from the list
3. Click "Preview" to see contents
4. Click "Restore"

✅ **Success**: Previous configuration restored

## Keyboard Shortcuts

| Action | Windows/Linux | macOS |
|--------|--------------|-------|
| Save | Ctrl+S | Cmd+S |
| Quit | Ctrl+Q | Cmd+Q |
| Toggle Selected | Space | Space |
| Select All | Ctrl+A | Cmd+A |
| Search | Ctrl+F | Cmd+F |
| Presets | Ctrl+P | Cmd+P |
| Add Server | Ctrl+N | Cmd+N |
| Settings | Ctrl+, | Cmd+, |

## Visual Indicators

- 🟢 **Green Toggle**: Server enabled
- 🔴 **Red Toggle**: Server disabled
- 🟡 **Yellow Dot**: Unsaved changes
- 🔵 **Blue Highlight**: Currently selected
- ⚠️ **Warning Icon**: Configuration issue

## Mode Indicator

The top toolbar shows your current mode:
- **Claude Only**: Changes affect only Claude
- **Gemini Only**: Changes affect only Gemini
- **Both (Synced)**: Changes sync between both

To change modes: Click the mode button or press Ctrl+M (Cmd+M)

## Quick Tips

1. **Batch Operations**: Select multiple servers with Ctrl+Click, then toggle all at once
2. **Quick Filter**: Start typing to filter the server list instantly
3. **Drag to Reorder**: Drag servers to reorder them (PyQt6 only)
4. **Right-Click Menu**: Right-click servers for quick actions
5. **Auto-Save**: Enable in Settings for automatic saving

## Validation Test

Run this quick test to verify everything works:

1. **Toggle Test**:
   - Toggle any server off
   - Toggle it back on
   - Verify configuration preserved

2. **Preset Test**:
   - Apply "Minimal" preset
   - Count enabled servers (should be 2)
   - Restore previous state

3. **Add Server Test**:
   - Add this test server:
   ```json
   {
     "name": "test-server",
     "command": "echo",
     "args": ["test"]
   }
   ```
   - Verify it appears in list
   - Remove it

## Troubleshooting

### GUI Won't Start
```bash
# Check installation
python -c "import PyQt6; print('PyQt6 OK')"

# Fall back to tkinter
mcp-config-manager gui --framework=tkinter
```

### Configuration Not Loading
```bash
# Validate configuration
mcp-config-manager validate ~/.claude.json

# Check permissions
ls -la ~/.claude.json ~/.gemini/settings.json
```

### Changes Not Saving
- Check file permissions
- Verify disk space
- Look for error messages in status bar
- Try "Save As" to alternate location

## Performance Check

The GUI should be responsive with:
- ✅ <100ms response to clicks
- ✅ <1s to load 100+ servers
- ✅ <2s to apply presets
- ✅ Smooth scrolling with 200+ servers

## Next Steps

1. **Customize Settings**: Tools → Settings
2. **Create Project Presets**: Build preset library
3. **Set Up Shortcuts**: Customize keyboard shortcuts
4. **Explore Themes**: Try dark/light themes

## Getting Help

- **In-App Help**: Press F1 or Help menu
- **Status Bar**: Hover for tooltips
- **Documentation**: [Full docs link]
- **Report Issues**: Help → Report Issue

## Success Criteria

You've successfully set up the GUI when you can:
- ✅ See all your MCP servers listed
- ✅ Toggle servers on/off
- ✅ Save changes successfully
- ✅ Apply a preset
- ✅ Add a new server

**Congratulations!** You're now managing MCP configurations visually. 🎉