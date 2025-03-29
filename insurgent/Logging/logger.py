import os
import datetime
import sys
from insurgent.Logging.terminal import *

def write_to_log_file(message):
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
            for color in [RED, GREEN, BLUE, YELLOW, MAGENTA, CYAN, RESET, BOLD]:
                clean_message = clean_message.replace(color, '')
            f.write(f"[{timestamp}] {clean_message}\n")
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}", file=sys.stderr)

def log(message, to_stdout=True):
    try:
        write_to_log_file(f"[BUILD] {message}")
        if to_stdout:
            formatted = f"{GREEN}[BUILD]{RESET} {message}"
            print(formatted)
    except Exception as e:
        print(f"Warning: Logging error: {e}", file=sys.stderr)
        if to_stdout:
            formatted = f"{GREEN}[BUILD]{RESET} {message}"
            print(formatted)

def error(message):
    try:
        write_to_log_file(f"[ERROR] {message}")
        formatted = f"{RED}[ERROR]{RESET} {message}"
        print(formatted)
    except Exception as e:
        print(f"Warning: Error logging error: {e}", file=sys.stderr)
        formatted = f"{RED}[ERROR]{RESET} {message}"
        print(formatted)