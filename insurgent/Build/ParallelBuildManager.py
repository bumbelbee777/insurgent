import asyncio
import os
import time
import threading
import multiprocessing
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor

from insurgent.Build.BuildEngine import BuildEngine
from insurgent.Build.BuildTask import BuildTask
from insurgent.Build.build import build, clean
from insurgent.Logging.logger import error, info, warning, success
from insurgent.TUI.box import Box
from insurgent.TUI.text import Text
from insurgent.Shell.Shell import Shell


class ParallelBuildManager:
    """
    Manages parallel building of targets with dependency resolution.
    """

    def __init__(self, project, max_workers=None, verbose=False):
        """
        Initialize the parallel build manager.

        Args:
            project: Project to build
            max_workers: Maximum number of parallel workers (default: CPU count)
            verbose: Whether to enable verbose output
        """
        self.project = project
        self.verbose = verbose
        self.tasks = {}
        self.queue = Queue()
        self.results = Queue()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.running = False
        self.workers = []

        # Determine the number of workers
        if max_workers is None:
            self.max_workers = multiprocessing.cpu_count()
        else:
            self.max_workers = max(1, int(max_workers))

        # Task status tracking
        self.pending_tasks = set()
        self.completed_tasks = set()
        self.failed_tasks = set()
        self.running_tasks = set()

    def _create_task(self, target):
        """
        Create a build task for the specified target.

        Args:
            target: Target name to build

        Returns:
            BuildTask object
        """
        if target in self.tasks:
            return self.tasks[target]

        # Get target information from the project
        action = self.project.get_target_action(target)
        dependencies = self.project.get_target_dependencies(target)

        # Create the task
        task = BuildTask(target, action, dependencies, self.project)
        self.tasks[target] = task
        return task

    def _process_dependencies(self, target):
        """
        Process dependencies for a target and add them to the queue.

        Args:
            target: Target name to process

        Returns:
            List of unresolved dependencies
        """
        task = self._create_task(target)
        unresolved = []

        for dep in task.dependencies:
            # Skip already completed dependencies
            if dep in self.completed_tasks:
                continue

            # Mark failed dependencies
            if dep in self.failed_tasks:
                unresolved.append(dep)
                continue

            # Add dependency to the pending queue if not already there
            if dep not in self.pending_tasks and dep not in self.running_tasks:
                self.pending_tasks.add(dep)
                # Recursively process its dependencies
                unresolved_deps = self._process_dependencies(dep)
                if not unresolved_deps:
                    # If all dependencies are resolved, add to the queue
                    self.queue.put(dep)
                else:
                    unresolved.extend(unresolved_deps)

        return unresolved

    def _worker(self):
        """Worker thread that processes build tasks from the queue."""
        while self.running:
            try:
                # Get a task from the queue with timeout
                target = self.queue.get(timeout=0.1)

                # Skip if the task was already processed
                if target in self.completed_tasks or target in self.failed_tasks:
                    self.queue.task_done()
                    continue

                # Get the task object
                task = self.tasks.get(target)
                if not task:
                    task = self._create_task(target)

                # Update status
                with self.lock:
                    self.pending_tasks.discard(target)
                    self.running_tasks.add(target)

                # Log start of task
                if self.verbose:
                    print(f"Building {Text(target).bold()}")

                # Execute the task
                task.execute()

                # Update status based on result
                with self.lock:
                    self.running_tasks.discard(target)
                    if task.failed:
                        self.failed_tasks.add(target)
                        # Log error
                        if self.verbose:
                            print(
                                f"Failed to build {Text(target).bold().red()}: {task.error}"
                            )
                    else:
                        self.completed_tasks.add(target)
                        # Log completion
                        if self.verbose:
                            duration = task.duration()
                            print(
                                f"Built {Text(target).bold().green()} in {duration:.2f}s"
                            )

                # Add the result to the results queue
                self.results.put(target)

                # Notify waiting threads
                with self.condition:
                    self.condition.notify_all()

                self.queue.task_done()

            except Empty:
                # No tasks in the queue, check if we should exit
                if not self.running or (
                    len(self.pending_tasks) == 0 and len(self.running_tasks) == 0
                ):
                    break

    def build(self, targets):
        """
        Build the specified targets in parallel.

        Args:
            targets: List of target names to build

        Returns:
            True if all targets were built successfully, False otherwise
        """
        if not targets:
            return True

        # Start the build process
        self.running = True

        # Clear previous state
        self.tasks = {}
        self.pending_tasks = set()
        self.completed_tasks = set()
        self.failed_tasks = set()
        self.running_tasks = set()

        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except Empty:
                break

        while not self.results.empty():
            try:
                self.results.get_nowait()
                self.results.task_done()
            except Empty:
                break

        # Process targets and their dependencies
        for target in targets:
            self.pending_tasks.add(target)
            unresolved = self._process_dependencies(target)
            if not unresolved:
                self.queue.put(target)

        # Start worker threads
        self.workers = []
        for _ in range(self.max_workers):
            thread = threading.Thread(target=self._worker)
            thread.daemon = True
            thread.start()
            self.workers.append(thread)

        # Wait for all tasks to complete
        try:
            while self.running and (
                len(self.running_tasks) > 0 or len(self.pending_tasks) > 0
            ):
                with self.condition:
                    # Wait for a notification or timeout
                    self.condition.wait(0.1)

                # Check for failed tasks that might block the queue
                if len(self.failed_tasks) > 0 and len(self.pending_tasks) > 0:
                    # Check if pending tasks are blocked by failures
                    blocked = False
                    for target in list(self.pending_tasks):
                        task = self.tasks.get(target)
                        if not task:
                            continue

                        for dep in task.dependencies:
                            if dep in self.failed_tasks:
                                blocked = True
                                self.pending_tasks.discard(target)
                                self.failed_tasks.add(target)
                                # Log dependency failure
                                if self.verbose:
                                    print(
                                        f"Skipping {Text(target).bold().yellow()}: "
                                        f"dependency {Text(dep).bold().red()} failed"
                                    )

                    if blocked:
                        # Notify waiting threads about the status change
                        with self.condition:
                            self.condition.notify_all()
        finally:
            # Stop all workers
            self.running = False

            # Wait for all workers to finish
            for thread in self.workers:
                thread.join(0.1)

            self.workers = []

        # Return success status
        return len(self.failed_tasks) == 0

    def get_failed_targets(self):
        """Get the list of failed targets."""
        return list(self.failed_tasks)

    def get_task_output(self, target):
        """Get the output of a specific task."""
        task = self.tasks.get(target)
        if not task:
            return []
        return task.output

    def get_task_error(self, target):
        """Get the error message for a failed task."""
        task = self.tasks.get(target)
        if not task or not task.failed:
            return None
        return task.error
