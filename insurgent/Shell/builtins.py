import os
import os.path
import asyncio
from insurgent.Meta.config import load_config
from insurgent.Build.BuildEngine import BuildEngine
from insurgent.Logging.logger import log, error

def ls(path="."):
    try:
        return os.listdir(path)
    except FileNotFoundError:
        return f"ls: cannot access '{path}': No such file or directory"
    except PermissionError:
        return f"ls: cannot access '{path}': Permission denied"

def cd(path):
    try:
        os.chdir(path)
    except FileNotFoundError:
        return f"cd: {path}: No such file or directory"
    except PermissionError:
        return f"cd: {path}: Permission denied"

def cwd():
    return os.getcwd()

def mkdir(name):
    try:
        os.mkdir(name)
    except FileExistsError:
        return f"mkdir: {name}: File exists"
    except PermissionError:
        return f"mkdir: {name}: Permission denied"

def touch(path):
    try:
        with open(path, "w") as f:
            f.write("")
        return 1
    except PermissionError:
        return f"touch: {path}: Permission denied"
    except FileNotFoundError:
        return f"touch: {path}: No such file or directory"

def rm(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        return f"rm: {path}: No such file or directory"
    except PermissionError:
        return f"rm: {path}: Permission denied"

def cp(source, destination):
    try:
        with open(source, "r") as f:
            data = f.read()
        with open(destination, "w") as f:
            f.write(data)
        return 1
    except FileNotFoundError:
        return f"cp: {source}: No such file or directory"
    except PermissionError:
        return f"cp: {source}: Permission denied"
    
def cat(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"cat: {path}: No such file or directory"
    except PermissionError:
        return f"cat: {path}: Permission denied"

def symlink(target, link_name):
    try:
        os.symlink(target, link_name)
    except FileExistsError:
        return f"symlink: {link_name}: File exists"
    except FileNotFoundError:
        return f"symlink: {target}: No such file or directory"
    except PermissionError:
        return f"symlink: {link_name}: Permission denied"
    
async def build(component: str):
    config = load_config()
    project_dirs = config.get("project_dirs", [])

    if not project_dirs:
        error("[BUILD] No project directories defined in configuration.")
        return

    log(f"[BUILD] Starting build for component: {component}")

    for project_dir in project_dirs:
        log(f"[BUILD] Initializing BuildEngine for {project_dir}...")
        build_engine = BuildEngine(project_dir)

        try:
            await build_engine.build(target=component)
            log(f"[BUILD] Successfully built {component} in {project_dir}.")
        except Exception as e:
            error(f"[BUILD] Build failed in {project_dir}: {str(e)}")
