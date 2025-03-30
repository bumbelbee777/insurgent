import os
import shutil
import tempfile
import pytest
import yaml


@pytest.fixture
def example_project(request):
    """
    Fixture to set up a temporary project directory with a valid project.yaml.
    """
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()

    # Define a basic project structure
    project_config = {
        "project": "test-project",
        "language": "c++",
        "standard": "c++17",
        "compiler": "g++",
        "project_type": "executable",
        "sources": ["sources/*.cpp"],
        "includes": ["include"],
        "libraries": ["pthread", "m"],
        "optimize": True,
        "debug": False,
        "warnings": "all",
    }

    # Create directories
    os.makedirs(os.path.join(temp_dir, "sources"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "include"), exist_ok=True)

    # Create project.yaml
    config_path = os.path.join(temp_dir, "project.yaml")
    with open(config_path, "w") as f:
        yaml.dump(project_config, f)

    # Create a sample source file
    source_path = os.path.join(temp_dir, "sources", "main.cpp")
    with open(source_path, "w") as f:
        f.write(
            """
#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
        """
        )

    # Create a sample header file
    header_path = os.path.join(temp_dir, "include", "test.h")
    with open(header_path, "w") as f:
        f.write(
            """
#pragma once

namespace test {
    void hello() {
        std::cout << "Hello from test!" << std::endl;
    }
}
        """
        )

    # Cleanup after test
    def finalizer():
        shutil.rmtree(temp_dir)

    request.addfinalizer(finalizer)

    return temp_dir
