"""Worker thread for background operations."""

import threading
from typing import Callable, Any, Optional, Dict
from queue import Queue, Empty
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a background task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackgroundTask:
    """Represents a background task."""
    
    def __init__(self, task_id: str, func: Callable, args: tuple = (), kwargs: dict = None):
        """Initialize a background task.
        
        Args:
            task_id: Unique identifier for the task
            func: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
        """
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.progress = 0.0
        self.progress_message = ""
        self.cancellation_token = threading.Event()
    
    def execute(self):
        """Execute the task."""
        try:
            self.status = TaskStatus.RUNNING
            
            # Pass cancellation token if function accepts it
            import inspect
            sig = inspect.signature(self.func)
            if 'cancellation_token' in sig.parameters:
                self.kwargs['cancellation_token'] = self.cancellation_token
            
            self.result = self.func(*self.args, **self.kwargs)
            
            if self.cancellation_token.is_set():
                self.status = TaskStatus.CANCELLED
            else:
                self.status = TaskStatus.COMPLETED
                
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.error = str(e)
            logger.error(f"Task {self.task_id} failed: {e}")
    
    def cancel(self):
        """Request cancellation of the task."""
        self.cancellation_token.set()
    
    def update_progress(self, progress: float, message: str = ""):
        """Update task progress.
        
        Args:
            progress: Progress value (0.0 to 1.0)
            message: Optional progress message
        """
        self.progress = max(0.0, min(1.0, progress))
        self.progress_message = message


class WorkerThread:
    """Worker thread for executing background tasks."""
    
    def __init__(self, name: str = "WorkerThread"):
        """Initialize the worker thread.
        
        Args:
            name: Name for the thread
        """
        self.name = name
        self.task_queue: Queue[BackgroundTask] = Queue()
        self.current_task: Optional[BackgroundTask] = None
        self.completed_tasks: Dict[str, BackgroundTask] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.on_task_complete_callbacks: list[Callable[[BackgroundTask], None]] = []
        self.on_task_progress_callbacks: list[Callable[[BackgroundTask], None]] = []
    
    def start(self):
        """Start the worker thread."""
        if self.running:
            logger.warning(f"Worker thread {self.name} already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, name=self.name, daemon=True)
        self.thread.start()
        logger.info(f"Worker thread {self.name} started")
    
    def stop(self, timeout: float = 5.0):
        """Stop the worker thread.
        
        Args:
            timeout: Maximum time to wait for thread to stop
        """
        if not self.running:
            return
        
        self.running = False
        
        # Cancel current task if any
        if self.current_task:
            self.current_task.cancel()
        
        # Add stop sentinel
        self.task_queue.put(None)
        
        # Wait for thread to finish
        if self.thread:
            self.thread.join(timeout)
        
        logger.info(f"Worker thread {self.name} stopped")
    
    def _run(self):
        """Main worker thread loop."""
        while self.running:
            try:
                # Get next task (blocks until available)
                task = self.task_queue.get(timeout=1.0)
                
                if task is None:  # Stop sentinel
                    break
                
                self.current_task = task
                logger.info(f"Executing task {task.task_id}")
                
                # Execute the task
                task.execute()
                
                # Store completed task
                self.completed_tasks[task.task_id] = task
                
                # Notify callbacks
                for callback in self.on_task_complete_callbacks:
                    try:
                        callback(task)
                    except Exception as e:
                        logger.error(f"Error in task complete callback: {e}")
                
                self.current_task = None
                
            except Empty:
                continue  # No tasks available, continue waiting
            except Exception as e:
                logger.error(f"Error in worker thread: {e}")
    
    def submit_task(self, task_id: str, func: Callable, args: tuple = (), 
                   kwargs: dict = None) -> BackgroundTask:
        """Submit a task for background execution.
        
        Args:
            task_id: Unique identifier for the task
            func: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            
        Returns:
            The created BackgroundTask object
        """
        task = BackgroundTask(task_id, func, args, kwargs)
        self.task_queue.put(task)
        logger.info(f"Task {task_id} submitted to queue")
        return task
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status or None if not found
        """
        # Check current task
        if self.current_task and self.current_task.task_id == task_id:
            return self.current_task.status
        
        # Check completed tasks
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id].status
        
        # Check queue
        for task in list(self.task_queue.queue):
            if task and task.task_id == task_id:
                return task.status
        
        return None
    
    def get_task_result(self, task_id: str) -> Any:
        """Get the result of a completed task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task result or None if not found/not completed
        """
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            if task.status == TaskStatus.COMPLETED:
                return task.result
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if task was cancelled
        """
        # Check current task
        if self.current_task and self.current_task.task_id == task_id:
            self.current_task.cancel()
            return True
        
        # Remove from queue if pending
        queue_items = list(self.task_queue.queue)
        for task in queue_items:
            if task and task.task_id == task_id:
                self.task_queue.queue.remove(task)
                task.status = TaskStatus.CANCELLED
                return True
        
        return False
    
    def on_task_complete(self, callback: Callable[[BackgroundTask], None]):
        """Register callback for task completion.
        
        Args:
            callback: Function to call when a task completes
        """
        self.on_task_complete_callbacks.append(callback)
    
    def on_task_progress(self, callback: Callable[[BackgroundTask], None]):
        """Register callback for task progress updates.
        
        Args:
            callback: Function to call when task progress updates
        """
        self.on_task_progress_callbacks.append(callback)


class FileOperationWorker(WorkerThread):
    """Specialized worker for file operations."""
    
    def __init__(self):
        """Initialize the file operation worker."""
        super().__init__(name="FileOperationWorker")
    
    def load_config_async(self, config_controller, mode: str = None) -> BackgroundTask:
        """Load configuration in background.
        
        Args:
            config_controller: ConfigController instance
            mode: Configuration mode
            
        Returns:
            BackgroundTask for the operation
        """
        def load_config(cancellation_token):
            if cancellation_token.is_set():
                return None
            return config_controller.load_config(mode)
        
        return self.submit_task(
            f"load_config_{mode or 'current'}",
            load_config
        )
    
    def save_config_async(self, config_controller, create_backup: bool = True) -> BackgroundTask:
        """Save configuration in background.
        
        Args:
            config_controller: ConfigController instance
            create_backup: Whether to create backup
            
        Returns:
            BackgroundTask for the operation
        """
        def save_config(cancellation_token):
            if cancellation_token.is_set():
                return None
            return config_controller.save_config(create_backup)
        
        return self.submit_task(
            "save_config",
            save_config
        )
    
    def validate_config_async(self, config_controller, config_path: str = None) -> BackgroundTask:
        """Validate configuration in background.
        
        Args:
            config_controller: ConfigController instance
            config_path: Path to config file
            
        Returns:
            BackgroundTask for the operation
        """
        def validate_config(cancellation_token):
            if cancellation_token.is_set():
                return None
            return config_controller.validate_config(config_path)
        
        return self.submit_task(
            f"validate_config_{config_path or 'current'}",
            validate_config
        )