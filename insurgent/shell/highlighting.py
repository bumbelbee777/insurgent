"""
Syntax highlighting functions for the InsurgeNT Shell.
Provides utilities for highlighting shell commands and code.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from insurgent.rich_utils import style_text

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
        return str(style_text(token, color="green"))
    elif token_type == "option":
        return str(style_text(token, color="yellow"))
    elif token_type == "path":
        return str(style_text(token, color="blue"))
    elif token_type == "string":
        return str(style_text(token, color="magenta"))
    elif token_type == "number":
        return str(style_text(token, color="cyan"))
    elif token_type == "pipe":
        return str(style_text(token, color="white", bold=True))
    elif token_type == "redirect":
        return str(style_text(token, color="red"))
    elif token_type == "operator":
        return str(style_text(token, color="red", bold=True))
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
