import os
from insurgent.Logging.terminal import *

# Dictionary to store registered commands and their completions
commands = {
    "about": [],
    "help": [],
    "exit": [],
    "clear": [],
    "ls": [],
    "cd": [],
    "mkdir": [],
    "rm": [],
    "touch": [],
    "cp": [],
    "cat": [],
    "build": [],
    "history": []
}

# Commands that should have file path completion
file_commands = ["cd", "mkdir", "rm", "touch", "cp", "cat", "build"]

def get_path_completions(partial_path):
    """
    Get completions for a partial file path
    """
    completions = []
    
    # Handle home directory expansion
    if partial_path.startswith("~"):
        partial_path = os.path.expanduser(partial_path)
    
    # Get the directory and partial filename
    if os.path.isdir(partial_path):
        directory = partial_path
        partial_file = ""
    else:
        directory = os.path.dirname(partial_path) if os.path.dirname(partial_path) else "."
        partial_file = os.path.basename(partial_path)
    
    # Make sure directory exists
    if not os.path.exists(directory):
        return completions
    
    # Get all matching files in the directory
    try:
        for item in os.listdir(directory):
            if item.startswith(partial_file):
                # Add trailing slash for directories
                full_path = os.path.join(directory, item)
                if os.path.isdir(full_path):
                    completions.append(f"{item}/")
                else:
                    completions.append(item)
    except (PermissionError, FileNotFoundError):
        pass
    
    return completions

def get_completions(input_text):
    """
    Get command completions based on current input
    """
    if not input_text:
        return list(commands.keys())
    
    parts = input_text.split()
    
    # Complete command name
    if len(parts) == 1:
        cmd_partial = parts[0]
        return [cmd for cmd in commands.keys() if cmd.startswith(cmd_partial)]
    
    # Complete command arguments
    command = parts[0].lower()
    if command in file_commands:
        # For file commands, provide path completion
        partial_path = parts[-1]
        return get_path_completions(partial_path)
    
    # Return command-specific completions if registered
    if command in commands and len(commands[command]) > 0:
        return [arg for arg in commands[command] if arg.startswith(parts[-1])]
    
    return []

def register_command_completions(command, completions):
    """
    Register possible completions for a command
    """
    if command in commands:
        commands[command] = completions
    else:
        commands[command] = completions

def complete_input(text, state):
    """
    Complete user input when tab is pressed
    Returns a tuple (new_input, display_matches)
    """
    if not text:
        return text, []
    
    parts = text.split()
    completions = get_completions(text)
    
    if state >= len(completions):
        return text, []
    
    # If there's only one match, return it
    if len(completions) == 1:
        if len(parts) <= 1:
            return completions[0] + " ", []
        else:
            # Replace the last part with the completion
            completed_parts = parts[:-1] + [completions[0]]
            return " ".join(completed_parts) + " ", []
    
    # If there are multiple matches, show them to the user
    if state == 0 and completions:
        # Format matched completions
        if len(parts) <= 1:
            # Command completions
            display = [f"{CYAN}{comp}{RESET}" for comp in completions]
        else:
            # Path completions
            display = []
            for comp in completions:
                if comp.endswith('/'):
                    display.append(f"{BLUE}{comp}{RESET}")
                else:
                    display.append(f"{RESET}{comp}{RESET}")
        
        return text, display
    
    return text, []

def handle_tab(input_text, tab_count=1):
    """
    Handle tab key press for completion
    tab_count: number of consecutive tab presses
    Returns tuple (new_input, should_redisplay)
    """
    # First tab shows completion suggestions
    if tab_count == 1:
        new_input, matches = complete_input(input_text, 0)
        
        if matches:
            # Display matches
            print()
            print(" ".join(matches))
            return input_text, True
        
        return new_input, new_input != input_text
    
    # Multiple tabs cycle through suggestions
    else:
        state = (tab_count - 2) % max(1, len(get_completions(input_text)))
        new_input, _ = complete_input(input_text, state)
        return new_input, False 