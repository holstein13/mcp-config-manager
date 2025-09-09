"""Tkinter-specific server list implementation."""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Callable

from ..widgets.server_list import ServerListWidget
from ..models.server_list_item import ServerListItem, ServerStatus


class TkinterServerList:
    """Tkinter-specific wrapper for the server list widget."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize the tkinter server list.
        
        Args:
            parent: Parent tkinter widget
        """
        self.parent = parent
        self.frame = ttk.Frame(parent)
        
        # Use the existing ServerListWidget
        self.server_list = ServerListWidget(self.frame)
        
        # Additional tkinter-specific features
        self._setup_search_bar()
        self._setup_filter_controls()
        
    def _setup_search_bar(self):
        """Set up the search bar."""
        search_frame = ttk.Frame(self.frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_changed)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(search_frame, text="Clear", command=self._clear_search).pack(side=tk.LEFT, padx=(5, 0))
    
    def _setup_filter_controls(self):
        """Set up filter controls."""
        filter_frame = ttk.Frame(self.frame)
        filter_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_var,
            values=["All", "Enabled", "Disabled", "Error"],
            state="readonly",
            width=15
        )
        filter_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        filter_combo.pack(side=tk.LEFT)
        
        # Server count label
        self.count_label = ttk.Label(filter_frame, text="0 servers")
        self.count_label.pack(side=tk.RIGHT, padx=(10, 0))
    
    def _on_search_changed(self, *args):
        """Handle search text change."""
        search_text = self.search_var.get()
        self.server_list.set_filter(search_text)
    
    def _on_filter_changed(self, event=None):
        """Handle filter change."""
        filter_type = self.filter_var.get()
        # Apply filter logic here
        self._apply_filter(filter_type)
    
    def _clear_search(self):
        """Clear the search field."""
        self.search_var.set("")
    
    def _apply_filter(self, filter_type: str):
        """Apply a filter to the server list.
        
        Args:
            filter_type: Type of filter to apply
        """
        # This would filter the displayed servers
        # For now, just use the existing filter method
        if filter_type != "All":
            # Filter implementation would go here
            pass
    
    def add_server(self, server: ServerListItem):
        """Add a server to the list.
        
        Args:
            server: Server to add
        """
        self.server_list.add_server(server)
        self._update_count()
    
    def remove_server(self, server_name: str):
        """Remove a server from the list.
        
        Args:
            server_name: Name of server to remove
        """
        self.server_list.remove_server(server_name)
        self._update_count()
    
    def clear(self):
        """Clear all servers."""
        self.server_list.clear()
        self._update_count()
    
    def get_selected_servers(self) -> List[str]:
        """Get currently selected servers.
        
        Returns:
            List of selected server names
        """
        return self.server_list.get_selected_servers()
    
    def _update_count(self):
        """Update the server count label."""
        total = len(self.server_list.servers)
        enabled = len(self.server_list.get_enabled_servers())
        self.count_label.config(text=f"{enabled}/{total} servers enabled")
    
    def get_widget(self) -> tk.Widget:
        """Get the main widget.
        
        Returns:
            The main frame widget
        """
        return self.frame
    
    def pack(self, **kwargs):
        """Pack the widget."""
        self.frame.pack(**kwargs)
        self.server_list.get_widget().pack(fill=tk.BOTH, expand=True)


class TkinterServerListAdvanced(TkinterServerList):
    """Advanced tkinter server list with additional features."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize the advanced server list.
        
        Args:
            parent: Parent tkinter widget
        """
        super().__init__(parent)
        self._setup_advanced_features()
    
    def _setup_advanced_features(self):
        """Set up advanced features."""
        # Add toolbar
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=tk.X, pady=(5, 0))
        
        # Bulk operation buttons
        ttk.Button(toolbar, text="Select All", command=self._select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Select None", command=self._select_none).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Invert Selection", command=self._invert_selection).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Import/Export buttons
        ttk.Button(toolbar, text="Import", command=self._import_servers).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Export", command=self._export_servers).pack(side=tk.LEFT, padx=2)
    
    def _select_all(self):
        """Select all servers."""
        all_servers = list(self.server_list.servers.keys())
        self.server_list.select_servers(all_servers)
    
    def _select_none(self):
        """Deselect all servers."""
        self.server_list.select_servers([])
    
    def _invert_selection(self):
        """Invert the current selection."""
        current = set(self.server_list.get_selected_servers())
        all_servers = set(self.server_list.servers.keys())
        inverted = list(all_servers - current)
        self.server_list.select_servers(inverted)
    
    def _import_servers(self):
        """Import servers from a file."""
        from tkinter import filedialog
        import json
        
        filename = filedialog.askopenfilename(
            title="Import Servers",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    servers = json.load(f)
                    # Process imported servers
                    for name, config in servers.items():
                        server = ServerListItem(
                            name=name,
                            command=config.get('command', ''),
                            args=config.get('args', []),
                            env=config.get('env', {}),
                            status=ServerStatus.DISABLED
                        )
                        self.add_server(server)
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Import Error", f"Failed to import servers: {str(e)}")
    
    def _export_servers(self):
        """Export servers to a file."""
        from tkinter import filedialog
        import json
        
        filename = filedialog.asksaveasfilename(
            title="Export Servers",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                servers = {}
                for name, server in self.server_list.servers.items():
                    servers[name] = {
                        'command': server.command,
                        'args': server.args,
                        'env': server.env
                    }
                
                with open(filename, 'w') as f:
                    json.dump(servers, f, indent=2)
                
                from tkinter import messagebox
                messagebox.showinfo("Export Complete", f"Servers exported to {filename}")
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Export Error", f"Failed to export servers: {str(e)}")