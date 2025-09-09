"""File watcher for configuration files."""

import os
import time
import threading
from pathlib import Path
from typing import Dict, Any, Callable, Optional, Set
import logging

logger = logging.getLogger(__name__)


class FileWatcher:
    """Watches configuration files for changes."""
    
    def __init__(self, check_interval: float = 1.0):
        """Initialize the file watcher.
        
        Args:
            check_interval: How often to check for changes (seconds)
        """
        self.check_interval = check_interval
        self.watched_files: Dict[str, float] = {}  # path -> last modified time
        self.callbacks: Dict[str, Callable[[str], None]] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def add_file(self, file_path: str, callback: Callable[[str], None]) -> bool:
        """Add a file to watch.
        
        Args:
            file_path: Path to the file to watch
            callback: Function to call when file changes
            
        Returns:
            True if file was added successfully
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"File does not exist: {file_path}")
                return False
            
            with self._lock:
                # Get initial modification time
                mtime = os.path.getmtime(file_path)
                self.watched_files[str(path)] = mtime
                self.callbacks[str(path)] = callback
                
            logger.info(f"Watching file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add file to watch: {e}")
            return False
    
    def remove_file(self, file_path: str) -> bool:
        """Remove a file from watching.
        
        Args:
            file_path: Path to the file to stop watching
            
        Returns:
            True if file was removed successfully
        """
        try:
            path = str(Path(file_path))
            
            with self._lock:
                if path in self.watched_files:
                    del self.watched_files[path]
                    del self.callbacks[path]
                    logger.info(f"Stopped watching file: {file_path}")
                    return True
                else:
                    logger.warning(f"File not being watched: {file_path}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to remove file from watch: {e}")
            return False
    
    def start(self) -> bool:
        """Start watching files.
        
        Returns:
            True if watcher started successfully
        """
        if self.running:
            logger.warning("File watcher already running")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        logger.info("File watcher started")
        return True
    
    def stop(self) -> bool:
        """Stop watching files.
        
        Returns:
            True if watcher stopped successfully
        """
        if not self.running:
            logger.warning("File watcher not running")
            return False
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=self.check_interval * 2)
        
        logger.info("File watcher stopped")
        return True
    
    def _watch_loop(self):
        """Main watch loop that runs in background thread."""
        while self.running:
            try:
                # Check each watched file
                with self._lock:
                    files_to_check = list(self.watched_files.items())
                
                for file_path, last_mtime in files_to_check:
                    try:
                        if not Path(file_path).exists():
                            logger.warning(f"Watched file no longer exists: {file_path}")
                            self.remove_file(file_path)
                            continue
                        
                        # Check if file has been modified
                        current_mtime = os.path.getmtime(file_path)
                        if current_mtime > last_mtime:
                            logger.info(f"File changed: {file_path}")
                            
                            # Update last modified time
                            with self._lock:
                                self.watched_files[file_path] = current_mtime
                                callback = self.callbacks.get(file_path)
                            
                            # Call the callback
                            if callback:
                                try:
                                    callback(file_path)
                                except Exception as e:
                                    logger.error(f"Error in file change callback: {e}")
                    
                    except Exception as e:
                        logger.error(f"Error checking file {file_path}: {e}")
                
                # Sleep before next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in watch loop: {e}")
                time.sleep(self.check_interval)
    
    def get_watched_files(self) -> Set[str]:
        """Get set of currently watched file paths.
        
        Returns:
            Set of file paths being watched
        """
        with self._lock:
            return set(self.watched_files.keys())
    
    def is_watching(self, file_path: str) -> bool:
        """Check if a file is being watched.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is being watched
        """
        path = str(Path(file_path))
        with self._lock:
            return path in self.watched_files


class ConfigFileWatcher:
    """Specialized watcher for configuration files."""
    
    def __init__(self, config_controller=None):
        """Initialize the config file watcher.
        
        Args:
            config_controller: Optional ConfigController to notify of changes
        """
        self.config_controller = config_controller
        self.file_watcher = FileWatcher(check_interval=1.0)
        self.on_config_changed_callbacks: list[Callable[[str], None]] = []
        
    def watch_config_files(self, claude_path: Optional[str] = None,
                          gemini_path: Optional[str] = None,
                          presets_path: Optional[str] = None) -> Dict[str, bool]:
        """Start watching configuration files.
        
        Args:
            claude_path: Path to Claude config file
            gemini_path: Path to Gemini config file
            presets_path: Path to presets file
            
        Returns:
            Dictionary with success status for each file
        """
        results = {}
        
        if claude_path:
            results['claude'] = self.file_watcher.add_file(
                claude_path,
                lambda p: self._handle_config_change('claude', p)
            )
        
        if gemini_path:
            results['gemini'] = self.file_watcher.add_file(
                gemini_path,
                lambda p: self._handle_config_change('gemini', p)
            )
        
        if presets_path:
            results['presets'] = self.file_watcher.add_file(
                presets_path,
                lambda p: self._handle_config_change('presets', p)
            )
        
        # Start the watcher if any files were added
        if any(results.values()):
            self.file_watcher.start()
        
        return results
    
    def stop_watching(self):
        """Stop watching all configuration files."""
        self.file_watcher.stop()
    
    def _handle_config_change(self, config_type: str, file_path: str):
        """Handle a configuration file change.
        
        Args:
            config_type: Type of config that changed ('claude', 'gemini', 'presets')
            file_path: Path to the changed file
        """
        logger.info(f"Configuration changed: {config_type} ({file_path})")
        
        # Notify callbacks
        for callback in self.on_config_changed_callbacks:
            try:
                callback(config_type)
            except Exception as e:
                logger.error(f"Error in config change callback: {e}")
        
        # If we have a config controller, reload the configuration
        if self.config_controller:
            try:
                if config_type in ['claude', 'gemini']:
                    # Reload the specific configuration
                    self.config_controller.load_config(config_type)
                elif config_type == 'presets':
                    # Presets changed, just notify
                    logger.info("Presets file changed, refresh may be needed")
            except Exception as e:
                logger.error(f"Failed to reload configuration: {e}")
    
    def on_config_changed(self, callback: Callable[[str], None]):
        """Register callback for configuration changes.
        
        Args:
            callback: Function to call with config type when changes occur
        """
        self.on_config_changed_callbacks.append(callback)
    
    def get_watched_files(self) -> Set[str]:
        """Get set of currently watched file paths.
        
        Returns:
            Set of file paths being watched
        """
        return self.file_watcher.get_watched_files()