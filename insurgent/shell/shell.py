"""
InsurgeNT Shell class - main entry point for the interactive shell
"""

import asyncio
import os
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

from .config import Config
from .executor import Executor
from .history import History

# Custom theme for rich
INSURGENT_THEME = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "red",
        "success": "green",
        "prompt": "bold blue",
        "code": "bold green",
        "path": "bold cyan",
        "version": "bold yellow",
    }
)

# Command symbols
COMMAND_SYMBOLS = {
    "build": "⚡",
    "test": "🧪",
    "clean": "🧹",
    "rebuild": "🔄",
    "scorch": "🔥",
    "init": "✨",
    "help": "❓",
    "exit": "👋",
}


def get_command_symbol(cmd: str) -> str:
    """Get the symbol for a command."""
    return COMMAND_SYMBOLS.get(cmd.split()[0], ">")


class Shell:
    """Interactive shell for InsurgeNT"""

    def __init__(
        self, config_file: Optional[str] = None, history_file: Optional[str] = None
    ):
        """
        Initialize the shell

        Args:
            config_file: Path to config file
            history_file: Path to history file
        """
        # Initialize configuration
        self.config = Config(config_file)

        # Initialize history
        self.history = History(history_file)

        # Initialize executor
        self.executor = Executor(self.config, self.history)

        # Initialize console
        self.console = Console(theme=INSURGENT_THEME)

        # Flag to indicate if the shell should exit
        self.running = True

    def run(self):
        """Run the interactive shell."""
        self.console.print(
            Panel.fit(
                "[bold green]✨ InsurgeNT Shell[/]\n"
                "[dim]Type 'help' for available commands, 'exit' to quit.[/]",
                title="Welcome",
                border_style="green",
            )
        )

        self.running = True

        # Main loop
        while self.running:
            try:
                # Display prompt
                prompt = f"(int) [path]{os.getcwd()}[/]% "

                # Get input
                command = input(prompt)

                # Skip empty commands
                if not command or command.strip() == "":
                    continue

                # Execute command
                output = self.executor.execute(command)

                # Check if we should exit
                if not self.executor.is_running():
                    self.running = False
                    self.console.print("[success]👋 Goodbye![/]")

                # Print output if any
                if output:
                    if hasattr(output, "__rich_console__") or hasattr(
                        output, "__rich__"
                    ):
                        self.console.print(output)
                    else:
                        print(output)

            except KeyboardInterrupt:
                print()
                continue
            except EOFError:
                self.running = False
                self.console.print("[success]👋 Goodbye![/]")
            except Exception as e:
                self.console.print(f"[error]Error: {str(e)}[/]")

        # Cleanup
        self.executor.cleanup()
        return 0

    def execute_command(self, command: str) -> int:
        """
        Execute a single command.

        Args:
            command: Command to execute

        Returns:
            Exit code (0 for success)
        """
        try:
            output = self.executor.execute(command)
            if output:
                if hasattr(output, "__rich_console__") or hasattr(output, "__rich__"):
                    self.console.print(output)
                else:
                    print(output)

            # Propagate the executor's running state so callers (and tests)
            # can observe shell exit without driving the full REPL loop.
            if not self.executor.is_running():
                self.running = False

            return 0 if self.executor.get_last_exit_code() == 0 else 1
        except Exception as e:
            self.console.print(f"[error]Error: {str(e)}[/]")
            return 1


class ShellInterface:
    """
    Main shell interface that combines executor and TUI components.
    """

    def __init__(self):
        self.executor = Executor()
        self.console = Console(theme=INSURGENT_THEME)

    def run_shell(self):
        """
        Run the interactive shell.

        Returns:
            int: Exit code (0 for success)
        """
        try:
            self.console.print(
                Panel.fit(
                    "[bold green]✨ InsurgeNT Shell[/]\n"
                    "[dim]Type 'help' for available commands, 'exit' to quit.[/]",
                    title="Welcome",
                    border_style="green",
                )
            )

            while True:
                try:
                    command = input(f"(int) [path]{os.getcwd()}[/]% ").strip()
                    if not command:
                        continue

                    output = self.executor.execute(command)

                    if output:
                        if hasattr(output, "__rich_console__") or hasattr(
                            output, "__rich__"
                        ):
                            self.console.print(output)
                        else:
                            print(output)

                    # Stop the loop on explicit exit commands or when the
                    # executor signals it is no longer running.
                    head = command.split()[0].lower() if command.split() else ""
                    if head in ("exit", "quit") or not self.executor.is_running():
                        self.console.print("[success]Goodbye![/]")
                        break

                except KeyboardInterrupt:
                    print("\nUse 'exit' to quit")
                except Exception as e:
                    self.console.print(f"[error]Error: {str(e)}[/]")
        except EOFError:
            self.console.print("[success]👋 Goodbye![/]")
            return 0
        finally:
            self.executor.cleanup()

    def run_command(self, cmd: str) -> Optional[str]:
        """
        Runs a single command and returns its output.

        Args:
            cmd: Command string to execute

        Returns:
            str: Command output or None
        """
        try:
            output = self.executor.execute(cmd)

            # Handle Rich text objects
            if hasattr(output, "__rich_console__") or hasattr(output, "__rich__"):
                with self.console.capture() as capture:
                    self.console.print(output)
                return capture.get()

            # Handle regular strings
            return str(output) if output is not None else None

        except Exception as e:
            return f"[error]Error: {str(e)}[/]"
        finally:
            self.executor.cleanup()


# Global command history for testing
command_history = []


def add_to_history(command):
    """
    Add a command to the history.
    Used for testing.

    Args:
        command: Command string
    """
    # Don't add empty commands
    if not command or command.strip() == "":
        return

    # Don't add duplicates of the most recent command
    if command_history and command_history[-1] == command:
        return

    # Add to history
    command_history.append(command)


def save_history(filename):
    """
    Save command history to a file.
    Used for testing.

    Args:
        filename: Path to save history to
    """
    with open(filename, "w") as f:
        for cmd in command_history:
            f.write(f"{cmd}\n")


def load_history(filename):
    """
    Load command history from a file.
    Used for testing.

    Args:
        filename: Path to load history from
    """
    command_history.clear()

    if not os.path.exists(filename):
        return

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                command_history.append(line)
