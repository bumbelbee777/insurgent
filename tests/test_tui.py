import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from insurgent.TUI.box import Box
from insurgent.TUI.text import Text
from insurgent.TUI.table import Table
from insurgent.TUI.theme import Theme


class TestText(unittest.TestCase):
    """Test cases for the Text class"""

    def test_style_color(self):
        """Test applying color styling to text"""
        styled = Text.style("Hello", color="red")
        self.assertIn("\033[31m", styled)
        self.assertIn("Hello", styled)
        self.assertIn("\033[0m", styled)

    def test_style_multiple(self):
        """Test applying multiple styles to text"""
        styled = Text.style("Hello", color="blue", bold=True, underline=True)
        self.assertIn("\033[34m", styled)
        self.assertIn("\033[1m", styled)
        self.assertIn("\033[4m", styled)
        self.assertIn("Hello", styled)

    def test_style_bg_color(self):
        """Test applying background color"""
        styled = Text.style("Hello", bg_color="green")
        self.assertIn("\033[42m", styled)
        self.assertIn("Hello", styled)

    def test_strip_ansi(self):
        """Test stripping ANSI codes from text"""
        styled = Text.style("Hello", color="red", bold=True)
        stripped = Text.strip_ansi(styled)
        self.assertEqual(stripped, "Hello")

    def test_visible_length(self):
        """Test getting visible length of styled text"""
        styled = Text.style("Hello", color="red", bold=True)
        length = Text.get_visible_length(styled)
        self.assertEqual(length, 5)

    def test_align(self):
        """Test text alignment"""
        # Left alignment (default)
        aligned = Text.align("Hello", 10)
        self.assertEqual(aligned, "Hello     ")

        # Center alignment
        aligned = Text.align("Hello", 10, alignment="center")
        self.assertEqual(aligned, "  Hello   ")

        # Right alignment
        aligned = Text.align("Hello", 10, alignment="right")
        self.assertEqual(aligned, "     Hello")


class TestBox(unittest.TestCase):
    """Test cases for the Box class"""

    def test_box_creation(self):
        """Test creating a simple box"""
        box = Box(style="single")
        result = box.draw(["Hello", "World"])

        # Should have at least 4 lines (top border, content * 2, bottom border)
        self.assertGreaterEqual(len(result), 4)

        # Top and bottom borders should contain box characters
        self.assertIn("┌", result[0])
        self.assertIn("┐", result[0])
        self.assertIn("└", result[-1])
        self.assertIn("┘", result[-1])

    def test_box_with_title(self):
        """Test creating a box with a title"""
        box = Box(style="single", title="Test Box")
        result = box.draw(["Hello"])

        # Title should be in the output
        title_found = False
        for line in result:
            if "Test Box" in line:
                title_found = True
                break
        self.assertTrue(title_found)

    def test_box_with_padding(self):
        """Test box with padding"""
        box = Box(style="single", padding=2)
        result = box.draw(["Hello"])

        # Should have at least 6 lines (top, padding*2, content, padding*2, bottom)
        self.assertGreaterEqual(len(result), 6)

    def test_different_styles(self):
        """Test different box styles"""
        # Double style
        box = Box(style="double")
        result = box.draw(["Hello"])
        self.assertIn("╔", result[0])

        # ASCII style
        box = Box(style="ascii")
        result = box.draw(["Hello"])
        self.assertIn("+", result[0])

        # None style
        box = Box(style="none")
        result = box.draw(["Hello"])
        self.assertNotIn("┌", result[0])
        self.assertNotIn("+", result[0])


class TestTable(unittest.TestCase):
    """Test cases for the Table class"""

    def test_table_creation(self):
        """Test creating a simple table"""
        table = Table(
            headers=["Name", "Age", "Location"],
            rows=[["Alice", "30", "New York"], ["Bob", "25", "Los Angeles"]],
        )
        result = table.draw()

        # Should have at least 5 lines (top, header, separator, data*2, bottom)
        self.assertGreaterEqual(len(result), 5)

        # Headers should be in the output
        headers_found = 0
        for line in result:
            for header in ["Name", "Age", "Location"]:
                if header in line:
                    headers_found += 1
        self.assertEqual(headers_found, 3)

    def test_table_alignment(self):
        """Test table column alignment"""
        table = Table(
            headers=["Left", "Center", "Right"],
            alignments=["left", "center", "right"],
            rows=[["1", "2", "3"]],
        )
        result = table.draw()

        # Check output for expected formatting
        # Just a basic check that the table was created
        self.assertGreaterEqual(len(result), 4)

    def test_table_with_title(self):
        """Test table with a title"""
        table = Table(
            headers=["Name", "Value"], rows=[["Test", "123"]], title="Test Table"
        )
        result = table.draw()

        # Title should be in the output
        title_found = False
        for line in result:
            if "Test Table" in line:
                title_found = True
                break
        self.assertTrue(title_found)


class TestTheme(unittest.TestCase):
    """Test cases for the Theme class"""

    def test_theme_creation(self):
        """Test creating a theme"""
        theme = Theme()
        self.assertIsNotNone(theme.current_theme)

    def test_theme_selection(self):
        """Test selecting different themes"""
        # Default theme
        theme = Theme("default")
        self.assertEqual(theme.theme_name, "default")

        # Light theme
        theme = Theme("light")
        self.assertEqual(theme.theme_name, "light")

        # Dark theme
        theme = Theme("dark")
        self.assertEqual(theme.theme_name, "dark")

        # Invalid theme (should fallback to default)
        theme = Theme("invalid")
        self.assertEqual(theme.theme_name, "invalid")
        self.assertEqual(theme.current_theme, theme.DEFAULT)

    def test_get_value(self):
        """Test getting theme values"""
        theme = Theme()

        # Top-level value
        primary = theme.get("primary")
        self.assertEqual(primary, "blue")

        # Nested value
        box_border = theme.get("box.border")
        self.assertEqual(box_border, "blue")

        # Non-existent value with default
        value = theme.get("nonexistent", "default_value")
        self.assertEqual(value, "default_value")

    def test_modify_theme(self):
        """Test modifying theme values"""
        theme = Theme()

        # Modify an existing value
        result = theme.modify_theme("default", "primary", "red")
        self.assertTrue(result)
        self.assertEqual(theme.get("primary"), "red")

        # Modify a nested value
        result = theme.modify_theme("default", "box.border", "green")
        self.assertTrue(result)
        self.assertEqual(theme.get("box.border"), "green")

        # Invalid theme name
        result = theme.modify_theme("nonexistent", "primary", "red")
        self.assertFalse(result)

    def test_style_text(self):
        """Test styling text with theme values"""
        theme = Theme()

        # Style with a theme color
        styled = theme.style_text("Hello", "primary")
        self.assertIn("\033[34m", styled)  # blue
        self.assertIn("Hello", styled)


if __name__ == "__main__":
    unittest.main()
