import os
import sys
import shlex
import shutil
import subprocess
import threading
from pathlib import Path

from .history import History
from .config import Config
from ..TUI.text import Text


class Executor:
    """
    Command executor for the InsurgeNT Shell.
    Handles command parsing, execution, and output capturing.
    """

    def __init__(self, config=None, history=None):
        """
        Initialize the command executor.

        Args:
            config: Shell configuration
            history: Command history manager
        """
        self.config = config or Config()
        self.history = history or History()
        self.builtin_commands = {
            "cd": self._change_directory,
            "exit": self._exit,
            "quit": self._exit,
            "history": self._show_history,
            "clear": self._clear_screen,
            "alias": self._manage_aliases,
            "help": self._show_help,
            "pwd": self._print_working_directory,
            "echo": self._echo,
        }
        self.running = True
        self.last_exit_code = 0

    def execute(self, command):
        """
        Execute a command.

        Args:
            command: Command string to execute

        Returns:
            Command output as string
        """
        if not command or command.strip() == "":
            return ""

        # Add to history
        self.history.add(command)

        # Parse the command
        args = self._parse_command(command)
        if not args:
            return ""

        # Check for command aliases
        command_name = args[0]
        if self.config and hasattr(self.config, "expand_alias"):
            expanded = self.config.expand_alias(command_name)
            if expanded != command_name:
                # Replace the command with its alias
                expanded_args = self._parse_command(expanded)
                args = expanded_args + args[1:]
                command_name = args[0]

        # Execute builtin command
        if command_name in self.builtin_commands:
            try:
                output = self.builtin_commands[command_name](args[1:])
                self.last_exit_code = 0
                return output or ""
            except Exception as e:
                self.last_exit_code = 1
                return str(e)

        # Execute external command
        return self._execute_external(args)

    def _parse_command(self, command):
        """
        Parse a command string into arguments.

        Args:
            command: Command string

        Returns:
            List of command arguments
        """
        try:
            return shlex.split(command)
        except ValueError as e:
            print(f"Error parsing command: {e}")
            return []

    def _execute_external(self, args):
        """
        Execute an external command.

        Args:
            args: Command arguments

        Returns:
            Command output as string
        """
        try:
            # Create subprocess
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True,
            )

            # Capture output
            stdout, stderr = process.communicate()

            # Set exit code
            self.last_exit_code = process.returncode

            # Return output
            if stderr and process.returncode != 0:
                return stderr
            return stdout

        except FileNotFoundError:
            self.last_exit_code = 127  # Command not found
            return f"Command not found: {args[0]}"
        except PermissionError:
            self.last_exit_code = 126  # Permission denied
            return f"Permission denied: {args[0]}"
        except Exception as e:
            self.last_exit_code = 1
            return f"Error executing command: {e}"

    def _change_directory(self, args):
        """
        Change current directory.

        Args:
            args: Directory path

        Returns:
            Empty string on success, error message on failure
        """
        if not args:
            # Change to home directory if no args provided
            path = os.path.expanduser("~")
        else:
            path = args[0]

        try:
            # Expand ~ to home directory
            path = os.path.expanduser(path)

            # Change directory
            os.chdir(path)
            return ""
        except FileNotFoundError:
            return f"cd: {path}: No such file or directory"
        except NotADirectoryError:
            return f"cd: {path}: Not a directory"
        except PermissionError:
            return f"cd: {path}: Permission denied"
        except Exception as e:
            return f"cd: Error: {e}"

    def _exit(self, args):
        """Exit the shell."""
        self.running = False
        return "Exiting..."

    def _show_history(self, args):
        """Show command history."""
        count = 10
        if args and args[0].isdigit():
            count = int(args[0])

        history_items = self.history.get_last_n(count)
        if not history_items:
            return "No history items"

        result = []
        for i, cmd in enumerate(history_items):
            result.append(f"{i+1}: {cmd}")

        return "\n".join(result)

    def _clear_screen(self, args):
        """Clear the terminal screen."""
        os.system("cls" if os.name == "nt" else "clear")
        return ""

    def _manage_aliases(self, args):
        """Manage command aliases."""
        if not self.config or not hasattr(self.config, "get_aliases"):
            return "Alias management not available"

        # No arguments: list all aliases
        if not args:
            aliases = self.config.get_aliases()
            if not aliases:
                return "No aliases defined"

            result = []
            for name, value in aliases.items():
                result.append(f"{name}='{value}'")
            return "\n".join(result)

        # One argument with '=': set alias
        if len(args) == 1 and "=" in args[0]:
            name, value = args[0].split("=", 1)
            name = name.strip()
            value = value.strip()

            if not name:
                return "Invalid alias name"

            # Remove quotes if present
            if value.startswith(("'", '"')) and value.endswith(("'", '"')):
                value = value[1:-1]

            self.config.add_alias(name, value)
            self.config.save()
            return f"Alias '{name}' set to '{value}'"

        # Two arguments: set alias
        if len(args) >= 2:
            name = args[0]
            value = " ".join(args[1:])

            self.config.add_alias(name, value)
            self.config.save()
            return f"Alias '{name}' set to '{value}'"

        return "Usage: alias [name=value]"

    def _show_help(self, args):
        """Show help information."""
        builtin_commands = sorted(self.builtin_commands.keys())

        result = ["Available built-in commands:"]
        for cmd in builtin_commands:
            result.append(f"  {cmd}")

        result.append(
            "\nFor external commands, refer to their respective documentation."
        )
        return "\n".join(result)

    def _print_working_directory(self, args):
        """Print current working directory."""
        return os.getcwd()

    def _echo(self, args):
        """Echo arguments to output."""
        return " ".join(args)

    def is_running(self):
        """Check if the executor is still running."""
        return self.running

    def get_last_exit_code(self):
        """Get the exit code of the last executed command."""
        return self.last_exit_code
