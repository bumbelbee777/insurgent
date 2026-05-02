"""
Configuration management for InsurgeNT.
"""

import json
import os
from typing import Any, Dict, List, Optional

import yaml

from insurgent.logging.logger import error, info, log, success, warning
from insurgent.logging.terminal import *
from insurgent.rich_utils import (
    create_panel,
    create_table,
    print_panel,
    print_styled,
    print_table,
    style_text,
)

MANDATORY_FIELDS = [
    "project",
    "authors",
    "license",
    "language",
    "standard",
    "compiler",
    "project_dirs",
    "project_type",
    "output",
]


def load_config(config_path: str) -> dict:
    """Load a project.yaml configuration file from a given path."""
    MANDATORY_FIELDS = [
        "project",
        "authors",
        "license",
        "language",
        "standard",
        "compiler",
        "project_dirs",
        "project_type",
        "output",
    ]

    if not os.path.exists(config_path):
        error(f"Config file {config_path} not found.")
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        error(f"Error parsing YAML file: {e}")
        return {}
    except Exception as e:
        error(f"Error reading config file: {e}")
        return {}

    config["_config_path"] = config_path

    missing_fields = [field for field in MANDATORY_FIELDS if field not in config]
    if missing_fields:
        error(f"Missing mandatory field(s): {', '.join(missing_fields)}")
        log("WARNING: Some mandatory fields are missing. Build may fail.")

    config.setdefault("description", f"{config.get('project', 'Unknown')} project")
    config.setdefault("version", "0.0.1")

    # Normalize authors field
    authors = config.get("authors")
    if isinstance(authors, str):
        config["authors"] = [authors]
    elif isinstance(authors, list):
        config["authors"] = [str(author) for author in authors]
    else:
        config["authors"] = []

    # Normalize compiler_flags
    if "compiler_flags" not in config:
        config["compiler_flags"] = {}
    elif isinstance(config["compiler_flags"], str):
        config["compiler_flags"] = {"common": config["compiler_flags"]}
    elif isinstance(config["compiler_flags"], list):
        try:
            flags_dict = {}
            for item in config["compiler_flags"]:
                if isinstance(item, dict):
                    flags_dict.update(item)
                else:
                    warning("Invalid entry in compiler_flags list; expected dict.")
            config["compiler_flags"] = flags_dict
        except Exception as e:
            warning(f"Failed to parse compiler_flags: {e}")
            config["compiler_flags"] = {}

    compiler_flags = config["compiler_flags"]
    for key in ["global", "common", "c", "cpp", "ar", "ld", "as"]:
        compiler_flags.setdefault(key, "")

    config.setdefault("subprojects", [])
    config.setdefault("ignore", [])

    # Bootstrap: expect list of dicts
    if "bootstrap" in config:
        if isinstance(config["bootstrap"], list):
            valid_bootstrap = []
            for step in config["bootstrap"]:
                if isinstance(step, dict) and any(
                    k in step for k in ("task", "command")
                ):
                    valid_bootstrap.append(step)
                else:
                    warning(
                        "Invalid bootstrap entry; expected dict with 'task' or 'command'."
                    )
            config["bootstrap"] = valid_bootstrap if valid_bootstrap else None
        else:
            warning("Expected bootstrap to be a list of dictionaries. Ignoring...")
            config["bootstrap"] = None
    else:
        config["bootstrap"] = None

    log(
        f"Loaded project configuration: {config.get('project', 'Unknown')} v{config.get('version', '0.0.1')}"
    )
    return config


def validate_config(config: dict) -> bool:
    """
    Validate if a config dictionary has all required fields and correct types

    Args:
        config: Project configuration dictionary

    Returns:
        True if valid, False if invalid
    """
    # Check for mandatory fields
    missing_fields = [field for field in MANDATORY_FIELDS if field not in config]
    if missing_fields:
        error(f"Missing mandatory field(s): {', '.join(missing_fields)}")
        return False

    # Validate 'language' field
    language = config.get("language", "").lower()
    if language not in ["c", "cpp", "c++"]:
        error(f"Invalid language '{language}'. Must be 'c' or 'c++/cpp'.")
        return False

    # Validate 'standard' field
    standard = config.get("standard", "").lower()
    valid_standards = [
        "ansic",
        "c99",
        "c11",
        "c17",
        "c++11",
        "c++14",
        "c++17",
        "c++20",
        "c++23",
    ]
    if standard not in valid_standards:
        error(
            f"Invalid standard '{standard}'. Must be one of {', '.join(valid_standards)}."
        )
        return False

    # Validate project_type
    project_type = config.get("project_type", "").lower()
    if project_type not in ["executable", "library"]:
        error(
            f"Invalid project_type '{project_type}'. Must be 'executable' or 'library'."
        )
        return False

    # Validate project_dirs exist
    project_dirs = config.get("project_dirs", [])
    for directory in project_dirs:
        dir_path = os.path.join(
            os.path.dirname(os.path.abspath(config.get("_config_path", ""))), directory
        )
        if not os.path.exists(dir_path):
            log(f"WARNING: Project directory '{directory}' does not exist.")

    return True


def to_compile_commands(config: dict) -> list:
    """
    Converts the loaded config into a compile_commands.json-style list of commands.

    Returns:
        List of compile command entries
    """
    compile_commands = []
    base_dir = os.path.dirname(os.path.abspath(config.get("_config_path", ".")))
    language = config.get("language", "c++").lower()
    std_flag = config["compiler_flags"].get("cpp" if "++" in language else "c", "")
    common_flags = config["compiler_flags"].get("common", "")
    global_flags = config["compiler_flags"].get("global", "")
    compiler = config.get("compiler", "g++")
    standard_flag = std_flag or ""

    for dir_name in config.get("project_dirs", []):
        abs_dir = os.path.join(base_dir, dir_name)
        if not os.path.isdir(abs_dir):
            continue
        for root, _, files in os.walk(abs_dir):
            for fname in files:
                if fname.endswith((".cpp", ".c", ".cc", ".cxx")):
                    source_path = os.path.join(root, fname)
                    entry = {
                        "directory": base_dir,
                        "file": source_path,
                        "command": f"{compiler} {global_flags} {common_flags} {standard_flag} -c {source_path}",
                    }
                    compile_commands.append(entry)

    return compile_commands


def export_compile_commands(config: dict, output_path: str = "compile_commands.json"):
    commands = to_compile_commands(config)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(commands, f, indent=2)
    log(f"Exported compile_commands.json with {len(commands)} entries.")
