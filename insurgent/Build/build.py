import os
import subprocess
import datetime, time
from insurgent.Build.BuildEngine import BuildEngine
from insurgent.Meta.config import load_config
from insurgent.Logging.logger import *

async def build(engine: BuildEngine, component: str = "all", incremental=False, multi_threaded=True, silent=False):
    start_time = time.time()
    start_time_formatted = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
    log(f"[BUILD] Build started at: {start_time_formatted} for target: {component}...")

    try:
        await engine._build_with_options(component, incremental, multi_threaded, silent)

        end_time = time.time()
        end_time_formatted = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
        duration = end_time - start_time
        log(f"[BUILD] Build completed successfully at: {end_time_formatted}. Duration: {duration:.2f} seconds.")
    except subprocess.CalledProcessError:
        error(f"[BUILD] Build failed.")

def clean(build_engine, component):
    log("Cleaning build artifacts...", False)
    try:
        subprocess.run(["make", "clean"], check=True)
    except subprocess.CalledProcessError:
        error("Clean failed.")
