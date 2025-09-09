"""Search bar widget for filtering servers."""

from typing import Optional, Callable, List
import logging

# Try to import Qt, fall back to tkinter
try:
    from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, 
                                 QPushButton, QComboBox, QLabel)
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QIcon
    USING_QT = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    USING_QT = False

logger = logging.getLogger(__name__)


if USING_QT:
    class SearchBar(QWidget):
        """Search bar widget for filtering servers (PyQt6 version)."""
        
        # Signals
        searchChanged = pyqtSignal(str)  # Emitted when search text changes
        filterChanged = pyqtSignal(str)  # Emitted when filter type changes
        
        def __init__(self, parent=None):
            """Initialize the search bar.
            
            Args:
                parent: Parent widget
            """
            super().__init__(parent)
            self.setup_ui()
            self.debounce_timer = QTimer()
            self.debounce_timer.timeout.connect(self._emit_search_changed)
            self.debounce_timer.setSingleShot(True)
            
        def setup_ui(self):
            """Set up the user interface."""
            layout = QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Search label
            self.search_label = QLabel("Search:")
            layout.addWidget(self.search_label)
            
            # Search input
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Filter servers...")
            self.search_input.textChanged.connect(self._on_text_changed)
            self.search_input.setClearButtonEnabled(True)
            layout.addWidget(self.search_input, 1)  # Stretch factor 1
            
            # Filter type combo
            self.filter_combo = QComboBox()
            self.filter_combo.addItems([
                "All",
                "Enabled",
                "Disabled",
                "Error",
                "Modified"
            ])
            self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
            layout.addWidget(self.filter_combo)
            
            # Clear button
            self.clear_button = QPushButton("Clear")
            self.clear_button.clicked.connect(self.clear_search)
            layout.addWidget(self.clear_button)
            
            self.setLayout(layout)
        
        def _on_text_changed(self, text: str):
            """Handle text change with debouncing.
            
            Args:
                text: New search text
            """
            # Cancel previous timer
            self.debounce_timer.stop()
            # Start new timer (300ms delay)
            self.debounce_timer.start(300)
        
        def _emit_search_changed(self):
            """Emit the search changed signal."""
            self.searchChanged.emit(self.search_input.text())
        
        def _on_filter_changed(self, filter_type: str):
            """Handle filter type change.
            
            Args:
                filter_type: New filter type
            """
            self.filterChanged.emit(filter_type)
        
        def clear_search(self):
            """Clear the search input and reset filter."""
            self.search_input.clear()
            self.filter_combo.setCurrentIndex(0)  # Reset to "All"
        
        def get_search_text(self) -> str:
            """Get current search text.
            
            Returns:
                Current search text
            """
            return self.search_input.text()
        
        def get_filter_type(self) -> str:
            """Get current filter type.
            
            Returns:
                Current filter type
            """
            return self.filter_combo.currentText()
        
        def set_search_text(self, text: str):
            """Set search text.
            
            Args:
                text: Text to set
            """
            self.search_input.setText(text)
        
        def set_filter_type(self, filter_type: str):
            """Set filter type.
            
            Args:
                filter_type: Filter type to set
            """
            index = self.filter_combo.findText(filter_type)
            if index >= 0:
                self.filter_combo.setCurrentIndex(index)
        
        def set_enabled(self, enabled: bool):
            """Enable or disable the search bar.
            
            Args:
                enabled: Whether to enable the search bar
            """
            self.search_input.setEnabled(enabled)
            self.filter_combo.setEnabled(enabled)
            self.clear_button.setEnabled(enabled)

else:
    class SearchBar(tk.Frame):
        """Search bar widget for filtering servers (tkinter version)."""
        
        def __init__(self, parent=None):
            """Initialize the search bar.
            
            Args:
                parent: Parent widget
            """
            super().__init__(parent)
            self.search_callbacks: List[Callable[[str], None]] = []
            self.filter_callbacks: List[Callable[[str], None]] = []
            self.setup_ui()
            self.debounce_after_id = None
            
        def setup_ui(self):
            """Set up the user interface."""
            # Search label
            self.search_label = tk.Label(self, text="Search:")
            self.search_label.pack(side=tk.LEFT, padx=(0, 5))
            
            # Search input
            self.search_var = tk.StringVar()
            self.search_var.trace('w', self._on_text_changed)
            self.search_input = tk.Entry(self, textvariable=self.search_var, width=30)
            self.search_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
            
            # Filter type combo
            self.filter_var = tk.StringVar(value="All")
            self.filter_combo = ttk.Combobox(
                self,
                textvariable=self.filter_var,
                values=["All", "Enabled", "Disabled", "Error", "Modified"],
                state="readonly",
                width=10
            )
            self.filter_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
            self.filter_combo.pack(side=tk.LEFT, padx=(0, 5))
            
            # Clear button
            self.clear_button = tk.Button(self, text="Clear", command=self.clear_search)
            self.clear_button.pack(side=tk.LEFT)
        
        def _on_text_changed(self, *args):
            """Handle text change with debouncing."""
            # Cancel previous debounce
            if self.debounce_after_id:
                self.after_cancel(self.debounce_after_id)
            
            # Schedule new debounce (300ms)
            self.debounce_after_id = self.after(300, self._emit_search_changed)
        
        def _emit_search_changed(self):
            """Emit the search changed signal."""
            text = self.search_var.get()
            for callback in self.search_callbacks:
                try:
                    callback(text)
                except Exception as e:
                    logger.error(f"Error in search callback: {e}")
        
        def _on_filter_changed(self, event=None):
            """Handle filter type change."""
            filter_type = self.filter_var.get()
            for callback in self.filter_callbacks:
                try:
                    callback(filter_type)
                except Exception as e:
                    logger.error(f"Error in filter callback: {e}")
        
        def clear_search(self):
            """Clear the search input and reset filter."""
            self.search_var.set("")
            self.filter_var.set("All")
        
        def get_search_text(self) -> str:
            """Get current search text.
            
            Returns:
                Current search text
            """
            return self.search_var.get()
        
        def get_filter_type(self) -> str:
            """Get current filter type.
            
            Returns:
                Current filter type
            """
            return self.filter_var.get()
        
        def set_search_text(self, text: str):
            """Set search text.
            
            Args:
                text: Text to set
            """
            self.search_var.set(text)
        
        def set_filter_type(self, filter_type: str):
            """Set filter type.
            
            Args:
                filter_type: Filter type to set
            """
            if filter_type in ["All", "Enabled", "Disabled", "Error", "Modified"]:
                self.filter_var.set(filter_type)
        
        def set_enabled(self, enabled: bool):
            """Enable or disable the search bar.
            
            Args:
                enabled: Whether to enable the search bar
            """
            state = tk.NORMAL if enabled else tk.DISABLED
            self.search_input.config(state=state)
            self.filter_combo.config(state="readonly" if enabled else tk.DISABLED)
            self.clear_button.config(state=state)
        
        def on_search_changed(self, callback: Callable[[str], None]):
            """Register callback for search text changes.
            
            Args:
                callback: Function to call when search text changes
            """
            self.search_callbacks.append(callback)
        
        def on_filter_changed(self, callback: Callable[[str], None]):
            """Register callback for filter type changes.
            
            Args:
                callback: Function to call when filter type changes
            """
            self.filter_callbacks.append(callback)


class ServerFilter:
    """Helper class for filtering servers based on search criteria."""
    
    @staticmethod
    def filter_servers(servers: List[dict], search_text: str = "", 
                      filter_type: str = "All") -> List[dict]:
        """Filter servers based on search text and filter type.
        
        Args:
            servers: List of server dictionaries
            search_text: Text to search for in server names
            filter_type: Type of filter to apply
            
        Returns:
            Filtered list of servers
        """
        filtered = servers.copy()
        
        # Apply text search
        if search_text:
            search_lower = search_text.lower()
            filtered = [
                s for s in filtered
                if search_lower in s.get('name', '').lower() or
                   search_lower in s.get('command', '').lower()
            ]
        
        # Apply filter type
        if filter_type == "Enabled":
            filtered = [s for s in filtered if s.get('enabled', False)]
        elif filter_type == "Disabled":
            filtered = [s for s in filtered if not s.get('enabled', False)]
        elif filter_type == "Error":
            filtered = [s for s in filtered if s.get('status') == 'error']
        elif filter_type == "Modified":
            filtered = [s for s in filtered if s.get('modified', False)]
        # "All" doesn't need filtering
        
        return filtered
    
    @staticmethod
    def matches_search(server: dict, search_text: str) -> bool:
        """Check if a server matches search text.
        
        Args:
            server: Server dictionary
            search_text: Text to search for
            
        Returns:
            True if server matches search
        """
        if not search_text:
            return True
        
        search_lower = search_text.lower()
        return (
            search_lower in server.get('name', '').lower() or
            search_lower in server.get('command', '').lower()
        )