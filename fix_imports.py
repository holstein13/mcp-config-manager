#!/usr/bin/env python3
"""Fix tkinter import issues in GUI files."""

import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Fix imports in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if this file has the problematic pattern
    if 'except ImportError:' not in content:
        return False
    
    # Check if it imports tkinter in except block
    if 'import tkinter as tk' not in content:
        return False
    
    # Check if already fixed
    if 'tk = None' in content and 'USING_QT = True' in content:
        return False
    
    # Pattern to match the try-except import block
    pattern = r'(try:\s+from PyQt6[^}]+USING_QT = True)\s*(except ImportError:\s+import tkinter[^}]+USING_QT = False)'
    
    # Replacement that handles missing tkinter properly
    def replacement(match):
        try_block = match.group(1)
        
        # Add tk = None after USING_QT = True
        try_block_fixed = try_block + '\n    tk = None\n    ttk = None\n    messagebox = None'
        
        # Build proper except block
        except_block = """except ImportError:
    USING_QT = False
    # Set Qt classes to object for fallback
    QDialog = object
    QWidget = object
    QMainWindow = object
    QVBoxLayout = object
    QHBoxLayout = object
    QLabel = object
    QPushButton = object
    QComboBox = object
    QCheckBox = object
    QSpinBox = object
    QGroupBox = object
    QFormLayout = object
    QTabWidget = object
    QDialogButtonBox = object
    QToolBar = object
    QMenuBar = object
    QStatusBar = object
    QAction = object
    QMessageBox = object
    QApplication = object
    QSplitter = object
    QListWidget = object
    QTreeWidget = object
    QTreeWidgetItem = object
    Qt = None
    QTimer = None
    pyqtSignal = None
    QIcon = None
    QKeySequence = None
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except ImportError:
        tk = None
        ttk = None
        messagebox = None"""
        
        return try_block_fixed + '\n' + except_block
    
    # Apply the fix
    fixed_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if fixed_content != content:
        with open(filepath, 'w') as f:
            f.write(fixed_content)
        print(f"Fixed: {filepath}")
        return True
    
    return False

def main():
    """Fix all GUI files."""
    gui_dir = Path('src/gui')
    fixed_count = 0
    
    for py_file in gui_dir.rglob('*.py'):
        if fix_imports_in_file(py_file):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")

if __name__ == '__main__':
    main()