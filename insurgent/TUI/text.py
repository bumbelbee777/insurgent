# ANSI color and style codes
RESET = "\033[0m"
BOLD = "\033[1m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
REVERSE = "\033[7m"
HIDDEN = "\033[8m"
STRIKETHROUGH = "\033[9m"

# Foreground colors
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BRIGHT_BLACK = "\033[90m"
BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_WHITE = "\033[97m"

# Background colors
BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"
BG_BRIGHT_BLACK = "\033[100m"
BG_BRIGHT_RED = "\033[101m"
BG_BRIGHT_GREEN = "\033[102m"
BG_BRIGHT_YELLOW = "\033[103m"
BG_BRIGHT_BLUE = "\033[104m"
BG_BRIGHT_MAGENTA = "\033[105m"
BG_BRIGHT_CYAN = "\033[106m"
BG_BRIGHT_WHITE = "\033[107m"


class Text:
    """
    Text styling utility for terminal output.
    Provides methods for applying colors and styles to text.
    """

    @staticmethod
    def style(
        text,
        color=None,
        bg_color=None,
        bold=False,
        italic=False,
        underline=False,
        blink=False,
        reverse=False,
        hidden=False,
        strikethrough=False,
    ):
        """
        Apply ANSI styles to text.

        Args:
            text: Text to style
            color: Foreground color name
            bg_color: Background color name
            bold: Apply bold style
            italic: Apply italic style
            underline: Apply underline style
            blink: Apply blink effect
            reverse: Apply reverse video
            hidden: Make text hidden
            strikethrough: Apply strikethrough

        Returns:
            Styled text with ANSI escape codes
        """
        style_codes = []

        # Apply text styles
        if bold:
            style_codes.append(BOLD)
        if italic:
            style_codes.append(ITALIC)
        if underline:
            style_codes.append(UNDERLINE)
        if blink:
            style_codes.append(BLINK)
        if reverse:
            style_codes.append(REVERSE)
        if hidden:
            style_codes.append(HIDDEN)
        if strikethrough:
            style_codes.append(STRIKETHROUGH)

        # Apply foreground color
        if color:
            color = color.lower()
            if color == "black":
                style_codes.append(BLACK)
            elif color == "red":
                style_codes.append(RED)
            elif color == "green":
                style_codes.append(GREEN)
            elif color == "yellow":
                style_codes.append(YELLOW)
            elif color == "blue":
                style_codes.append(BLUE)
            elif color == "magenta":
                style_codes.append(MAGENTA)
            elif color == "cyan":
                style_codes.append(CYAN)
            elif color == "white":
                style_codes.append(WHITE)
            elif color == "bright_black" or color == "gray" or color == "grey":
                style_codes.append(BRIGHT_BLACK)
            elif color == "bright_red":
                style_codes.append(BRIGHT_RED)
            elif color == "bright_green":
                style_codes.append(BRIGHT_GREEN)
            elif color == "bright_yellow":
                style_codes.append(BRIGHT_YELLOW)
            elif color == "bright_blue":
                style_codes.append(BRIGHT_BLUE)
            elif color == "bright_magenta":
                style_codes.append(BRIGHT_MAGENTA)
            elif color == "bright_cyan":
                style_codes.append(BRIGHT_CYAN)
            elif color == "bright_white":
                style_codes.append(BRIGHT_WHITE)

        # Apply background color
        if bg_color:
            bg_color = bg_color.lower()
            if bg_color == "black":
                style_codes.append(BG_BLACK)
            elif bg_color == "red":
                style_codes.append(BG_RED)
            elif bg_color == "green":
                style_codes.append(BG_GREEN)
            elif bg_color == "yellow":
                style_codes.append(BG_YELLOW)
            elif bg_color == "blue":
                style_codes.append(BG_BLUE)
            elif bg_color == "magenta":
                style_codes.append(BG_MAGENTA)
            elif bg_color == "cyan":
                style_codes.append(BG_CYAN)
            elif bg_color == "white":
                style_codes.append(BG_WHITE)
            elif bg_color == "bright_black" or bg_color == "gray" or bg_color == "grey":
                style_codes.append(BG_BRIGHT_BLACK)
            elif bg_color == "bright_red":
                style_codes.append(BG_BRIGHT_RED)
            elif bg_color == "bright_green":
                style_codes.append(BG_BRIGHT_GREEN)
            elif bg_color == "bright_yellow":
                style_codes.append(BG_BRIGHT_YELLOW)
            elif bg_color == "bright_blue":
                style_codes.append(BG_BRIGHT_BLUE)
            elif bg_color == "bright_magenta":
                style_codes.append(BG_BRIGHT_MAGENTA)
            elif bg_color == "bright_cyan":
                style_codes.append(BG_BRIGHT_CYAN)
            elif bg_color == "bright_white":
                style_codes.append(BG_BRIGHT_WHITE)

        # Return styled text or original text if no styles applied
        if style_codes:
            styled_text = "".join(style_codes) + str(text) + RESET
            return styled_text
        return str(text)

    @staticmethod
    def strip_ansi(text):
        """
        Remove ANSI escape codes from text.

        Args:
            text: Text with ANSI escape codes

        Returns:
            Clean text without ANSI codes
        """
        import re

        ansi_pattern = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
        return ansi_pattern.sub("", text)

    @staticmethod
    def get_visible_length(text):
        """
        Get the visible length of text (ignoring ANSI codes).

        Args:
            text: Text with possible ANSI codes

        Returns:
            Visible length of the text
        """
        return len(Text.strip_ansi(text))

    @classmethod
    def visible_length(cls, text):
        """
        Get the visible length of text (ignoring ANSI codes).
        Alias for get_visible_length for backward compatibility.

        Args:
            text: Text with possible ANSI codes

        Returns:
            Visible length of the text
        """
        return cls.get_visible_length(text)

    @staticmethod
    def align(text, width, alignment="left", fill_char=" "):
        """
        Align text within a given width.

        Args:
            text: Text to align
            width: Width to align within
            alignment: Alignment type (left, center, right)
            fill_char: Character to use for padding

        Returns:
            Aligned text
        """
        visible_length = Text.get_visible_length(text)

        if visible_length >= width:
            return text

        padding = width - visible_length

        if alignment == "left":
            return text + (fill_char * padding)
        elif alignment == "center":
            left_padding = padding // 2
            right_padding = padding - left_padding
            return (fill_char * left_padding) + text + (fill_char * right_padding)
        elif alignment == "right":
            return (fill_char * padding) + text
        else:
            return text  # Default to left alignment

    @staticmethod
    def truncate(text, max_length, ellipsis="..."):
        """
        Truncate text to a maximum visible length.

        Args:
            text: Text to truncate
            max_length: Maximum visible length
            ellipsis: String to indicate truncation

        Returns:
            Truncated text
        """
        visible_text = Text.strip_ansi(text)

        if len(visible_text) <= max_length:
            return text

        # Find all ANSI codes in the text
        import re

        ansi_pattern = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
        ansi_positions = [(m.start(), m.end()) for m in ansi_pattern.finditer(text)]

        # Calculate the truncation position accounting for ANSI codes
        visible_pos = 0
        actual_pos = 0

        while visible_pos < max_length - len(ellipsis) and actual_pos < len(text):
            # Skip ANSI codes
            is_ansi = False
            for start, end in ansi_positions:
                if actual_pos == start:
                    actual_pos = end
                    is_ansi = True
                    break

            if not is_ansi:
                visible_pos += 1
                actual_pos += 1

        # Collect ANSI codes at the end to properly close styling
        end_codes = []
        for start, end in ansi_positions:
            if start >= actual_pos:
                break
            code = text[start:end]
            if not code.endswith("m"):  # Only collect color/style codes
                continue
            if code.endswith("0m"):  # Reset code
                end_codes = []
            else:
                end_codes.append(code)

        # Add reset code if needed
        if end_codes:
            end_codes.append(RESET)

        return text[:actual_pos] + ellipsis + "".join(end_codes)
