import os
import subprocess
import time
from config import load_config
from logger import *

def build(component, options):
    build_start = time.time()
    config = load_config()
    if not config:
        return

    jobs = options.get("jobs", config.get("jobs", os.cpu_count()))
    cflags = config.get("flags", {}).get("cflags", "")
    ldflags = config.get("flags", {}).get("ldflags", "")

    log(f"Building {component} with make -j{jobs}...", options.get("silent", False))
    build_cmd = ["make", "-j", str(jobs), f"CFLAGS={cflags}", f"LDFLAGS={ldflags}"]

    try:
        result = subprocess.run(
            build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        print(result.stdout)
        write_to_log_file(result.stdout)
        if result.stderr:
            print(result.stderr)
            write_to_log_file(result.stderr)
    except subprocess.CalledProcessError as e:
        error(f"Build failed: {e}")

def clean():
    log("Cleaning build artifacts...", False)
    try:
        subprocess.run(["make", "clean"], check=True)
    except subprocess.CalledProcessError:
        error("Clean failed.")
