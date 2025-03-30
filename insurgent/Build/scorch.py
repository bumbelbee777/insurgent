import asyncio
import os
from pathlib import Path

from insurgent.Build.build import clean
from insurgent.Build.BuildEngine import BuildEngine
from insurgent.Logging.logger import error, log
from insurgent.Logging.terminal import *
from insurgent.Meta.config import load_config


def scorch_src_tree(options=None):
    """
    Clean the project by removing all build artifacts.

    Args:
        options: Additional options for cleaning

    Returns:
        True if successful, False if failed
    """
    options = options or []
    verbose = "--verbose" in options

    if verbose:
        log(f"{YELLOW}✦ Scorching source tree{RESET}")

    # Get the current directory to clean
    project_dir = os.getcwd()
    config_path = os.path.join(project_dir, "project.yaml")

    # Try to load config if it exists
    config = None
    if os.path.exists(config_path):
        config = load_config(config_path)

    # Run the clean operation using the BuildEngine
    clean_result = clean(config=config, options=options)

    if clean_result:
        if verbose:
            log(f"{GREEN}✔ Successfully scorched source tree{RESET}")
        return True
    else:
        error("Failed to clean project")
        return False


async def scorch_all(projects_dir=None, options=None):
    """
    Clean multiple projects in a directory.

    Args:
        projects_dir: Directory containing multiple projects
        options: Additional options for cleaning

    Returns:
        True if all projects were cleaned successfully, False otherwise
    """
    options = options or []
    verbose = "--verbose" in options

    if projects_dir is None:
        projects_dir = os.getcwd()

    if verbose:
        log(f"{YELLOW}✦ Scorching all projects in {projects_dir}{RESET}")

    # Find all subdirectories with project.yaml files
    projects = []
    for root, dirs, files in os.walk(projects_dir):
        if "project.yaml" in files:
            projects.append(root)

    if not projects:
        error(f"No projects found in {projects_dir}")
        return False

    success = True
    for project_path in projects:
        # Save current directory
        old_cwd = os.getcwd()

        try:
            # Change to project directory
            os.chdir(project_path)

            if verbose:
                log(
                    f"{YELLOW}Cleaning project: {os.path.basename(project_path)}{RESET}"
                )

            # Create a BuildEngine for this project
            engine = BuildEngine(project_path)

            # Run clean operation
            clean_result = await engine.clean(clean_subprojects=True)

            if not clean_result:
                error(f"Failed to clean project: {os.path.basename(project_path)}")
                success = False

        finally:
            # Restore original directory
            os.chdir(old_cwd)

    if success and verbose:
        log(f"{GREEN}✔ Successfully scorched all projects{RESET}")

    return success


def scorch_all_sync(projects_dir=None, options=None):
    """
    Synchronous wrapper for scorch_all.

    Args:
        projects_dir: Directory containing multiple projects
        options: Additional options for cleaning

    Returns:
        True if all projects were cleaned successfully, False otherwise
    """
    # Create an event loop and run the coroutine
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(scorch_all(projects_dir, options))
        return result
    finally:
        if not loop.is_closed():
            loop.close()
