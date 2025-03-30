#!/usr/bin/env python3
# Copyright (c) InsurgeNT Project
# SPDX-License-Identifier: Apache-2.0

"""
Logging utility functions for the InsurgeNT project.
"""

import datetime
import os
import sys

from insurgent.Logging.terminal import *
from insurgent.TUI.text import Text
from insurgent.TUI.box import Box


def write_to_log_file(message):
    """
    Write a message to the build log file.

    Args:
        message: The message to write to the log file
    """
    log_file_path = os.path.join(os.path.dirname(__file__), "../build.log")
    try:
        if os.path.exists(log_file_path):
            try:
                # Try to rename the existing log file
                if not os.path.exists(log_file_path + ".old"):
                    os.rename(log_file_path, log_file_path + ".old")
                else:
                    # If .old already exists, append to the existing log
                    pass
            except (OSError, IOError):
                # If rename fails, we'll just append to the existing file
                pass

        # Open in append mode to add new log entries
        with open(log_file_path, "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Strip color codes for log file
            clean_message = message
            for color in [
                RED,
                GREEN,
                BLUE,
                YELLOW,
                MAGENTA,
                CYAN,
                RESET,
                BOLD,
                ITALIC,
                UNDERLINE,
            ]:
                clean_message = clean_message.replace(color, "")
            f.write(f"[{timestamp}] {clean_message}\n")
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}", file=sys.stderr)


def log(message, to_stdout=True, use_box=False):
    """
    Log a build message.

    Args:
        message: The message to log
        to_stdout: Whether to print the message to stdout
        use_box: Whether to display the message in a box (for important messages)
    """
    try:
        write_to_log_file(f"[BUILD] {message}")
        if to_stdout:
            if use_box:
                box = Box(style="light", title="Build")
                box_lines = box.draw([message])
                for line in box_lines:
                    print(line)
            else:
                label = Text.style("[BUILD]", color="green", bold=True)
                formatted = f"{label} {message}"
                print(formatted)
    except Exception as e:
        print(f"Warning: Logging error: {e}", file=sys.stderr)
        if to_stdout:
            formatted = f"{GREEN}[BUILD]{RESET} {message}"
            print(formatted)


def error(message, use_box=True):
    """
    Log an error message.

    Args:
        message: The error message to log
        use_box: Whether to display the message in a box
    """
    try:
        write_to_log_file(f"[ERROR] {message}")
        if use_box:
            box = Box(style="heavy", title="Error")
            box_lines = box.draw([message])
            for line in box_lines:
                print(line)
        else:
            label = Text.style("[ERROR]", color="red", bold=True)
            formatted = f"{label} {message}"
            print(formatted)
    except Exception as e:
        print(f"Warning: Error logging error: {e}", file=sys.stderr)
        formatted = f"{RED}[ERROR]{RESET} {message}"
        print(formatted)


def warning(message, use_box=False):
    """
    Log a warning message.

    Args:
        message: The warning message to log
        use_box: Whether to display the message in a box
    """
    try:
        write_to_log_file(f"[WARNING] {message}")
        if use_box:
            box = Box(style="light", title="Warning")
            box_lines = box.draw([message])
            for line in box_lines:
                print(line)
        else:
            label = Text.style("[WARNING]", color="yellow", bold=True)
            formatted = f"{label} {message}"
            print(formatted)
    except Exception as e:
        print(f"Warning: Warning logging error: {e}", file=sys.stderr)
        formatted = f"{YELLOW}[WARNING]{RESET} {message}"
        print(formatted)


def info(message, use_box=False):
    """
    Log an info message.

    Args:
        message: The info message to log
        use_box: Whether to display the message in a box
    """
    try:
        write_to_log_file(f"[INFO] {message}")
        if use_box:
            box = Box(style="light", title="Info")
            box_lines = box.draw([message])
            for line in box_lines:
                print(line)
        else:
            label = Text.style("[INFO]", color="blue", bold=True)
            formatted = f"{label} {message}"
            print(formatted)
    except Exception as e:
        print(f"Warning: Info logging error: {e}", file=sys.stderr)
        formatted = f"{BLUE}[INFO]{RESET} {message}"
        print(formatted)


def success(message, use_box=False):
    """
    Log a success message.

    Args:
        message: The success message to log
        use_box: Whether to display the message in a box
    """
    try:
        write_to_log_file(f"[SUCCESS] {message}")
        if use_box:
            box = Box(style="light", title="Success")
            box_lines = box.draw([message])
            for line in box_lines:
                print(line)
        else:
            label = Text.style("[SUCCESS]", color="green", bold=True)
            formatted = f"{label} {message}"
            print(formatted)
    except Exception as e:
        print(f"Warning: Success logging error: {e}", file=sys.stderr)
        formatted = f"{GREEN}[SUCCESS]{RESET} {message}"
        print(formatted)
