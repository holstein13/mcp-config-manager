"""Mode selector widget for MCP Config Manager."""

from typing import Optional, Callable, List
from enum import Enum

try:
    from PyQt6.QtWidgets import (
        QWidget, QHBoxLayout, QVBoxLayout, QRadioButton, QButtonGroup,
        QGroupBox, QLabel, QComboBox
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
    USING_QT = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    USING_QT = False

from ..models.app_state import ClientMode


class ModeSelectorWidget(QWidget if USING_QT else object):
    """Widget for selecting the client mode (Claude/Gemini/Both)."""
    
    # Qt signals
    if USING_QT:
        mode_changed = pyqtSignal(str)  # new_mode
    
    def __init__(self, parent=None):
        """Initialize the mode selector widget."""
        if USING_QT:
            super().__init__(parent)
            self._setup_qt_widget()
        else:
            self._setup_tk_widget(parent)
        
        self.current_mode = ClientMode.BOTH
        self._mode_callbacks: List[Callable] = []
    
    def _setup_qt_widget(self):
        """Set up Qt widget."""
        layout = QVBoxLayout(self)
        
        # Group box for mode selection
        group = QGroupBox("Client Mode")
        group_layout = QVBoxLayout()
        
        # Description label
        desc_label = QLabel("Select which client configurations to manage:")
        desc_label.setWordWrap(True)
        group_layout.addWidget(desc_label)
        
        # Radio buttons
        self.button_group = QButtonGroup()
        
        self.claude_radio = QRadioButton("Claude Only")
        self.claude_radio.setToolTip("Manage only Claude Desktop configuration")
        self.button_group.addButton(self.claude_radio, 0)
        group_layout.addWidget(self.claude_radio)
        
        self.gemini_radio = QRadioButton("Gemini Only")
        self.gemini_radio.setToolTip("Manage only Gemini configuration")
        self.button_group.addButton(self.gemini_radio, 1)
        group_layout.addWidget(self.gemini_radio)
        
        self.both_radio = QRadioButton("Both (Synchronized)")
        self.both_radio.setToolTip("Manage both Claude and Gemini configurations together")
        self.both_radio.setChecked(True)
        self.button_group.addButton(self.both_radio, 2)
        group_layout.addWidget(self.both_radio)
        
        # Connect signal
        self.button_group.idClicked.connect(self._on_mode_changed_qt)
        
        # Status indicator
        self.status_layout = QHBoxLayout()
        self.status_label = QLabel("Status:")
        self.status_value = QLabel("Both clients synchronized")
        self.status_value.setStyleSheet("color: green; font-weight: bold;")
        self.status_layout.addWidget(self.status_label)
        self.status_layout.addWidget(self.status_value)
        self.status_layout.addStretch()
        group_layout.addLayout(self.status_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        # Compact mode - horizontal layout option
        self.compact_layout = QHBoxLayout()
        self.compact_label = QLabel("Mode:")
        self.compact_combo = QComboBox()
        self.compact_combo.addItems(["Claude Only", "Gemini Only", "Both"])
        self.compact_combo.setCurrentIndex(2)
        self.compact_combo.currentIndexChanged.connect(self._on_combo_changed)
        self.compact_combo.hide()  # Hidden by default
        self.compact_label.hide()
        
        self.compact_layout.addWidget(self.compact_label)
        self.compact_layout.addWidget(self.compact_combo)
        self.compact_layout.addStretch()
        layout.addLayout(self.compact_layout)
        
        layout.addStretch()
    
    def _setup_tk_widget(self, parent):
        """Set up tkinter widget."""
        self.frame = ttk.Frame(parent)
        
        # Label frame for mode selection
        group = ttk.LabelFrame(self.frame, text="Client Mode", padding=10)
        group.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Description label
        desc_label = ttk.Label(group, text="Select which client configurations to manage:",
                              wraplength=300)
        desc_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Radio buttons
        self.mode_var = tk.StringVar(value="both")
        
        self.claude_radio = ttk.Radiobutton(group, text="Claude Only", 
                                           variable=self.mode_var, value="claude",
                                           command=self._on_mode_changed_tk)
        self.claude_radio.pack(anchor=tk.W, pady=2)
        
        self.gemini_radio = ttk.Radiobutton(group, text="Gemini Only",
                                           variable=self.mode_var, value="gemini",
                                           command=self._on_mode_changed_tk)
        self.gemini_radio.pack(anchor=tk.W, pady=2)
        
        self.both_radio = ttk.Radiobutton(group, text="Both (Synchronized)",
                                         variable=self.mode_var, value="both",
                                         command=self._on_mode_changed_tk)
        self.both_radio.pack(anchor=tk.W, pady=2)
        
        # Status frame
        status_frame = ttk.Frame(group)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, text="Both clients synchronized",
                                     foreground="green", font=('', 9, 'bold'))
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Compact mode (alternative layout)
        self.compact_frame = ttk.Frame(parent)
        ttk.Label(self.compact_frame, text="Mode:").pack(side=tk.LEFT)
        
        self.compact_combo = ttk.Combobox(self.compact_frame, 
                                         values=["Claude Only", "Gemini Only", "Both"],
                                         state="readonly", width=15)
        self.compact_combo.current(2)
        self.compact_combo.bind("<<ComboboxSelected>>", self._on_combo_changed_tk)
        self.compact_combo.pack(side=tk.LEFT, padx=(5, 0))
    
    def _on_mode_changed_qt(self, button_id: int):
        """Handle mode change (Qt)."""
        if button_id == 0:
            self.set_mode(ClientMode.CLAUDE)
        elif button_id == 1:
            self.set_mode(ClientMode.GEMINI)
        else:
            self.set_mode(ClientMode.BOTH)
    
    def _on_combo_changed(self, index: int):
        """Handle combo box change (Qt compact mode)."""
        if index == 0:
            self.set_mode(ClientMode.CLAUDE)
        elif index == 1:
            self.set_mode(ClientMode.GEMINI)
        else:
            self.set_mode(ClientMode.BOTH)
    
    def _on_mode_changed_tk(self):
        """Handle mode change (tkinter)."""
        mode_str = self.mode_var.get()
        if mode_str == "claude":
            self.set_mode(ClientMode.CLAUDE)
        elif mode_str == "gemini":
            self.set_mode(ClientMode.GEMINI)
        else:
            self.set_mode(ClientMode.BOTH)
    
    def _on_combo_changed_tk(self, event=None):
        """Handle combo box change (tkinter compact mode)."""
        selection = self.compact_combo.get()
        if "Claude" in selection:
            self.set_mode(ClientMode.CLAUDE)
        elif "Gemini" in selection:
            self.set_mode(ClientMode.GEMINI)
        else:
            self.set_mode(ClientMode.BOTH)
    
    def set_mode(self, mode: ClientMode):
        """Set the current mode."""
        if mode == self.current_mode:
            return
        
        self.current_mode = mode
        
        # Update UI
        if USING_QT:
            if mode == ClientMode.CLAUDE:
                self.claude_radio.setChecked(True)
                self.compact_combo.setCurrentIndex(0)
                self._update_status("Claude Desktop only", "blue")
            elif mode == ClientMode.GEMINI:
                self.gemini_radio.setChecked(True)
                self.compact_combo.setCurrentIndex(1)
                self._update_status("Gemini only", "purple")
            else:
                self.both_radio.setChecked(True)
                self.compact_combo.setCurrentIndex(2)
                self._update_status("Both clients synchronized", "green")
            
            # Emit signal
            self.mode_changed.emit(mode.value)
        else:
            # Update tkinter
            if mode == ClientMode.CLAUDE:
                self.mode_var.set("claude")
                self.compact_combo.current(0)
                self._update_status("Claude Desktop only", "blue")
            elif mode == ClientMode.GEMINI:
                self.mode_var.set("gemini")
                self.compact_combo.current(1)
                self._update_status("Gemini only", "purple")
            else:
                self.mode_var.set("both")
                self.compact_combo.current(2)
                self._update_status("Both clients synchronized", "green")
        
        # Call callbacks
        for callback in self._mode_callbacks:
            callback(mode.value)
    
    def _update_status(self, text: str, color: str):
        """Update the status indicator."""
        if USING_QT:
            self.status_value.setText(text)
            self.status_value.setStyleSheet(f"color: {color}; font-weight: bold;")
        else:
            self.status_label.config(text=text, foreground=color)
    
    def get_mode(self) -> ClientMode:
        """Get the current mode."""
        return self.current_mode
    
    def set_compact(self, compact: bool):
        """Switch between normal and compact layout."""
        if USING_QT:
            if compact:
                # Hide radio buttons, show combo box
                self.claude_radio.parent().hide()
                self.compact_label.show()
                self.compact_combo.show()
            else:
                # Show radio buttons, hide combo box
                self.claude_radio.parent().show()
                self.compact_label.hide()
                self.compact_combo.hide()
        else:
            # In tkinter, swap which frame is packed
            if compact:
                self.frame.pack_forget()
                self.compact_frame.pack(fill=tk.X, padx=5, pady=5)
            else:
                self.compact_frame.pack_forget()
                self.frame.pack(fill=tk.BOTH, expand=True)
    
    def add_mode_callback(self, callback: Callable):
        """Add callback for mode change events."""
        self._mode_callbacks.append(callback)
    
    def remove_mode_callback(self, callback: Callable):
        """Remove a mode change callback."""
        if callback in self._mode_callbacks:
            self._mode_callbacks.remove(callback)
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the mode selector."""
        if USING_QT:
            self.claude_radio.setEnabled(enabled)
            self.gemini_radio.setEnabled(enabled)
            self.both_radio.setEnabled(enabled)
            self.compact_combo.setEnabled(enabled)
        else:
            state = tk.NORMAL if enabled else tk.DISABLED
            self.claude_radio.config(state=state)
            self.gemini_radio.config(state=state)
            self.both_radio.config(state=state)
            self.compact_combo.config(state="readonly" if enabled else "disabled")
    
    def show_sync_warning(self, show: bool):
        """Show or hide synchronization warning."""
        # This could be extended to show a warning icon or message
        # when modes are out of sync
        pass
    
    def get_widget(self):
        """Get the underlying widget (for tkinter compatibility)."""
        if USING_QT:
            return self
        else:
            return self.frame
    
    def get_compact_widget(self):
        """Get the compact mode widget."""
        if USING_QT:
            # Return a container with just the combo box
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.compact_label)
            layout.addWidget(self.compact_combo)
            return widget
        else:
            return self.compact_frame