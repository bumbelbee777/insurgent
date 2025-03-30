"""
Syntax highlighting functions for the InsurgeNT Shell.
Provides utilities for highlighting shell commands and code.
"""

import re
from typing import Dict, List, Tuple, Optional, Any

from ..TUI.text import Text
from ..Logging.terminal import (
    RESET,
    BOLD,
    FG_RED,
    FG_GREEN,
    FG_YELLOW,
    FG_BLUE,
    FG_MAGENTA,
    FG_CYAN,
    FG_WHITE,
)


# Regex patterns for different token types
PATTERNS = {
    "command": r"^([a-zA-Z0-9_\-]+)",
    "option": r"(\s+--?[a-zA-Z0-9_\-]+)",
    "path": r"(\s+[~]?[/\\]?[.a-zA-Z0-9_\-/\\]+)",
    "string": r'(\s+"[^"]*"|\s+\'[^\']*\')',
    "number": r"(\s+\d+)",
    "pipe": r"(\s*\|\s*)",
    "redirect": r"(\s*[><]{1,2}\s*)",
    "operator": r"(\s*[;|&]{1,2}\s*)",
}


def strip_ansi(text: str) -> str:
    """
    Remove ANSI escape codes from a string.

    Args:
        text: Text with ANSI codes

    Returns:
        Clean text without ANSI codes
    """
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def highlight_token(token_type: str, token: str) -> str:
    """
    Apply syntax highlighting to a token.

    Args:
        token_type: Type of token
        token: Token text

    Returns:
        Highlighted token
    """
    if token_type == "command":
        return f"{FG_GREEN}{token}{RESET}"
    elif token_type == "option":
        return f"{FG_YELLOW}{token}{RESET}"
    elif token_type == "path":
        return f"{FG_BLUE}{token}{RESET}"
    elif token_type == "string":
        return f"{FG_MAGENTA}{token}{RESET}"
    elif token_type == "number":
        return f"{FG_CYAN}{token}{RESET}"
    elif token_type == "pipe":
        return f"{BOLD}{FG_WHITE}{token}{RESET}"
    elif token_type == "redirect":
        return f"{FG_RED}{token}{RESET}"
    elif token_type == "operator":
        return f"{BOLD}{FG_RED}{token}{RESET}"
    else:
        return token


def tokenize_command(command: str) -> List[Tuple[str, str]]:
    """
    Tokenize a command into a list of token types and values.

    Args:
        command: Command string

    Returns:
        List of (token_type, token_value) tuples
    """
    remaining = command
    tokens = []

    # Process first token as command
    command_match = re.match(PATTERNS["command"], remaining)
    if command_match:
        token = command_match.group(1)
        tokens.append(("command", token))
        remaining = remaining[len(token) :]

    # Process remaining tokens
    while remaining:
        matched = False
        for token_type, pattern in PATTERNS.items():
            if token_type == "command":
                continue  # Already processed

            match = re.match(pattern, remaining)
            if match:
                token = match.group(1)
                tokens.append((token_type, token))
                remaining = remaining[len(token) :]
                matched = True
                break

        if not matched:
            # Unrecognized token, consume one character
            tokens.append(("text", remaining[0]))
            remaining = remaining[1:]

    return tokens


def format_input_with_highlighting(command: str) -> str:
    """
    Format command input with syntax highlighting.

    Args:
        command: Command string

    Returns:
        Highlighted command string
    """
    if not command:
        return ""

    tokens = tokenize_command(command)
    highlighted = ""

    for token_type, token in tokens:
        highlighted += highlight_token(token_type, token)

    return highlighted
