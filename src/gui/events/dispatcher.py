"""Central event dispatcher for GUI application.

Provides a decoupled event system that allows components to communicate
without direct references. Supports both synchronous and asynchronous event handling.
"""

import logging
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum
import inspect
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class EventType(Enum):
    """All possible event types in the application."""
    
    # Configuration events
    CONFIG_LOADED = "config_loaded"
    CONFIG_SAVED = "config_saved"
    CONFIG_ERROR = "config_error"
    CONFIG_VALIDATION_ERROR = "config_validation_error"
    
    # Server events
    SERVER_TOGGLED = "server_toggled"
    SERVER_ADDED = "server_added"
    SERVER_REMOVED = "server_removed"
    SERVER_VALIDATION_ERROR = "server_validation_error"
    SERVERS_BULK_TOGGLED = "servers_bulk_toggled"
    
    # Preset events
    PRESET_APPLIED = "preset_applied"
    PRESET_SAVED = "preset_saved"
    PRESET_DELETED = "preset_deleted"
    PRESET_FAVORITED = "preset_favorited"
    
    # Mode events
    MODE_CHANGED = "mode_changed"
    MODE_SYNC_STARTED = "mode_sync_started"
    MODE_SYNC_COMPLETED = "mode_sync_completed"
    
    # Backup events
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    BACKUP_DELETED = "backup_deleted"
    BACKUP_ERROR = "backup_error"
    
    # Application events
    APP_STARTED = "app_started"
    APP_CLOSING = "app_closing"
    APP_ERROR = "app_error"
    
    # UI events
    UI_STATE_CHANGED = "ui_state_changed"
    UI_SEARCH_CHANGED = "ui_search_changed"
    UI_SELECTION_CHANGED = "ui_selection_changed"
    UI_VIEW_CHANGED = "ui_view_changed"
    UI_THEME_CHANGED = "ui_theme_changed"


@dataclass
class Event:
    """Event object containing event data."""
    
    type: EventType
    data: Dict[str, Any]
    timestamp: datetime
    source: Optional[str] = None
    
    def __init__(self, type: EventType, data: Optional[Dict[str, Any]] = None, source: Optional[str] = None):
        self.type = type
        self.data = data or {}
        self.timestamp = datetime.now()
        self.source = source


class EventDispatcher:
    """Central event dispatcher for the application.
    
    Manages event subscriptions and dispatches events to registered handlers.
    Supports both synchronous and asynchronous handlers.
    """
    
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._async_handlers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history_size = 100
        self._paused = False
        
    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """Subscribe to an event type.
        
        Args:
            event_type: The type of event to subscribe to
            handler: The function to call when the event occurs
        """
        if inspect.iscoroutinefunction(handler):
            if event_type not in self._async_handlers:
                self._async_handlers[event_type] = []
            if handler not in self._async_handlers[event_type]:
                self._async_handlers[event_type].append(handler)
                logger.debug(f"Subscribed async handler {handler.__name__} to {event_type.value}")
        else:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)
                logger.debug(f"Subscribed handler {handler.__name__} to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """Unsubscribe from an event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler function to remove
        """
        if inspect.iscoroutinefunction(handler):
            if event_type in self._async_handlers and handler in self._async_handlers[event_type]:
                self._async_handlers[event_type].remove(handler)
                logger.debug(f"Unsubscribed async handler {handler.__name__} from {event_type.value}")
        else:
            if event_type in self._handlers and handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
                logger.debug(f"Unsubscribed handler {handler.__name__} from {event_type.value}")
    
    def emit(self, event: Event) -> None:
        """Emit an event to all registered handlers.
        
        Args:
            event: The event to emit
        """
        if self._paused:
            logger.debug(f"Event emission paused, skipping {event.type.value}")
            return
            
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history_size:
            self._event_history.pop(0)
        
        logger.info(f"Emitting event: {event.type.value} from {event.source}")
        
        # Call synchronous handlers
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in handler {handler.__name__}: {e}")
        
        # Schedule async handlers
        if event.type in self._async_handlers:
            for handler in self._async_handlers[event.type]:
                asyncio.create_task(self._call_async_handler(handler, event))
    
    async def _call_async_handler(self, handler: Callable, event: Event) -> None:
        """Call an async handler with error handling.
        
        Args:
            handler: The async handler to call
            event: The event to pass to the handler
        """
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Error in async handler {handler.__name__}: {e}")
    
    def emit_now(self, event_type: EventType, data: Optional[Dict[str, Any]] = None, source: Optional[str] = None) -> None:
        """Convenience method to create and emit an event immediately.
        
        Args:
            event_type: The type of event to emit
            data: Optional event data
            source: Optional source identifier
        """
        event = Event(event_type, data, source)
        self.emit(event)
    
    def clear_handlers(self, event_type: Optional[EventType] = None) -> None:
        """Clear all handlers for a specific event type or all handlers.
        
        Args:
            event_type: The event type to clear handlers for, or None to clear all
        """
        if event_type:
            self._handlers.pop(event_type, None)
            self._async_handlers.pop(event_type, None)
            logger.debug(f"Cleared handlers for {event_type.value}")
        else:
            self._handlers.clear()
            self._async_handlers.clear()
            logger.debug("Cleared all handlers")
    
    def pause(self) -> None:
        """Pause event emission."""
        self._paused = True
        logger.debug("Event dispatcher paused")
    
    def resume(self) -> None:
        """Resume event emission."""
        self._paused = False
        logger.debug("Event dispatcher resumed")
    
    def get_history(self, event_type: Optional[EventType] = None, limit: int = 10) -> List[Event]:
        """Get recent event history.
        
        Args:
            event_type: Filter by event type, or None for all events
            limit: Maximum number of events to return
            
        Returns:
            List of recent events
        """
        history = self._event_history
        if event_type:
            history = [e for e in history if e.type == event_type]
        return history[-limit:]
    
    def get_handler_count(self, event_type: EventType) -> int:
        """Get the number of handlers for an event type.
        
        Args:
            event_type: The event type to check
            
        Returns:
            Number of registered handlers
        """
        sync_count = len(self._handlers.get(event_type, []))
        async_count = len(self._async_handlers.get(event_type, []))
        return sync_count + async_count


# Global dispatcher instance
dispatcher = EventDispatcher()


def get_dispatcher() -> EventDispatcher:
    """Get the global event dispatcher instance.
    
    Returns:
        The global EventDispatcher instance
    """
    return dispatcher