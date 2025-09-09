"""Settings dialog for application preferences."""

from typing import Dict, Any, Optional, Callable
from enum import Enum

try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
        QPushButton, QDialogButtonBox, QLabel, QComboBox,
        QCheckBox, QSpinBox, QGroupBox, QFormLayout
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    USING_QT = True
    tk = None
    ttk = None
except ImportError:
    USING_QT = False
    QDialog = object
    QVBoxLayout = object
    QHBoxLayout = object
    QTabWidget = object
    QWidget = object
    QPushButton = object
    QDialogButtonBox = object
    QLabel = object
    QComboBox = object
    QCheckBox = object
    QSpinBox = object
    QGroupBox = object
    QFormLayout = object
    Qt = None
    pyqtSignal = None
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        tk = None
        ttk = None


class Theme(Enum):
    """Application theme options."""
    LIGHT = "Light"
    DARK = "Dark"
    SYSTEM = "System"


class SettingsDialog:
    """Dialog for configuring application settings."""
    
    def __init__(self, parent=None):
        """Initialize the Settings dialog.
        
        Args:
            parent: Parent widget/window
        """
        self.parent = parent
        self.settings: Dict[str, Any] = {}
        self.on_settings_changed_callbacks = []
        
        if USING_QT:
            self._init_qt()
        else:
            self._init_tk()
    
    def _init_qt(self):
        """Initialize Qt version of the dialog."""
        self.dialog = QDialog(self.parent)
        self.dialog.setWindowTitle("Settings")
        self.dialog.setModal(True)
        self.dialog.resize(600, 500)
        
        # Main layout
        layout = QVBoxLayout(self.dialog)
        
        # Tab widget for categories
        self.tabs = QTabWidget()
        
        # General tab
        general_tab = self._create_general_tab_qt()
        self.tabs.addTab(general_tab, "General")
        
        # Appearance tab
        appearance_tab = self._create_appearance_tab_qt()
        self.tabs.addTab(appearance_tab, "Appearance")
        
        # Behavior tab
        behavior_tab = self._create_behavior_tab_qt()
        self.tabs.addTab(behavior_tab, "Behavior")
        
        # Advanced tab
        advanced_tab = self._create_advanced_tab_qt()
        self.tabs.addTab(advanced_tab, "Advanced")
        
        layout.addWidget(self.tabs)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self._on_qt_accept)
        button_box.rejected.connect(self.dialog.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_qt_apply)
        
        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._on_qt_reset)
        button_box.addButton(reset_btn, QDialogButtonBox.ButtonRole.ResetRole)
        
        layout.addWidget(button_box)
    
    def _init_tk(self):
        """Initialize tkinter version of the dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Settings")
        self.dialog.geometry("600x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        
        # General tab
        general_tab = self._create_general_tab_tk()
        self.notebook.add(general_tab, text="General")
        
        # Appearance tab
        appearance_tab = self._create_appearance_tab_tk()
        self.notebook.add(appearance_tab, text="Appearance")
        
        # Behavior tab
        behavior_tab = self._create_behavior_tab_tk()
        self.notebook.add(behavior_tab, text="Behavior")
        
        # Advanced tab
        advanced_tab = self._create_advanced_tab_tk()
        self.notebook.add(advanced_tab, text="Advanced")
        
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Buttons
        reset_btn = ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self._on_tk_reset
        )
        reset_btn.pack(side=tk.LEFT)
        
        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        apply_btn = ttk.Button(
            button_frame,
            text="Apply",
            command=self._on_tk_apply
        )
        apply_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        ok_btn = ttk.Button(
            button_frame,
            text="OK",
            command=self._on_tk_accept
        )
        ok_btn.pack(side=tk.RIGHT)
    
    def _create_general_tab_qt(self) -> QWidget:
        """Create general settings tab for Qt."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Default mode group
        mode_group = QGroupBox("Default Mode")
        mode_layout = QFormLayout()
        
        self.default_mode_combo = QComboBox()
        self.default_mode_combo.addItems(["Claude Only", "Gemini Only", "Both"])
        mode_layout.addRow("Startup Mode:", self.default_mode_combo)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Backup settings
        backup_group = QGroupBox("Backup Settings")
        backup_layout = QFormLayout()
        
        self.auto_backup_check = QCheckBox("Enable automatic backups")
        backup_layout.addRow(self.auto_backup_check)
        
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 100)
        self.backup_count_spin.setValue(10)
        backup_layout.addRow("Max backups to keep:", self.backup_count_spin)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # File paths
        paths_group = QGroupBox("File Paths")
        paths_layout = QFormLayout()
        
        self.claude_path_label = QLabel("~/.claude.json")
        paths_layout.addRow("Claude config:", self.claude_path_label)
        
        self.gemini_path_label = QLabel("~/.gemini/settings.json")
        paths_layout.addRow("Gemini config:", self.gemini_path_label)
        
        self.presets_path_label = QLabel("~/.mcp_presets.json")
        paths_layout.addRow("Presets file:", self.presets_path_label)
        
        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)
        
        layout.addStretch()
        return widget
    
    def _create_general_tab_tk(self) -> ttk.Frame:
        """Create general settings tab for tkinter."""
        frame = ttk.Frame(self.notebook)
        
        # Default mode group
        mode_frame = ttk.LabelFrame(frame, text="Default Mode", padding="10")
        mode_frame.pack(fill=tk.X, pady=(10, 5), padx=10)
        
        ttk.Label(mode_frame, text="Startup Mode:").grid(row=0, column=0, sticky=tk.W)
        self.default_mode_var = tk.StringVar(value="Claude Only")
        mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.default_mode_var,
            values=["Claude Only", "Gemini Only", "Both"],
            state="readonly"
        )
        mode_combo.grid(row=0, column=1, padx=(10, 0))
        
        # Backup settings
        backup_frame = ttk.LabelFrame(frame, text="Backup Settings", padding="10")
        backup_frame.pack(fill=tk.X, pady=5, padx=10)
        
        self.auto_backup_var = tk.BooleanVar(value=True)
        auto_backup_check = ttk.Checkbutton(
            backup_frame,
            text="Enable automatic backups",
            variable=self.auto_backup_var
        )
        auto_backup_check.grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(backup_frame, text="Max backups to keep:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.backup_count_var = tk.IntVar(value=10)
        backup_spin = ttk.Spinbox(
            backup_frame,
            from_=1,
            to=100,
            textvariable=self.backup_count_var,
            width=10
        )
        backup_spin.grid(row=1, column=1, padx=(10, 0), pady=(5, 0))
        
        # File paths
        paths_frame = ttk.LabelFrame(frame, text="File Paths", padding="10")
        paths_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(paths_frame, text="Claude config:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(paths_frame, text="~/.claude.json").grid(row=0, column=1, padx=(10, 0))
        
        ttk.Label(paths_frame, text="Gemini config:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Label(paths_frame, text="~/.gemini/settings.json").grid(row=1, column=1, padx=(10, 0), pady=(5, 0))
        
        ttk.Label(paths_frame, text="Presets file:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Label(paths_frame, text="~/.mcp_presets.json").grid(row=2, column=1, padx=(10, 0), pady=(5, 0))
        
        return frame
    
    def _create_appearance_tab_qt(self) -> QWidget:
        """Create appearance settings tab for Qt."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Theme settings
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([t.value for t in Theme])
        theme_layout.addRow("Application Theme:", self.theme_combo)
        
        self.compact_mode_check = QCheckBox("Use compact mode")
        theme_layout.addRow(self.compact_mode_check)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Display settings
        display_group = QGroupBox("Display")
        display_layout = QFormLayout()
        
        self.show_status_check = QCheckBox("Show status bar")
        self.show_status_check.setChecked(True)
        display_layout.addRow(self.show_status_check)
        
        self.show_toolbar_check = QCheckBox("Show toolbar")
        self.show_toolbar_check.setChecked(True)
        display_layout.addRow(self.show_toolbar_check)
        
        self.show_icons_check = QCheckBox("Show icons in menus")
        self.show_icons_check.setChecked(True)
        display_layout.addRow(self.show_icons_check)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        layout.addStretch()
        return widget
    
    def _create_appearance_tab_tk(self) -> ttk.Frame:
        """Create appearance settings tab for tkinter."""
        frame = ttk.Frame(self.notebook)
        
        # Theme settings
        theme_frame = ttk.LabelFrame(frame, text="Theme", padding="10")
        theme_frame.pack(fill=tk.X, pady=(10, 5), padx=10)
        
        ttk.Label(theme_frame, text="Application Theme:").grid(row=0, column=0, sticky=tk.W)
        self.theme_var = tk.StringVar(value=Theme.SYSTEM.value)
        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=[t.value for t in Theme],
            state="readonly"
        )
        theme_combo.grid(row=0, column=1, padx=(10, 0))
        
        self.compact_mode_var = tk.BooleanVar(value=False)
        compact_check = ttk.Checkbutton(
            theme_frame,
            text="Use compact mode",
            variable=self.compact_mode_var
        )
        compact_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Display settings
        display_frame = ttk.LabelFrame(frame, text="Display", padding="10")
        display_frame.pack(fill=tk.X, pady=5, padx=10)
        
        self.show_status_var = tk.BooleanVar(value=True)
        status_check = ttk.Checkbutton(
            display_frame,
            text="Show status bar",
            variable=self.show_status_var
        )
        status_check.pack(anchor=tk.W)
        
        self.show_toolbar_var = tk.BooleanVar(value=True)
        toolbar_check = ttk.Checkbutton(
            display_frame,
            text="Show toolbar",
            variable=self.show_toolbar_var
        )
        toolbar_check.pack(anchor=tk.W)
        
        self.show_icons_var = tk.BooleanVar(value=True)
        icons_check = ttk.Checkbutton(
            display_frame,
            text="Show icons in menus",
            variable=self.show_icons_var
        )
        icons_check.pack(anchor=tk.W)
        
        return frame
    
    def _create_behavior_tab_qt(self) -> QWidget:
        """Create behavior settings tab for Qt."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Confirmation settings
        confirm_group = QGroupBox("Confirmations")
        confirm_layout = QVBoxLayout()
        
        self.confirm_disable_check = QCheckBox("Confirm before disabling servers")
        self.confirm_disable_check.setChecked(True)
        confirm_layout.addWidget(self.confirm_disable_check)
        
        self.confirm_preset_check = QCheckBox("Confirm before applying presets")
        self.confirm_preset_check.setChecked(True)
        confirm_layout.addWidget(self.confirm_preset_check)
        
        self.confirm_exit_check = QCheckBox("Confirm before exit with unsaved changes")
        self.confirm_exit_check.setChecked(True)
        confirm_layout.addWidget(self.confirm_exit_check)
        
        confirm_group.setLayout(confirm_layout)
        layout.addWidget(confirm_group)
        
        # Auto-save settings
        autosave_group = QGroupBox("Auto-save")
        autosave_layout = QFormLayout()
        
        self.autosave_check = QCheckBox("Enable auto-save")
        autosave_layout.addRow(self.autosave_check)
        
        self.autosave_interval_spin = QSpinBox()
        self.autosave_interval_spin.setRange(1, 60)
        self.autosave_interval_spin.setValue(5)
        self.autosave_interval_spin.setSuffix(" minutes")
        autosave_layout.addRow("Auto-save interval:", self.autosave_interval_spin)
        
        autosave_group.setLayout(autosave_layout)
        layout.addWidget(autosave_group)
        
        layout.addStretch()
        return widget
    
    def _create_behavior_tab_tk(self) -> ttk.Frame:
        """Create behavior settings tab for tkinter."""
        frame = ttk.Frame(self.notebook)
        
        # Confirmation settings
        confirm_frame = ttk.LabelFrame(frame, text="Confirmations", padding="10")
        confirm_frame.pack(fill=tk.X, pady=(10, 5), padx=10)
        
        self.confirm_disable_var = tk.BooleanVar(value=True)
        disable_check = ttk.Checkbutton(
            confirm_frame,
            text="Confirm before disabling servers",
            variable=self.confirm_disable_var
        )
        disable_check.pack(anchor=tk.W)
        
        self.confirm_preset_var = tk.BooleanVar(value=True)
        preset_check = ttk.Checkbutton(
            confirm_frame,
            text="Confirm before applying presets",
            variable=self.confirm_preset_var
        )
        preset_check.pack(anchor=tk.W)
        
        self.confirm_exit_var = tk.BooleanVar(value=True)
        exit_check = ttk.Checkbutton(
            confirm_frame,
            text="Confirm before exit with unsaved changes",
            variable=self.confirm_exit_var
        )
        exit_check.pack(anchor=tk.W)
        
        # Auto-save settings
        autosave_frame = ttk.LabelFrame(frame, text="Auto-save", padding="10")
        autosave_frame.pack(fill=tk.X, pady=5, padx=10)
        
        self.autosave_var = tk.BooleanVar(value=False)
        autosave_check = ttk.Checkbutton(
            autosave_frame,
            text="Enable auto-save",
            variable=self.autosave_var
        )
        autosave_check.grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(autosave_frame, text="Auto-save interval:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.autosave_interval_var = tk.IntVar(value=5)
        interval_spin = ttk.Spinbox(
            autosave_frame,
            from_=1,
            to=60,
            textvariable=self.autosave_interval_var,
            width=10
        )
        interval_spin.grid(row=1, column=1, padx=(10, 0), pady=(5, 0))
        ttk.Label(autosave_frame, text="minutes").grid(row=1, column=2, padx=(5, 0), pady=(5, 0))
        
        return frame
    
    def _create_advanced_tab_qt(self) -> QWidget:
        """Create advanced settings tab for Qt."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Validation settings
        validation_group = QGroupBox("Validation")
        validation_layout = QVBoxLayout()
        
        self.validate_on_save_check = QCheckBox("Validate configuration before saving")
        self.validate_on_save_check.setChecked(True)
        validation_layout.addWidget(self.validate_on_save_check)
        
        self.strict_validation_check = QCheckBox("Use strict validation rules")
        validation_layout.addWidget(self.strict_validation_check)
        
        validation_group.setLayout(validation_layout)
        layout.addWidget(validation_group)
        
        # Logging settings
        logging_group = QGroupBox("Logging")
        logging_layout = QFormLayout()
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        logging_layout.addRow("Log Level:", self.log_level_combo)
        
        self.log_to_file_check = QCheckBox("Log to file")
        logging_layout.addRow(self.log_to_file_check)
        
        logging_group.setLayout(logging_layout)
        layout.addWidget(logging_group)
        
        layout.addStretch()
        return widget
    
    def _create_advanced_tab_tk(self) -> ttk.Frame:
        """Create advanced settings tab for tkinter."""
        frame = ttk.Frame(self.notebook)
        
        # Validation settings
        validation_frame = ttk.LabelFrame(frame, text="Validation", padding="10")
        validation_frame.pack(fill=tk.X, pady=(10, 5), padx=10)
        
        self.validate_on_save_var = tk.BooleanVar(value=True)
        validate_check = ttk.Checkbutton(
            validation_frame,
            text="Validate configuration before saving",
            variable=self.validate_on_save_var
        )
        validate_check.pack(anchor=tk.W)
        
        self.strict_validation_var = tk.BooleanVar(value=False)
        strict_check = ttk.Checkbutton(
            validation_frame,
            text="Use strict validation rules",
            variable=self.strict_validation_var
        )
        strict_check.pack(anchor=tk.W)
        
        # Logging settings
        logging_frame = ttk.LabelFrame(frame, text="Logging", padding="10")
        logging_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(logging_frame, text="Log Level:").grid(row=0, column=0, sticky=tk.W)
        self.log_level_var = tk.StringVar(value="INFO")
        log_combo = ttk.Combobox(
            logging_frame,
            textvariable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            state="readonly"
        )
        log_combo.grid(row=0, column=1, padx=(10, 0))
        
        self.log_to_file_var = tk.BooleanVar(value=False)
        log_file_check = ttk.Checkbutton(
            logging_frame,
            text="Log to file",
            variable=self.log_to_file_var
        )
        log_file_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        return frame
    
    def _gather_settings_qt(self) -> Dict[str, Any]:
        """Gather settings from Qt widgets."""
        return {
            'general': {
                'default_mode': self.default_mode_combo.currentText(),
                'auto_backup': self.auto_backup_check.isChecked(),
                'backup_count': self.backup_count_spin.value()
            },
            'appearance': {
                'theme': self.theme_combo.currentText(),
                'compact_mode': self.compact_mode_check.isChecked(),
                'show_status_bar': self.show_status_check.isChecked(),
                'show_toolbar': self.show_toolbar_check.isChecked(),
                'show_icons': self.show_icons_check.isChecked()
            },
            'behavior': {
                'confirm_disable': self.confirm_disable_check.isChecked(),
                'confirm_preset': self.confirm_preset_check.isChecked(),
                'confirm_exit': self.confirm_exit_check.isChecked(),
                'autosave': self.autosave_check.isChecked(),
                'autosave_interval': self.autosave_interval_spin.value()
            },
            'advanced': {
                'validate_on_save': self.validate_on_save_check.isChecked(),
                'strict_validation': self.strict_validation_check.isChecked(),
                'log_level': self.log_level_combo.currentText(),
                'log_to_file': self.log_to_file_check.isChecked()
            }
        }
    
    def _gather_settings_tk(self) -> Dict[str, Any]:
        """Gather settings from tkinter widgets."""
        return {
            'general': {
                'default_mode': self.default_mode_var.get(),
                'auto_backup': self.auto_backup_var.get(),
                'backup_count': self.backup_count_var.get()
            },
            'appearance': {
                'theme': self.theme_var.get(),
                'compact_mode': self.compact_mode_var.get(),
                'show_status_bar': self.show_status_var.get(),
                'show_toolbar': self.show_toolbar_var.get(),
                'show_icons': self.show_icons_var.get()
            },
            'behavior': {
                'confirm_disable': self.confirm_disable_var.get(),
                'confirm_preset': self.confirm_preset_var.get(),
                'confirm_exit': self.confirm_exit_var.get(),
                'autosave': self.autosave_var.get(),
                'autosave_interval': self.autosave_interval_var.get()
            },
            'advanced': {
                'validate_on_save': self.validate_on_save_var.get(),
                'strict_validation': self.strict_validation_var.get(),
                'log_level': self.log_level_var.get(),
                'log_to_file': self.log_to_file_var.get()
            }
        }
    
    def _on_qt_accept(self):
        """Handle OK button in Qt version."""
        self.settings = self._gather_settings_qt()
        for callback in self.on_settings_changed_callbacks:
            callback(self.settings)
        self.dialog.accept()
    
    def _on_qt_apply(self):
        """Handle Apply button in Qt version."""
        self.settings = self._gather_settings_qt()
        for callback in self.on_settings_changed_callbacks:
            callback(self.settings)
    
    def _on_qt_reset(self):
        """Handle Reset button in Qt version."""
        # Reset to defaults
        self.default_mode_combo.setCurrentText("Claude Only")
        self.auto_backup_check.setChecked(True)
        self.backup_count_spin.setValue(10)
        self.theme_combo.setCurrentText(Theme.SYSTEM.value)
        self.compact_mode_check.setChecked(False)
        self.show_status_check.setChecked(True)
        self.show_toolbar_check.setChecked(True)
        self.show_icons_check.setChecked(True)
        self.confirm_disable_check.setChecked(True)
        self.confirm_preset_check.setChecked(True)
        self.confirm_exit_check.setChecked(True)
        self.autosave_check.setChecked(False)
        self.autosave_interval_spin.setValue(5)
        self.validate_on_save_check.setChecked(True)
        self.strict_validation_check.setChecked(False)
        self.log_level_combo.setCurrentText("INFO")
        self.log_to_file_check.setChecked(False)
    
    def _on_tk_accept(self):
        """Handle OK button in tkinter version."""
        self.settings = self._gather_settings_tk()
        for callback in self.on_settings_changed_callbacks:
            callback(self.settings)
        self.dialog.destroy()
    
    def _on_tk_apply(self):
        """Handle Apply button in tkinter version."""
        self.settings = self._gather_settings_tk()
        for callback in self.on_settings_changed_callbacks:
            callback(self.settings)
    
    def _on_tk_reset(self):
        """Handle Reset button in tkinter version."""
        # Reset to defaults
        self.default_mode_var.set("Claude Only")
        self.auto_backup_var.set(True)
        self.backup_count_var.set(10)
        self.theme_var.set(Theme.SYSTEM.value)
        self.compact_mode_var.set(False)
        self.show_status_var.set(True)
        self.show_toolbar_var.set(True)
        self.show_icons_var.set(True)
        self.confirm_disable_var.set(True)
        self.confirm_preset_var.set(True)
        self.confirm_exit_var.set(True)
        self.autosave_var.set(False)
        self.autosave_interval_var.set(5)
        self.validate_on_save_var.set(True)
        self.strict_validation_var.set(False)
        self.log_level_var.set("INFO")
        self.log_to_file_var.set(False)
    
    def on_settings_changed(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for when settings are changed.
        
        Args:
            callback: Function to call with settings dict
        """
        self.on_settings_changed_callbacks.append(callback)
    
    def show(self) -> Optional[Dict[str, Any]]:
        """Show the dialog and return the settings.
        
        Returns:
            Dictionary with settings or None if cancelled
        """
        if USING_QT:
            if self.dialog.exec() == QDialog.DialogCode.Accepted:
                return self.settings
        else:
            self.dialog.wait_window()
            return self.settings
        
        return None