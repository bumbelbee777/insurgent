"""
Built-in commands for the InsurgeNT Shell.
"""

import os
import shutil
from typing import Optional, List
import asyncio

from insurgent.logging.logger import error, info, log, success, warning
from insurgent.rich_utils import print_styled
from insurgent.build.BuildEngine import BuildEngine

# ANSI color codes
BLUE = "\033[34m"
RESET = "\033[0m"


def about(*args):
    """Show version information."""
    from insurgent.meta.version import VERSION, about as version_about
    return version_about()


def help_cmd(*args):
    """Show help information."""
    help_text = """
Available commands:
  about     - Show version information
  help      - Show this help message
  exit      - Exit the shell
  clear     - Clear the screen
  ls        - List directory contents
  cd        - Change directory
  mkdir     - Create directory
  rm        - Remove file/directory
  touch     - Create file
  cp        - Copy files
  cat       - Show file contents
  pwd       - Show current directory
  history   - Show command history
  build     - Build project
"""
    return help_text


def exit_cmd(*args):
    """Exit the shell."""
    return "exit"


def clear(*args):
    """Clear the screen."""
    os.system("cls" if os.name == "nt" else "clear")
    return ""


def ls(*args):
    """List directory contents."""
    path = args[0] if args else "."
    try:
        items = os.listdir(path)
        items.sort()
        return "\n".join(items)
    except Exception as e:
        return f"Error: {str(e)}"


def cd(*args):
    """Change directory."""
    if not args:
        path = os.path.expanduser("~")
    else:
        path = args[0]

    try:
        os.chdir(path)
        return ""
    except Exception as e:
        return f"Error: {str(e)}"


def mkdir(*args):
    """Create directory."""
    if not args:
        return "Error: No directory specified"

    try:
        os.makedirs(args[0], exist_ok=True)
        return ""
    except Exception as e:
        return f"Error: {str(e)}"


def rm(*args):
    """Remove file/directory."""
    if not args:
        return "Error: No file/directory specified"

    try:
        path = args[0]
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return ""
    except Exception as e:
        return f"Error: {str(e)}"


def touch(*args):
    """Create file."""
    if not args:
        return "Error: No file specified"

    try:
        with open(args[0], "a"):
            pass
        return ""
    except Exception as e:
        return f"Error: {str(e)}"


def cp(*args):
    """Copy files."""
    if len(args) < 2:
        return "Error: Source and destination required"

    try:
        shutil.copy2(args[0], args[1])
        return ""
    except Exception as e:
        return f"Error: {str(e)}"


def cat(*args):
    """Show file contents."""
    if not args:
        return "Error: No file specified"

    try:
        with open(args[0], "r") as f:
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"


def cwd(*args):
    """Show current directory."""
    return os.getcwd()


def history(*args):
    """Show command history."""
    from .History import History
    history = History()
    return "\n".join(history.get_last_n(10))


async def build(*args):
    """Build project in the current working directory."""
    try:
        engine = BuildEngine(os.getcwd())

        incremental = "--no-incremental" not in args
        silent = "--silent" in args
        build_subprojects = "--with-subprojects" in args

        ok, reason = await engine.build(
            incremental=incremental,
            silent=silent,
            build_subprojects=build_subprojects,
        )
        return "" if ok else f"Build failed: {reason}"

    except Exception as e:
        return f"Error: {str(e)}"
