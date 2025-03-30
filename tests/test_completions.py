import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add insurgent module to path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from insurgent.Shell.completions import (get_completions, get_path_completions,
                                         handle_tab,
                                         register_command_completions)


class TestCompletions(unittest.TestCase):
    def setUp(self):
        # Create a temporary test directory
        self.test_dir = os.path.join(os.getcwd(), "test_completions_dir")
        if not os.path.exists(self.test_dir):
            os.mkdir(self.test_dir)

        # Create some files in the test directory
        for file_name in ["file1.txt", "file2.txt", "test_file.py"]:
            with open(os.path.join(self.test_dir, file_name), "w") as f:
                f.write("Test content")

        # Create a subdirectory
        self.subdir = os.path.join(self.test_dir, "subdir")
        if not os.path.exists(self.subdir):
            os.mkdir(self.subdir)

    def tearDown(self):
        # Remove test directory
        if os.path.exists(self.test_dir):
            import shutil

            shutil.rmtree(self.test_dir)

    def test_command_completions(self):
        # Test empty input
        completions = get_completions("")
        self.assertTrue(len(completions) > 0)
        self.assertIn("ls", completions)
        self.assertIn("cd", completions)

        # Test partial command
        completions = get_completions("c")
        self.assertIn("cd", completions)
        self.assertIn("cp", completions)
        self.assertIn("cat", completions)
        self.assertIn("clear", completions)

        # Test specific command
        completions = get_completions("cd")
        self.assertEqual(len(completions), 1)
        self.assertEqual(completions[0], "cd")

    def test_path_completions(self):
        # Test with real files in the test directory
        os.chdir(self.test_dir)
        
        # Test path completion with empty string (should list current directory)
        completions = get_path_completions("")
        self.assertEqual(len(completions), 4)  # 3 files + 1 subdirectory
        self.assertIn("file1.txt", completions)
        self.assertIn("file2.txt", completions)
        self.assertIn("test_file.py", completions)
        self.assertIn("subdir/", completions)
        
        # Test partial path completion
        completions = get_path_completions("f")
        self.assertEqual(len(completions), 2)
        self.assertIn("file1.txt", completions)
        self.assertIn("file2.txt", completions)
        
        # Test completion with specific extension
        completions = get_path_completions("test")
        self.assertEqual(len(completions), 1)
        self.assertIn("test_file.py", completions)
        
        # Test completion with path to subdirectory
        completions = get_path_completions("sub")
        self.assertEqual(len(completions), 1)
        self.assertIn("subdir/", completions)
        
        # Return to original directory after test
        os.chdir("..")

    @patch("os.listdir")
    @patch("os.path.isdir")
    @patch("os.path.exists")
    def test_path_completions_with_mocks(self, mock_exists, mock_isdir, mock_listdir):
        # Mock os.path.isdir to identify directories correctly
        mock_isdir.side_effect = lambda path: path.endswith("subdir")
        
        # Mock os.path.exists to return True for test paths
        mock_exists.return_value = True
        
        # Mock os.listdir to return test files
        mock_listdir.return_value = ["file1.txt", "file2.txt", "subdir"]
        
        # Test path completion with empty path
        completions = get_path_completions("")
        mock_listdir.assert_called_with(".")
        self.assertEqual(len(completions), 3)
        self.assertIn("file1.txt", completions)
        self.assertIn("file2.txt", completions)
        self.assertIn("subdir/", completions)
        
        # Test path completion with specific prefix
        completions = get_path_completions("f")
        self.assertEqual(len(completions), 2)
        self.assertIn("file1.txt", completions)
        self.assertIn("file2.txt", completions)

    def test_register_command_completions(self):
        # Register completions for a command
        register_command_completions("test-command", ["option1", "option2", "flag"])

        # Test completions for the registered command
        completions = get_completions("test-command ")
        self.assertEqual(len(completions), 3)
        self.assertIn("option1", completions)
        self.assertIn("option2", completions)
        self.assertIn("flag", completions)

        # Test partial completions
        completions = get_completions("test-command o")
        self.assertEqual(len(completions), 2)
        self.assertIn("option1", completions)
        self.assertIn("option2", completions)

    def test_handle_tab(self):
        # Test single tab with a unique completion
        new_input, should_redisplay = handle_tab("l", 1)
        self.assertEqual(new_input, "ls ")

        # Test tab with multiple possibilities (first tab should show options)
        with patch("builtins.print"):
            new_input, should_redisplay = handle_tab("c", 1)
            self.assertEqual(new_input, "c")
            self.assertTrue(should_redisplay)
        
        # Since cycling depends on the completions available, which can vary
        # by environment, we'll skip testing that part for now
        pass


if __name__ == "__main__":
    unittest.main()
