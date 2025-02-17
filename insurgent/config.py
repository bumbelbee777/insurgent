import yaml
from logger import *

def load_config():
    try:
        with open("project.yml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        error("project.yml not found.")
        return None