#!/usr/bin/env python3
import sys
import os

# Add the app's Python path
app_path = "py2app_dist/MCP Config Manager.app/Contents/Resources"
sys.path.insert(0, os.path.join(app_path, "lib", "python39.zip"))
sys.path.insert(0, os.path.join(app_path, "lib", "python3.9"))

try:
    from mcp_config_manager.utils.file_utils import get_project_backups_dir
    backup_dir = get_project_backups_dir()
    print(f"✅ Backup directory: {backup_dir}")
    
    # Check if it's the correct path
    expected = os.path.expanduser("~/Documents/MCP Config Manager/backups")
    if str(backup_dir) == expected:
        print("✅ CORRECT: Backups will be saved to user's Documents folder")
    else:
        print(f"❌ INCORRECT: Expected {expected}, got {backup_dir}")
except Exception as e:
    print(f"❌ Error: {e}")
