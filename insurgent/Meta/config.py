import os
import yaml
from insurgent.Logging.logger import error, log

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
    """
    Load and validate project configuration from YAML file
    
    Args:
        config_path: Path to the project.yaml file
        
    Returns:
        Dictionary with project configuration or empty dict if error
    """
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

    # Check for mandatory fields with a more flexible approach
    missing_fields = [field for field in MANDATORY_FIELDS if field not in config]
    if missing_fields:
        error(f"Missing mandatory field(s) in {config_path}: {', '.join(missing_fields)}")
        # Don't return empty - return what we have, but with a warning
        log(f"WARNING: Some mandatory fields are missing. Build may fail.")

    # Set default values for optional fields
    config.setdefault("description", f"{config.get('project', 'Unknown')} project")
    config.setdefault("version", "0.0.1")
    config.setdefault("build_rule", "all")
    config.setdefault("clean_rule", "clean")

    # Handle compiler flags structure
    if "compiler_flags" in config and isinstance(config["compiler_flags"], str):
        # Convert string to structured format
        flags_str = config["compiler_flags"]
        config["compiler_flags"] = {
            "common": flags_str
        }
    elif "compiler_flags" not in config:
        config["compiler_flags"] = {}
    
    # Set compiler flags defaults
    compiler_flags = config["compiler_flags"]
    compiler_flags.setdefault("global", "")
    compiler_flags.setdefault("common", "")
    compiler_flags.setdefault("c", "")
    compiler_flags.setdefault("cpp", "")
    compiler_flags.setdefault("ar", "")
    compiler_flags.setdefault("ld", "")
    compiler_flags.setdefault("as", "")

    # Handle other optional fields
    config.setdefault("subprojects", [])
    config.setdefault("ignore", [])
    
    # Handle bootstrap if defined
    if "bootstrap" in config and isinstance(config["bootstrap"], dict):
        bootstrap = config["bootstrap"]
        bootstrap.setdefault("task", "bootstrap")
        bootstrap.setdefault("command", "")
    else:
        config["bootstrap"] = {"task": "bootstrap", "command": ""}

    log(f"Loaded project configuration: {config.get('project', 'Unknown')} v{config.get('version', '0.0.1')}")
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
    valid_standards = ["ansic", "c99", "c11", "c17", "c++11", "c++14", "c++17", "c++20", "c++23"]
    if standard not in valid_standards:
        error(f"Invalid standard '{standard}'. Must be one of {', '.join(valid_standards)}.")
        return False
    
    # Validate project_type
    project_type = config.get("project_type", "").lower()
    if project_type not in ["executable", "library"]:
        error(f"Invalid project_type '{project_type}'. Must be 'executable' or 'library'.")
        return False
    
    # Validate project_dirs exist
    project_dirs = config.get("project_dirs", [])
    for directory in project_dirs:
        dir_path = os.path.join(os.path.dirname(os.path.abspath(config.get("_config_path", ""))), directory)
        if not os.path.exists(dir_path):
            log(f"WARNING: Project directory '{directory}' does not exist.")
    
    return True
