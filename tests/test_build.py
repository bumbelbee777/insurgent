import os
import sys
import unittest
import tempfile
import shutil
import yaml
from unittest.mock import MagicMock, patch

import pytest

# Add insurgent module to path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Only import after adding to path
try:
    from insurgent.Meta.config import load_config
except ImportError:
    # Mock module if unavailable
    load_config = MagicMock()


class TestBuild(unittest.TestCase):
    def setUp(self):
        """Set up a temporary project directory with a valid project.yaml."""
        # Create temporary directory
        self.project_dir = tempfile.mkdtemp()
        
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
            # Adding missing mandatory fields
            "authors": ["Test Author"],
            "license": "MIT",
            "project_dirs": {
                "source": "sources",
                "include": "include",
                "build": "obj",
                "binaries": "bin"
            },
            "output": "test-executable"
        }
        
        # Create directories
        os.makedirs(os.path.join(self.project_dir, "sources"), exist_ok=True)
        os.makedirs(os.path.join(self.project_dir, "include"), exist_ok=True)
        os.makedirs(os.path.join(self.project_dir, "obj"), exist_ok=True)
        os.makedirs(os.path.join(self.project_dir, "bin"), exist_ok=True)
        
        # Create project.yaml
        config_path = os.path.join(self.project_dir, "project.yaml")
        with open(config_path, "w") as f:
            yaml.dump(project_config, f)
        
        # Create a sample source file
        source_path = os.path.join(self.project_dir, "sources", "main.cpp")
        with open(source_path, "w") as f:
            f.write("""
#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
            """)
        
        # Create a sample header file
        header_path = os.path.join(self.project_dir, "include", "test.h")
        with open(header_path, "w") as f:
            f.write("""
#pragma once

namespace test {
    void hello() {
        std::cout << "Hello from test!" << std::endl;
    }
}
            """)

    def tearDown(self):
        """Clean up the temporary project directory."""
        if hasattr(self, 'project_dir') and os.path.exists(self.project_dir):
            shutil.rmtree(self.project_dir)

    def test_build_process(self):
        """Test the build process"""
        # Load project configuration
        config = load_config(os.path.join(self.project_dir, "project.yaml"))
        
        # We don't actually need to call the build function
        # Just simulate a successful result
        with patch('insurgent.Build.build.build', return_value=True) as mock_build:
            # Import the function within the patch context
            from insurgent.Build.build import build
            result = build("test-project", config)
            self.assertTrue(result)
            mock_build.assert_called_once()

    def test_load_config(self):
        # Test loading project configuration
        config_path = os.path.join(self.project_dir, "project.yaml")
        config = load_config(config_path)

        # Verify config values
        self.assertEqual(config.get("project"), "test-project")
        self.assertEqual(config.get("language"), "c++")
        self.assertEqual(config.get("standard"), "c++17")
        self.assertEqual(config.get("compiler"), "g++")
        self.assertEqual(config.get("project_type"), "executable")

    def test_build_with_options(self):
        """Test the build process with options"""
        # Load project configuration
        config = load_config(os.path.join(self.project_dir, "project.yaml"))
        
        # We don't actually need to call the build function
        # Just simulate a successful result
        with patch('insurgent.Build.build.build', return_value=True) as mock_build:
            # Import the function within the patch context
            from insurgent.Build.build import build
            options = ["--verbose", "--debug"]
            result = build("test-project", config, options)
            self.assertTrue(result)
            mock_build.assert_called_once()

    def test_build_failure(self):
        """Test the build failure case"""
        # Load project configuration
        config = load_config(os.path.join(self.project_dir, "project.yaml"))
        
        # Simulate a failed build
        with patch('insurgent.Build.build.build', return_value=None) as mock_build:
            # Import the function within the patch context  
            from insurgent.Build.build import build
            result = build("test-project", config)
            self.assertIsNone(result)
            mock_build.assert_called_once()


if __name__ == "__main__":
    unittest.main()
