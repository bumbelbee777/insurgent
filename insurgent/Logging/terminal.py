#!/usr/bin/env python3
# Copyright (c) InsurgeNT Project
# SPDX-License-Identifier: Apache-2.0

"""
Terminal color and styling constants.
Provides basic ANSI color codes and symbols for terminal output.
"""

# Define ANSI color and style codes directly
RESET = "\033[0m"
BOLD = "\033[1m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Foreground colors
FG_BLACK = "\033[30m"
FG_RED = "\033[31m"
FG_GREEN = "\033[32m"
FG_YELLOW = "\033[33m"
FG_BLUE = "\033[34m"
FG_MAGENTA = "\033[35m"
FG_CYAN = "\033[36m"
FG_WHITE = "\033[37m"

# Re-export the standard ANSI color codes with simpler names
WHITE = FG_WHITE
GREEN = FG_GREEN
YELLOW = FG_YELLOW
RED = FG_RED
CYAN = FG_CYAN
BLUE = FG_BLUE
MAGENTA = FG_MAGENTA
GRAY = "\033[90m"  # Keep this one as it's not in the TUI Text module

# Common symbols with colors
CHECK = f"{GREEN}✔{RESET}"
CROSS = f"{RED}❌{RESET}"
ARROW = f"{CYAN}➜{RESET}"
INFO = f"{BLUE}ℹ{RESET}"

def style_text(text, **kwargs):
    """
    Style text with the specified options.
    A convenience wrapper around the Text.style method.
    """
    # Apply styling directly
    styled = text
    
    if kwargs.get('bold'):
        styled = f"{BOLD}{styled}{RESET}"
    if kwargs.get('color'):
        color_code = globals().get(f"FG_{kwargs['color'].upper()}", "")
        if color_code:
            styled = f"{color_code}{styled}{RESET}"
            
    return styled
