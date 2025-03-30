from .text import Text


# Box drawing characters for different styles
BOX_STYLES = {
    "single": {
        "top_left": "┌",
        "top_right": "┐",
        "bottom_left": "└",
        "bottom_right": "┘",
        "horizontal": "─",
        "vertical": "│",
        "left_t": "├",
        "right_t": "┤",
        "top_t": "┬",
        "bottom_t": "┴",
        "cross": "┼",
    },
    "double": {
        "top_left": "╔",
        "top_right": "╗",
        "bottom_left": "╚",
        "bottom_right": "╝",
        "horizontal": "═",
        "vertical": "║",
        "left_t": "╠",
        "right_t": "╣",
        "top_t": "╦",
        "bottom_t": "╩",
        "cross": "╬",
    },
    "rounded": {
        "top_left": "╭",
        "top_right": "╮",
        "bottom_left": "╰",
        "bottom_right": "╯",
        "horizontal": "─",
        "vertical": "│",
        "left_t": "├",
        "right_t": "┤",
        "top_t": "┬",
        "bottom_t": "┴",
        "cross": "┼",
    },
    "bold": {
        "top_left": "┏",
        "top_right": "┓",
        "bottom_left": "┗",
        "bottom_right": "┛",
        "horizontal": "━",
        "vertical": "┃",
        "left_t": "┣",
        "right_t": "┫",
        "top_t": "┳",
        "bottom_t": "┻",
        "cross": "╋",
    },
    "light": {
        "top_left": "┌",
        "top_right": "┐",
        "bottom_left": "└",
        "bottom_right": "┘",
        "horizontal": "─",
        "vertical": "│",
        "left_t": "├",
        "right_t": "┤",
        "top_t": "┬",
        "bottom_t": "┴",
        "cross": "┼",
    },
    "heavy": {
        "top_left": "┏",
        "top_right": "┓",
        "bottom_left": "┗",
        "bottom_right": "┛",
        "horizontal": "━",
        "vertical": "┃",
        "left_t": "┣",
        "right_t": "┫",
        "top_t": "┳",
        "bottom_t": "┻",
        "cross": "╋",
    },
    "simple": {
        "top_left": "+",
        "top_right": "+",
        "bottom_left": "+",
        "bottom_right": "+",
        "horizontal": "-",
        "vertical": "|",
        "left_t": "+",
        "right_t": "+",
        "top_t": "+",
        "bottom_t": "+",
        "cross": "+",
    },
    "ascii": {
        "top_left": "+",
        "top_right": "+",
        "bottom_left": "+",
        "bottom_right": "+",
        "horizontal": "-",
        "vertical": "|",
        "left_t": "+",
        "right_t": "+",
        "top_t": "+",
        "bottom_t": "+",
        "cross": "+",
    },
    "none": {
        "top_left": " ",
        "top_right": " ",
        "bottom_left": " ",
        "bottom_right": " ",
        "horizontal": " ",
        "vertical": " ",
        "left_t": " ",
        "right_t": " ",
        "top_t": " ",
        "bottom_t": " ",
        "cross": " ",
    },
}


class Box:
    """
    Box drawing utility for TUI elements.
    Provides frames and borders for UI components.
    """

    def __init__(
        self,
        width=None,
        style="single",
        title=None,
        color=None,
        padding=1,
        align="left",
        margin=0,
    ):
        """
        Initialize a box for terminal output.

        Args:
            width: Box width (or None for auto-sizing)
            style: Box style ('single', 'double', 'rounded', 'bold', 'light', 'heavy', 'simple', 'ascii', 'none')
            title: Box title
            color: Color for the box borders
            padding: Padding inside the box
            align: Content alignment ('left', 'center', 'right')
            margin: External margin around the box
        """
        self.width = width
        self.style = style if style in BOX_STYLES else "single"
        self.title = title
        self.color = color
        self.padding = max(0, padding)
        self.align = align
        self.margin = max(0, margin)

        # Set up border characters
        self.chars = self.get_styled_char

    def get_styled_char(self, char_name):
        """Get a styled box character (with color if set)."""
        char = BOX_STYLES[self.style][char_name]
        if self.color:
            return Text(char).color(self.color)
        return char

    def wrap_content(self, content, width=None, height=None):
        """
        Wrap content with a box.

        Args:
            content: Content to wrap (string or list of strings)
            width: Width of the box (auto-calculated if None)
            height: Height of the box (auto-calculated if None)

        Returns:
            List of lines forming the boxed content
        """
        # Process content
        if content is None:
            content = []
        elif isinstance(content, str):
            content = content.split("\n")

        # Auto-calculate width if not provided
        if width is None:
            # Find the maximum content width
            content_width = (
                max([Text.visible_length(line) for line in content]) if content else 0
            )
            # Add padding
            width = content_width + (self.padding * 2) + 2  # +2 for borders
            # Add margin
            width += self.margin * 2

            # Ensure minimum width for title
            if self.title:
                title_width = (
                    Text.visible_length(self.title) + 4
                )  # +4 for borders and spacing
                width = max(width, title_width)

        # Prepare result lines
        result = []

        # Add top margin
        result.extend([""] * self.margin)

        # Add top border with title
        h_char = BOX_STYLES[self.style]["horizontal"]
        top_border = self.get_styled_char("top_left")

        # Handle title
        if self.title:
            title_text = f" {self.title} "
            title_len = Text.visible_length(title_text)
            remaining_width = width - 2 - title_len  # -2 for corners

            if remaining_width >= 0:
                left_pad = remaining_width // 2
                right_pad = remaining_width - left_pad

                top_border += h_char * left_pad
                top_border += title_text
                top_border += h_char * right_pad
            else:
                # Title too wide, truncate
                truncated_title = Text.truncate(
                    self.title, width - 6
                )  # -6 for corners and spaces
                top_border += f" {truncated_title} "
                top_border += h_char * (
                    width - 4 - Text.visible_length(truncated_title)
                )
        else:
            top_border += h_char * (width - 2)

        top_border += self.get_styled_char("top_right")
        result.append(top_border)

        # Add top padding
        for _ in range(self.padding):
            padding_line = (
                self.get_styled_char("vertical")
                + " " * (width - 2)
                + self.get_styled_char("vertical")
            )
            result.append(padding_line)

        # Add content with padding and borders
        for line in content:
            # Apply horizontal padding
            padded_line = " " * self.padding + line

            # Ensure line fits in the box width
            if Text.visible_length(padded_line) > width - 2 - self.padding:
                # Truncate if too wide
                padded_line = Text.truncate(padded_line, width - 2 - self.padding)

            # Add right padding to match width
            content_width = Text.visible_length(padded_line)
            right_padding = width - 2 - content_width
            padded_line += " " * right_padding

            # Add border
            content_line = (
                self.get_styled_char("vertical")
                + padded_line
                + self.get_styled_char("vertical")
            )
            result.append(content_line)

        # Add bottom padding
        for _ in range(self.padding):
            padding_line = (
                self.get_styled_char("vertical")
                + " " * (width - 2)
                + self.get_styled_char("vertical")
            )
            result.append(padding_line)

        # Add bottom border
        bottom_border = (
            self.get_styled_char("bottom_left")
            + h_char * (width - 2)
            + self.get_styled_char("bottom_right")
        )
        result.append(bottom_border)

        # Add bottom margin
        result.extend([""] * self.margin)

        return result

    def draw(self, content=None):
        """
        Draw the box with the given content.

        Args:
            content: Content to place inside the box (list of strings or string)

        Returns:
            List of strings representing the drawn box
        """
        return self.wrap_content(content, self.width)

    def top_border(self, width, with_title=True):
        """
        Generate the top border of the box.

        Args:
            width: Width of the box
            with_title: Whether to include the title in the border

        Returns:
            String with the top border
        """
        if not with_title or not self.title:
            return (
                self.get_styled_char("top_left")
                + self.get_styled_char("horizontal") * (width - 2)
                + self.get_styled_char("top_right")
            )

        title = f" {self.title} "
        title_len = Text.visible_length(title)

        # Ensure the box is wide enough for the title
        if width - 2 < title_len:
            title = Text.truncate(title, width - 4) + " "
            title_len = Text.visible_length(title)

        if self.align == "left":
            left_padding = 1
        elif self.align == "center":
            left_padding = (width - 2 - title_len) // 2
        else:  # right
            left_padding = width - 2 - title_len - 1

        left_padding = max(0, left_padding)
        right_padding = max(0, width - 2 - title_len - left_padding)

        return (
            self.get_styled_char("top_left")
            + self.get_styled_char("horizontal") * left_padding
            + title
            + self.get_styled_char("horizontal") * right_padding
            + self.get_styled_char("top_right")
        )

    def bottom_border(self, width):
        """
        Generate the bottom border of the box.

        Args:
            width: Width of the box

        Returns:
            String with the bottom border
        """
        return (
            self.get_styled_char("bottom_left")
            + self.get_styled_char("horizontal") * (width - 2)
            + self.get_styled_char("bottom_right")
        )

    def left_border(self):
        """Get the left border character."""
        return self.get_styled_char("vertical")

    def right_border(self):
        """Get the right border character."""
        return self.get_styled_char("vertical")

    def wrap_line(self, line, width):
        """
        Wrap a line with box borders.

        Args:
            line: Content line to wrap
            width: Total width of the box

        Returns:
            Line wrapped with borders
        """
        content_width = width - 2
        if Text.visible_length(line) > content_width:
            line = Text.truncate(line, content_width)
        else:
            line = Text.pad(line, content_width)

        return self.left_border() + line + self.right_border()

    @staticmethod
    def simple_box(content, title=None, style="single", color=None):
        """
        Create a simple box for the given content.

        Args:
            content: Content to place inside the box
            title: Optional box title
            style: Box style
            color: Border color

        Returns:
            List of strings representing the drawn box
        """
        box = Box(style=style, title=title, color=color)
        return box.draw(content)
