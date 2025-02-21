import os
from insurgent.Logging.terminal import *

def write_to_log_file(message):
    log_file_path = os.path.join(os.path.dirname(__file__), "../build.log")
    if os.path.exists(log_file_path):
        os.rename(log_file_path, log_file_path + ".old")
    with open(log_file_path, "a") as f:
        f.write(message + "\n")

def log(message, silent=False):
    formatted = f"{GREEN}[BUILD]{RESET} {message}"
    if not silent:
        print(formatted)
    write_to_log_file(f"[BUILD] {message}")

def error(message):
    formatted = f"{RED}[ERROR]{RESET} {message}"
    print(formatted)
    write_to_log_file(f"[ERROR] {message}")