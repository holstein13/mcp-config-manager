"""Tkinter dialog adapters for consistent interface."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class TkinterDialogAdapter:
    """Base adapter for tkinter dialogs."""
    
    @staticmethod
    def show_info(title: str, message: str, parent=None):
        """Show information dialog."""
        messagebox.showinfo(title, message, parent=parent)
    
    @staticmethod
    def show_warning(title: str, message: str, parent=None):
        """Show warning dialog."""
        messagebox.showwarning(title, message, parent=parent)
    
    @staticmethod
    def show_error(title: str, message: str, parent=None):
        """Show error dialog."""
        messagebox.showerror(title, message, parent=parent)
    
    @staticmethod
    def ask_yes_no(title: str, message: str, parent=None) -> bool:
        """Show yes/no dialog."""
        return messagebox.askyesno(title, message, parent=parent)
    
    @staticmethod
    def ask_yes_no_cancel(title: str, message: str, parent=None) -> Optional[bool]:
        """Show yes/no/cancel dialog."""
        result = messagebox.askyesnocancel(title, message, parent=parent)
        return result  # Returns True, False, or None
    
    @staticmethod
    def ask_string(title: str, prompt: str, initial: str = "", parent=None) -> Optional[str]:
        """Show string input dialog."""
        return simpledialog.askstring(title, prompt, initialvalue=initial, parent=parent)
    
    @staticmethod
    def ask_integer(title: str, prompt: str, initial: int = 0, parent=None) -> Optional[int]:
        """Show integer input dialog."""
        return simpledialog.askinteger(title, prompt, initialvalue=initial, parent=parent)
    
    @staticmethod
    def open_file(title: str = "Open File", filetypes=None, parent=None) -> Optional[str]:
        """Show file open dialog."""
        if filetypes is None:
            filetypes = [("All files", "*.*")]
        return filedialog.askopenfilename(title=title, filetypes=filetypes, parent=parent)
    
    @staticmethod
    def save_file(title: str = "Save File", filetypes=None, default_ext="", parent=None) -> Optional[str]:
        """Show file save dialog."""
        if filetypes is None:
            filetypes = [("All files", "*.*")]
        return filedialog.asksaveasfilename(
            title=title,
            filetypes=filetypes,
            defaultextension=default_ext,
            parent=parent
        )
    
    @staticmethod
    def select_directory(title: str = "Select Directory", parent=None) -> Optional[str]:
        """Show directory selection dialog."""
        return filedialog.askdirectory(title=title, parent=parent)


class AddServerDialogTk(tk.Toplevel):
    """Tkinter implementation of Add Server dialog."""
    
    def __init__(self, parent=None, server_controller=None):
        """Initialize the dialog.
        
        Args:
            parent: Parent window
            server_controller: ServerController instance
        """
        super().__init__(parent)
        self.title("Add Server")
        self.server_controller = server_controller
        self.result = None
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        
        # Center on parent
        if parent:
            self.geometry(f"+{parent.winfo_x() + 50}+{parent.winfo_y() + 50}")
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main frame
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        ttk.Label(
            main_frame,
            text="Paste server configuration JSON:"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # JSON input area
        self.json_text = tk.Text(main_frame, height=15, width=60)
        self.json_text.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.json_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.json_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.json_text.yview)
        
        # Example placeholder
        example = '''{
  "server-name": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-name"],
    "env": {
      "API_KEY": "your-key-here"
    }
  }
}'''
        self.json_text.insert("1.0", example)
        self.json_text.tag_add("sel", "1.0", "end")
        
        # Error label
        self.error_label = ttk.Label(main_frame, text="", foreground="red")
        self.error_label.pack(pady=(10, 0))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        
        ttk.Button(button_frame, text="Add", command=self._on_add).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.LEFT, padx=5)
    
    def _on_add(self):
        """Handle add button click."""
        json_str = self.json_text.get("1.0", "end-1c")
        
        try:
            server_config = json.loads(json_str)
            
            if self.server_controller:
                result = self.server_controller.add_server(server_config)
                if result['success']:
                    self.result = server_config
                    self.destroy()
                else:
                    self.error_label.config(text=result.get('error', 'Failed to add server'))
            else:
                self.result = server_config
                self.destroy()
                
        except json.JSONDecodeError as e:
            self.error_label.config(text=f"Invalid JSON: {str(e)}")
        except Exception as e:
            self.error_label.config(text=str(e))
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.destroy()


class PresetManagerDialogTk(tk.Toplevel):
    """Tkinter implementation of Preset Manager dialog."""
    
    def __init__(self, parent=None, preset_controller=None):
        """Initialize the dialog.
        
        Args:
            parent: Parent window
            preset_controller: PresetController instance
        """
        super().__init__(parent)
        self.title("Preset Manager")
        self.preset_controller = preset_controller
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        self._load_presets()
        
        # Set size and center
        self.geometry("600x400")
        if parent:
            self.geometry(f"+{parent.winfo_x() + 50}+{parent.winfo_y() + 50}")
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main frame
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - preset list
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(left_frame, text="Presets:").pack(anchor=tk.W)
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.preset_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.preset_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.preset_listbox.yview)
        
        self.preset_listbox.bind('<<ListboxSelect>>', self._on_preset_selected)
        
        # Right side - buttons and details
        right_frame = ttk.Frame(main_frame, width=200)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # Buttons
        ttk.Button(right_frame, text="Apply", command=self._on_apply).pack(fill=tk.X, pady=2)
        ttk.Button(right_frame, text="Save Current", command=self._on_save).pack(fill=tk.X, pady=2)
        ttk.Button(right_frame, text="Delete", command=self._on_delete).pack(fill=tk.X, pady=2)
        ttk.Button(right_frame, text="Export", command=self._on_export).pack(fill=tk.X, pady=2)
        ttk.Button(right_frame, text="Import", command=self._on_import).pack(fill=tk.X, pady=2)
        
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Details
        ttk.Label(right_frame, text="Details:").pack(anchor=tk.W)
        
        self.details_text = tk.Text(right_frame, height=10, width=25, wrap=tk.WORD)
        self.details_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Close button
        ttk.Button(right_frame, text="Close", command=self.destroy).pack(pady=(10, 0))
    
    def _load_presets(self):
        """Load presets from controller."""
        if not self.preset_controller:
            return
        
        result = self.preset_controller.get_preset_list()
        if result['success']:
            self.preset_listbox.delete(0, tk.END)
            for preset in result['presets']:
                name = preset['name']
                if preset.get('is_builtin'):
                    name += " (built-in)"
                if preset.get('is_favorite'):
                    name = "★ " + name
                self.preset_listbox.insert(tk.END, name)
    
    def _on_preset_selected(self, event):
        """Handle preset selection."""
        selection = self.preset_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        preset_name = self.preset_listbox.get(index)
        
        # Clean up the name
        preset_name = preset_name.replace(" (built-in)", "").replace("★ ", "")
        
        if self.preset_controller:
            result = self.preset_controller.get_preset_details(preset_name)
            if result['success']:
                preset = result['preset']
                details = f"Name: {preset['name']}\n"
                details += f"Description: {preset.get('description', 'N/A')}\n"
                details += f"Servers: {len(preset.get('enabled_servers', {})) + len(preset.get('disabled_servers', {}))}\n"
                details += f"Mode: {preset.get('mode', 'both')}\n"
                
                self.details_text.delete("1.0", tk.END)
                self.details_text.insert("1.0", details)
    
    def _on_apply(self):
        """Apply selected preset."""
        selection = self.preset_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a preset to apply")
            return
        
        preset_name = self.preset_listbox.get(selection[0])
        preset_name = preset_name.replace(" (built-in)", "").replace("★ ", "")
        
        if self.preset_controller:
            result = self.preset_controller.load_preset(preset_name)
            if result['success']:
                messagebox.showinfo("Success", f"Applied preset: {preset_name}")
                self.destroy()
            else:
                messagebox.showerror("Error", f"Failed to apply preset: {result.get('error')}")
    
    def _on_save(self):
        """Save current configuration as preset."""
        name = simpledialog.askstring("Save Preset", "Enter preset name:")
        if not name:
            return
        
        description = simpledialog.askstring("Save Preset", "Enter description (optional):") or ""
        
        if self.preset_controller:
            result = self.preset_controller.save_preset(name, description)
            if result['success']:
                messagebox.showinfo("Success", f"Saved preset: {name}")
                self._load_presets()
            else:
                messagebox.showerror("Error", f"Failed to save preset: {result.get('error')}")
    
    def _on_delete(self):
        """Delete selected preset."""
        selection = self.preset_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a preset to delete")
            return
        
        preset_name = self.preset_listbox.get(selection[0])
        
        if "(built-in)" in preset_name:
            messagebox.showerror("Error", "Cannot delete built-in presets")
            return
        
        preset_name = preset_name.replace("★ ", "")
        
        if messagebox.askyesno("Confirm Delete", f"Delete preset '{preset_name}'?"):
            if self.preset_controller:
                result = self.preset_controller.delete_preset(preset_name)
                if result['success']:
                    messagebox.showinfo("Success", f"Deleted preset: {preset_name}")
                    self._load_presets()
                else:
                    messagebox.showerror("Error", f"Failed to delete preset: {result.get('error')}")
    
    def _on_export(self):
        """Export presets to file."""
        filename = filedialog.asksaveasfilename(
            title="Export Presets",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            # Export logic would go here
            messagebox.showinfo("Export", f"Presets would be exported to {filename}")
    
    def _on_import(self):
        """Import presets from file."""
        filename = filedialog.askopenfilename(
            title="Import Presets",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            # Import logic would go here
            messagebox.showinfo("Import", f"Presets would be imported from {filename}")