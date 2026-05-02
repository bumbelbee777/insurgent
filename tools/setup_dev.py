#!/usr/bin/env python3
"""
Setup script for InsurgeNT development environment.
This script helps set up a virtual environment, install dependencies, and configure linting tools.
"""

import argparse
import os
import platform
import subprocess
import sys
import venv
from pathlib import Path

def run_command(cmd, **kwargs):
    """Run a command and print its output."""
    print(f"Running: {' '.join(cmd)}")
    process = subprocess.run(cmd, **kwargs)
    if process.returncode != 0:
        print(f"Command failed with exit code {process.returncode}")
        sys.exit(process.returncode)
    return process

def create_venv(venv_path):
    """Create a virtual environment at the specified path."""
    venv_path = os.path.abspath(venv_path)
    print(f"Creating virtual environment at {venv_path}...")
    venv.create(venv_path, with_pip=True)
    
    # Get the path to the Python executable in the virtual environment
    if platform.system() == "Windows":
        python_executable = os.path.join(venv_path, "Scripts", "python.exe")
        pip_executable = os.path.join(venv_path, "Scripts", "pip.exe")
    else:
        python_executable = os.path.join(venv_path, "bin", "python")
        pip_executable = os.path.join(venv_path, "bin", "pip")
    
    # Upgrade pip
    run_command([python_executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    return python_executable, pip_executable

def install_dependencies(pip_executable, editable=True):
    """Install required dependencies."""
    print("Installing dependencies...")
    run_command([pip_executable, "install", "-r", "requirements.txt"])
    
    # Install development tools
    print("Installing development tools...")
    run_command([pip_executable, "install", "flake8", "black", "isort", "pytest", "pytest-cov"])
    
    # Install the package in editable mode
    if editable:
        print("Installing InsurgeNT package in editable mode...")
        run_command([pip_executable, "install", "-e", "."])

def setup_git_hooks(python_executable):
    return

def run_lint(python_executable):
    """Run linting tools."""
    print("Running Black (code formatter)...")
    run_command([python_executable, "-m", "black", "insurgent", "tests"])
    
    print("Running isort (import sorter)...")
    run_command([python_executable, "-m", "isort", "insurgent", "tests"])
    
    print("Running flake8 (code linter)...")
    run_command([
        python_executable, "-m", "flake8", 
        "insurgent", "tests", 
        "--count", "--select=E9,F63,F7,F82", 
        "--show-source", "--statistics"
    ])

def main():
    parser = argparse.ArgumentParser(description="Set up development environment for InsurgeNT")
    parser.add_argument("--venv", default=".venv", help="Path to virtual environment")
    parser.add_argument("--no-editable", action="store_true", help="Don't install package in editable mode")
    parser.add_argument("--lint", action="store_true", help="Run linting tools after setup")
    parser.add_argument("--hooks", action="store_true", help="Set up git hooks")
    
    args = parser.parse_args()
    
    # Get absolute path to the project root
    project_root = Path(__file__).parent.parent.resolve()
    os.chdir(project_root)
    
    # Create virtual environment (use absolute path)
    venv_path = Path(args.venv).resolve()
    python_executable, pip_executable = create_venv(venv_path)
    
    # Install dependencies
    install_dependencies(pip_executable, not args.no_editable)
    
    # Set up git hooks if requested
    if args.hooks:
        setup_git_hooks(python_executable)
    
    # Run linting if requested
    if args.lint:
        run_lint(python_executable)
    
    # Print activation instructions
    if platform.system() == "Windows":
        activate_bat = os.path.join(venv_path, "Scripts", "activate.bat")
        activate_ps1 = os.path.join(venv_path, "Scripts", "Activate.ps1")
        print(f"\nTo activate the virtual environment in CMD, run:")
        print(f"    {activate_bat}")
        print(f"\nTo activate in PowerShell, run:")
        print(f"    {activate_ps1}")
        print("\nNote: In PowerShell, you may need to change execution policy:")
        print("    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser")
    else:
        activate_cmd = f"source {os.path.join(venv_path, 'bin', 'activate')}"
        print(f"\nTo activate the virtual environment, run:")
        print(f"    {activate_cmd}")
    
    # Test if python is in PATH after activation
    try:
        if platform.system() == "Windows":
            test_cmd = f"cmd /c \"{activate_bat} && where python\""
        else:
            test_cmd = f"bash -c \"{activate_cmd} && which python\""
        
        result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print("\nWARNING: Virtual environment activation may not be adding Python to your PATH.")
            print("After activation, if 'python' command is not found, use the full path:")
            print(f"    {python_executable}")
    except Exception:
        # Silently ignore errors in this test
        pass
    
    print("\nSetup complete! 🚀")

if __name__ == "__main__":
    main() 