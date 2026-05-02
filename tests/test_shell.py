import os
import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

# Add insurgent module to path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from insurgent.shell.builtins import cat, cd, cp, ls, mkdir, rm, touch
from insurgent.shell.shell import (
    Shell,
    ShellInterface,
    add_to_history,
    command_history,
    load_history,
    save_history,
)


@pytest.fixture
def shell():
    return Shell()


@pytest.fixture
def shell_interface():
    return ShellInterface()


def test_shell_initialization(shell):
    """Test shell initialization."""
    assert shell.running == True
    assert shell.executor is not None
    assert shell.history is not None
    assert shell.config is not None


def test_shell_interface_initialization(shell_interface):
    """Test shell interface initialization."""
    assert shell_interface.executor is not None
    assert shell_interface.console is not None


def test_command_execution(shell):
    """Test command execution."""
    with patch.object(shell.executor, "execute") as mock_execute:
        mock_execute.return_value = "Test output"
        result = shell.execute_command("test")
        assert result == 0
        mock_execute.assert_called_once_with("test")


def test_command_execution_with_error(shell):
    """Test command execution with error."""
    with patch.object(shell.executor, "execute") as mock_execute:
        mock_execute.side_effect = Exception("Test error")
        result = shell.execute_command("test")
        assert result == 1


def test_shell_interface_command_execution(shell_interface):
    """Test shell interface command execution."""
    with patch.object(shell_interface.executor, "execute") as mock_execute:
        mock_execute.return_value = "Test output"
        result = shell_interface.run_command("test")
        assert result == "Test output"
        mock_execute.assert_called_once_with("test")


def test_shell_interface_command_execution_with_error(shell_interface):
    """Test shell interface command execution with error."""
    with patch.object(shell_interface.executor, "execute") as mock_execute:
        mock_execute.side_effect = Exception("Test error")
        result = shell_interface.run_command("test")
        assert result == "[error]Error: Test error[/]"


def test_command_history():
    """Test command history functionality."""
    # Clear history
    add_to_history("")
    assert len(command_history) == 0

    # Add commands
    add_to_history("test1")
    add_to_history("test2")
    assert len(command_history) == 2
    assert command_history[0] == "test1"
    assert command_history[1] == "test2"

    # Test duplicate prevention
    add_to_history("test2")
    assert len(command_history) == 2


def test_history_file_operations(tmp_path):
    """Test history file operations."""
    history_file = tmp_path / "history.txt"

    # Add some commands
    add_to_history("test1")
    add_to_history("test2")

    # Save history
    save_history(str(history_file))
    assert history_file.exists()

    # Clear history
    command_history.clear()
    assert len(command_history) == 0

    # Load history
    load_history(str(history_file))
    assert len(command_history) == 2
    assert command_history[0] == "test1"
    assert command_history[1] == "test2"


def test_shell_exit(shell):
    """Test shell exit functionality."""
    with patch.object(shell.executor, "is_running") as mock_running:
        mock_running.return_value = False
        shell.execute_command("exit")
        assert shell.running == False


def test_shell_interface_exit(shell_interface):
    """Test shell interface exit functionality."""
    with patch("builtins.input", return_value="exit"):
        with patch.object(shell_interface.executor, "execute") as mock_execute:
            mock_execute.return_value = None
            shell_interface.run_shell()
            mock_execute.assert_called_once_with("exit")


def test_rich_output_handling(shell_interface):
    """Test handling of Rich output objects."""

    class RichOutput:
        def __rich_console__(self, console, options):
            yield "Rich output"

    with patch.object(shell_interface.executor, "execute") as mock_execute:
        mock_execute.return_value = RichOutput()
        result = shell_interface.run_command("test")
        assert "Rich output" in result


def test_command_symbols():
    """Test command symbol mapping."""
    from insurgent.shell.shell import get_command_symbol

    assert get_command_symbol("build") == "⚡"
    assert get_command_symbol("test") == "🧪"
    assert get_command_symbol("clean") == "🧹"
    assert get_command_symbol("rebuild") == "🔄"
    assert get_command_symbol("scorch") == "🔥"
    assert get_command_symbol("init") == "✨"
    assert get_command_symbol("help") == "❓"
    assert get_command_symbol("exit") == "👋"
    assert get_command_symbol("unknown") == ">"


class TestShellHistory(unittest.TestCase):
    def setUp(self):
        # Reset command history before each test
        command_history.clear()

    def test_add_to_history(self):
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
