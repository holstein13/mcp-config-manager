"""Tkinter implementation of the main window."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional, Dict, Any

from ..controllers.config_controller import ConfigController
from ..controllers.server_controller import ServerController
from ..controllers.preset_controller import PresetController
from ..controllers.backup_controller import BackupController
from ..widgets.server_list import ServerListWidget
from ..models.app_state import ApplicationState

logger = logging.getLogger(__name__)


class TkinterMainWindow:
    """Tkinter implementation of the main application window."""
    
    def __init__(self, root: Optional[tk.Tk] = None):
        """Initialize the tkinter main window.
        
        Args:
            root: Optional root window, creates new if not provided
        """
        self.root = root or tk.Tk()
        self.root.title("MCP Config Manager")
        self.root.geometry("900x600")
        
        # Controllers
        self.config_controller = ConfigController()
        self.server_controller = ServerController(self.config_controller.config_manager)
        self.preset_controller = PresetController(self.config_controller.config_manager)
        self.backup_controller = BackupController(self.config_controller.config_manager)
        
        # State
        self.app_state = ApplicationState()
        self.unsaved_changes = False
        
        # Setup UI
        self._setup_menu()
        self._setup_toolbar()
        self._setup_main_content()
        self._setup_status_bar()
        
        # Bind events
        self._bind_events()
        
        # Load initial configuration
        self._load_config()
    
    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Configuration", command=self._on_load_config, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Configuration", command=self._on_save_config, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Create Backup", command=self._on_create_backup)
        file_menu.add_command(label="Restore Backup", command=self._on_restore_backup)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_exit, accelerator="Ctrl+Q")
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Add Server", command=self._on_add_server, accelerator="Ctrl+N")
        edit_menu.add_command(label="Enable All", command=self._on_enable_all)
        edit_menu.add_command(label="Disable All", command=self._on_disable_all)
        edit_menu.add_separator()
        edit_menu.add_command(label="Settings", command=self._on_settings)
        
        # Presets menu
        presets_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Presets", menu=presets_menu)
        presets_menu.add_command(label="Manage Presets", command=self._on_manage_presets, accelerator="Ctrl+P")
        presets_menu.add_separator()
        presets_menu.add_command(label="Apply Minimal", command=lambda: self._apply_preset("minimal"))
        presets_menu.add_command(label="Apply Web Dev", command=lambda: self._apply_preset("web_dev"))
        presets_menu.add_command(label="Apply Data Science", command=lambda: self._apply_preset("data_science"))
        presets_menu.add_command(label="Apply Full", command=lambda: self._apply_preset("full"))
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Validate Configuration", command=self._on_validate_config)
        tools_menu.add_command(label="Watch Config Files", command=self._on_toggle_file_watch)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._on_about)
        help_menu.add_command(label="Documentation", command=self._on_documentation)
    
    def _setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        
        # Toolbar buttons
        ttk.Button(toolbar, text="Save", command=self._on_save_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Add Server", command=self._on_add_server).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="Enable All", command=self._on_enable_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Disable All", command=self._on_disable_all).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="Presets", command=self._on_manage_presets).pack(side=tk.LEFT, padx=2)
    
    def _setup_main_content(self):
        """Set up the main content area."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Mode selector removed - using per-client checkboxes instead
        
        # Server list
        list_frame = ttk.LabelFrame(main_frame, text="Servers", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.server_list = ServerListWidget(list_frame)
        self.server_list.get_widget().pack(fill=tk.BOTH, expand=True)
    
    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = ttk.Label(
            self.root,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _bind_events(self):
        """Bind keyboard shortcuts and other events."""
        # Keyboard shortcuts
        self.root.bind("<Control-o>", lambda e: self._on_load_config())
        self.root.bind("<Control-s>", lambda e: self._on_save_config())
        self.root.bind("<Control-n>", lambda e: self._on_add_server())
        self.root.bind("<Control-p>", lambda e: self._on_manage_presets())
        self.root.bind("<Control-q>", lambda e: self._on_exit())
        
        # Window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_exit)
        
        # Server list callbacks
        self.server_list.add_toggle_callback(self._on_server_toggled)
        self.server_list.add_selection_callback(self._on_server_selected)
        
        # Mode selector callback removed - using per-client operations instead
    
    def _load_config(self):
        """Load the initial configuration."""
        try:
            result = self.config_controller.load_config()
            if result['success']:
                self._update_server_list()
                self._set_status("Configuration loaded")
            else:
                messagebox.showerror("Error", f"Failed to load configuration: {result.get('error')}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def _update_server_list(self):
        """Update the server list from the current configuration."""
        try:
            result = self.server_controller.get_server_list()
            if result['success']:
                self.server_list.clear()
                for server_data in result['servers']:
                    from ..models.server_list_item import ServerListItem, ServerStatus
                    server = ServerListItem(
                        name=server_data['name'],
                        command=server_data.get('command', ''),
                        args=server_data.get('args', []),
                        env=server_data.get('env', {}),
                        status=ServerStatus.ENABLED if server_data.get('enabled') else ServerStatus.DISABLED
                    )
                    self.server_list.add_server(server)
                
                self.server_list.update_status_count()
        except Exception as e:
            logger.error(f"Failed to update server list: {e}")
    
    def _on_load_config(self):
        """Handle load configuration action."""
        self._load_config()
    
    def _on_save_config(self):
        """Handle save configuration action."""
        try:
            result = self.config_controller.save_config()
            if result['success']:
                self.unsaved_changes = False
                self._update_title()
                self._set_status("Configuration saved")
                if result.get('backup_file'):
                    self._set_status(f"Configuration saved (backup: {result['backup_file']})")
            else:
                messagebox.showerror("Error", f"Failed to save configuration: {result.get('error')}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def _on_add_server(self):
        """Handle add server action."""
        from ..dialogs.add_server_dialog import AddServerDialog
        dialog = AddServerDialog(self.root)
        # The dialog would handle adding the server
    
    def _on_enable_all(self):
        """Handle enable all servers action."""
        result = self.server_controller.bulk_operation('enable_all')
        if result['success']:
            self._update_server_list()
            self._mark_unsaved()
    
    def _on_disable_all(self):
        """Handle disable all servers action."""
        result = self.server_controller.bulk_operation('disable_all')
        if result['success']:
            self._update_server_list()
            self._mark_unsaved()
    
    def _on_manage_presets(self):
        """Handle manage presets action."""
        from ..dialogs.preset_manager_dialog import PresetManagerDialog
        dialog = PresetManagerDialog(self.root)
        # The dialog would handle preset management
    
    def _apply_preset(self, preset_name: str):
        """Apply a preset configuration."""
        result = self.preset_controller.load_preset(preset_name)
        if result['success']:
            self._update_server_list()
            self._mark_unsaved()
            self._set_status(f"Applied preset: {preset_name}")
        else:
            messagebox.showerror("Error", f"Failed to apply preset: {result.get('error')}")
    
    def _on_create_backup(self):
        """Handle create backup action."""
        result = self.backup_controller.create_backup()
        if result['success']:
            self._set_status(f"Backup created: {result.get('backup_file')}")
        else:
            messagebox.showerror("Error", f"Failed to create backup: {result.get('error')}")
    
    def _on_restore_backup(self):
        """Handle restore backup action."""
        from ..dialogs.backup_restore_dialog import BackupRestoreDialog
        dialog = BackupRestoreDialog(self.root)
        # The dialog would handle backup restoration
    
    def _on_validate_config(self):
        """Handle validate configuration action."""
        result = self.config_controller.validate_config()
        if result['success']:
            if result['valid']:
                messagebox.showinfo("Validation", "Configuration is valid")
            else:
                errors = "\n".join(result.get('errors', []))
                warnings = "\n".join(result.get('warnings', []))
                msg = f"Validation errors:\n{errors}\n\nWarnings:\n{warnings}"
                messagebox.showwarning("Validation Failed", msg)
    
    def _on_toggle_file_watch(self):
        """Handle toggle file watch action."""
        # This would toggle file watching
        pass
    
    def _on_settings(self):
        """Handle settings action."""
        from ..dialogs.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.root)
        # The dialog would handle settings
    
    def _on_about(self):
        """Handle about action."""
        messagebox.showinfo(
            "About MCP Config Manager",
            "MCP Config Manager v1.0.0\n\n"
            "A cross-platform utility for managing Model Context Protocol server configurations."
        )
    
    def _on_documentation(self):
        """Handle documentation action."""
        import webbrowser
        webbrowser.open("https://github.com/holstein13/mcp-config-manager")
    
    def _on_server_toggled(self, server_name: str, enabled: bool):
        """Handle server toggle event."""
        result = self.server_controller.toggle_server(server_name)
        if result['success']:
            self._mark_unsaved()
    
    def _on_server_selected(self, server_name: str):
        """Handle server selection event."""
        self.app_state.selected_server = server_name
    
    def _on_mode_changed(self, mode: str):
        """Handle mode change event."""
        result = self.config_controller.change_mode(mode)
        if result['success']:
            self._update_server_list()
            self._set_status(f"Switched to {mode} mode")
    
    def _on_exit(self):
        """Handle application exit."""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before exiting?"
            )
            if result is True:  # Yes - save and exit
                self._on_save_config()
                self.root.quit()
            elif result is False:  # No - exit without saving
                self.root.quit()
            # Cancel - do nothing
        else:
            self.root.quit()
    
    def _mark_unsaved(self):
        """Mark that there are unsaved changes."""
        self.unsaved_changes = True
        self._update_title()
    
    def _update_title(self):
        """Update the window title."""
        title = "MCP Config Manager"
        if self.unsaved_changes:
            title += " *"
        self.root.title(title)
    
    def _set_status(self, message: str):
        """Set the status bar message."""
        self.status_bar.config(text=message)
    
    def run(self):
        """Run the application."""
        self.root.mainloop()