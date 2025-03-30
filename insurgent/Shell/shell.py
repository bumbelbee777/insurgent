"""
InsurgeNT Shell class - main entry point for the interactive shell
"""

import os
import sys
import shlex
import time
from typing import Dict, List, Optional, Tuple

from insurgent.Logging.terminal import *
from .config import Config
from .history import History
from .executor import Executor


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

        # Flag to indicate if the shell should exit
        self.running = True

    def run(self):
        """Run the interactive shell."""
        print(f"{GREEN}InsurgeNT Shell{RESET}")
        print(
            f"Type {CYAN}help{RESET} for available commands, {CYAN}exit{RESET} to quit."
        )
        print()

        self.running = True

        # Main loop
        while self.running:
            try:
                # Display prompt
                prompt = f"{BLUE}{os.getcwd()}{RESET}> "

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

                # Print output if any
                if output:
                    print(output)

            except KeyboardInterrupt:
                print()
                continue
            except EOFError:
                self.running = False
                print("exit")
            except Exception as e:
                print(f"{RED}Error:{RESET} {str(e)}")

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
                print(output)
            return 0 if self.executor.get_last_exit_code() == 0 else 1
        except Exception as e:
            print(f"{RED}Error:{RESET} {str(e)}")
            return 1


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
