"""Field editor widgets for server configuration editing.

This module provides specialized editor widgets for different field types
in MCP server configurations. Each editor handles a specific data type
and provides validation, visual feedback, and change tracking.
"""

from typing import Any, Optional, Callable, List, Dict, Tuple
from abc import ABC, abstractmethod
import json
import os

try:
    from PyQt6.QtWidgets import (
        QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QSpinBox,
        QCheckBox, QTextEdit, QPushButton, QListWidget, QListWidgetItem,
        QComboBox, QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
        QHeaderView, QDoubleSpinBox
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QIntValidator, QDoubleValidator
    USING_QT = True
except ImportError:
    USING_QT = False
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    

class FieldEditor(ABC):
    """Base class for all field editors.
    
    Provides common functionality for validation, change tracking,
    and visual feedback across all field types.
    """
    
    def __init__(self, field_name: str, initial_value: Any = None,
                 required: bool = False, parent: Optional[Any] = None):
        """Initialize the field editor.
        
        Args:
            field_name: Name of the field being edited
            initial_value: Initial value for the field
            required: Whether the field is required
            parent: Parent widget
        """
        self.field_name = field_name
        self.initial_value = initial_value
        self.current_value = initial_value
        self.required = required
        self.parent = parent
        self.is_modified = False
        self.validation_error = None
        self.change_callbacks: List[Callable] = []
        
        self._create_widget()
        self._setup_signals()
        if initial_value is not None:
            self.set_value(initial_value)
    
    @abstractmethod
    def _create_widget(self) -> None:
        """Create the actual widget for this editor."""
        pass
    
    @abstractmethod
    def _setup_signals(self) -> None:
        """Set up change signals/callbacks for the widget."""
        pass
    
    @abstractmethod
    def get_value(self) -> Any:
        """Get the current value from the widget."""
        pass
    
    @abstractmethod
    def set_value(self, value: Any) -> None:
        """Set the value in the widget."""
        pass
    
    @abstractmethod
    def get_widget(self) -> Any:
        """Get the actual widget to add to layouts."""
        pass
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate the current value.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        value = self.get_value()
        
        # Check required fields
        if self.required and not value:
            return False, f"{self.field_name} is required"
        
        # Subclasses can override for specific validation
        return self._validate_value(value)
    
    def _validate_value(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate the specific value. Override in subclasses.
        
        Args:
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, None
    
    def has_changes(self) -> bool:
        """Check if the field has been modified."""
        return self.current_value != self.initial_value
    
    def reset(self) -> None:
        """Reset to initial value."""
        self.set_value(self.initial_value)
        self.is_modified = False
        self._update_visual_state()
    
    def commit(self) -> None:
        """Commit current value as the new initial value."""
        self.initial_value = self.current_value
        self.is_modified = False
        self._update_visual_state()
    
    def add_change_callback(self, callback: Callable) -> None:
        """Add a callback for value changes."""
        self.change_callbacks.append(callback)
    
    def _on_value_changed(self) -> None:
        """Handle value changes."""
        self.current_value = self.get_value()
        self.is_modified = self.has_changes()
        self._update_visual_state()
        
        # Notify callbacks
        for callback in self.change_callbacks:
            callback(self.field_name, self.current_value)
    
    def _update_visual_state(self) -> None:
        """Update visual indicators for modified/error states."""
        if USING_QT and hasattr(self, 'widget'):
            # Update Qt widget styling
            if self.validation_error:
                self.widget.setStyleSheet("border: 1px solid red;")
            elif self.is_modified:
                self.widget.setStyleSheet("border: 1px solid orange;")
            else:
                self.widget.setStyleSheet("")
        elif not USING_QT and hasattr(self, 'widget'):
            # Update tkinter widget styling
            if self.validation_error:
                self.widget.configure(highlightcolor='red', highlightthickness=2)
            elif self.is_modified:
                self.widget.configure(highlightcolor='orange', highlightthickness=2)
            else:
                self.widget.configure(highlightthickness=1)


class StringEditor(FieldEditor):
    """Editor for string/text fields."""
    
    def _create_widget(self) -> None:
        """Create a text input widget."""
        if USING_QT:
            self.widget = QLineEdit(self.parent)
            self.widget.setPlaceholderText(f"Enter {self.field_name}")
        else:
            self.widget = ttk.Entry(self.parent)
    
    def _setup_signals(self) -> None:
        """Set up text change signals."""
        if USING_QT:
            self.widget.textChanged.connect(self._on_value_changed)
        else:
            self.widget.bind('<KeyRelease>', lambda e: self._on_value_changed())
    
    def get_value(self) -> str:
        """Get the current text value."""
        if USING_QT:
            return self.widget.text()
        else:
            return self.widget.get()
    
    def set_value(self, value: Any) -> None:
        """Set the text value."""
        if USING_QT:
            self.widget.setText(str(value) if value else "")
        else:
            self.widget.delete(0, tk.END)
            if value:
                self.widget.insert(0, str(value))
    
    def get_widget(self) -> Any:
        """Get the widget."""
        return self.widget


class NumberEditor(FieldEditor):
    """Editor for numeric fields."""
    
    def __init__(self, field_name: str, initial_value: Any = None,
                 required: bool = False, parent: Optional[Any] = None,
                 min_value: Optional[float] = None, max_value: Optional[float] = None,
                 decimals: int = 0):
        """Initialize number editor with range constraints."""
        self.min_value = min_value
        self.max_value = max_value
        self.decimals = decimals
        super().__init__(field_name, initial_value, required, parent)
    
    def _create_widget(self) -> None:
        """Create a numeric input widget."""
        if USING_QT:
            if self.decimals > 0:
                self.widget = QDoubleSpinBox(self.parent)
                self.widget.setDecimals(self.decimals)
            else:
                self.widget = QSpinBox(self.parent)
            
            if self.min_value is not None:
                self.widget.setMinimum(self.min_value)
            else:
                self.widget.setMinimum(-999999999)
            
            if self.max_value is not None:
                self.widget.setMaximum(self.max_value)
            else:
                self.widget.setMaximum(999999999)
        else:
            self.widget = ttk.Spinbox(self.parent)
            if self.min_value is not None:
                self.widget.configure(from_=self.min_value)
            if self.max_value is not None:
                self.widget.configure(to=self.max_value)
    
    def _setup_signals(self) -> None:
        """Set up value change signals."""
        if USING_QT:
            self.widget.valueChanged.connect(self._on_value_changed)
        else:
            self.widget.configure(command=self._on_value_changed)
    
    def get_value(self) -> float:
        """Get the current numeric value."""
        if USING_QT:
            return self.widget.value()
        else:
            try:
                return float(self.widget.get())
            except ValueError:
                return 0
    
    def set_value(self, value: Any) -> None:
        """Set the numeric value."""
        if USING_QT:
            self.widget.setValue(float(value) if value else 0)
        else:
            self.widget.set(str(value) if value else "0")
    
    def get_widget(self) -> Any:
        """Get the widget."""
        return self.widget


class BooleanEditor(FieldEditor):
    """Editor for boolean/checkbox fields."""
    
    def _create_widget(self) -> None:
        """Create a checkbox widget."""
        if USING_QT:
            self.widget = QCheckBox(self.field_name, self.parent)
        else:
            self.var = tk.BooleanVar()
            self.widget = ttk.Checkbutton(self.parent, text=self.field_name,
                                         variable=self.var)
    
    def _setup_signals(self) -> None:
        """Set up change signals."""
        if USING_QT:
            self.widget.stateChanged.connect(self._on_value_changed)
        else:
            self.var.trace('w', lambda *args: self._on_value_changed())
    
    def get_value(self) -> bool:
        """Get the current boolean value."""
        if USING_QT:
            return self.widget.isChecked()
        else:
            return self.var.get()
    
    def set_value(self, value: Any) -> None:
        """Set the boolean value."""
        if USING_QT:
            self.widget.setChecked(bool(value))
        else:
            self.var.set(bool(value))
    
    def get_widget(self) -> Any:
        """Get the widget."""
        return self.widget


class ArrayEditor(FieldEditor):
    """Editor for array/list fields."""
    
    def _create_widget(self) -> None:
        """Create a list widget with add/remove controls."""
        if USING_QT:
            self.container = QWidget(self.parent)
            layout = QVBoxLayout(self.container)
            
            # List widget
            self.list_widget = QListWidget()
            layout.addWidget(self.list_widget)
            
            # Add/Remove buttons
            button_layout = QHBoxLayout()
            self.add_button = QPushButton("+")
            self.remove_button = QPushButton("-")
            self.add_button.clicked.connect(self._add_item)
            self.remove_button.clicked.connect(self._remove_item)
            button_layout.addWidget(self.add_button)
            button_layout.addWidget(self.remove_button)
            button_layout.addStretch()
            layout.addLayout(button_layout)
            
            self.widget = self.container
        else:
            self.container = ttk.Frame(self.parent)
            
            # List box with scrollbar
            list_frame = ttk.Frame(self.container)
            list_frame.pack(fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
            self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=self.listbox.yview)
            
            # Add/Remove buttons
            button_frame = ttk.Frame(self.container)
            button_frame.pack(fill=tk.X)
            
            ttk.Button(button_frame, text="+", command=self._add_item).pack(side=tk.LEFT)
            ttk.Button(button_frame, text="-", command=self._remove_item).pack(side=tk.LEFT)
            
            self.widget = self.container
    
    def _setup_signals(self) -> None:
        """Set up change signals."""
        # Signals are connected in _create_widget for buttons
        pass
    
    def _add_item(self) -> None:
        """Add a new item to the list."""
        if USING_QT:
            from PyQt6.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(self.widget, "Add Item",
                                           f"Enter value for {self.field_name}:")
            if ok and text:
                self.list_widget.addItem(text)
                self._on_value_changed()
        else:
            import tkinter.simpledialog as simpledialog
            text = simpledialog.askstring("Add Item",
                                         f"Enter value for {self.field_name}:")
            if text:
                self.listbox.insert(tk.END, text)
                self._on_value_changed()
    
    def _remove_item(self) -> None:
        """Remove selected item from the list."""
        if USING_QT:
            current = self.list_widget.currentRow()
            if current >= 0:
                self.list_widget.takeItem(current)
                self._on_value_changed()
        else:
            selection = self.listbox.curselection()
            if selection:
                self.listbox.delete(selection[0])
                self._on_value_changed()
    
    def get_value(self) -> List[str]:
        """Get the current list value."""
        if USING_QT:
            return [self.list_widget.item(i).text() 
                   for i in range(self.list_widget.count())]
        else:
            return list(self.listbox.get(0, tk.END))
    
    def set_value(self, value: Any) -> None:
        """Set the list value."""
        if USING_QT:
            self.list_widget.clear()
            if value:
                for item in value:
                    self.list_widget.addItem(str(item))
        else:
            self.listbox.delete(0, tk.END)
            if value:
                for item in value:
                    self.listbox.insert(tk.END, str(item))
    
    def get_widget(self) -> Any:
        """Get the widget."""
        return self.widget


class KeyValueEditor(FieldEditor):
    """Editor for key-value pairs (environment variables)."""
    
    def _create_widget(self) -> None:
        """Create a table widget for key-value pairs."""
        if USING_QT:
            self.container = QWidget(self.parent)
            layout = QVBoxLayout(self.container)
            
            # Table widget
            self.table = QTableWidget()
            self.table.setColumnCount(2)
            self.table.setHorizontalHeaderLabels(["Key", "Value"])
            self.table.horizontalHeader().setStretchLastSection(True)
            layout.addWidget(self.table)
            
            # Add/Remove buttons
            button_layout = QHBoxLayout()
            self.add_button = QPushButton("+")
            self.remove_button = QPushButton("-")
            self.add_button.clicked.connect(self._add_pair)
            self.remove_button.clicked.connect(self._remove_pair)
            button_layout.addWidget(self.add_button)
            button_layout.addWidget(self.remove_button)
            button_layout.addStretch()
            layout.addLayout(button_layout)
            
            self.widget = self.container
        else:
            self.container = ttk.Frame(self.parent)
            
            # Treeview for key-value pairs
            tree_frame = ttk.Frame(self.container)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            
            self.tree = ttk.Treeview(tree_frame, columns=('Value',), show='tree headings')
            self.tree.heading('#0', text='Key')
            self.tree.heading('Value', text='Value')
            self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(tree_frame, command=self.tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.tree.config(yscrollcommand=scrollbar.set)
            
            # Add/Remove buttons
            button_frame = ttk.Frame(self.container)
            button_frame.pack(fill=tk.X)
            
            ttk.Button(button_frame, text="+", command=self._add_pair).pack(side=tk.LEFT)
            ttk.Button(button_frame, text="-", command=self._remove_pair).pack(side=tk.LEFT)
            
            self.widget = self.container
    
    def _setup_signals(self) -> None:
        """Set up change signals."""
        if USING_QT:
            self.table.itemChanged.connect(self._on_value_changed)
    
    def _add_pair(self) -> None:
        """Add a new key-value pair."""
        if USING_QT:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(""))
            self.table.setItem(row, 1, QTableWidgetItem(""))
            self._on_value_changed()
        else:
            import tkinter.simpledialog as simpledialog
            key = simpledialog.askstring("Add Key-Value", "Enter key:")
            if key:
                value = simpledialog.askstring("Add Key-Value", f"Enter value for {key}:")
                self.tree.insert('', tk.END, text=key, values=(value or '',))
                self._on_value_changed()
    
    def _remove_pair(self) -> None:
        """Remove selected key-value pair."""
        if USING_QT:
            current = self.table.currentRow()
            if current >= 0:
                self.table.removeRow(current)
                self._on_value_changed()
        else:
            selection = self.tree.selection()
            if selection:
                self.tree.delete(selection[0])
                self._on_value_changed()
    
    def get_value(self) -> Dict[str, str]:
        """Get the current key-value pairs."""
        result = {}
        if USING_QT:
            for row in range(self.table.rowCount()):
                key_item = self.table.item(row, 0)
                value_item = self.table.item(row, 1)
                if key_item and value_item:
                    key = key_item.text()
                    value = value_item.text()
                    if key:
                        result[key] = value
        else:
            for item in self.tree.get_children():
                key = self.tree.item(item)['text']
                value = self.tree.item(item)['values'][0] if self.tree.item(item)['values'] else ''
                if key:
                    result[key] = value
        return result
    
    def set_value(self, value: Any) -> None:
        """Set the key-value pairs."""
        if USING_QT:
            self.table.setRowCount(0)
            if value and isinstance(value, dict):
                for key, val in value.items():
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(str(key)))
                    self.table.setItem(row, 1, QTableWidgetItem(str(val)))
        else:
            for item in self.tree.get_children():
                self.tree.delete(item)
            if value and isinstance(value, dict):
                for key, val in value.items():
                    self.tree.insert('', tk.END, text=str(key), values=(str(val),))
    
    def get_widget(self) -> Any:
        """Get the widget."""
        return self.widget


class PathEditor(StringEditor):
    """Editor for file/directory path fields with browse button."""
    
    def __init__(self, field_name: str, initial_value: Any = None,
                 required: bool = False, parent: Optional[Any] = None,
                 directory: bool = True):
        """Initialize path editor.
        
        Args:
            directory: If True, browse for directories; if False, browse for files
        """
        self.directory = directory
        super().__init__(field_name, initial_value, required, parent)
    
    def _create_widget(self) -> None:
        """Create a text input with browse button."""
        if USING_QT:
            self.container = QWidget(self.parent)
            layout = QHBoxLayout(self.container)
            layout.setContentsMargins(0, 0, 0, 0)
            
            self.text_widget = QLineEdit()
            self.text_widget.setPlaceholderText(f"Enter {self.field_name} path")
            self.browse_button = QPushButton("Browse...")
            self.browse_button.clicked.connect(self._browse)
            
            layout.addWidget(self.text_widget, 1)
            layout.addWidget(self.browse_button)
            
            self.widget = self.container
        else:
            self.container = ttk.Frame(self.parent)
            
            self.text_widget = ttk.Entry(self.container)
            self.text_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            ttk.Button(self.container, text="Browse...",
                      command=self._browse).pack(side=tk.RIGHT)
            
            self.widget = self.container
    
    def _setup_signals(self) -> None:
        """Set up text change signals."""
        if USING_QT:
            self.text_widget.textChanged.connect(self._on_value_changed)
        else:
            self.text_widget.bind('<KeyRelease>', lambda e: self._on_value_changed())
    
    def _browse(self) -> None:
        """Open file/directory browser."""
        if USING_QT:
            if self.directory:
                path = QFileDialog.getExistingDirectory(self.widget, 
                                                       f"Select {self.field_name}")
            else:
                path, _ = QFileDialog.getOpenFileName(self.widget,
                                                     f"Select {self.field_name}")
            if path:
                self.text_widget.setText(path)
        else:
            if self.directory:
                path = filedialog.askdirectory(title=f"Select {self.field_name}")
            else:
                path = filedialog.askopenfilename(title=f"Select {self.field_name}")
            if path:
                self.text_widget.delete(0, tk.END)
                self.text_widget.insert(0, path)
    
    def get_value(self) -> str:
        """Get the current path value."""
        if USING_QT:
            return self.text_widget.text()
        else:
            return self.text_widget.get()
    
    def set_value(self, value: Any) -> None:
        """Set the path value."""
        if USING_QT:
            self.text_widget.setText(str(value) if value else "")
        else:
            self.text_widget.delete(0, tk.END)
            if value:
                self.text_widget.insert(0, str(value))
    
    def _validate_value(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate that the path exists if provided."""
        if value and not os.path.exists(str(value)):
            return False, f"Path does not exist: {value}"
        return True, None


class DropdownEditor(FieldEditor):
    """Editor for enum/dropdown fields."""
    
    def __init__(self, field_name: str, initial_value: Any = None,
                 required: bool = False, parent: Optional[Any] = None,
                 options: Optional[List[str]] = None):
        """Initialize dropdown editor with options."""
        self.options = options or []
        super().__init__(field_name, initial_value, required, parent)
    
    def _create_widget(self) -> None:
        """Create a dropdown/combo box widget."""
        if USING_QT:
            self.widget = QComboBox(self.parent)
            self.widget.addItems(self.options)
            if not self.required:
                self.widget.setEditable(True)
        else:
            self.var = tk.StringVar()
            self.widget = ttk.Combobox(self.parent, textvariable=self.var,
                                      values=self.options)
            if not self.required:
                self.widget.configure(state='normal')
            else:
                self.widget.configure(state='readonly')
    
    def _setup_signals(self) -> None:
        """Set up change signals."""
        if USING_QT:
            self.widget.currentTextChanged.connect(self._on_value_changed)
        else:
            self.var.trace('w', lambda *args: self._on_value_changed())
    
    def get_value(self) -> str:
        """Get the current selected value."""
        if USING_QT:
            return self.widget.currentText()
        else:
            return self.var.get()
    
    def set_value(self, value: Any) -> None:
        """Set the selected value."""
        if USING_QT:
            index = self.widget.findText(str(value) if value else "")
            if index >= 0:
                self.widget.setCurrentIndex(index)
            elif self.widget.isEditable():
                self.widget.setCurrentText(str(value) if value else "")
        else:
            self.var.set(str(value) if value else "")
    
    def set_options(self, options: List[str]) -> None:
        """Update the available options."""
        self.options = options
        current = self.get_value()
        
        if USING_QT:
            self.widget.clear()
            self.widget.addItems(options)
            # Restore previous value if still valid
            if current in options:
                self.set_value(current)
        else:
            self.widget['values'] = options
            # Restore previous value if still valid
            if current in options:
                self.var.set(current)
    
    def get_widget(self) -> Any:
        """Get the widget."""
        return self.widget