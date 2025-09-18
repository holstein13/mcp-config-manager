"""Project Server Consolidation Wizard for MCP Config Manager

A multi-step wizard to guide users through discovering and consolidating
project-specific MCP servers into the global configuration.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Import Qt or fallback to tkinter
try:
    from PyQt6.QtWidgets import (
        QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QProgressBar, QTreeWidget, QTreeWidgetItem,
        QCheckBox, QRadioButton, QButtonGroup, QTextEdit,
        QListWidget, QListWidgetItem, QGroupBox, QSplitter,
        QMessageBox, QFileDialog, QApplication
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor
    USE_QT = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, scrolledtext
    import threading
    USE_QT = False


@dataclass
class ConflictResolution:
    """Represents how to resolve a server name conflict"""
    server_name: str
    project_path: str
    strategy: str  # 'skip', 'replace', 'rename', 'merge'
    new_name: Optional[str] = None  # For 'rename' strategy


@dataclass
class ConsolidationPlan:
    """Represents the planned consolidation actions"""
    servers_to_promote: List[Dict[str, Any]]
    conflicts: List[ConflictResolution]
    backup_path: Optional[str] = None
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConsolidationPlan':
        """Create from dictionary"""
        if 'timestamp' in data and data['timestamp']:
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        conflicts = [ConflictResolution(**c) for c in data.get('conflicts', [])]
        return cls(
            servers_to_promote=data.get('servers_to_promote', []),
            conflicts=conflicts,
            backup_path=data.get('backup_path'),
            timestamp=data.get('timestamp')
        )


if USE_QT:

    class DiscoveryWorker(QThread):
        """Background worker for project discovery"""
        progress = pyqtSignal(int, str)  # percent, message
        finished = pyqtSignal(dict)  # discovered servers
        error = pyqtSignal(str)

        def __init__(self, discovery_service):
            super().__init__()
            self.discovery_service = discovery_service

        def run(self):
            """Run discovery in background"""
            try:
                def progress_callback(current, total, message):
                    percent = int((current / total) * 100) if total > 0 else 0
                    self.progress.emit(percent, message)

                servers = self.discovery_service.scan_projects(
                    progress_callback=progress_callback
                )
                self.finished.emit(servers)
            except Exception as e:
                self.error.emit(str(e))


    class ScanPage(QWizardPage):
        """Step 1: Scan and discover all project servers"""

        def __init__(self, discovery_service, parent=None):
            super().__init__(parent)
            self.discovery_service = discovery_service
            self.discovered_servers = {}
            self.setTitle("Discover Project Servers")
            self.setSubTitle("Scanning your system for project-specific MCP server configurations...")

            # Layout
            layout = QVBoxLayout()
            self.setLayout(layout)

            # Progress bar
            self.progress_bar = QProgressBar()
            layout.addWidget(self.progress_bar)

            # Status label
            self.status_label = QLabel("Preparing to scan...")
            layout.addWidget(self.status_label)

            # Results summary
            self.results_group = QGroupBox("Discovery Results")
            results_layout = QVBoxLayout()
            self.results_group.setLayout(results_layout)

            self.results_text = QTextEdit()
            self.results_text.setReadOnly(True)
            self.results_text.setMaximumHeight(200)
            results_layout.addWidget(self.results_text)

            layout.addWidget(self.results_group)
            self.results_group.setVisible(False)

            # Start scan button
            self.scan_button = QPushButton("Start Scan")
            self.scan_button.clicked.connect(self.start_scan)
            layout.addWidget(self.scan_button)

            layout.addStretch()

            # Worker thread
            self.worker = None

        def initializePage(self):
            """Called when page is shown"""
            super().initializePage()
            # Auto-start scan
            QTimer.singleShot(100, self.start_scan)

        def start_scan(self):
            """Start the discovery scan"""
            self.scan_button.setEnabled(False)
            self.progress_bar.setValue(0)
            self.status_label.setText("Scanning for project configurations...")

            # Create and start worker
            self.worker = DiscoveryWorker(self.discovery_service)
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.scan_complete)
            self.worker.error.connect(self.scan_error)
            self.worker.start()

        def update_progress(self, percent, message):
            """Update progress display"""
            self.progress_bar.setValue(percent)
            self.status_label.setText(message)

        def scan_complete(self, servers):
            """Handle scan completion"""
            self.discovered_servers = servers
            self.scan_button.setEnabled(True)
            self.scan_button.setText("Rescan")

            # Show results
            self.results_group.setVisible(True)

            # Count servers
            total_servers = sum(len(s) for s in servers.values())
            project_count = len(servers)

            # Build summary
            summary = f"Found {total_servers} servers across {project_count} projects:\n\n"

            for project_path, project_servers in servers.items():
                project_name = Path(project_path).name
                summary += f"📁 {project_name} ({len(project_servers)} servers)\n"
                for server_name in project_servers[:3]:  # Show first 3
                    summary += f"   • {server_name}\n"
                if len(project_servers) > 3:
                    summary += f"   ... and {len(project_servers) - 3} more\n"
                summary += "\n"

            self.results_text.setPlainText(summary)
            self.status_label.setText(f"Discovery complete! Found {total_servers} servers.")
            self.completeChanged.emit()

        def scan_error(self, error_msg):
            """Handle scan error"""
            self.scan_button.setEnabled(True)
            self.status_label.setText(f"Error: {error_msg}")
            QMessageBox.critical(self, "Scan Error", f"Failed to scan projects:\n{error_msg}")

        def isComplete(self):
            """Check if page is complete"""
            return bool(self.discovered_servers)


    class ConflictPage(QWizardPage):
        """Step 2: Review and resolve conflicts"""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setTitle("Resolve Conflicts")
            self.setSubTitle("Some servers exist in multiple locations. Choose how to handle conflicts.")

            # Store resolutions
            self.resolutions = []

            # Layout
            layout = QVBoxLayout()
            self.setLayout(layout)

            # Conflicts tree
            self.conflicts_tree = QTreeWidget()
            self.conflicts_tree.setHeaderLabels(["Server/Location", "Resolution"])
            self.conflicts_tree.itemChanged.connect(self.on_resolution_changed)
            layout.addWidget(self.conflicts_tree)

            # Resolution strategy group
            strategy_group = QGroupBox("Default Resolution Strategy")
            strategy_layout = QHBoxLayout()
            strategy_group.setLayout(strategy_layout)

            self.skip_radio = QRadioButton("Skip")
            self.replace_radio = QRadioButton("Replace")
            self.rename_radio = QRadioButton("Rename")
            self.replace_radio.setChecked(True)

            strategy_layout.addWidget(self.skip_radio)
            strategy_layout.addWidget(self.replace_radio)
            strategy_layout.addWidget(self.rename_radio)

            apply_button = QPushButton("Apply to All")
            apply_button.clicked.connect(self.apply_strategy_to_all)
            strategy_layout.addWidget(apply_button)

            layout.addWidget(strategy_group)

        def initializePage(self):
            """Called when page is shown"""
            super().initializePage()
            self.populate_conflicts()

        def populate_conflicts(self):
            """Populate the conflicts tree"""
            self.conflicts_tree.clear()
            wizard = self.wizard()

            # Get discovered servers from scan page
            discovered = wizard.scan_page.discovered_servers

            # Find conflicts (servers that exist in multiple places)
            server_locations = {}
            for project_path, servers in discovered.items():
                for server_name, config in servers.items():
                    if server_name not in server_locations:
                        server_locations[server_name] = []
                    server_locations[server_name].append(project_path)

            # Check against global config
            try:
                global_servers = wizard.server_manager.list_all_servers(mode='claude')
                for server in global_servers:
                    if isinstance(server, dict):
                        name = server.get('name')
                    else:
                        name = server
                    if name in server_locations:
                        server_locations[name].insert(0, 'global')
            except:
                pass

            # Add conflicts to tree
            self.resolutions.clear()
            for server_name, locations in server_locations.items():
                if len(locations) > 1:
                    # This is a conflict
                    server_item = QTreeWidgetItem([server_name, ""])
                    server_item.setFont(0, QFont("", -1, QFont.Weight.Bold))

                    for location in locations:
                        loc_name = "Global" if location == 'global' else Path(location).name
                        loc_item = QTreeWidgetItem([f"  📁 {loc_name}", "Replace"])
                        loc_item.setData(0, Qt.ItemDataRole.UserRole, {
                            'server': server_name,
                            'location': location
                        })
                        server_item.addChild(loc_item)

                    self.conflicts_tree.addTopLevelItem(server_item)
                    server_item.setExpanded(True)

                    # Create resolution
                    resolution = ConflictResolution(
                        server_name=server_name,
                        project_path=locations[0] if locations[0] != 'global' else locations[1],
                        strategy='replace'
                    )
                    self.resolutions.append(resolution)

            if not self.resolutions:
                # No conflicts
                no_conflicts = QTreeWidgetItem(["No conflicts found! ✅", ""])
                self.conflicts_tree.addTopLevelItem(no_conflicts)

            self.completeChanged.emit()

        def on_resolution_changed(self, item, column):
            """Handle resolution change"""
            if column == 1:
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data:
                    # Update resolution
                    server_name = data['server']
                    new_strategy = item.text(1).lower()

                    for resolution in self.resolutions:
                        if resolution.server_name == server_name:
                            resolution.strategy = new_strategy
                            if new_strategy == 'rename':
                                resolution.new_name = f"{server_name}_project"
                            break

        def apply_strategy_to_all(self):
            """Apply selected strategy to all conflicts"""
            if self.skip_radio.isChecked():
                strategy = "skip"
            elif self.replace_radio.isChecked():
                strategy = "replace"
            else:
                strategy = "rename"

            # Update all resolutions
            for resolution in self.resolutions:
                resolution.strategy = strategy
                if strategy == 'rename':
                    resolution.new_name = f"{resolution.server_name}_project"

            # Update tree display
            for i in range(self.conflicts_tree.topLevelItemCount()):
                item = self.conflicts_tree.topLevelItem(i)
                for j in range(item.childCount()):
                    child = item.child(j)
                    child.setText(1, strategy.capitalize())

        def isComplete(self):
            """Check if page is complete"""
            return True  # Always complete, conflicts are optional


    class SelectionPage(QWizardPage):
        """Step 3: Select servers to promote"""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setTitle("Select Servers")
            self.setSubTitle("Choose which servers to promote to the global configuration.")

            # Selected servers
            self.selected_servers = []

            # Layout
            layout = QVBoxLayout()
            self.setLayout(layout)

            # Select all checkbox
            self.select_all = QCheckBox("Select All")
            self.select_all.clicked.connect(self.toggle_select_all)
            layout.addWidget(self.select_all)

            # Servers tree
            self.servers_tree = QTreeWidget()
            self.servers_tree.setHeaderLabels(["Server", "Project", "Status"])
            self.servers_tree.itemChanged.connect(self.on_selection_changed)
            layout.addWidget(self.servers_tree)

        def initializePage(self):
            """Called when page is shown"""
            super().initializePage()
            self.populate_servers()

        def populate_servers(self):
            """Populate the servers tree"""
            self.servers_tree.clear()
            self.selected_servers.clear()
            wizard = self.wizard()

            # Get discovered servers
            discovered = wizard.scan_page.discovered_servers
            resolutions = wizard.conflict_page.resolutions

            # Build conflict lookup
            conflict_lookup = {r.server_name: r for r in resolutions}

            # Add servers to tree
            for project_path, servers in discovered.items():
                project_name = Path(project_path).name

                for server_name, config in servers.items():
                    item = QTreeWidgetItem()
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

                    # Check if this is a conflict
                    if server_name in conflict_lookup:
                        resolution = conflict_lookup[server_name]
                        if resolution.strategy == 'skip':
                            item.setText(0, f"{server_name} (skipped)")
                            item.setText(2, "⏭️ Skip")
                            item.setCheckState(0, Qt.CheckState.Unchecked)
                            item.setDisabled(True)
                        elif resolution.strategy == 'rename':
                            item.setText(0, f"{server_name} → {resolution.new_name}")
                            item.setText(2, "✏️ Rename")
                            item.setCheckState(0, Qt.CheckState.Checked)
                        else:
                            item.setText(0, server_name)
                            item.setText(2, "🔄 Replace")
                            item.setCheckState(0, Qt.CheckState.Checked)
                    else:
                        item.setText(0, server_name)
                        item.setText(2, "✅ New")
                        item.setCheckState(0, Qt.CheckState.Checked)

                    item.setText(1, project_name)
                    item.setData(0, Qt.ItemDataRole.UserRole, {
                        'name': server_name,
                        'project': project_path,
                        'config': config
                    })

                    self.servers_tree.addTopLevelItem(item)

            self.update_selection()

        def toggle_select_all(self):
            """Toggle all server selections"""
            check_state = Qt.CheckState.Checked if self.select_all.isChecked() else Qt.CheckState.Unchecked

            for i in range(self.servers_tree.topLevelItemCount()):
                item = self.servers_tree.topLevelItem(i)
                if not item.isDisabled():
                    item.setCheckState(0, check_state)

        def on_selection_changed(self, item, column):
            """Handle selection change"""
            if column == 0:
                self.update_selection()

        def update_selection(self):
            """Update the selected servers list"""
            self.selected_servers.clear()

            for i in range(self.servers_tree.topLevelItemCount()):
                item = self.servers_tree.topLevelItem(i)
                if item.checkState(0) == Qt.CheckState.Checked:
                    data = item.data(0, Qt.ItemDataRole.UserRole)
                    if data:
                        self.selected_servers.append(data)

            self.completeChanged.emit()

        def isComplete(self):
            """Check if page is complete"""
            return bool(self.selected_servers)


    class PreviewPage(QWizardPage):
        """Step 4: Preview changes"""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setTitle("Preview Changes")
            self.setSubTitle("Review the changes that will be made to your configuration.")

            # Layout
            layout = QVBoxLayout()
            self.setLayout(layout)

            # Preview text
            self.preview_text = QTextEdit()
            self.preview_text.setReadOnly(True)
            layout.addWidget(self.preview_text)

            # Backup checkbox
            self.backup_check = QCheckBox("Create backup before applying changes")
            self.backup_check.setChecked(True)
            layout.addWidget(self.backup_check)

        def initializePage(self):
            """Called when page is shown"""
            super().initializePage()
            self.generate_preview()

        def generate_preview(self):
            """Generate preview of changes"""
            wizard = self.wizard()
            selected = wizard.selection_page.selected_servers
            resolutions = wizard.conflict_page.resolutions

            # Build preview text
            preview = "Consolidation Plan\n"
            preview += "=" * 50 + "\n\n"

            # Summary
            preview += f"Servers to promote: {len(selected)}\n"
            preview += f"Conflicts to resolve: {len(resolutions)}\n\n"

            # Details
            if selected:
                preview += "Servers to Promote:\n"
                preview += "-" * 30 + "\n"
                for server_data in selected:
                    name = server_data['name']
                    project = Path(server_data['project']).name
                    preview += f"  • {name} (from {project})\n"
                preview += "\n"

            if resolutions:
                preview += "Conflict Resolutions:\n"
                preview += "-" * 30 + "\n"
                for resolution in resolutions:
                    if resolution.strategy == 'skip':
                        preview += f"  • {resolution.server_name}: SKIP\n"
                    elif resolution.strategy == 'rename':
                        preview += f"  • {resolution.server_name}: RENAME to {resolution.new_name}\n"
                    else:
                        preview += f"  • {resolution.server_name}: REPLACE global\n"
                preview += "\n"

            # Warnings
            preview += "⚠️ Important:\n"
            preview += "• Project-specific servers will be copied to global config\n"
            preview += "• Original project configs will NOT be modified\n"
            preview += "• A backup is recommended before proceeding\n"

            self.preview_text.setPlainText(preview)

        def get_consolidation_plan(self):
            """Get the consolidation plan"""
            wizard = self.wizard()

            plan = ConsolidationPlan(
                servers_to_promote=wizard.selection_page.selected_servers,
                conflicts=wizard.conflict_page.resolutions,
                timestamp=datetime.now()
            )

            if self.backup_check.isChecked():
                # Generate backup path
                backup_dir = Path.home() / '.mcp-config-backups'
                backup_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                plan.backup_path = str(backup_dir / f"consolidation_{timestamp}.json")

            return plan


    class ApplyPage(QWizardPage):
        """Step 5: Apply changes with backup"""

        def __init__(self, server_manager=None, parent=None):
            super().__init__(parent)
            self.server_manager = server_manager
            self.setTitle("Apply Changes")
            self.setSubTitle("Applying the consolidation plan...")

            # Track success
            self.success = False
            self.report = None

            # Layout
            layout = QVBoxLayout()
            self.setLayout(layout)

            # Progress
            self.progress_bar = QProgressBar()
            layout.addWidget(self.progress_bar)

            # Status
            self.status_label = QLabel("Ready to apply changes...")
            layout.addWidget(self.status_label)

            # Log
            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            layout.addWidget(self.log_text)

            # Apply button
            self.apply_button = QPushButton("Apply Changes")
            self.apply_button.clicked.connect(self.apply_changes)
            layout.addWidget(self.apply_button)

        def initializePage(self):
            """Called when page is shown"""
            super().initializePage()
            self.setFinalPage(True)

        def apply_changes(self):
            """Apply the consolidation plan"""
            self.apply_button.setEnabled(False)
            self.progress_bar.setValue(0)

            wizard = self.wizard()
            plan = wizard.preview_page.get_consolidation_plan()

            try:
                # Create backup if requested
                if plan.backup_path:
                    self.log("Creating backup...")
                    self.create_backup(plan.backup_path)
                    self.log(f"✓ Backup saved to: {plan.backup_path}")
                    self.progress_bar.setValue(20)

                # Apply each server
                total = len(plan.servers_to_promote)
                for i, server_data in enumerate(plan.servers_to_promote):
                    name = server_data['name']
                    project = server_data['project']
                    config = server_data['config']

                    self.log(f"Promoting {name}...")

                    # Check for conflict resolution
                    resolution = next((r for r in plan.conflicts if r.server_name == name), None)

                    if resolution:
                        if resolution.strategy == 'skip':
                            self.log(f"  Skipped (conflict)")
                            continue
                        elif resolution.strategy == 'rename':
                            name = resolution.new_name
                            self.log(f"  Renamed to {name}")

                    # Promote the server
                    if self.server_manager:
                        self.server_manager.promote_project_server(
                            name, project, remove_from_project=False
                        )

                    self.log(f"✓ Promoted {name}")
                    progress = 20 + int((i + 1) / total * 70)
                    self.progress_bar.setValue(progress)

                # Generate report
                self.generate_report(plan)
                self.progress_bar.setValue(100)

                self.status_label.setText("✅ Consolidation complete!")
                self.success = True

            except Exception as e:
                self.log(f"❌ Error: {str(e)}")
                self.status_label.setText("Failed to complete consolidation")
                QMessageBox.critical(self, "Error", f"Consolidation failed:\n{str(e)}")

            self.completeChanged.emit()

        def log(self, message):
            """Add message to log"""
            self.log_text.append(message)
            QApplication.processEvents()

        def create_backup(self, backup_path):
            """Create a backup of current configuration"""
            if self.server_manager:
                # Get current config
                try:
                    current_config = {
                        'claude': self.server_manager.config_manager.get_claude_config(),
                        'gemini': self.server_manager.config_manager.get_gemini_config(),
                        'disabled': self.server_manager.load_disabled_servers()
                    }

                    # Save backup
                    with open(backup_path, 'w') as f:
                        json.dump(current_config, f, indent=2)
                except Exception as e:
                    logger.error(f"Failed to create backup: {e}")

        def generate_report(self, plan):
            """Generate consolidation report"""
            self.report = {
                'timestamp': plan.timestamp.isoformat() if plan.timestamp else None,
                'servers_promoted': len(plan.servers_to_promote),
                'conflicts_resolved': len(plan.conflicts),
                'backup_path': plan.backup_path
            }

            # Save report
            report_dir = Path.home() / '.mcp-config-reports'
            report_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = report_dir / f"consolidation_report_{timestamp}.json"

            with open(report_path, 'w') as f:
                json.dump(self.report, f, indent=2)

            self.log(f"\n📄 Report saved to: {report_path}")

        def isComplete(self):
            """Check if page is complete"""
            return self.success


    class ConsolidationWizard(QWizard):
        """Main consolidation wizard"""

        def __init__(self, discovery_service, server_manager=None, parent=None):
            super().__init__(parent)
            self.discovery_service = discovery_service
            self.server_manager = server_manager

            self.setWindowTitle("Project Server Consolidation Wizard")
            self.resize(800, 600)

            # Create pages
            self.scan_page = ScanPage(discovery_service, self)
            self.conflict_page = ConflictPage(self)
            self.selection_page = SelectionPage(self)
            self.preview_page = PreviewPage(self)
            self.apply_page = ApplyPage(server_manager, self)

            # Add pages
            self.addPage(self.scan_page)
            self.addPage(self.conflict_page)
            self.addPage(self.selection_page)
            self.addPage(self.preview_page)
            self.addPage(self.apply_page)

            # Style
            self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        def get_report(self):
            """Get the consolidation report"""
            return self.apply_page.report


else:
    # Tkinter implementation

    class ConsolidationWizard:
        """Tkinter consolidation wizard"""

        def __init__(self, discovery_service, server_manager=None, parent=None):
            self.discovery_service = discovery_service
            self.server_manager = server_manager
            self.parent = parent

            # Data
            self.discovered_servers = {}
            self.resolutions = []
            self.selected_servers = []
            self.report = None

            # Create window
            self.window = tk.Toplevel(parent) if parent else tk.Tk()
            self.window.title("Project Server Consolidation Wizard")
            self.window.geometry("800x600")

            # Current step
            self.current_step = 0
            self.steps = [
                self.create_scan_step,
                self.create_conflict_step,
                self.create_selection_step,
                self.create_preview_step,
                self.create_apply_step
            ]

            # Main frame
            self.main_frame = ttk.Frame(self.window, padding="10")
            self.main_frame.pack(fill=tk.BOTH, expand=True)

            # Navigation buttons
            nav_frame = ttk.Frame(self.window)
            nav_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

            self.back_button = ttk.Button(nav_frame, text="< Back",
                                         command=self.go_back, state=tk.DISABLED)
            self.back_button.pack(side=tk.LEFT)

            self.next_button = ttk.Button(nav_frame, text="Next >",
                                         command=self.go_next)
            self.next_button.pack(side=tk.RIGHT)

            self.cancel_button = ttk.Button(nav_frame, text="Cancel",
                                           command=self.cancel)
            self.cancel_button.pack(side=tk.RIGHT, padx=5)

            # Show first step
            self.show_step(0)

        def show_step(self, step_index):
            """Show a specific step"""
            # Clear main frame
            for widget in self.main_frame.winfo_children():
                widget.destroy()

            # Create step content
            self.current_step = step_index
            self.steps[step_index]()

            # Update navigation
            self.back_button['state'] = tk.NORMAL if step_index > 0 else tk.DISABLED

            if step_index == len(self.steps) - 1:
                self.next_button['text'] = "Finish"
            else:
                self.next_button['text'] = "Next >"

        def go_back(self):
            """Go to previous step"""
            if self.current_step > 0:
                self.show_step(self.current_step - 1)

        def go_next(self):
            """Go to next step or finish"""
            if self.current_step < len(self.steps) - 1:
                self.show_step(self.current_step + 1)
            else:
                self.finish()

        def cancel(self):
            """Cancel wizard"""
            self.window.destroy()

        def finish(self):
            """Complete wizard"""
            self.window.destroy()

        def create_scan_step(self):
            """Create scan step UI"""
            # Title
            title = ttk.Label(self.main_frame, text="Step 1: Discover Project Servers",
                            font=('', 14, 'bold'))
            title.pack(pady=10)

            # Description
            desc = ttk.Label(self.main_frame,
                           text="Scanning your system for project-specific MCP server configurations...")
            desc.pack(pady=5)

            # Progress
            self.scan_progress = ttk.Progressbar(self.main_frame, mode='indeterminate')
            self.scan_progress.pack(fill=tk.X, pady=10)

            # Status
            self.scan_status = ttk.Label(self.main_frame, text="Click 'Start Scan' to begin")
            self.scan_status.pack(pady=5)

            # Results
            results_frame = ttk.LabelFrame(self.main_frame, text="Discovery Results", padding=10)
            results_frame.pack(fill=tk.BOTH, expand=True, pady=10)

            self.results_text = scrolledtext.ScrolledText(results_frame, height=10)
            self.results_text.pack(fill=tk.BOTH, expand=True)

            # Scan button
            scan_button = ttk.Button(self.main_frame, text="Start Scan",
                                   command=self.start_scan)
            scan_button.pack(pady=5)

        def start_scan(self):
            """Start discovery scan"""
            self.scan_progress.start()
            self.scan_status['text'] = "Scanning for project configurations..."

            # Run scan in thread
            def scan_thread():
                try:
                    servers = self.discovery_service.scan_projects()
                    self.discovered_servers = servers

                    # Update UI in main thread
                    self.window.after(0, self.scan_complete, servers)
                except Exception as e:
                    self.window.after(0, self.scan_error, str(e))

            thread = threading.Thread(target=scan_thread)
            thread.daemon = True
            thread.start()

        def scan_complete(self, servers):
            """Handle scan completion"""
            self.scan_progress.stop()

            # Count servers
            total_servers = sum(len(s) for s in servers.values())
            project_count = len(servers)

            self.scan_status['text'] = f"Found {total_servers} servers across {project_count} projects"

            # Show results
            summary = f"Discovery Results:\n\n"
            for project_path, project_servers in servers.items():
                project_name = Path(project_path).name
                summary += f"📁 {project_name} ({len(project_servers)} servers)\n"
                for server_name in list(project_servers.keys())[:3]:
                    summary += f"   • {server_name}\n"
                if len(project_servers) > 3:
                    summary += f"   ... and {len(project_servers) - 3} more\n"
                summary += "\n"

            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, summary)

        def scan_error(self, error_msg):
            """Handle scan error"""
            self.scan_progress.stop()
            self.scan_status['text'] = f"Error: {error_msg}"
            messagebox.showerror("Scan Error", f"Failed to scan projects:\n{error_msg}")

        def create_conflict_step(self):
            """Create conflict resolution step"""
            # Title
            title = ttk.Label(self.main_frame, text="Step 2: Resolve Conflicts",
                            font=('', 14, 'bold'))
            title.pack(pady=10)

            # Description
            desc = ttk.Label(self.main_frame,
                           text="Some servers exist in multiple locations. Choose how to handle conflicts.")
            desc.pack(pady=5)

            # Conflicts list
            list_frame = ttk.Frame(self.main_frame)
            list_frame.pack(fill=tk.BOTH, expand=True, pady=10)

            # Create treeview
            self.conflicts_tree = ttk.Treeview(list_frame, columns=('resolution',),
                                              show='tree headings')
            self.conflicts_tree.heading('#0', text='Server/Location')
            self.conflicts_tree.heading('resolution', text='Resolution')
            self.conflicts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Scrollbar
            scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                     command=self.conflicts_tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.conflicts_tree['yscrollcommand'] = scrollbar.set

            # Strategy buttons
            strategy_frame = ttk.LabelFrame(self.main_frame, text="Default Resolution", padding=10)
            strategy_frame.pack(fill=tk.X, pady=10)

            self.strategy_var = tk.StringVar(value="replace")

            ttk.Radiobutton(strategy_frame, text="Skip",
                          variable=self.strategy_var, value="skip").pack(side=tk.LEFT, padx=5)
            ttk.Radiobutton(strategy_frame, text="Replace",
                          variable=self.strategy_var, value="replace").pack(side=tk.LEFT, padx=5)
            ttk.Radiobutton(strategy_frame, text="Rename",
                          variable=self.strategy_var, value="rename").pack(side=tk.LEFT, padx=5)

            ttk.Button(strategy_frame, text="Apply to All",
                      command=self.apply_strategy_to_all).pack(side=tk.RIGHT)

            # Populate conflicts
            self.populate_conflicts()

        def populate_conflicts(self):
            """Populate conflicts tree"""
            # Find conflicts
            server_locations = {}
            for project_path, servers in self.discovered_servers.items():
                for server_name in servers:
                    if server_name not in server_locations:
                        server_locations[server_name] = []
                    server_locations[server_name].append(project_path)

            # Clear resolutions
            self.resolutions.clear()

            # Add to tree
            for server_name, locations in server_locations.items():
                if len(locations) > 1:
                    # Add conflict
                    server_id = self.conflicts_tree.insert('', 'end', text=server_name)

                    for location in locations:
                        loc_name = Path(location).name
                        self.conflicts_tree.insert(server_id, 'end',
                                                  text=f"  📁 {loc_name}",
                                                  values=("Replace",))

                    # Create resolution
                    resolution = ConflictResolution(
                        server_name=server_name,
                        project_path=locations[0],
                        strategy='replace'
                    )
                    self.resolutions.append(resolution)

        def apply_strategy_to_all(self):
            """Apply selected strategy to all conflicts"""
            strategy = self.strategy_var.get()

            # Update resolutions
            for resolution in self.resolutions:
                resolution.strategy = strategy
                if strategy == 'rename':
                    resolution.new_name = f"{resolution.server_name}_project"

        def create_selection_step(self):
            """Create server selection step"""
            # Title
            title = ttk.Label(self.main_frame, text="Step 3: Select Servers",
                            font=('', 14, 'bold'))
            title.pack(pady=10)

            # Description
            desc = ttk.Label(self.main_frame,
                           text="Choose which servers to promote to the global configuration.")
            desc.pack(pady=5)

            # Select all
            select_all_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(self.main_frame, text="Select All",
                          variable=select_all_var,
                          command=lambda: self.toggle_all_servers(select_all_var.get())).pack(pady=5)

            # Servers list
            list_frame = ttk.Frame(self.main_frame)
            list_frame.pack(fill=tk.BOTH, expand=True, pady=10)

            # Create listbox with checkboxes
            self.servers_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE)
            self.servers_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Scrollbar
            scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                     command=self.servers_listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.servers_listbox['yscrollcommand'] = scrollbar.set

            # Populate servers
            self.populate_server_selection()

        def populate_server_selection(self):
            """Populate server selection list"""
            self.selected_servers.clear()

            for project_path, servers in self.discovered_servers.items():
                project_name = Path(project_path).name

                for server_name, config in servers.items():
                    # Check if conflict
                    conflict = next((r for r in self.resolutions if r.server_name == server_name), None)

                    if conflict and conflict.strategy == 'skip':
                        display_name = f"{server_name} (skipped) - {project_name}"
                    elif conflict and conflict.strategy == 'rename':
                        display_name = f"{server_name} → {conflict.new_name} - {project_name}"
                    else:
                        display_name = f"{server_name} - {project_name}"

                    self.servers_listbox.insert(tk.END, display_name)

                    # Store data
                    server_data = {
                        'name': server_name,
                        'project': project_path,
                        'config': config
                    }
                    self.selected_servers.append(server_data)

            # Select all by default
            self.servers_listbox.select_set(0, tk.END)

        def toggle_all_servers(self, select_all):
            """Toggle all server selections"""
            if select_all:
                self.servers_listbox.select_set(0, tk.END)
            else:
                self.servers_listbox.select_clear(0, tk.END)

        def create_preview_step(self):
            """Create preview step"""
            # Title
            title = ttk.Label(self.main_frame, text="Step 4: Preview Changes",
                            font=('', 14, 'bold'))
            title.pack(pady=10)

            # Description
            desc = ttk.Label(self.main_frame,
                           text="Review the changes that will be made to your configuration.")
            desc.pack(pady=5)

            # Preview text
            preview_frame = ttk.Frame(self.main_frame)
            preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

            self.preview_text = scrolledtext.ScrolledText(preview_frame, height=15)
            self.preview_text.pack(fill=tk.BOTH, expand=True)

            # Generate preview
            self.generate_preview()

            # Backup option
            self.backup_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(self.main_frame, text="Create backup before applying changes",
                          variable=self.backup_var).pack(pady=5)

        def generate_preview(self):
            """Generate preview text"""
            # Get selected indices
            selected_indices = self.servers_listbox.curselection()
            selected = [self.selected_servers[i] for i in selected_indices]

            # Build preview
            preview = "Consolidation Plan\n"
            preview += "=" * 50 + "\n\n"

            preview += f"Servers to promote: {len(selected)}\n"
            preview += f"Conflicts to resolve: {len(self.resolutions)}\n\n"

            if selected:
                preview += "Servers to Promote:\n"
                preview += "-" * 30 + "\n"
                for server_data in selected:
                    name = server_data['name']
                    project = Path(server_data['project']).name
                    preview += f"  • {name} (from {project})\n"
                preview += "\n"

            if self.resolutions:
                preview += "Conflict Resolutions:\n"
                preview += "-" * 30 + "\n"
                for resolution in self.resolutions:
                    if resolution.strategy == 'skip':
                        preview += f"  • {resolution.server_name}: SKIP\n"
                    elif resolution.strategy == 'rename':
                        preview += f"  • {resolution.server_name}: RENAME to {resolution.new_name}\n"
                    else:
                        preview += f"  • {resolution.server_name}: REPLACE\n"

            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, preview)

        def create_apply_step(self):
            """Create apply step"""
            # Title
            title = ttk.Label(self.main_frame, text="Step 5: Apply Changes",
                            font=('', 14, 'bold'))
            title.pack(pady=10)

            # Description
            desc = ttk.Label(self.main_frame, text="Click 'Apply' to consolidate servers.")
            desc.pack(pady=5)

            # Progress
            self.apply_progress = ttk.Progressbar(self.main_frame)
            self.apply_progress.pack(fill=tk.X, pady=10)

            # Status
            self.apply_status = ttk.Label(self.main_frame, text="Ready to apply changes")
            self.apply_status.pack(pady=5)

            # Log
            log_frame = ttk.Frame(self.main_frame)
            log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

            self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
            self.log_text.pack(fill=tk.BOTH, expand=True)

            # Apply button
            self.apply_button = ttk.Button(self.main_frame, text="Apply Changes",
                                         command=self.apply_changes)
            self.apply_button.pack(pady=5)

        def apply_changes(self):
            """Apply consolidation changes"""
            self.apply_button['state'] = tk.DISABLED
            self.apply_progress['value'] = 0

            # Get selected servers
            selected_indices = self.servers_listbox.curselection()
            selected = [self.selected_servers[i] for i in selected_indices]

            try:
                # Create backup if requested
                if self.backup_var.get():
                    self.log("Creating backup...")
                    # Backup logic here
                    self.apply_progress['value'] = 20

                # Apply each server
                total = len(selected)
                for i, server_data in enumerate(selected):
                    name = server_data['name']
                    project = server_data['project']

                    self.log(f"Promoting {name}...")

                    # Check for resolution
                    resolution = next((r for r in self.resolutions if r.server_name == name), None)

                    if resolution:
                        if resolution.strategy == 'skip':
                            self.log(f"  Skipped")
                            continue
                        elif resolution.strategy == 'rename':
                            name = resolution.new_name
                            self.log(f"  Renamed to {name}")

                    # Promote server
                    if self.server_manager:
                        self.server_manager.promote_project_server(
                            name, project, remove_from_project=False
                        )

                    self.log(f"✓ Promoted {name}")
                    progress = 20 + int((i + 1) / total * 70)
                    self.apply_progress['value'] = progress

                self.apply_progress['value'] = 100
                self.apply_status['text'] = "✅ Consolidation complete!"
                self.next_button['text'] = "Finish"

            except Exception as e:
                self.log(f"❌ Error: {str(e)}")
                self.apply_status['text'] = "Failed to complete consolidation"
                messagebox.showerror("Error", f"Consolidation failed:\n{str(e)}")

        def log(self, message):
            """Add message to log"""
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.window.update()

        def get_report(self):
            """Get consolidation report"""
            return self.report