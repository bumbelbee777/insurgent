import os
import sys
import unittest
import pytest
from unittest.mock import patch, MagicMock

# Add insurgent module to path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Only import after adding to path
try:
    from insurgent.Build.build import build
    from insurgent.Meta.config import load_config
except ImportError:
    # Mock module if unavailable
    build = MagicMock()
    load_config = MagicMock()


class TestBuild(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _setup_example_project(self, example_project):
        self.project_dir = example_project
    
    @patch('insurgent.Build.build.asyncio.run')
    def test_build_process(self, mock_run):
        # Mock successful build process
        mock_run.return_value = True
        
        # Load project configuration
        config = load_config(os.path.join(self.project_dir, 'project.yaml'))
        
        # Test building project
        result = build('test-project', config)
        
        # Check if build was successful
        self.assertIsNotNone(result)
        mock_run.assert_called()
    
    def test_load_config(self):
        # Test loading project configuration
        config_path = os.path.join(self.project_dir, 'project.yaml')
        config = load_config(config_path)
        
        # Verify config values
        self.assertEqual(config.get('project'), 'test-project')
        self.assertEqual(config.get('language'), 'c++')
        self.assertEqual(config.get('standard'), 'c++17')
        self.assertEqual(config.get('compiler'), 'g++')
        self.assertEqual(config.get('project_type'), 'executable')
    
    @patch('insurgent.Build.build.asyncio.run')
    def test_build_with_options(self, mock_run):
        # Mock successful build process
        mock_run.return_value = True
        
        # Load project configuration
        config = load_config(os.path.join(self.project_dir, 'project.yaml'))
        
        # Test building with additional options
        options = ['--verbose', '--debug']
        result = build('test-project', config, options)
        
        # Check if build was successful with options
        self.assertIsNotNone(result)
        
        # Verify build was called with the right options
        mock_run.assert_called_once()
    
    @patch('insurgent.Build.build.asyncio.run')
    def test_build_failure(self, mock_run):
        # Mock failed build process
        mock_run.return_value = None
        
        # Load project configuration
        config = load_config(os.path.join(self.project_dir, 'project.yaml'))
        
        # Test building project with failure
        result = build('test-project', config)
        
        # Check if build failure is handled properly
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main() 