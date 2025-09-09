"""Error dialog with detailed information."""

from typing import Optional
import traceback

try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
        QPushButton, QDialogButtonBox, QGroupBox
    )
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont, QIcon
    USING_QT = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk, scrolledtext
    USING_QT = False


class ErrorDialog:
    """Dialog for displaying error messages with details."""
    
    def __init__(self, parent=None, title: str = "Error", 
                 message: str = "", details: str = "",
                 error_type: str = "error"):
        """Initialize the Error dialog.
        
        Args:
            parent: Parent widget/window
            title: Dialog title
            message: Main error message
            details: Detailed error information
            error_type: Type of error ('error', 'warning', 'info')
        """
        self.parent = parent
        self.title = title
        self.message = message
        self.details = details
        self.error_type = error_type
        
        if USING_QT:
            self._init_qt()
        else:
            self._init_tk()
    
    def _init_qt(self):
        """Initialize Qt version of the dialog."""
        self.dialog = QDialog(self.parent)
        self.dialog.setWindowTitle(self.title)
        self.dialog.setModal(True)
        self.dialog.resize(600, 400)
        
        # Main layout
        layout = QVBoxLayout(self.dialog)
        
        # Icon and message layout
        message_layout = QHBoxLayout()
        
        # Icon label (would need actual icons in resources)
        icon_label = QLabel()
        if self.error_type == "error":
            icon_label.setText("❌")
        elif self.error_type == "warning":
            icon_label.setText("⚠️")
        else:
            icon_label.setText("ℹ️")
        icon_label.setFont(QFont("", 24))
        message_layout.addWidget(icon_label)
        
        # Message label
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setMinimumWidth(400)
        message_layout.addWidget(message_label, 1)
        
        layout.addLayout(message_layout)
        
        # Details section (if provided)
        if self.details:
            details_group = QGroupBox("Details")
            details_layout = QVBoxLayout()
            
            self.details_text = QTextEdit()
            self.details_text.setPlainText(self.details)
            self.details_text.setReadOnly(True)
            self.details_text.setFont(QFont("Courier", 9))
            details_layout.addWidget(self.details_text)
            
            # Copy button for details
            copy_btn = QPushButton("Copy Details")
            copy_btn.clicked.connect(self._copy_details_qt)
            details_layout.addWidget(copy_btn)
            
            details_group.setLayout(details_layout)
            layout.addWidget(details_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.dialog.accept)
        
        # Report button
        if self.error_type == "error":
            report_btn = QPushButton("Report Issue")
            report_btn.clicked.connect(self._report_issue_qt)
            button_box.addButton(report_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        layout.addWidget(button_box)
    
    def _init_tk(self):
        """Initialize tkinter version of the dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("600x400")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Icon and message frame
        message_frame = ttk.Frame(main_frame)
        message_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Icon label
        icon_text = "❌" if self.error_type == "error" else "⚠️" if self.error_type == "warning" else "ℹ️"
        icon_label = ttk.Label(message_frame, text=icon_text, font=("", 24))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Message label
        message_label = ttk.Label(
            message_frame,
            text=self.message,
            wraplength=500
        )
        message_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Details section (if provided)
        if self.details:
            details_frame = ttk.LabelFrame(main_frame, text="Details", padding="5")
            details_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            self.details_text = scrolledtext.ScrolledText(
                details_frame,
                wrap=tk.WORD,
                width=60,
                height=10,
                font=("Courier", 9)
            )
            self.details_text.pack(fill=tk.BOTH, expand=True)
            self.details_text.insert("1.0", self.details)
            self.details_text.config(state=tk.DISABLED)
            
            # Copy button for details
            copy_btn = ttk.Button(
                details_frame,
                text="Copy Details",
                command=self._copy_details_tk
            )
            copy_btn.pack(pady=(5, 0))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Report button (for errors)
        if self.error_type == "error":
            report_btn = ttk.Button(
                button_frame,
                text="Report Issue",
                command=self._report_issue_tk
            )
            report_btn.pack(side=tk.LEFT)
        
        # OK button
        ok_btn = ttk.Button(
            button_frame,
            text="OK",
            command=self.dialog.destroy
        )
        ok_btn.pack(side=tk.RIGHT)
    
    def _copy_details_qt(self):
        """Copy details to clipboard in Qt version."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.details)
        
        # Show feedback
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self.dialog,
            "Copied",
            "Details copied to clipboard"
        )
    
    def _copy_details_tk(self):
        """Copy details to clipboard in tkinter version."""
        self.dialog.clipboard_clear()
        self.dialog.clipboard_append(self.details)
        self.dialog.update()
        
        # Show feedback
        from tkinter import messagebox
        messagebox.showinfo("Copied", "Details copied to clipboard")
    
    def _report_issue_qt(self):
        """Handle report issue in Qt version."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self.dialog,
            "Report Issue",
            "To report this issue, please visit:\n"
            "https://github.com/your-repo/mcp-config-manager/issues\n\n"
            "Include the error details in your report."
        )
    
    def _report_issue_tk(self):
        """Handle report issue in tkinter version."""
        from tkinter import messagebox
        messagebox.showinfo(
            "Report Issue",
            "To report this issue, please visit:\n"
            "https://github.com/your-repo/mcp-config-manager/issues\n\n"
            "Include the error details in your report."
        )
    
    def show(self):
        """Show the dialog."""
        if USING_QT:
            self.dialog.exec()
        else:
            self.dialog.wait_window()
    
    @classmethod
    def show_error(cls, parent=None, title: str = "Error",
                  message: str = "", exception: Optional[Exception] = None):
        """Convenience method to show an error dialog.
        
        Args:
            parent: Parent widget/window
            title: Dialog title
            message: Error message
            exception: Optional exception to include in details
        """
        details = ""
        if exception:
            details = f"{type(exception).__name__}: {str(exception)}\n\n"
            details += traceback.format_exc()
        
        dialog = cls(parent, title, message, details, "error")
        dialog.show()
    
    @classmethod
    def show_warning(cls, parent=None, title: str = "Warning",
                    message: str = "", details: str = ""):
        """Convenience method to show a warning dialog.
        
        Args:
            parent: Parent widget/window
            title: Dialog title
            message: Warning message
            details: Optional details
        """
        dialog = cls(parent, title, message, details, "warning")
        dialog.show()
    
    @classmethod
    def show_info(cls, parent=None, title: str = "Information",
                 message: str = "", details: str = ""):
        """Convenience method to show an info dialog.
        
        Args:
            parent: Parent widget/window
            title: Dialog title
            message: Info message
            details: Optional details
        """
        dialog = cls(parent, title, message, details, "info")
        dialog.show()