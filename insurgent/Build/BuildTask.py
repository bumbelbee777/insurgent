"""
Build task management for InsurgeNT.
"""

import asyncio
import os
import time
from typing import Any, Dict, List, Optional, Callable, Awaitable
from pathlib import Path

from insurgent.logging.logger import error, info, log, success, warning
from insurgent.logging.terminal import *
from insurgent.rich_utils import (
    create_panel,
    create_table,
    style_text,
    print_panel,
    print_table,
    print_styled
)
from insurgent.build.BuildEngine import BuildEngine


class BuildTask:
    """
    Represents an asynchronous build task.
    """

    def __init__(
        self,
        name: str,
        action: Callable[..., Awaitable[bool]],
        dependencies: Optional[List[str]] = None,
        engine: Optional[BuildEngine] = None,
        **kwargs
    ):
        """
        Initialize a build task.

        Args:
            name: Task name
            action: Async function to execute for this task
            dependencies: List of task names that must be built first
            engine: BuildEngine instance to use
            **kwargs: Additional task configuration
        """
        self.name = name
        self.action = action
        self.dependencies = dependencies or []
        self.engine = engine
        self.config = kwargs
        
        # Task state
        self.completed = False
        self.failed = False
        self.start_time = None
        self.end_time = None
        self.output = []
        self.error = None
        
        # Task metadata
        self.metadata = {
            'created_at': time.time(),
            'last_run': None,
            'run_count': 0,
            'total_duration': 0,
        }

    async def execute(self) -> bool:
        """
        Execute the build task asynchronously.

        Returns:
            True if task succeeded, False otherwise
        """
        self.start_time = time.time()
        self.metadata['last_run'] = self.start_time
        self.metadata['run_count'] += 1
        
        try:
            # Run the action
            result = await self.action(**self.config)
            self.completed = result
            if not result:
                self.failed = True
                self.error = "Task action returned False"
        except Exception as e:
            self.failed = True
            self.error = str(e)
            # Include traceback in the output
            import traceback
            self.output.append(traceback.format_exc())
        finally:
            self.end_time = time.time()
            duration = self.duration()
            self.metadata['total_duration'] += duration
            
        return self.completed and not self.failed

    def duration(self) -> float:
        """
        Get the task execution duration in seconds.

        Returns:
            Duration in seconds
        """
        if self.start_time is None:
            return 0
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time

    def add_dependency(self, dependency: str) -> None:
        """
        Add a dependency to this task.

        Args:
            dependency: Name of the dependency task
        """
        if dependency not in self.dependencies:
            self.dependencies.append(dependency)

    def remove_dependency(self, dependency: str) -> None:
        """
        Remove a dependency from this task.

        Args:
            dependency: Name of the dependency task
        """
        if dependency in self.dependencies:
            self.dependencies.remove(dependency)

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get task metadata.

        Returns:
            Dictionary of task metadata
        """
        return {
            **self.metadata,
            'dependencies': self.dependencies,
            'completed': self.completed,
            'failed': self.failed,
            'last_duration': self.duration(),
        }

    def __str__(self) -> str:
        return f"BuildTask({self.name})"
