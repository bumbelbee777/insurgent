import datetime
import os
import sys
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from insurgent.rich_utils import (
    create_panel,
    style_text,
    print_panel,
    print_styled
)


def _find_project_root():
    # Start from the current file's directory and search upward for project.yaml
    path = os.path.abspath(os.path.dirname(__file__))
    while True:
        candidate = os.path.join(path, "project.yaml")
        if os.path.isfile(candidate):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    # Fallback: use cwd
    return os.getcwd()


def write_to_log_file(message):
    project_root = _find_project_root()
    log_file_path = os.path.join(project_root, "build.log")
    try:
        if os.path.exists(log_file_path):
            try:
                if not os.path.exists(log_file_path + ".old"):
                    os.rename(log_file_path, log_file_path + ".old")
            except (OSError, IOError):
                pass
        with open(log_file_path, "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Convert Rich Text objects to plain text
            if isinstance(message, Text):
                clean_message = message.plain
            else:
                clean_message = str(message)
            f.write(f"[{timestamp}] {clean_message}\n")
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}", file=sys.stderr)


def log(message, to_stdout=True, use_box=False):
    # Convert message to string if it's not a Rich Text object
    if not isinstance(message, Text):
        message = str(message) if message is not None else ""
    try:
        write_to_log_file(f"[BUILD] {message}")
        if to_stdout:
            if use_box:
                print_panel(message, title="Build")
            else:
                print_styled("[BUILD]", color="green", bold=True)
                print(message)
    except Exception as e:
        print(f"Warning: Logging error: {e}", file=sys.stderr)
        if to_stdout:
            print(f"[BUILD] {message}")


def error(message, use_box=True):
    # Convert message to string if it's not a Rich Text object
    if not isinstance(message, Text):
        message = str(message) if message is not None else ""
    try:
        write_to_log_file(f"[ERROR] {message}")
        if use_box:
            print_panel(message, title="Error", box_style="heavy")
        else:
            print_styled("[ERROR]", color="red", bold=True)
            print(message)
    except Exception as e:
        print(f"Warning: Error logging error: {str(e)}", file=sys.stderr)
        print(f"[ERROR] {message}")


def warning(message, use_box=False):
    # Convert message to string if it's not a Rich Text object
    if not isinstance(message, Text):
        message = str(message) if message is not None else ""
    try:
        write_to_log_file(f"[WARNING] {message}")
        if use_box:
            print_panel(message, title="Warning")
        else:
            print_styled("[WARNING]", color="yellow", bold=True)
            print(message)
    except Exception as e:
        print(f"Warning: Warning logging error: {str(e)}", file=sys.stderr)
        print(f"[WARNING] {message}")


def info(message, use_box=False):
    # Convert message to string if it's not a Rich Text object
    if not isinstance(message, Text):
        message = str(message) if message is not None else ""
    try:
        write_to_log_file(f"[INFO] {message}")
        if use_box:
            print_panel(message, title="Info")
        else:
            print_styled("[INFO]", color="blue", bold=True)
            print(message)
    except Exception as e:
        print(f"Warning: Info logging error: {str(e)}", file=sys.stderr)
        print(f"[INFO] {message}")


def success(message, use_box=False):
    # Convert message to string if it's not a Rich Text object
    if not isinstance(message, Text):
        message = str(message) if message is not None else ""
    try:
        write_to_log_file(f"[SUCCESS] {message}")
        if use_box:
            print_panel(message, title="Success")
        else:
            print_styled("[SUCCESS]", color="green", bold=True)
            print(message)
    except Exception as e:
        print(f"Warning: Success logging error: {str(e)}", file=sys.stderr)
        print(f"[SUCCESS] {message}")


def debug(message):
    # Convert message to string if it's not a Rich Text object
    if not isinstance(message, Text):
        message = str(message) if message is not None else ""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        write_to_log_file(f"({timestamp}) [DEBUG] {message}")
        print(f"({timestamp}) [DEBUG] {message}")
    except Exception as e:
        print(f"Warning: Debug logging error: {str(e)}", file=sys.stderr)
