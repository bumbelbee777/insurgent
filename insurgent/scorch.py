import os
import subprocess
from config import load_config
from logger import log, error
from terminal import *

def scorch_src_tree():
    config = load_config()
    if not config:
        error("Failed to load configuration.")
        return

    clean_rule = config.get("clean_rule", "clean")

    log(f"{YELLOW}✦ Running clean rule: {clean_rule}{RESET}")

    try:
        result = subprocess.run(
            ["make", clean_rule],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        log(result.stdout.strip())
        if result.stderr.strip():
            error(result.stderr.strip())

        log(f"{GREEN}✔ Successfully cleaned the build artifacts using '{clean_rule}'{RESET}")
    except subprocess.CalledProcessError as e:
        error(f"Make clean failed: {e.stderr.strip()}")