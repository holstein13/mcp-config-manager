"""Dialog for managing presets."""

from typing import List, Optional, Callable
from dataclasses import dataclass

try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
        QPushButton, QDialogButtonBox, QMessageBox, QGroupBox,
        QLabel, QInputDialog, QSplitter
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    USING_QT = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk, messagebox, simpledialog
    USING_QT = False


@dataclass
class PresetInfo:
    """Information about a preset."""
    name: str
    description: str
    server_count: int
    is_builtin: bool = False
    is_favorite: bool = False


class PresetManagerDialog:
    """Dialog for managing presets."""
    
    def __init__(self, parent=None):
        """Initialize the Preset Manager dialog.
        
        Args:
            parent: Parent widget/window
        """
        self.parent = parent
        self.presets: List[PresetInfo] = []
        self.selected_preset: Optional[str] = None
        self.on_preset_applied_callbacks = []
        self.on_preset_saved_callbacks = []
        self.on_preset_deleted_callbacks = []
        
        if USING_QT:
            self._init_qt()
        else:
            self._init_tk()
    
    def _init_qt(self):
        """Initialize Qt version of the dialog."""
        self.dialog = QDialog(self.parent)
        self.dialog.setWindowTitle("Preset Manager")
        self.dialog.setModal(True)
        self.dialog.resize(700, 500)
        
        # Main layout
        layout = QVBoxLayout(self.dialog)
        
        # Splitter for list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - preset list
        list_group = QGroupBox("Available Presets")
        list_layout = QVBoxLayout()
        
        self.preset_list = QListWidget()
        self.preset_list.itemSelectionChanged.connect(self._on_qt_selection_changed)
        self.preset_list.itemDoubleClicked.connect(self._on_qt_apply_preset)
        list_layout.addWidget(self.preset_list)
        
        # List buttons
        list_button_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._on_qt_apply_preset)
        self.apply_btn.setEnabled(False)
        list_button_layout.addWidget(self.apply_btn)
        
        self.save_btn = QPushButton("Save Current as...")
        self.save_btn.clicked.connect(self._on_qt_save_preset)
        list_button_layout.addWidget(self.save_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_qt_delete_preset)
        self.delete_btn.setEnabled(False)
        list_button_layout.addWidget(self.delete_btn)
        
        list_button_layout.addStretch()
        list_layout.addLayout(list_button_layout)
        
        list_group.setLayout(list_layout)
        splitter.addWidget(list_group)
        
        # Right side - preset details
        details_group = QGroupBox("Preset Details")
        details_layout = QVBoxLayout()
        
        self.details_label = QLabel("Select a preset to view details")
        self.details_label.setWordWrap(True)
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        details_layout.addWidget(self.details_label)
        
        details_group.setLayout(details_layout)
        splitter.addWidget(details_group)
        
        # Set splitter proportions
        splitter.setSizes([400, 300])
        layout.addWidget(splitter)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.dialog.reject)
        layout.addWidget(button_box)
    
    def _init_tk(self):
        """Initialize tkinter version of the dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Preset Manager")
        self.dialog.geometry("700x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create paned window for split view
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left side - preset list
        list_frame = ttk.LabelFrame(paned, text="Available Presets", padding="5")
        
        # Listbox with scrollbar
        list_scroll_frame = ttk.Frame(list_frame)
        list_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.preset_listbox = tk.Listbox(
            list_scroll_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE
        )
        self.preset_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.preset_listbox.yview)
        
        self.preset_listbox.bind("<<ListboxSelect>>", self._on_tk_selection_changed)
        self.preset_listbox.bind("<Double-Button-1>", lambda e: self._on_tk_apply_preset())
        
        # List buttons
        list_button_frame = ttk.Frame(list_frame)
        list_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.apply_btn = ttk.Button(
            list_button_frame,
            text="Apply",
            command=self._on_tk_apply_preset,
            state=tk.DISABLED
        )
        self.apply_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.save_btn = ttk.Button(
            list_button_frame,
            text="Save Current as...",
            command=self._on_tk_save_preset
        )
        self.save_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.delete_btn = ttk.Button(
            list_button_frame,
            text="Delete",
            command=self._on_tk_delete_preset,
            state=tk.DISABLED
        )
        self.delete_btn.pack(side=tk.LEFT)
        
        paned.add(list_frame, weight=2)
        
        # Right side - preset details
        details_frame = ttk.LabelFrame(paned, text="Preset Details", padding="10")
        
        self.details_text = tk.Text(
            details_frame,
            wrap=tk.WORD,
            width=30,
            height=20,
            state=tk.DISABLED
        )
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        paned.add(details_frame, weight=1)
        
        # Dialog buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        close_btn = ttk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy
        )
        close_btn.pack(side=tk.RIGHT)
    
    def set_presets(self, presets: List[PresetInfo]):
        """Set the list of available presets.
        
        Args:
            presets: List of preset information
        """
        self.presets = presets
        self._refresh_preset_list()
    
    def _refresh_preset_list(self):
        """Refresh the preset list display."""
        if USING_QT:
            self.preset_list.clear()
            for preset in self.presets:
                item = QListWidgetItem()
                # Format display text
                text = preset.name
                if preset.is_builtin:
                    text += " [Built-in]"
                if preset.is_favorite:
                    text = "★ " + text
                text += f" ({preset.server_count} servers)"
                
                item.setText(text)
                item.setData(Qt.ItemDataRole.UserRole, preset.name)
                
                # Disable deletion for built-in presets
                if preset.is_builtin:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                
                self.preset_list.addItem(item)
        else:
            self.preset_listbox.delete(0, tk.END)
            for preset in self.presets:
                # Format display text
                text = preset.name
                if preset.is_builtin:
                    text += " [Built-in]"
                if preset.is_favorite:
                    text = "★ " + text
                text += f" ({preset.server_count} servers)"
                
                self.preset_listbox.insert(tk.END, text)
    
    def _on_qt_selection_changed(self):
        """Handle selection change in Qt version."""
        current = self.preset_list.currentItem()
        if current:
            preset_name = current.data(Qt.ItemDataRole.UserRole)
            preset = next((p for p in self.presets if p.name == preset_name), None)
            
            if preset:
                self.selected_preset = preset_name
                self._update_details_qt(preset)
                
                # Enable/disable buttons
                self.apply_btn.setEnabled(True)
                self.delete_btn.setEnabled(not preset.is_builtin)
        else:
            self.selected_preset = None
            self.details_label.setText("Select a preset to view details")
            self.apply_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
    
    def _on_tk_selection_changed(self, event):
        """Handle selection change in tkinter version."""
        selection = self.preset_listbox.curselection()
        if selection:
            index = selection[0]
            preset = self.presets[index]
            self.selected_preset = preset.name
            self._update_details_tk(preset)
            
            # Enable/disable buttons
            self.apply_btn.config(state=tk.NORMAL)
            self.delete_btn.config(state=tk.DISABLED if preset.is_builtin else tk.NORMAL)
        else:
            self.selected_preset = None
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete("1.0", tk.END)
            self.details_text.insert("1.0", "Select a preset to view details")
            self.details_text.config(state=tk.DISABLED)
            self.apply_btn.config(state=tk.DISABLED)
            self.delete_btn.config(state=tk.DISABLED)
    
    def _update_details_qt(self, preset: PresetInfo):
        """Update details display for Qt version."""
        details = f"<b>Name:</b> {preset.name}<br><br>"
        details += f"<b>Type:</b> {'Built-in' if preset.is_builtin else 'Custom'}<br>"
        details += f"<b>Server Count:</b> {preset.server_count}<br><br>"
        details += f"<b>Description:</b><br>{preset.description}"
        
        if preset.is_favorite:
            details += "<br><br>⭐ This is a favorite preset"
        
        self.details_label.setText(details)
    
    def _update_details_tk(self, preset: PresetInfo):
        """Update details display for tkinter version."""
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete("1.0", tk.END)
        
        details = f"Name: {preset.name}\n\n"
        details += f"Type: {'Built-in' if preset.is_builtin else 'Custom'}\n"
        details += f"Server Count: {preset.server_count}\n\n"
        details += f"Description:\n{preset.description}"
        
        if preset.is_favorite:
            details += "\n\n⭐ This is a favorite preset"
        
        self.details_text.insert("1.0", details)
        self.details_text.config(state=tk.DISABLED)
    
    def _on_qt_apply_preset(self):
        """Handle apply preset in Qt version."""
        if self.selected_preset:
            reply = QMessageBox.question(
                self.dialog,
                "Apply Preset",
                f"Apply preset '{self.selected_preset}'?\n\n"
                "This will replace your current server configuration.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                for callback in self.on_preset_applied_callbacks:
                    callback(self.selected_preset)
                self.dialog.accept()
    
    def _on_tk_apply_preset(self):
        """Handle apply preset in tkinter version."""
        if self.selected_preset:
            result = messagebox.askyesno(
                "Apply Preset",
                f"Apply preset '{self.selected_preset}'?\n\n"
                "This will replace your current server configuration."
            )
            
            if result:
                for callback in self.on_preset_applied_callbacks:
                    callback(self.selected_preset)
                self.dialog.destroy()
    
    def _on_qt_save_preset(self):
        """Handle save preset in Qt version."""
        name, ok = QInputDialog.getText(
            self.dialog,
            "Save Preset",
            "Enter name for the new preset:"
        )
        
        if ok and name:
            # Check for duplicate
            if any(p.name == name for p in self.presets):
                QMessageBox.warning(
                    self.dialog,
                    "Duplicate Name",
                    f"A preset named '{name}' already exists."
                )
                return
            
            description, ok = QInputDialog.getMultiLineText(
                self.dialog,
                "Save Preset",
                "Enter description for the preset (optional):"
            )
            
            if ok:
                for callback in self.on_preset_saved_callbacks:
                    callback(name, description)
                
                # Refresh the list (caller should update presets)
                QMessageBox.information(
                    self.dialog,
                    "Preset Saved",
                    f"Preset '{name}' has been saved."
                )
    
    def _on_tk_save_preset(self):
        """Handle save preset in tkinter version."""
        name = simpledialog.askstring(
            "Save Preset",
            "Enter name for the new preset:",
            parent=self.dialog
        )
        
        if name:
            # Check for duplicate
            if any(p.name == name for p in self.presets):
                messagebox.showwarning(
                    "Duplicate Name",
                    f"A preset named '{name}' already exists."
                )
                return
            
            # Create a simple dialog for description
            desc_dialog = tk.Toplevel(self.dialog)
            desc_dialog.title("Preset Description")
            desc_dialog.geometry("400x200")
            desc_dialog.transient(self.dialog)
            desc_dialog.grab_set()
            
            ttk.Label(
                desc_dialog,
                text="Enter description for the preset (optional):"
            ).pack(pady=10)
            
            desc_text = tk.Text(desc_dialog, width=40, height=5)
            desc_text.pack(pady=10, padx=10)
            
            description = ""
            
            def save_description():
                nonlocal description
                description = desc_text.get("1.0", "end").strip()
                desc_dialog.destroy()
            
            ttk.Button(
                desc_dialog,
                text="OK",
                command=save_description
            ).pack(pady=10)
            
            desc_dialog.wait_window()
            
            for callback in self.on_preset_saved_callbacks:
                callback(name, description)
            
            messagebox.showinfo(
                "Preset Saved",
                f"Preset '{name}' has been saved."
            )
    
    def _on_qt_delete_preset(self):
        """Handle delete preset in Qt version."""
        if self.selected_preset:
            preset = next((p for p in self.presets if p.name == self.selected_preset), None)
            if preset and not preset.is_builtin:
                reply = QMessageBox.question(
                    self.dialog,
                    "Delete Preset",
                    f"Delete preset '{self.selected_preset}'?\n\n"
                    "This action cannot be undone.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    for callback in self.on_preset_deleted_callbacks:
                        callback(self.selected_preset)
                    
                    # Remove from list
                    self.presets = [p for p in self.presets if p.name != self.selected_preset]
                    self._refresh_preset_list()
    
    def _on_tk_delete_preset(self):
        """Handle delete preset in tkinter version."""
        if self.selected_preset:
            preset = next((p for p in self.presets if p.name == self.selected_preset), None)
            if preset and not preset.is_builtin:
                result = messagebox.askyesno(
                    "Delete Preset",
                    f"Delete preset '{self.selected_preset}'?\n\n"
                    "This action cannot be undone."
                )
                
                if result:
                    for callback in self.on_preset_deleted_callbacks:
                        callback(self.selected_preset)
                    
                    # Remove from list
                    self.presets = [p for p in self.presets if p.name != self.selected_preset]
                    self._refresh_preset_list()
    
    def on_preset_applied(self, callback: Callable[[str], None]):
        """Register callback for when preset is applied.
        
        Args:
            callback: Function to call with preset name
        """
        self.on_preset_applied_callbacks.append(callback)
    
    def on_preset_saved(self, callback: Callable[[str, str], None]):
        """Register callback for when preset is saved.
        
        Args:
            callback: Function to call with name and description
        """
        self.on_preset_saved_callbacks.append(callback)
    
    def on_preset_deleted(self, callback: Callable[[str], None]):
        """Register callback for when preset is deleted.
        
        Args:
            callback: Function to call with preset name
        """
        self.on_preset_deleted_callbacks.append(callback)
    
    def show(self):
        """Show the dialog."""
        if USING_QT:
            self.dialog.exec()
        else:
            self.dialog.wait_window()