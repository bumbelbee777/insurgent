import os
import sys
import shutil
import tempfile
import pytest

# Ensure the insurgent module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    # Change to the temp directory
    os.chdir(temp_dir)
    
    yield temp_dir
    
    # Cleanup and return to original directory
    os.chdir(original_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_history():
    """Create a temporary history file and reset command history"""
    from insurgent.Shell.shell import command_history
    
    # Save original history
    original_history = command_history.copy()
    
    # Reset history for testing
    command_history.clear()
    
    # Create temporary history file
    temp_history_file = tempfile.mktemp(suffix=".txt")
    
    yield temp_history_file
    
    # Cleanup
    if os.path.exists(temp_history_file):
        os.remove(temp_history_file)
    
    # Restore original history
    command_history.clear()
    command_history.extend(original_history)


@pytest.fixture
def example_project():
    """Create an example project structure for testing"""
    temp_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    # Create project structure
    os.makedirs(os.path.join(temp_dir, "sources"), exist_ok=True)
    
    # Create example source file
    with open(os.path.join(temp_dir, "sources", "main.cpp"), "w") as f:
        f.write("""
#include <iostream>

int main() {
    std::cout << "Hello, InsurgeNT!" << std::endl;
    return 0;
}
""")
    
    # Create project.yaml
    with open(os.path.join(temp_dir, "project.yaml"), "w") as f:
        f.write("""
project: test-project
description: Test project for InsurgeNT
authors: Test Author
license: MIT
version: 0.1.0
language: c++
standard: c++17
compiler: g++
compiler_flags:
  global: "-fPIC"
  common: "-O2 -Wall"
  cpp: "-std=c++17"
project_dirs:
- sources
project_type: executable
output: bin/test-project
bootstrap:
  task: prepare
  command: mkdir -p bin
""")
    
    # Change to project directory
    os.chdir(temp_dir)
    
    yield temp_dir
    
    # Cleanup and return to original directory
    os.chdir(original_dir)
    shutil.rmtree(temp_dir) 