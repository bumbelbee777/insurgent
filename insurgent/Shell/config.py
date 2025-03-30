import os
import yaml

from insurgent.Logging.logger import error, warning, info
from insurgent.TUI.text import Text


class Config:
    """
    Configuration handler for the InsurgeNT Shell.
    Manages loading, saving, and accessing shell configuration.
    """

    def __init__(self, config_file=None):
        """
        Initialize the configuration handler.

        Args:
            config_file: Path to the configuration file (default: ~/.insurgent/config.yaml)
        """
        # Default configuration values
        self.defaults = {
            "theme": {
                "prompt": "blue",
                "status": "green",
                "error": "red",
                "warning": "yellow",
                "info": "cyan",
                "success": "green",
                "highlight": "magenta",
                "command": "blue",
                "path": "cyan",
                "input": "white",
                "output": "white",
            },
            "shell": {
                "prompt": "InsurgeNT> ",
                "history_size": 1000,
                "max_output_lines": 1000,
                "autocompletion": True,
                "syntax_highlighting": True,
                "show_line_numbers": True,
            },
            "build": {
                "parallelism": True,
                "max_workers": os.cpu_count() or 4,
                "incremental": True,
                "default_compiler": "gcc",
                "default_cxx_compiler": "g++",
            },
            "logging": {
                "level": "INFO",
                "file": "~/.insurgent/logs/insurgent.log",
                "max_size": 10 * 1024 * 1024,  # 10 MB
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "editor": {
                "path": "vim",
                "terminal": True,
            },
            "paths": {
                "workspace": os.path.expanduser("~/insurgent/workspace"),
                "projects": os.path.expanduser("~/insurgent/projects"),
                "temp": os.path.expanduser("~/.insurgent/temp"),
            },
            # Add aliases for common commands
            "aliases": {
                "b": "build",  # build
                "i": "build --incremental",  # incremental build
                "r": "clean && build",  # rebuild (clean then build)
                "c": "clean",  # clean
                "s": "scorch",  # scorch (same as clean)
                "bt": "bootstrap",  # run bootstrap task
                "sb": "scorch && build",  # scorch and rebuild everything
            },
        }

        # Current configuration
        self.config = self.defaults.copy()

        # Determine the configuration file path
        if config_file is None:
            config_dir = os.path.expanduser("~/.insurgent")
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            self.config_file = os.path.join(config_dir, "config.yaml")
        else:
            self.config_file = os.path.expanduser(config_file)

        # Load configuration from file
        self.load()

    def load(self):
        """
        Load configuration from the config file.
        If the file doesn't exist, creates it with default values.
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self._merge_configs(self.config, user_config)
                        info(f"Loaded configuration from {self.config_file}")
            else:
                # Create the configuration file with defaults
                self.save()
                info(f"Created default configuration file at {self.config_file}")
        except Exception as e:
            error(f"Failed to load configuration: {str(e)}")
            warning(f"Using default configuration")

    def save(self):
        """Save the current configuration to the config file."""
        try:
            # Create parent directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)

            info(f"Saved configuration to {self.config_file}")
            return True
        except Exception as e:
            error(f"Failed to save configuration: {str(e)}")
            return False

    def _merge_configs(self, base, update):
        """
        Recursively merge two configuration dictionaries.

        Args:
            base: Base configuration dictionary to update
            update: Dictionary with values to merge into base
        """
        for key, value in update.items():
            if key in base:
                if isinstance(base[key], dict) and isinstance(value, dict):
                    self._merge_configs(base[key], value)
                else:
                    base[key] = value
            else:
                base[key] = value

    def get(self, section, key=None, default=None):
        """
        Get a configuration value.

        Args:
            section: Configuration section
            key: Configuration key (if None, returns the entire section)
            default: Default value if the key doesn't exist

        Returns:
            Configuration value or default if not found
        """
        if section not in self.config:
            return default

        if key is None:
            return self.config[section]

        if key in self.config[section]:
            return self.config[section][key]

        return default

    def set(self, section, key, value):
        """
        Set a configuration value.

        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set

        Returns:
            True if successful, False otherwise
        """
        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = value
        return True

    def reset(self, section=None, key=None):
        """
        Reset configuration to defaults.

        Args:
            section: Section to reset (if None, resets everything)
            key: Key to reset (if None, resets entire section)

        Returns:
            True if successful, False otherwise
        """
        if section is None:
            # Reset entire configuration
            self.config = self.defaults.copy()
            return True

        if section not in self.defaults:
            return False

        if key is None:
            # Reset entire section
            self.config[section] = self.defaults[section].copy()
            return True

        if key not in self.defaults[section]:
            return False

        # Reset specific key
        self.config[section][key] = self.defaults[section][key]
        return True

    def get_aliases(self):
        """
        Get all command aliases

        Returns:
            Dictionary of aliases
        """
        return self.config.get("aliases", {})

    def add_alias(self, name, command):
        """
        Add a command alias

        Args:
            name: Alias name
            command: Command to alias

        Returns:
            True if added, False if already exists
        """
        aliases = self.get_aliases()
        if name in aliases:
            return False

        if "aliases" not in self.config:
            self.config["aliases"] = {}

        self.config["aliases"][name] = command
        return True

    def update_alias(self, name, command):
        """
        Update an existing alias

        Args:
            name: Alias name
            command: New command

        Returns:
            True if updated, False if doesn't exist
        """
        aliases = self.get_aliases()
        if name not in aliases:
            return False

        self.config["aliases"][name] = command
        return True

    def remove_alias(self, name):
        """
        Remove an alias

        Args:
            name: Alias name

        Returns:
            True if removed, False if doesn't exist
        """
        aliases = self.get_aliases()
        if name not in aliases:
            return False

        del self.config["aliases"][name]
        return True

    def expand_alias(self, command_line):
        """
        Expand alias in command line

        Args:
            command_line: Command line to expand

        Returns:
            Expanded command line
        """
        parts = command_line.split(maxsplit=1)
        if not parts:
            return command_line

        command = parts[0]
        aliases = self.get_aliases()

        if command in aliases:
            expanded = aliases[command]

            # Append arguments if any
            if len(parts) > 1:
                expanded += " " + parts[1]

            return expanded

        return command_line
