import os
import time
import json
from datetime import datetime


class History:
    """
    Command history manager for the InsurgeNT Shell.
    Handles storing, retrieving, and navigating shell command history.
    """
    
    def __init__(self, history_file=None, max_size=1000):
        """
        Initialize the history manager.
        
        Args:
            history_file: Path to the history file (default: ~/.insurgent/history.json)
            max_size: Maximum number of history entries to keep
        """
        self.max_size = max_size
        self.current_index = -1
        self.entries = []
        
        # Determine the history file path
        if history_file is None:
            history_dir = os.path.expanduser("~/.insurgent")
            if not os.path.exists(history_dir):
                os.makedirs(history_dir, exist_ok=True)
            self.history_file = os.path.join(history_dir, "history.json")
        else:
            self.history_file = os.path.expanduser(history_file)
            
        # Load history from file
        self.load()
        
    def add(self, command, output=None):
        """
        Add a command to the history.
        
        Args:
            command: Command string
            output: Command output (optional)
        """
        # Don't add empty commands
        if not command or command.strip() == "":
            return
            
        # Don't add duplicates of the most recent command
        if self.entries and self.entries[-1]["command"] == command:
            return
            
        # Create history entry
        entry = {
            "command": command,
            "timestamp": time.time(),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        if output is not None:
            entry["output"] = output
            
        # Add to history
        self.entries.append(entry)
        
        # Trim history if needed
        if len(self.entries) > self.max_size:
            self.entries = self.entries[-self.max_size:]
            
        # Reset current index to the end of history
        self.current_index = -1
        
        # Save to file
        self.save()
        
    def get_previous(self, current_input=""):
        """
        Get the previous command in history.
        
        Args:
            current_input: Current input (for saving position on first navigation)
            
        Returns:
            Previous command or empty string if at the beginning
        """
        if not self.entries:
            return ""
            
        # If at the end of history, save the current input
        if self.current_index == -1:
            self.current_input = current_input
            
        # Move to previous entry if possible
        if self.current_index < len(self.entries) - 1:
            self.current_index += 1
            
        # Return the command at the current index
        if 0 <= self.current_index < len(self.entries):
            return self.entries[-(self.current_index + 1)]["command"]
            
        return ""
        
    def get_next(self):
        """
        Get the next command in history.
        
        Returns:
            Next command or saved input if at the end
        """
        if not self.entries:
            return ""
            
        # Move to next entry if possible
        if self.current_index > -1:
            self.current_index -= 1
            
        # If at the end of history, return the saved input
        if self.current_index == -1:
            return getattr(self, "current_input", "")
            
        # Return the command at the current index
        if 0 <= self.current_index < len(self.entries):
            return self.entries[-(self.current_index + 1)]["command"]
            
        return ""
        
    def search(self, term):
        """
        Search history for commands containing the given term.
        
        Args:
            term: Search term
            
        Returns:
            List of matching commands
        """
        if not term:
            return []
            
        matches = []
        for entry in reversed(self.entries):
            if term.lower() in entry["command"].lower():
                matches.append(entry["command"])
                
        return matches
        
    def clear(self):
        """Clear the command history."""
        self.entries = []
        self.current_index = -1
        self.save()
        
    def load(self):
        """Load history from file."""
        if not os.path.exists(self.history_file):
            return
            
        try:
            with open(self.history_file, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.entries = data
                    # Trim history if needed
                    if len(self.entries) > self.max_size:
                        self.entries = self.entries[-self.max_size:]
        except Exception:
            # If loading fails, start with empty history
            self.entries = []
            
    def save(self):
        """Save history to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            
            with open(self.history_file, "w") as f:
                json.dump(self.entries, f, indent=2)
        except Exception:
            # Silently ignore save failures
            pass
            
    def get_last_n(self, n=10):
        """
        Get the last N commands from history.
        
        Args:
            n: Number of commands to retrieve
            
        Returns:
            List of the last N commands
        """
        if not self.entries:
            return []
            
        n = min(n, len(self.entries))
        return [entry["command"] for entry in self.entries[-n:]] 