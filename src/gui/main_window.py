"""
Main window for MCP Config Manager GUI.

This module provides the main application window with support for both
PyQt6 and tkinter frameworks.
"""

from typing import Optional
from . import GUI_FRAMEWORK


class MainWindow:
    """
    Main application window.
    
    Provides a unified interface that works with both PyQt6 and tkinter.
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the main window.
        
        Args:
            config_manager: ConfigManager instance for handling configurations
        """
        self.config_manager = config_manager
        self.window = None
        
    def setup(self):
        """Set up the main window based on available framework."""
        if GUI_FRAMEWORK == "pyqt6":
            self._setup_pyqt6()
        elif GUI_FRAMEWORK == "tkinter":
            self._setup_tkinter()
        else:
            raise RuntimeError("No GUI framework available")
    
    def _setup_pyqt6(self):
        """Set up PyQt6-based window."""
        from PyQt6 import QtWidgets
        
        class PyQt6MainWindow(QtWidgets.QMainWindow):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("MCP Config Manager")
                self.setGeometry(100, 100, 800, 600)
                
                # Central widget
                central_widget = QtWidgets.QWidget()
                self.setCentralWidget(central_widget)
                
                # Basic layout
                layout = QtWidgets.QVBoxLayout(central_widget)
                
                # Placeholder label
                label = QtWidgets.QLabel("MCP Config Manager - GUI Mode")
                label.setStyleSheet("font-size: 18px; padding: 20px;")
                layout.addWidget(label)
                
                # Server list placeholder
                server_list = QtWidgets.QListWidget()
                layout.addWidget(server_list)
                
                # Button bar
                button_layout = QtWidgets.QHBoxLayout()
                enable_btn = QtWidgets.QPushButton("Enable")
                disable_btn = QtWidgets.QPushButton("Disable")
                add_btn = QtWidgets.QPushButton("Add Server")
                button_layout.addWidget(enable_btn)
                button_layout.addWidget(disable_btn)
                button_layout.addWidget(add_btn)
                layout.addLayout(button_layout)
        
        self.window = PyQt6MainWindow()
        
    def _setup_tkinter(self):
        """Set up tkinter-based window."""
        import tkinter as tk
        from tkinter import ttk
        
        self.window = tk.Tk()
        self.window.title("MCP Config Manager")
        self.window.geometry("800x600")
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title label
        title_label = ttk.Label(main_frame, text="MCP Config Manager - GUI Mode", 
                                font=('', 18))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Server list
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        server_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        server_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=server_listbox.yview)
        
        # Buttons
        enable_btn = ttk.Button(main_frame, text="Enable")
        enable_btn.grid(row=2, column=0, padx=5, pady=10)
        
        disable_btn = ttk.Button(main_frame, text="Disable")
        disable_btn.grid(row=2, column=1, padx=5, pady=10)
        
        add_btn = ttk.Button(main_frame, text="Add Server")
        add_btn.grid(row=2, column=2, padx=5, pady=10)
        
        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(1, weight=1)
    
    def show(self):
        """Show the main window."""
        if GUI_FRAMEWORK == "pyqt6":
            self.window.show()
        elif GUI_FRAMEWORK == "tkinter":
            self.window.mainloop()
    
    def run(self):
        """Run the GUI application."""
        self.setup()
        self.show()