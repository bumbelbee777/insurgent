import asyncio
import os
import shlex
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple, Union

from insurgent.logging.logger import error, info, log, success, warning
from insurgent.logging.terminal import *
from insurgent.rich_utils import (
    create_panel,
    create_table,
    print_panel,
    print_styled,
    print_table,
    style_text,
)

from .config import Config
from .history import History


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
        self.executor = ThreadPoolExecutor(max_workers=os.cpu_count() or 4)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Import built-in commands
        from insurgent.shell.builtins import (
            about,
            build,
            cat,
            cd,
            clear,
            cp,
            cwd,
            exit_cmd,
            help_cmd,
            history,
            ls,
            mkdir,
            rm,
            test,
            touch,
            version_cmd,
        )

        self.builtin_commands = {
            "about": {"func": about, "help": "Show version information"},
            "help": {"func": help_cmd, "help": "Show help"},
            "h": {"func": help_cmd, "help": "Show help (alias)"},
            "?": {"func": help_cmd, "help": "Show help (alias)"},
            "version": {"func": version_cmd, "help": "Print version"},
            "v": {"func": version_cmd, "help": "Print version (alias)"},
            "exit": {"func": exit_cmd, "help": "Exit the shell"},
            "quit": {"func": exit_cmd, "help": "Exit the shell"},
            "clear": {"func": clear, "help": "Clear the screen"},
            "ls": {"func": ls, "help": "List directory contents"},
            "cd": {"func": cd, "help": "Change directory"},
            "mkdir": {"func": mkdir, "help": "Create directory"},
            "rm": {"func": rm, "help": "Remove file/directory"},
            "touch": {"func": touch, "help": "Create file"},
            "cp": {"func": cp, "help": "Copy files"},
            "cat": {"func": cat, "help": "Show file contents"},
            "pwd": {"func": cwd, "help": "Show current directory"},
            "history": {"func": history, "help": "Show command history"},
            "build": {"func": build, "help": "Build project"},
            "test": {"func": test, "help": "Build and run unit tests"},
            # Original built-ins
            "alias": {"func": self._manage_aliases, "help": "Manage aliases"},
            "echo": {"func": self._echo, "help": "Print arguments"},
        }

        # Initialize completer
        from insurgent.shell.Completer import Completer

        self.completer = Completer(
            commands={cmd: info["help"] for cmd, info in self.builtin_commands.items()}
        )

        self.running = True
        self.last_exit_code = 0

    def execute(self, command: str) -> str:
        """
        Execute a command, supporting:
        - && (execute next only if previous succeeded)
        - || (execute next only if previous failed)
        - ; (execute next regardless of previous result)
        - | (pipe output between commands)

        Args:
            command: Command string to execute

        Returns:
            Command output as string
        """
        if command in (
            "no more hiding!",
            "no more hiding",
            "NO MORE HIDING",
            "NO MORE HIDING!",
            "No more hiding",
            "No more hiding!",
        ):
            return "ALL INVADERS WILL BE EXECUTED"

        if not command or command.strip() == "":
            return ""

        # Add to history
        self.history.add(command)

        # Handle command operators
        if "&&" in command:
            return self._execute_chain(command.split("&&"), mode="success")
        elif "||" in command:
            return self._execute_chain(command.split("||"), mode="failure")
        elif ";" in command:
            return self._execute_chain(command.split(";"), mode="always")
        elif "|" in command:
            return self._execute_pipe(command.split("|"))

        # Single command execution
        return self._execute_command(command)

    def _execute_command(self, cmd: str) -> str:
        """
        Execute a single command, handling both sync and async functions.

        Args:
            cmd: Command string to execute

        Returns:
            Command output as string
        """
        # Split command into parts
        parts = cmd.split()
        if not parts:
            return ""

        command_name = parts[0]
        args = parts[1:]

        # Get command function
        if command_name not in self.builtin_commands:
            return self._execute_external(parts)

        command_func = self.builtin_commands[command_name]["func"]

        # Handle async commands
        if asyncio.iscoroutinefunction(command_func):
            try:
                result = self.loop.run_until_complete(command_func(*args))
                self.last_exit_code = 0 if result else 1
                return str(result) if result is not None else ""
            except Exception as e:
                self.last_exit_code = 1
                return str(e)
        else:
            # Handle sync commands
            try:
                result = command_func(*args)
                self.last_exit_code = 0
                return str(result) if result is not None else ""
            except Exception as e:
                self.last_exit_code = 1
                return str(e)

    def _execute_chain(self, commands: List[str], mode: str) -> str:
        """
        Execute commands in sequence with chaining logic.

        Args:
            commands: List of commands to execute
            mode: Chain mode ('success', 'failure', or 'always')

        Returns:
            Output of last executed command
        """
        output = ""
        for cmd in commands:
            cmd = cmd.strip()
            if not cmd:
                continue

            # Check if we should execute based on previous result and mode
            should_execute = (
                (mode == "always")
                or (mode == "success" and self.last_exit_code == 0)
                or (mode == "failure" and self.last_exit_code != 0)
            )

            if should_execute:
                output = self._execute_command(cmd)
            else:
                break

        return output

    def _execute_pipe(self, commands: List[str]) -> str:
        """
        Execute commands with piping (|) between them.

        Args:
            commands: List of commands to pipe together

        Returns:
            Output of last command in pipe
        """
        if len(commands) < 2:
            return self.execute(commands[0])

        # Execute first command
        output = self.execute(commands[0])

        # Pipe output to subsequent commands
        for cmd in commands[1:]:
            cmd = cmd.strip()
            if not cmd:
                continue

            # Create temp file with previous command's output
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w+") as f:
                f.write(output)
                f.flush()

                # Execute command with input from temp file
                output = self.execute(f"{cmd} < {f.name}")

        return output

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

    def _execute_external(self, args: List[str]) -> str:
        """
        Execute an external command.

        Args:
            args: Command arguments

        Returns:
            Command output as string
        """
        try:
            result = subprocess.run(args, capture_output=True, text=True, check=False)
            self.last_exit_code = result.returncode
            return result.stdout if result.stdout else result.stderr
        except Exception as e:
            self.last_exit_code = 1
            return str(e)

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

    def is_running(self) -> bool:
        """Check if the executor is still running."""
        return self.running

    def get_last_exit_code(self) -> int:
        """Get the last command's exit code."""
        return self.last_exit_code

    def cleanup(self):
        """Clean up resources."""
        self.executor.shutdown(wait=True)
        self.loop.close()
