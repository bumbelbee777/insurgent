"""
Tab completion for the InsurgeNT Shell.
"""

import os
import sys
import re
from typing import Dict, List, Optional, Callable, Any


class Completer:
    """
    Provides tab completion functionality for the shell.
    Supports command completion and path completion.
    """

    def __init__(self, commands=None):
        """
        Initialize the completer.

        Args:
            commands: Dictionary of commands available in the shell
        """
        self.commands = commands or {}
        self.completions_cache = {}
        self.custom_completers = {}

    def register_completer(self, command: str, completer: Callable):
        """
        Register a custom completer function for a command.

        Args:
            command: Command name
            completer: Function that returns completions for the command
        """
        self.custom_completers[command] = completer

    def get_completions(self, line: str, point: int = None) -> List[str]:
        """
        Get completions for a given input line.

        Args:
            line: The input line to complete
            point: Cursor position in the line (defaults to end of line)

        Returns:
            List of possible completions
        """
        if point is None:
            point = len(line)

        # Get the text being completed
        text = line[:point]

        # Split into command and args
        parts = text.split()
        if not parts:
            # Empty line, complete commands
            return self._complete_commands("")

        if len(parts) == 1 and not text.endswith(" "):
            # Completing the command name
            return self._complete_commands(parts[0])

        # Completing arguments
        command = parts[0]

        # Check for custom completer
        if command in self.custom_completers:
            return self.custom_completers[command](line, point)

        # Get word being completed
        if text.endswith(" "):
            # New argument
            current_word = ""
        else:
            current_word = parts[-1]

        # Path completion for most commands
        return self._complete_path(current_word)

    def _complete_commands(self, prefix: str) -> List[str]:
        """
        Complete command names.

        Args:
            prefix: Command prefix to complete

        Returns:
            List of matching commands
        """
        return [cmd for cmd in self.commands if cmd.startswith(prefix)]

    def _complete_path(self, prefix: str) -> List[str]:
        """
        Complete file and directory paths.

        Args:
            prefix: Path prefix to complete

        Returns:
            List of matching paths
        """
        # Handle empty input
        if not prefix:
            return self._get_directory_contents(".")

        # Expand user directory
        prefix = os.path.expanduser(prefix)

        # Get directory and filename prefix
        if os.path.isdir(prefix):
            directory = prefix
            filename_prefix = ""
        else:
            directory = os.path.dirname(prefix) or "."
            filename_prefix = os.path.basename(prefix)

        try:
            # Get contents of the directory
            contents = self._get_directory_contents(directory)

            # Filter by prefix
            matches = [item for item in contents if item.startswith(filename_prefix)]

            # Convert relative to the original path
            if directory != "." and directory != "":
                matches = [os.path.join(directory, item) for item in matches]

            return matches
        except (FileNotFoundError, PermissionError):
            return []

    def _get_directory_contents(self, directory: str) -> List[str]:
        """
        Get contents of a directory with trailing slashes for subdirectories.

        Args:
            directory: Directory path

        Returns:
            List of files and directories
        """
        try:
            items = os.listdir(directory)
            result = []

            for item in items:
                full_path = os.path.join(directory, item)
                if os.path.isdir(full_path):
                    result.append(f"{item}/")
                else:
                    result.append(item)

            return sorted(result)
        except (FileNotFoundError, PermissionError):
            return []

    def complete(self, text: str, state: int) -> Optional[str]:
        """
        Get a specific completion for readline.

        Args:
            text: Text to complete
            state: Which completion to return (0 for first match, etc.)

        Returns:
            Completion string or None if no more completions
        """
        # Cache completions for performance
        if text not in self.completions_cache:
            self.completions_cache[text] = self.get_completions(text)

        completions = self.completions_cache[text]
        if state < len(completions):
            return completions[state]
        return None
