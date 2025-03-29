import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

# Add insurgent module to path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from insurgent.Shell.shell import save_history, load_history, add_to_history
from insurgent.Shell.builtins import ls, cd, mkdir, rm, touch, cp, cat

class TestShellHistory(unittest.TestCase):
    def setUp(self):
        # Reset command history before each test
        from insurgent.Shell.shell import command_history
        command_history.clear()
    
    def test_add_to_history(self):
        from insurgent.Shell.shell import command_history
        
        # Test adding a command
        add_to_history("test command")
        self.assertEqual(len(command_history), 1)
        self.assertEqual(command_history[0], "test command")
        
        # Test adding duplicate command (should not add)
        add_to_history("test command")
        self.assertEqual(len(command_history), 1)
        
        # Test adding different command
        add_to_history("another command")
        self.assertEqual(len(command_history), 2)
        self.assertEqual(command_history[1], "another command")
    
    def test_save_and_load_history(self):
        from insurgent.Shell.shell import command_history
        
        # Add some commands
        add_to_history("command one")
        add_to_history("command two")
        
        # Create a temporary history file
        temp_history_file = "temp_test_history.txt"
        
        # Save history
        save_history(temp_history_file)
        
        # Clear history
        command_history.clear()
        self.assertEqual(len(command_history), 0)
        
        # Load history
        load_history(temp_history_file)
        
        # Verify loaded history
        self.assertEqual(len(command_history), 2)
        self.assertEqual(command_history[0], "command one")
        self.assertEqual(command_history[1], "command two")
        
        # Clean up
        if os.path.exists(temp_history_file):
            os.remove(temp_history_file)


class TestShellBuiltins(unittest.TestCase):
    def setUp(self):
        # Save current directory to restore after test
        self.original_dir = os.getcwd()
        
        # Create a temporary test directory
        self.test_dir = os.path.join(os.getcwd(), "test_shell_dir")
        if not os.path.exists(self.test_dir):
            os.mkdir(self.test_dir)
        
        # Change to test directory
        os.chdir(self.test_dir)
    
    def tearDown(self):
        # Change back to original directory
        os.chdir(self.original_dir)
        
        # Remove test directory
        if os.path.exists(self.test_dir):
            import shutil
            shutil.rmtree(self.test_dir)
    
    def test_ls(self):
        # Create some files
        touch("test_file1.txt")
        touch("test_file2.txt")
        
        # Test ls command
        files = ls()
        self.assertIn("test_file1.txt", files)
        self.assertIn("test_file2.txt", files)
    
    def test_mkdir_and_cd(self):
        # Test mkdir
        mkdir("test_subdir")
        self.assertTrue(os.path.exists("test_subdir"))
        
        # Test cd
        cd("test_subdir")
        self.assertEqual(os.path.basename(os.getcwd()), "test_subdir")
    
    def test_touch_and_cat(self):
        # Test touch
        touch("test_content.txt")
        self.assertTrue(os.path.exists("test_content.txt"))
        
        # Write some content
        with open("test_content.txt", "w") as f:
            f.write("Test content")
        
        # Test cat
        content = cat("test_content.txt")
        self.assertEqual(content, "Test content")
    
    def test_cp_and_rm(self):
        # Create a file
        touch("source_file.txt")
        with open("source_file.txt", "w") as f:
            f.write("Test content")
        
        # Test cp
        cp("source_file.txt", "dest_file.txt")
        self.assertTrue(os.path.exists("dest_file.txt"))
        
        # Verify content was copied
        with open("dest_file.txt", "r") as f:
            content = f.read()
        self.assertEqual(content, "Test content")
        
        # Test rm
        rm("source_file.txt")
        self.assertFalse(os.path.exists("source_file.txt"))


if __name__ == "__main__":
    unittest.main() 