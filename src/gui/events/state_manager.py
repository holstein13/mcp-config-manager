"""State management and change notification system.

Manages application state changes and notifies components through the event dispatcher.
Provides centralized state management with automatic change detection and notification.
Thread-safe for use with background operations.
"""

import logging
import threading
from typing import Any, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from .dispatcher import dispatcher, EventType, Event
from ..models.app_state import ApplicationState

logger = logging.getLogger(__name__)


class StateProperty(Enum):
    """Trackable state properties."""
    MODE = "mode"
    ACTIVE_SERVERS = "active_servers"
    DISABLED_SERVERS = "disabled_servers"
    SELECTED_SERVER = "selected_server"
    SELECTED_PRESET = "selected_preset"
    SEARCH_FILTER = "search_filter"
    CURRENT_VIEW = "current_view"
    UNSAVED_CHANGES = "unsaved_changes"
    VALIDATION_ERRORS = "validation_errors"
    LOADING = "loading"
    THEME = "theme"


@dataclass
class StateChange:
    """Represents a state change."""
    property: StateProperty
    old_value: Any
    new_value: Any
    source: Optional[str] = None


class StateManager:
    """Manages application state with automatic change detection.
    
    Tracks state changes and emits events when state properties change.
    Provides undo/redo capabilities and state history.
    """
    
    def __init__(self):
        """Initialize the state manager."""
        self._state = ApplicationState()
        self._previous_state: Dict[StateProperty, Any] = {}
        self._state_history: list[StateChange] = []
        self._max_history_size = 50
        self._undo_stack: list[StateChange] = []
        self._redo_stack: list[StateChange] = []
        self._suspended_properties: Set[StateProperty] = set()
        self._batch_mode = False
        self._batch_changes: list[StateChange] = []
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        
        # Initialize previous state
        self._capture_state()
    
    def _capture_state(self) -> Dict[StateProperty, Any]:
        """Capture current state values.
        
        Returns:
            Dictionary of current state values
        """
        return {
            StateProperty.MODE: self._state.mode,
            StateProperty.ACTIVE_SERVERS: set(self._state.active_servers),
            StateProperty.DISABLED_SERVERS: set(self._state.disabled_servers),
            StateProperty.SELECTED_SERVER: self._state.selected_server,
            StateProperty.SELECTED_PRESET: self._state.selected_preset,
            StateProperty.SEARCH_FILTER: self._state.search_filter,
            StateProperty.CURRENT_VIEW: self._state.current_view,
            StateProperty.UNSAVED_CHANGES: self._state.unsaved_changes,
            StateProperty.VALIDATION_ERRORS: list(self._state.validation_errors),
            StateProperty.LOADING: self._state.loading,
        }
    
    def get_state(self) -> ApplicationState:
        """Get the current application state (thread-safe).
        
        Returns:
            Current ApplicationState object
        """
        with self._lock:
            return self._state
    
    def set_property(self, property: StateProperty, value: Any, source: Optional[str] = None) -> bool:
        """Set a state property value (thread-safe).
        
        Args:
            property: The property to set
            value: The new value
            source: Optional source identifier
            
        Returns:
            True if the value changed, False otherwise
        """
        with self._lock:
            if property in self._suspended_properties:
                logger.debug(f"Property {property.value} is suspended, ignoring change")
                return False
            
            # Get current value
            current_state = self._capture_state()
            old_value = current_state.get(property)
            
            # Check if value actually changed
            if old_value == value:
                return False
            
            # Apply the change
            self._apply_change(property, value)
            
            # Create state change record
            change = StateChange(property, old_value, value, source)
            
            if self._batch_mode:
                self._batch_changes.append(change)
            else:
                self._process_change(change)
            
            return True
    
    def _apply_change(self, property: StateProperty, value: Any) -> None:
        """Apply a change to the state.
        
        Args:
            property: The property to change
            value: The new value
        """
        if property == StateProperty.MODE:
            self._state.mode = value
        elif property == StateProperty.ACTIVE_SERVERS:
            self._state.active_servers = list(value) if isinstance(value, (set, list)) else value
        elif property == StateProperty.DISABLED_SERVERS:
            self._state.disabled_servers = list(value) if isinstance(value, (set, list)) else value
        elif property == StateProperty.SELECTED_SERVER:
            self._state.selected_server = value
        elif property == StateProperty.SELECTED_PRESET:
            self._state.selected_preset = value
        elif property == StateProperty.SEARCH_FILTER:
            self._state.search_filter = value
        elif property == StateProperty.CURRENT_VIEW:
            self._state.current_view = value
        elif property == StateProperty.UNSAVED_CHANGES:
            self._state.unsaved_changes = value
        elif property == StateProperty.VALIDATION_ERRORS:
            self._state.validation_errors = value
        elif property == StateProperty.LOADING:
            self._state.loading = value
    
    def _process_change(self, change: StateChange) -> None:
        """Process a state change.
        
        Args:
            change: The state change to process
        """
        # Add to history
        self._state_history.append(change)
        if len(self._state_history) > self._max_history_size:
            self._state_history.pop(0)
        
        # Add to undo stack
        self._undo_stack.append(change)
        self._redo_stack.clear()  # Clear redo stack on new change
        
        # Emit change event
        self._emit_change_event(change)
        
        logger.info(f"State changed: {change.property.value} = {change.new_value} (from {change.source})")
    
    def _emit_change_event(self, change: StateChange) -> None:
        """Emit an event for a state change.
        
        Args:
            change: The state change
        """
        event_data = {
            'property': change.property.value,
            'old_value': change.old_value,
            'new_value': change.new_value,
            'source': change.source
        }
        
        dispatcher.emit_now(EventType.UI_STATE_CHANGED, event_data, source='StateManager')
        
        # Emit specific events for certain properties
        if change.property == StateProperty.MODE:
            dispatcher.emit_now(EventType.MODE_CHANGED, 
                               {'mode': change.new_value}, 
                               source='StateManager')
        elif change.property == StateProperty.SEARCH_FILTER:
            dispatcher.emit_now(EventType.UI_SEARCH_CHANGED,
                               {'filter': change.new_value},
                               source='StateManager')
        elif change.property == StateProperty.SELECTED_SERVER:
            dispatcher.emit_now(EventType.UI_SELECTION_CHANGED,
                               {'selection': change.new_value},
                               source='StateManager')
        elif change.property == StateProperty.CURRENT_VIEW:
            dispatcher.emit_now(EventType.UI_VIEW_CHANGED,
                               {'view': change.new_value},
                               source='StateManager')
    
    def batch_begin(self) -> None:
        """Begin a batch of state changes (thread-safe).
        
        Changes will be collected but not processed until batch_end is called.
        """
        with self._lock:
            self._batch_mode = True
            self._batch_changes = []
            logger.debug("Batch mode started")
    
    def batch_end(self) -> None:
        """End a batch of state changes and process them (thread-safe)."""
        with self._lock:
            if not self._batch_mode:
                return
            
            self._batch_mode = False
            changes = self._batch_changes
            self._batch_changes = []
            
            # Process all changes
            for change in changes:
                self._process_change(change)
            
            logger.debug(f"Batch mode ended, processed {len(changes)} changes")
    
    def suspend_property(self, property: StateProperty) -> None:
        """Suspend change notifications for a property.
        
        Args:
            property: The property to suspend
        """
        self._suspended_properties.add(property)
        logger.debug(f"Suspended property: {property.value}")
    
    def resume_property(self, property: StateProperty) -> None:
        """Resume change notifications for a property.
        
        Args:
            property: The property to resume
        """
        self._suspended_properties.discard(property)
        logger.debug(f"Resumed property: {property.value}")
    
    def undo(self) -> bool:
        """Undo the last state change.
        
        Returns:
            True if undo was successful, False otherwise
        """
        if not self._undo_stack:
            logger.debug("No changes to undo")
            return False
        
        change = self._undo_stack.pop()
        
        # Apply the reverse change
        self._apply_change(change.property, change.old_value)
        
        # Add to redo stack
        self._redo_stack.append(change)
        
        # Emit undo event
        reverse_change = StateChange(change.property, change.new_value, change.old_value, "undo")
        self._emit_change_event(reverse_change)
        
        logger.info(f"Undid change: {change.property.value}")
        return True
    
    def redo(self) -> bool:
        """Redo the last undone state change.
        
        Returns:
            True if redo was successful, False otherwise
        """
        if not self._redo_stack:
            logger.debug("No changes to redo")
            return False
        
        change = self._redo_stack.pop()
        
        # Apply the original change
        self._apply_change(change.property, change.new_value)
        
        # Add back to undo stack
        self._undo_stack.append(change)
        
        # Emit redo event
        self._emit_change_event(change)
        
        logger.info(f"Redid change: {change.property.value}")
        return True
    
    def get_history(self, limit: int = 10) -> list[StateChange]:
        """Get recent state change history.
        
        Args:
            limit: Maximum number of changes to return
            
        Returns:
            List of recent state changes
        """
        return self._state_history[-limit:]
    
    def clear_history(self) -> None:
        """Clear all state history."""
        self._state_history.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()
        logger.debug("State history cleared")
    
    def reset_state(self) -> None:
        """Reset state to initial values."""
        self._state = ApplicationState()
        self._capture_state()
        self.clear_history()
        
        # Emit reset event
        dispatcher.emit_now(EventType.UI_STATE_CHANGED,
                           {'property': 'all', 'action': 'reset'},
                           source='StateManager')
        
        logger.info("State reset to initial values")


# Global state manager instance
state_manager = StateManager()


def get_state_manager() -> StateManager:
    """Get the global state manager instance.
    
    Returns:
        The global StateManager instance
    """
    return state_manager