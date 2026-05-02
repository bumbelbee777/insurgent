"""
Rich-based utilities for InsurgeNT.
This module provides utilities for creating beautiful terminal interfaces using Rich.
"""

from rich.panel import Panel
from rich.table import Table as RichTable
from rich.text import Text as RichText
from rich.console import Console
from rich.theme import Theme as RichTheme
from rich.box import (
    ROUNDED,
    DOUBLE,
    HEAVY,
    SIMPLE,
    MINIMAL,
    ASCII,
    SQUARE,
    MARKDOWN
)

# Create a default console instance
console = Console()

# Default theme styles
DEFAULT_STYLES = {
    "info": "blue",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "path": "cyan",
    "command": "white",
    "highlight": "magenta"
}

# Create default theme
default_theme = RichTheme(DEFAULT_STYLES)

def create_panel(content, title=None, box_style=ROUNDED, padding=1):
    """Create a Rich panel with the given content and style.
    
    Args:
        content: The content to display in the panel
        title: Optional title for the panel
        box_style: Box style from rich.box
        padding: Padding around content
        
    Returns:
        Panel: Rich Panel object
    """
    return Panel(
        content,
        title=title,
        box=box_style,
        padding=padding
    )

def create_table(headers=None, title=None):
    """Create a Rich table with the given headers.
    
    Args:
        headers: List of column headers
        title: Optional table title
        
    Returns:
        Table: Rich Table object
    """
    table = RichTable(title=title)
    if headers:
        for header in headers:
            table.add_column(header)
    return table

def style_text(text, color=None, bg_color=None, bold=False, italic=False, underline=False):
    """Apply styling to text.
    
    Args:
        text: Text to style
        color: Text color
        bg_color: Background color
        bold: Whether to make text bold
        italic: Whether to make text italic
        underline: Whether to underline text
        
    Returns:
        Text: Rich Text object
    """
    rich_text = RichText(str(text))
    if color:
        rich_text.stylize(color, 0, len(str(text)))
    if bg_color:
        rich_text.stylize(f"on {bg_color}", 0, len(str(text)))
    if bold:
        rich_text.stylize("bold", 0, len(str(text)))
    if italic:
        rich_text.stylize("italic", 0, len(str(text)))
    if underline:
        rich_text.stylize("underline", 0, len(str(text)))
    return rich_text

def print_panel(content, title=None, box_style=ROUNDED, padding=1):
    """Print a panel to the console.
    
    Args:
        content: The content to display in the panel
        title: Optional title for the panel
        box_style: Box style from rich.box
        padding: Padding around content
    """
    console.print(create_panel(content, title, box_style, padding))

def print_table(headers=None, rows=None, title=None):
    """Print a table to the console.
    
    Args:
        headers: List of column headers
        rows: List of rows to add to the table
        title: Optional table title
    """
    table = create_table(headers, title)
    if rows:
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
    console.print(table)

def print_styled(text, color=None, bg_color=None, bold=False, italic=False, underline=False):
    """Print styled text to the console.
    
    Args:
        text: Text to print
        color: Text color
        bg_color: Background color
        bold: Whether to make text bold
        italic: Whether to make text italic
        underline: Whether to underline text
    """
    console.print(style_text(text, color, bg_color, bold, italic, underline)) 