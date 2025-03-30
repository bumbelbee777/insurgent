import time
from insurgent.Logging.logger import error, info, warning, success

class BuildTask:
    """
    Represents a build task to be executed in the build queue.
    """

    def __init__(self, target, action, dependencies=None, project=None):
        """
        Initialize a build task.

        Args:
            target: Target name to build
            action: Build action to perform
            dependencies: List of dependencies that must be built first
            project: Project this task belongs to
        """
        self.target = target
        self.action = action
        self.dependencies = dependencies or []
        self.project = project
        self.completed = False
        self.failed = False
        self.start_time = None
        self.end_time = None
        self.output = []
        self.error = None

    def execute(self):
        """Execute the build task and update its status."""
        self.start_time = time.time()
        try:
            # Run the action
            self.action()
            self.completed = True
        except Exception as e:
            self.failed = True
            self.error = str(e)
            # Include traceback in the output
            import traceback

            self.output.append(traceback.format_exc())
        finally:
            self.end_time = time.time()

    def duration(self):
        """Get the task execution duration in seconds."""
        if self.start_time is None:
            return 0
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time

    def __str__(self):
        """Get string representation of the task."""
        return f"BuildTask({self.target})"