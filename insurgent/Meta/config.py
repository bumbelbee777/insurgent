import os
import yaml
from insurgent.Logging.logger import error, log

MANDATORY_FIELDS = [
    "project",
    "license",
    "language",
    "standard",
    "compiler",
    "project_dirs",
    "project_type",
    "output",
]


def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        error(f"Config file {config_path} not found.")
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        error(f"Error parsing YAML file: {e}")
        return {}

    for field in MANDATORY_FIELDS:
        if field not in config:
            error(f"Missing mandatory field '{field}' in {config_path}.")
            return {}

    config.setdefault("version", "0.0.1")
    config.setdefault("build_rule", "all")
    config.setdefault("clean_rule", "clean")
    config.setdefault("compiler_flags", "")
    config.setdefault("subprojects", [])

    log(f"Loaded project configuration: {config['project']} v{config['version']}")
    return config
