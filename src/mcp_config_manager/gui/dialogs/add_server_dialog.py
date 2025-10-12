"""Dialog for adding new servers via JSON paste."""

import json
import re
from typing import Dict, Any, Optional, Callable

try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
        QPushButton, QDialogButtonBox, QMessageBox, QGroupBox
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
    USING_QT = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    USING_QT = False

from ...parsers.cli_parser import ClaudeCliParser


class AddServerDialog:
    """Dialog for adding new MCP servers via JSON configuration."""
    
    def __init__(self, parent=None):
        """Initialize the Add Server dialog.

        Args:
            parent: Parent widget/window
        """
        self.parent = parent
        self.result = None
        self.on_server_added_callbacks = []
        self.claude_enabled = True  # Default to enabled for both
        self.gemini_enabled = True

        if USING_QT:
            self._init_qt()
        else:
            self._init_tk()
    
    def _init_qt(self):
        """Initialize Qt version of the dialog."""
        self.dialog = QDialog(self.parent)
        self.dialog.setWindowTitle("Add Server")
        self.dialog.setModal(True)
        self.dialog.resize(600, 500)
        
        # Main layout
        layout = QVBoxLayout(self.dialog)
        
        # Instructions
        instructions = QLabel(
            "Paste the server JSON configuration or Claude CLI command below.\n"
            "JSON Format: {\"server_name\": {\"command\": \"...\", \"args\": [...]}}\n"
            "CLI Format: claude mcp add servername -- npx -y package-name"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # JSON input area
        input_group = QGroupBox("Server Configuration (JSON)")
        input_layout = QVBoxLayout()
        
        self.json_input = QTextEdit()
        self.json_input.setFont(QFont("Courier", 10))
        self.json_input.setPlaceholderText(
            '{\n'
            '  "my-server": {\n'
            '    "command": "node",\n'
            '    "args": ["path/to/server.js"],\n'
            '    "env": {"NODE_ENV": "production"}\n'
            '  }\n'
            '}'
        )
        input_layout.addWidget(self.json_input)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Client enablement checkboxes
        from PyQt6.QtWidgets import QCheckBox
        enablement_group = QGroupBox("Enable for:")
        enablement_layout = QHBoxLayout()

        self.claude_checkbox = QCheckBox("Claude")
        self.claude_checkbox.setChecked(True)  # Default to enabled
        self.claude_checkbox.stateChanged.connect(self._on_client_enablement_changed)
        enablement_layout.addWidget(self.claude_checkbox)

        self.gemini_checkbox = QCheckBox("Gemini")
        self.gemini_checkbox.setChecked(True)  # Default to enabled
        self.gemini_checkbox.stateChanged.connect(self._on_client_enablement_changed)
        enablement_layout.addWidget(self.gemini_checkbox)

        enablement_layout.addStretch()
        enablement_group.setLayout(enablement_layout)
        layout.addWidget(enablement_group)

        # Conversion options
        options_group = QGroupBox("Options:")
        options_layout = QVBoxLayout()

        checkbox_layout = QHBoxLayout()
        self.convert_mcp_remote_checkbox = QCheckBox("Convert mcp-remote to native SSE")
        self.convert_mcp_remote_checkbox.setChecked(False)  # Default to NOT converting
        self.convert_mcp_remote_checkbox.setToolTip(
            "When enabled, commands using 'npx mcp-remote <url>' will be converted to native SSE format.\n"
            "When disabled (default), the original command structure is preserved."
        )
        checkbox_layout.addWidget(self.convert_mcp_remote_checkbox)
        checkbox_layout.addStretch()
        options_layout.addLayout(checkbox_layout)

        # Add explanation text
        help_label = QLabel(
            "ℹ️  When enabled: npx mcp-remote commands → {type: 'sse', url: '...'}\n"
            "   When disabled (default): keeps original → {command: 'npx', args: [...]}"
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 10px; padding-left: 20px;")
        options_layout.addWidget(help_label)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Validation status
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_qt_accept)
        button_box.rejected.connect(self.dialog.reject)
        
        # Validate button
        validate_btn = QPushButton("Validate JSON")
        validate_btn.clicked.connect(lambda: self._validate_json_qt(cleanup_on_validate=True))
        button_box.addButton(validate_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        layout.addWidget(button_box)
        
        # Connect text change for live validation
        self.json_input.textChanged.connect(self._on_qt_text_changed)
    
    def _init_tk(self):
        """Initialize tkinter version of the dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Add Server")
        self.dialog.geometry("600x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        instructions = ttk.Label(
            main_frame,
            text="Paste the server JSON configuration or Claude CLI command below.\n"
                 "JSON Format: {\"server_name\": {\"command\": \"...\", \"args\": [...]}}\n"
                 "CLI Format: claude mcp add servername -- npx -y package-name",
            wraplength=550
        )
        instructions.pack(pady=(0, 10))
        
        # JSON input area
        input_frame = ttk.LabelFrame(main_frame, text="Server Configuration (JSON)", padding="5")
        input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.json_input = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            width=60,
            height=15,
            font=("Courier", 10)
        )
        self.json_input.pack(fill=tk.BOTH, expand=True)
        
        # Add placeholder text
        placeholder = (
            '{\n'
            '  "my-server": {\n'
            '    "command": "node",\n'
            '    "args": ["path/to/server.js"],\n'
            '    "env": {"NODE_ENV": "production"}\n'
            '  }\n'
            '}'
        )
        self.json_input.insert("1.0", placeholder)
        self.json_input.tag_add("placeholder", "1.0", "end")
        self.json_input.tag_config("placeholder", foreground="gray")
        
        # Clear placeholder on focus
        def clear_placeholder(event):
            if "placeholder" in self.json_input.tag_names("1.0"):
                self.json_input.delete("1.0", "end")
                self.json_input.tag_remove("placeholder", "1.0", "end")
        
        self.json_input.bind("<FocusIn>", clear_placeholder)
        
        # Client enablement checkboxes
        enablement_frame = ttk.LabelFrame(main_frame, text="Enable for:", padding="5")
        enablement_frame.pack(fill=tk.X, pady=(0, 10))

        self.claude_var = tk.BooleanVar(value=True)  # Default to enabled
        self.claude_checkbox = ttk.Checkbutton(
            enablement_frame,
            text="Claude",
            variable=self.claude_var,
            command=self._on_client_enablement_changed
        )
        self.claude_checkbox.pack(side=tk.LEFT, padx=(0, 10))

        self.gemini_var = tk.BooleanVar(value=True)  # Default to enabled
        self.gemini_checkbox = ttk.Checkbutton(
            enablement_frame,
            text="Gemini",
            variable=self.gemini_var,
            command=self._on_client_enablement_changed
        )
        self.gemini_checkbox.pack(side=tk.LEFT)

        # Conversion options
        options_frame = ttk.LabelFrame(main_frame, text="Options:", padding="5")
        options_frame.pack(fill=tk.X, pady=(0, 10))

        self.convert_mcp_remote_var = tk.BooleanVar(value=False)  # Default to NOT converting
        self.convert_mcp_remote_checkbox = ttk.Checkbutton(
            options_frame,
            text="Convert mcp-remote to native SSE",
            variable=self.convert_mcp_remote_var
        )
        self.convert_mcp_remote_checkbox.pack(anchor=tk.W)

        # Add explanation text
        help_text = ttk.Label(
            options_frame,
            text="ℹ️  When enabled: npx mcp-remote commands → {type: 'sse', url: '...'}\n"
                 "   When disabled (default): keeps original → {command: 'npx', args: [...]}",
            foreground="gray",
            font=("TkDefaultFont", 9)
        )
        help_text.pack(anchor=tk.W, padx=(20, 0), pady=(5, 0))

        # Validation status
        self.status_label = ttk.Label(main_frame, text="", foreground="red")
        self.status_label.pack(pady=(0, 10))

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Buttons
        validate_btn = ttk.Button(
            button_frame,
            text="Validate JSON",
            command=lambda: self._validate_json_tk(cleanup_on_validate=True)
        )
        validate_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        ok_btn = ttk.Button(
            button_frame,
            text="Add Server",
            command=self._on_tk_accept
        )
        ok_btn.pack(side=tk.RIGHT)
        
        # Bind text change for live validation
        self.json_input.bind("<KeyRelease>", self._on_tk_text_changed)
    
    def _cleanup_json_input(self, json_text: str) -> str:
        """Clean up and format messy JSON input.

        Also handles CLI commands and converts them to JSON.

        Args:
            json_text: Raw JSON input that might be malformed, or a CLI command

        Returns:
            Cleaned up JSON string
        """
        if not json_text.strip():
            return json_text

        # Check if this is a CLI command first
        if ClaudeCliParser.is_cli_command(json_text):
            try:
                # Get the convert_mcp_remote preference
                convert_mcp_remote = False
                if USING_QT and hasattr(self, 'convert_mcp_remote_checkbox'):
                    convert_mcp_remote = self.convert_mcp_remote_checkbox.isChecked()
                elif hasattr(self, 'convert_mcp_remote_var'):
                    convert_mcp_remote = self.convert_mcp_remote_var.get()

                # Parse the CLI command to JSON
                parsed_config = ClaudeCliParser.parse_cli_command(json_text,
                                                                   convert_mcp_remote=convert_mcp_remote)
                return json.dumps(parsed_config, indent=2, ensure_ascii=False)
            except ValueError as e:
                # If CLI parsing fails, let it fall through to JSON parsing
                # (maybe it's a JSON that happens to start with 'claude')
                pass

        # Remove escape characters like \\ at the end
        json_text = re.sub(r'\\+$', '', json_text.strip())

        # Remove extra escape characters in the middle
        json_text = re.sub(r'\\\\', '', json_text)

        # Remove extra braces or brackets at the end that might be malformed
        json_text = re.sub(r'[}\]]+\\*$', '', json_text)

        # Try to parse the JSON as-is first
        try:
            # If it's valid JSON, just reformat it nicely
            parsed = json.loads(json_text)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pass

        # If it's not wrapped in outer braces, try to detect if it's a server config
        # and wrap it appropriately
        cleaned_text = json_text.strip()
        if not cleaned_text.startswith('{') or not cleaned_text.endswith('}'):
            # Look for server name pattern at the start (e.g., "playwright": {)
            server_pattern = r'^"([^"]+)":\s*\{'
            match = re.match(server_pattern, cleaned_text)

            if match:
                # It looks like a server config, wrap it in outer braces
                # Make sure the closing brace matches the opening structure
                json_text = '{\n' + cleaned_text + '\n}'
            else:
                # Try to add outer braces anyway and see if it parses
                json_text = '{\n' + cleaned_text + '\n}'

        # Try to parse again after cleanup
        try:
            parsed = json.loads(json_text)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            # If still failing, try some more aggressive cleanup
            # Remove trailing commas
            json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)

            # Fix common bracket/brace issues
            json_text = re.sub(r'}\s*{', '},{', json_text)
            json_text = re.sub(r']\s*\[', '],[', json_text)

            # Try to fix missing closing braces by counting
            open_braces = json_text.count('{')
            close_braces = json_text.count('}')
            if open_braces > close_braces:
                json_text += '}' * (open_braces - close_braces)

            # Try one more time
            try:
                parsed = json.loads(json_text)
                return json.dumps(parsed, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                # Return original if we can't fix it
                return json_text
    
    def _validate_json_qt(self, cleanup_on_validate: bool = False) -> bool:
        """Validate JSON input for Qt version.
        
        Args:
            cleanup_on_validate: If True, attempt to cleanup the JSON first
        """
        json_text = self.json_input.toPlainText().strip()
        
        if not json_text or json_text == self.json_input.placeholderText():
            self.status_label.setText("Please enter server configuration")
            self.status_label.setStyleSheet("color: orange;")
            return False
        
        # If cleanup is requested, try to clean up the JSON first
        if cleanup_on_validate:
            # Check if original text was a CLI command
            was_cli_command = ClaudeCliParser.is_cli_command(json_text)

            cleaned_json = self._cleanup_json_input(json_text)
            if cleaned_json != json_text:
                # Update the text field with cleaned JSON
                self.json_input.setPlainText(cleaned_json)
                json_text = cleaned_json

                # Provide appropriate feedback
                if was_cli_command:
                    self.status_label.setText("✓ CLI command converted to JSON")
                    self.status_label.setStyleSheet("color: blue;")
                else:
                    self.status_label.setText("JSON cleaned up and formatted")
                    self.status_label.setStyleSheet("color: blue;")
        
        try:
            config = json.loads(json_text)
            
            # Validate structure
            if not isinstance(config, dict):
                self.status_label.setText("JSON must be an object")
                self.status_label.setStyleSheet("color: red;")
                return False
            
            if not config:
                self.status_label.setText("JSON must contain at least one server")
                self.status_label.setStyleSheet("color: red;")
                return False
            
            # Validate each server
            for name, server in config.items():
                if not isinstance(server, dict):
                    self.status_label.setText(f"Server '{name}' must be an object")
                    self.status_label.setStyleSheet("color: red;")
                    return False

                # Skip _client_enablement metadata
                if name == '_client_enablement':
                    continue

                # Check if it's an SSE/HTTP server (requires type and url)
                server_type = server.get('type')
                if server_type in ['sse', 'http']:
                    if 'url' not in server:
                        self.status_label.setText(f"Server '{name}' with type '{server_type}' missing 'url' field")
                        self.status_label.setStyleSheet("color: red;")
                        return False
                # Otherwise it's a stdio server (requires command)
                else:
                    if 'command' not in server:
                        self.status_label.setText(f"Server '{name}' missing 'command' field")
                        self.status_label.setStyleSheet("color: red;")
                        return False
            
            self.status_label.setText("✓ Valid JSON configuration")
            self.status_label.setStyleSheet("color: green;")
            return True
            
        except json.JSONDecodeError as e:
            self.status_label.setText(f"Invalid JSON: {str(e)}. Click 'Validate JSON' button below to fix.")
            self.status_label.setStyleSheet("color: red;")
            return False
    
    def _validate_json_tk(self, cleanup_on_validate: bool = False) -> bool:
        """Validate JSON input for tkinter version.
        
        Args:
            cleanup_on_validate: If True, attempt to cleanup the JSON first
        """
        json_text = self.json_input.get("1.0", "end").strip()
        
        # Check if it's placeholder text
        if not json_text or "placeholder" in self.json_input.tag_names("1.0"):
            self.status_label.config(text="Please enter server configuration", foreground="orange")
            return False
        
        # If cleanup is requested, try to clean up the JSON first
        if cleanup_on_validate:
            # Check if original text was a CLI command
            was_cli_command = ClaudeCliParser.is_cli_command(json_text)

            cleaned_json = self._cleanup_json_input(json_text)
            if cleaned_json != json_text:
                # Update the text field with cleaned JSON
                self.json_input.delete("1.0", "end")
                self.json_input.insert("1.0", cleaned_json)
                json_text = cleaned_json

                # Provide appropriate feedback
                if was_cli_command:
                    self.status_label.config(text="✓ CLI command converted to JSON", foreground="blue")
                else:
                    self.status_label.config(text="JSON cleaned up and formatted", foreground="blue")
        
        try:
            config = json.loads(json_text)
            
            # Validate structure
            if not isinstance(config, dict):
                self.status_label.config(text="JSON must be an object", foreground="red")
                return False
            
            if not config:
                self.status_label.config(text="JSON must contain at least one server", foreground="red")
                return False
            
            # Validate each server
            for name, server in config.items():
                if not isinstance(server, dict):
                    self.status_label.config(text=f"Server '{name}' must be an object", foreground="red")
                    return False

                # Skip _client_enablement metadata
                if name == '_client_enablement':
                    continue

                # Check if it's an SSE/HTTP server (requires type and url)
                server_type = server.get('type')
                if server_type in ['sse', 'http']:
                    if 'url' not in server:
                        self.status_label.config(text=f"Server '{name}' with type '{server_type}' missing 'url' field", foreground="red")
                        return False
                # Otherwise it's a stdio server (requires command)
                else:
                    if 'command' not in server:
                        self.status_label.config(text=f"Server '{name}' missing 'command' field", foreground="red")
                        return False
            
            self.status_label.config(text="✓ Valid JSON configuration", foreground="green")
            return True
            
        except json.JSONDecodeError as e:
            self.status_label.config(text=f"Invalid JSON: {str(e)}. Click 'Validate JSON' button below to fix.", foreground="red")
            return False
    
    def _on_qt_text_changed(self):
        """Handle text change in Qt version."""
        # Provide live validation feedback
        if self.json_input.toPlainText().strip():
            self._validate_json_qt()
    
    def _on_tk_text_changed(self, event):
        """Handle text change in tkinter version."""
        # Provide live validation feedback
        if self.json_input.get("1.0", "end").strip():
            self._validate_json_tk()
    
    def _on_client_enablement_changed(self):
        """Handle client enablement checkbox change."""
        if USING_QT:
            self.claude_enabled = self.claude_checkbox.isChecked()
            self.gemini_enabled = self.gemini_checkbox.isChecked()
        else:
            self.claude_enabled = self.claude_var.get()
            self.gemini_enabled = self.gemini_var.get()

    def _on_qt_accept(self):
        """Handle accept action in Qt version."""
        if self._validate_json_qt():
            json_text = self.json_input.toPlainText().strip()
            self.result = json.loads(json_text)

            # Add client enablement info to result
            self.result['_client_enablement'] = {
                'claude': self.claude_enabled,
                'gemini': self.gemini_enabled
            }

            # Notify callbacks
            for callback in self.on_server_added_callbacks:
                callback(self.result)

            self.dialog.accept()
        else:
            QMessageBox.warning(
                self.dialog,
                "Invalid Configuration",
                "Please fix the JSON configuration before proceeding."
            )
    
    def _on_tk_accept(self):
        """Handle accept action in tkinter version."""
        if self._validate_json_tk():
            json_text = self.json_input.get("1.0", "end").strip()
            self.result = json.loads(json_text)

            # Add client enablement info to result
            self.result['_client_enablement'] = {
                'claude': self.claude_enabled,
                'gemini': self.gemini_enabled
            }

            # Notify callbacks
            for callback in self.on_server_added_callbacks:
                callback(self.result)

            self.dialog.destroy()
        else:
            messagebox.showwarning(
                "Invalid Configuration",
                "Please fix the JSON configuration before proceeding."
            )
    
    def on_server_added(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for when server is added.
        
        Args:
            callback: Function to call with server config
        """
        self.on_server_added_callbacks.append(callback)
    
    def show(self) -> Optional[Dict[str, Any]]:
        """Show the dialog and return the result.
        
        Returns:
            Dictionary with server configuration or None if cancelled
        """
        if USING_QT:
            self.dialog.exec()
            return self.result
        else:
            self.dialog.wait_window()
            return self.result
    
    def get_server_json(self) -> Optional[Dict[str, Any]]:
        """Get the server JSON configuration.
        
        Returns:
            Dictionary with server configuration or None if cancelled
        """
        return self.result
    
    def set_initial_json(self, json_text: str):
        """Set initial JSON text in the input field.
        
        Args:
            json_text: JSON string to populate
        """
        if USING_QT:
            self.json_input.setPlainText(json_text)
        else:
            self.json_input.delete("1.0", "end")
            self.json_input.insert("1.0", json_text)