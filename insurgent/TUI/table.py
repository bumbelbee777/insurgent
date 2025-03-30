from .text import Text
from .box import Box


class Table:
    """
    Terminal UI table component that displays data in rows and columns.
    Supports styling, alignment, and different border styles.
    """

    def __init__(
        self,
        headers=None,
        rows=None,
        style="light",
        alignments=None,
        widths=None,
        padding=1,
        title=None,
        border_color=None,
    ):
        """
        Initialize a table.

        Args:
            headers: List of column headers
            rows: List of rows, where each row is a list of cells
            style: Table border style (light, heavy, double, simple, ascii, none)
            alignments: List of alignments for each column (left, center, right)
            widths: List of column widths (or None for auto-sizing)
            padding: Cell padding
            title: Table title
            border_color: Color for table borders
        """
        self.headers = headers or []
        self.rows = rows or []
        self.style = style
        self.alignments = alignments or []
        self.widths = widths or []
        self.padding = max(0, padding)
        self.title = title
        self.border_color = border_color

        # Box drawing characters for different styles
        self.styles = {
            "light": {
                "horizontal": "─",
                "vertical": "│",
                "top_left": "┌",
                "top_right": "┐",
                "bottom_left": "└",
                "bottom_right": "┘",
                "top_t": "┬",
                "bottom_t": "┴",
                "left_t": "├",
                "right_t": "┤",
                "cross": "┼",
            },
            "heavy": {
                "horizontal": "━",
                "vertical": "┃",
                "top_left": "┏",
                "top_right": "┓",
                "bottom_left": "┗",
                "bottom_right": "┛",
                "top_t": "┳",
                "bottom_t": "┻",
                "left_t": "┣",
                "right_t": "┫",
                "cross": "╋",
            },
            "double": {
                "horizontal": "═",
                "vertical": "║",
                "top_left": "╔",
                "top_right": "╗",
                "bottom_left": "╚",
                "bottom_right": "╝",
                "top_t": "╦",
                "bottom_t": "╩",
                "left_t": "╠",
                "right_t": "╣",
                "cross": "╬",
            },
            "simple": {
                "horizontal": "-",
                "vertical": "|",
                "top_left": "+",
                "top_right": "+",
                "bottom_left": "+",
                "bottom_right": "+",
                "top_t": "+",
                "bottom_t": "+",
                "left_t": "+",
                "right_t": "+",
                "cross": "+",
            },
            "ascii": {
                "horizontal": "-",
                "vertical": "|",
                "top_left": "+",
                "top_right": "+",
                "bottom_left": "+",
                "bottom_right": "+",
                "top_t": "+",
                "bottom_t": "+",
                "left_t": "+",
                "right_t": "+",
                "cross": "+",
            },
            "none": {
                "horizontal": " ",
                "vertical": " ",
                "top_left": " ",
                "top_right": " ",
                "bottom_left": " ",
                "bottom_right": " ",
                "top_t": " ",
                "bottom_t": " ",
                "left_t": " ",
                "right_t": " ",
                "cross": " ",
            },
        }

        # Use light style if specified style not found
        if self.style not in self.styles:
            self.style = "light"

    def add_row(self, row):
        """
        Add a row to the table.

        Args:
            row: List of cells
        """
        self.rows.append(row)

    def add_rows(self, rows):
        """
        Add multiple rows to the table.

        Args:
            rows: List of rows, where each row is a list of cells
        """
        self.rows.extend(rows)

    def set_headers(self, headers):
        """
        Set the table headers.

        Args:
            headers: List of column headers
        """
        self.headers = headers

    def _style_char(self, char):
        """Apply color styling to a table character if needed."""
        if not char or not self.border_color:
            return char
        return Text.style(char, color=self.border_color)

    def _calculate_widths(self):
        """Calculate column widths based on content."""
        num_cols = max(
            len(self.headers), max([len(row) for row in self.rows]) if self.rows else 0
        )

        # Initialize widths list if needed
        if not self.widths:
            self.widths = [0] * num_cols
        else:
            # Ensure widths list has enough elements
            self.widths.extend([0] * (num_cols - len(self.widths)))

        # Calculate minimum width for each column based on content
        for i in range(num_cols):
            # Check header width
            if i < len(self.headers):
                header_len = Text.visible_length(str(self.headers[i]))
                self.widths[i] = max(self.widths[i], header_len)

            # Check data width in each row
            for row in self.rows:
                if i < len(row):
                    cell_len = Text.visible_length(str(row[i]))
                    self.widths[i] = max(self.widths[i], cell_len)

        # Add padding
        self.widths = [w + (self.padding * 2) for w in self.widths]

    def _get_alignment(self, col_index):
        """Get alignment for a column."""
        if col_index < len(self.alignments):
            return self.alignments[col_index]
        return "left"  # Default alignment

    def _format_cell(self, content, col_index):
        """Format a cell with proper alignment and padding."""
        width = self.widths[col_index]
        alignment = self._get_alignment(col_index)
        content_str = str(content)

        visible_length = Text.visible_length(content_str)
        remaining_space = width - visible_length

        if alignment == "center":
            left_space = remaining_space // 2
            right_space = remaining_space - left_space
            return " " * left_space + content_str + " " * right_space
        elif alignment == "right":
            return " " * remaining_space + content_str
        else:  # left alignment
            return content_str + " " * remaining_space

    def draw(self):
        """
        Draw the table.

        Returns:
            List of strings representing the table
        """
        # Calculate column widths if not specified
        self._calculate_widths()

        # Get style characters
        chars = self.styles[self.style]

        # Prepare result
        result = []

        # Calculate total width
        total_width = sum(self.widths) + len(self.widths) + 1

        # Add title if provided
        if self.title:
            title_row = self._style_char(chars["top_left"])
            title_row += self._style_char(chars["horizontal"] * (total_width - 2))
            title_row += self._style_char(chars["top_right"])
            result.append(title_row)

            # Add title content
            title_content = self._style_char(chars["vertical"])
            title_text = Text.align(
                f" {self.title} ", total_width - 2, alignment="center"
            )
            title_content += title_text
            title_content += self._style_char(chars["vertical"])
            result.append(title_content)

        # Add top border
        top_border = ""
        if self.title:
            top_border += self._style_char(chars["left_t"])
        else:
            top_border += self._style_char(chars["top_left"])

        for i, width in enumerate(self.widths):
            top_border += self._style_char(chars["horizontal"] * width)
            if i < len(self.widths) - 1:
                top_border += self._style_char(chars["top_t"])

        if self.title:
            top_border += self._style_char(chars["right_t"])
        else:
            top_border += self._style_char(chars["top_right"])

        result.append(top_border)

        # Add headers if provided
        if self.headers:
            header_row = self._style_char(chars["vertical"])
            for i, header in enumerate(self.headers):
                formatted_cell = self._format_cell(header, i)
                header_row += formatted_cell
                header_row += self._style_char(chars["vertical"])
            result.append(header_row)

            # Add header separator
            header_sep = self._style_char(chars["left_t"])
            for i, width in enumerate(self.widths):
                header_sep += self._style_char(chars["horizontal"] * width)
                if i < len(self.widths) - 1:
                    header_sep += self._style_char(chars["cross"])
            header_sep += self._style_char(chars["right_t"])
            result.append(header_sep)

        # Add data rows
        for row in self.rows:
            data_row = self._style_char(chars["vertical"])
            for i in range(len(self.widths)):
                cell_content = row[i] if i < len(row) else ""
                formatted_cell = self._format_cell(cell_content, i)
                data_row += formatted_cell
                data_row += self._style_char(chars["vertical"])
            result.append(data_row)

        # Add bottom border
        bottom_border = self._style_char(chars["bottom_left"])
        for i, width in enumerate(self.widths):
            bottom_border += self._style_char(chars["horizontal"] * width)
            if i < len(self.widths) - 1:
                bottom_border += self._style_char(chars["bottom_t"])
        bottom_border += self._style_char(chars["bottom_right"])
        result.append(bottom_border)

        return result

    def has_rows(self):
        """Check if the table has any rows."""
        return bool(self.rows)

    def __str__(self):
        """Return the table as a string."""
        return "\n".join(self.draw())
