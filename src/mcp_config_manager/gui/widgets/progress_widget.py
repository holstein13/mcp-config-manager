"""Progress indicator widgets for long operations."""

from typing import Optional
import logging

try:
    from PyQt6.QtWidgets import (QWidget, QProgressBar, QLabel, QVBoxLayout, 
                                 QHBoxLayout, QPushButton, QDialog, QDialogButtonBox)
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QCloseEvent
    USING_QT = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    USING_QT = False

logger = logging.getLogger(__name__)


if USING_QT:
    class ProgressWidget(QWidget):
        """Progress widget for displaying operation progress (PyQt6)."""
        
        cancelled = pyqtSignal()  # Emitted when cancel is clicked
        
        def __init__(self, parent=None):
            """Initialize the progress widget.
            
            Args:
                parent: Parent widget
            """
            super().__init__(parent)
            self.setup_ui()
            
        def setup_ui(self):
            """Set up the user interface."""
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Progress label
            self.label = QLabel("Processing...")
            layout.addWidget(self.label)
            
            # Progress bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            layout.addWidget(self.progress_bar)
            
            # Status label
            self.status_label = QLabel("")
            self.status_label.setWordWrap(True)
            layout.addWidget(self.status_label)
            
            # Cancel button (optional)
            self.cancel_button = QPushButton("Cancel")
            self.cancel_button.clicked.connect(self.cancelled.emit)
            self.cancel_button.hide()  # Hidden by default
            layout.addWidget(self.cancel_button)
            
            self.setLayout(layout)
        
        def set_progress(self, value: float, message: str = ""):
            """Set progress value.
            
            Args:
                value: Progress value (0.0 to 1.0)
                message: Optional status message
            """
            self.progress_bar.setValue(int(value * 100))
            if message:
                self.status_label.setText(message)
        
        def set_indeterminate(self, enabled: bool = True):
            """Set indeterminate progress mode.
            
            Args:
                enabled: Whether to enable indeterminate mode
            """
            if enabled:
                self.progress_bar.setRange(0, 0)
            else:
                self.progress_bar.setRange(0, 100)
        
        def set_label(self, text: str):
            """Set the main label text.
            
            Args:
                text: Label text
            """
            self.label.setText(text)
        
        def show_cancel_button(self, show: bool = True):
            """Show or hide the cancel button.
            
            Args:
                show: Whether to show the cancel button
            """
            self.cancel_button.setVisible(show)
        
        def reset(self):
            """Reset the progress widget."""
            self.progress_bar.setValue(0)
            self.label.setText("Processing...")
            self.status_label.setText("")
            self.set_indeterminate(False)
    
    
    class ProgressDialog(QDialog):
        """Modal progress dialog for long operations (PyQt6)."""
        
        cancelled = pyqtSignal()  # Emitted when cancel is clicked
        
        def __init__(self, title: str = "Progress", parent=None):
            """Initialize the progress dialog.
            
            Args:
                title: Dialog title
                parent: Parent widget
            """
            super().__init__(parent)
            self.setWindowTitle(title)
            self.setModal(True)
            self.setup_ui()
            self._can_close = False
            
        def setup_ui(self):
            """Set up the user interface."""
            layout = QVBoxLayout()
            
            # Progress widget
            self.progress_widget = ProgressWidget()
            self.progress_widget.cancelled.connect(self.cancelled.emit)
            layout.addWidget(self.progress_widget)
            
            # Dialog buttons
            self.button_box = QDialogButtonBox()
            self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
            self.button_box.rejected.connect(self._on_cancel)
            layout.addWidget(self.button_box)
            
            self.setLayout(layout)
            self.setMinimumWidth(400)
        
        def _on_cancel(self):
            """Handle cancel button click."""
            self.cancelled.emit()
        
        def set_progress(self, value: float, message: str = ""):
            """Set progress value.
            
            Args:
                value: Progress value (0.0 to 1.0)
                message: Optional status message
            """
            self.progress_widget.set_progress(value, message)
        
        def set_indeterminate(self, enabled: bool = True):
            """Set indeterminate progress mode.
            
            Args:
                enabled: Whether to enable indeterminate mode
            """
            self.progress_widget.set_indeterminate(enabled)
        
        def set_label(self, text: str):
            """Set the main label text.
            
            Args:
                text: Label text
            """
            self.progress_widget.set_label(text)
        
        def set_can_close(self, can_close: bool):
            """Set whether the dialog can be closed.
            
            Args:
                can_close: Whether the dialog can be closed
            """
            self._can_close = can_close
            self.button_box.setEnabled(can_close)
        
        def closeEvent(self, event: QCloseEvent):
            """Handle close event.
            
            Args:
                event: Close event
            """
            if not self._can_close:
                event.ignore()
            else:
                super().closeEvent(event)

else:
    class ProgressWidget(tk.Frame):
        """Progress widget for displaying operation progress (tkinter)."""
        
        def __init__(self, parent=None):
            """Initialize the progress widget.
            
            Args:
                parent: Parent widget
            """
            super().__init__(parent)
            self.cancel_callbacks = []
            self.setup_ui()
            
        def setup_ui(self):
            """Set up the user interface."""
            # Progress label
            self.label = tk.Label(self, text="Processing...")
            self.label.pack(pady=(0, 5))
            
            # Progress bar
            self.progress_var = tk.DoubleVar()
            self.progress_bar = ttk.Progressbar(
                self,
                variable=self.progress_var,
                maximum=100
            )
            self.progress_bar.pack(fill=tk.X, pady=(0, 5))
            
            # Status label
            self.status_label = tk.Label(self, text="", wraplength=300)
            self.status_label.pack(pady=(0, 5))
            
            # Cancel button
            self.cancel_button = tk.Button(
                self,
                text="Cancel",
                command=self._on_cancel
            )
            # Hidden by default
            
        def _on_cancel(self):
            """Handle cancel button click."""
            for callback in self.cancel_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in cancel callback: {e}")
        
        def set_progress(self, value: float, message: str = ""):
            """Set progress value.
            
            Args:
                value: Progress value (0.0 to 1.0)
                message: Optional status message
            """
            self.progress_var.set(value * 100)
            if message:
                self.status_label.config(text=message)
        
        def set_indeterminate(self, enabled: bool = True):
            """Set indeterminate progress mode.
            
            Args:
                enabled: Whether to enable indeterminate mode
            """
            if enabled:
                self.progress_bar.config(mode='indeterminate')
                self.progress_bar.start(10)  # Start animation
            else:
                self.progress_bar.stop()
                self.progress_bar.config(mode='determinate')
        
        def set_label(self, text: str):
            """Set the main label text.
            
            Args:
                text: Label text
            """
            self.label.config(text=text)
        
        def show_cancel_button(self, show: bool = True):
            """Show or hide the cancel button.
            
            Args:
                show: Whether to show the cancel button
            """
            if show:
                self.cancel_button.pack(pady=(5, 0))
            else:
                self.cancel_button.pack_forget()
        
        def reset(self):
            """Reset the progress widget."""
            self.progress_var.set(0)
            self.label.config(text="Processing...")
            self.status_label.config(text="")
            self.set_indeterminate(False)
        
        def on_cancelled(self, callback):
            """Register callback for cancel event.
            
            Args:
                callback: Function to call when cancelled
            """
            self.cancel_callbacks.append(callback)
    
    
    class ProgressDialog(tk.Toplevel):
        """Modal progress dialog for long operations (tkinter)."""
        
        def __init__(self, title: str = "Progress", parent=None):
            """Initialize the progress dialog.
            
            Args:
                title: Dialog title
                parent: Parent widget
            """
            super().__init__(parent)
            self.title(title)
            self.transient(parent)
            self.grab_set()  # Make modal
            
            self.cancel_callbacks = []
            self._can_close = False
            self.setup_ui()
            
            # Center on parent
            if parent:
                self.geometry(f"+{parent.winfo_x() + 50}+{parent.winfo_y() + 50}")
            
            # Handle close button
            self.protocol("WM_DELETE_WINDOW", self._on_close)
            
        def setup_ui(self):
            """Set up the user interface."""
            # Main frame
            main_frame = tk.Frame(self, padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Progress widget
            self.progress_widget = ProgressWidget(main_frame)
            self.progress_widget.pack(fill=tk.X)
            
            # Button frame
            button_frame = tk.Frame(main_frame)
            button_frame.pack(pady=(10, 0))
            
            self.cancel_button = tk.Button(
                button_frame,
                text="Cancel",
                command=self._on_cancel
            )
            self.cancel_button.pack()
            
            # Set minimum size
            self.minsize(400, 150)
        
        def _on_cancel(self):
            """Handle cancel button click."""
            for callback in self.cancel_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in cancel callback: {e}")
        
        def _on_close(self):
            """Handle window close."""
            if self._can_close:
                self.destroy()
        
        def set_progress(self, value: float, message: str = ""):
            """Set progress value.
            
            Args:
                value: Progress value (0.0 to 1.0)
                message: Optional status message
            """
            self.progress_widget.set_progress(value, message)
        
        def set_indeterminate(self, enabled: bool = True):
            """Set indeterminate progress mode.
            
            Args:
                enabled: Whether to enable indeterminate mode
            """
            self.progress_widget.set_indeterminate(enabled)
        
        def set_label(self, text: str):
            """Set the main label text.
            
            Args:
                text: Label text
            """
            self.progress_widget.set_label(text)
        
        def set_can_close(self, can_close: bool):
            """Set whether the dialog can be closed.
            
            Args:
                can_close: Whether the dialog can be closed
            """
            self._can_close = can_close
            self.cancel_button.config(state=tk.NORMAL if can_close else tk.DISABLED)
        
        def on_cancelled(self, callback):
            """Register callback for cancel event.
            
            Args:
                callback: Function to call when cancelled
            """
            self.cancel_callbacks.append(callback)
            self.progress_widget.on_cancelled(callback)