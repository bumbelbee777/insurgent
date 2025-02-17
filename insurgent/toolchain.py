import os
import subprocess
import sys
import time
from terminal import *

TOOLCHAIN_DIR = os.path.abspath("toolchain")
BUILD_DIR = os.path.abspath("build")
INSTALL_DIR = "/usr/bin"

def run_command(cmd, cwd=None, show_output=False):
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if show_output:
            print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"{CROSS} {RED}Error:{RESET} Command '{cmd}' failed.\n{GRAY}{e.stderr.strip()}{RESET}")
        sys.exit(1)

def download_sources():
    return

def build_toolchain():
    return

def install_toolchain():
    if INSTALL_DIR not in os.environ["PATH"]:
        print(f"{ARROW} {YELLOW}Adding {INSTALL_DIR}/bin to PATH...{RESET}")
        os.environ["PATH"] += os.pathsep + os.path.join(INSTALL_DIR, "bin")
        print(f"{CHECK} {GREEN}Toolchain added to PATH! Restart your shell or add it manually.{RESET}")

def make_toolchain():
    print(f"{BOLD}{MAGENTA}🔥 InsurgeNT Toolchain Builder 🔥{RESET}")
    download_sources()
    build_toolchain()
    install_toolchain()
    print(f"\n{BOLD}{GREEN}🚀 Toolchain setup complete! May your project compile without errors!{RESET}\n")
