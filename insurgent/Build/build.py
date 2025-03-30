import asyncio
import datetime
import os
import subprocess
import time

from insurgent.Build.BuildEngine import BuildEngine
from insurgent.Logging.logger import *
from insurgent.Meta.config import load_config


async def _build_async(
    engine,
    component="all",
    incremental=False,
    multi_threaded=True,
    silent=False,
    build_subprojects=True,
):
    """Internal async implementation of the build process"""
    start_time = time.time()
    start_time_formatted = datetime.datetime.fromtimestamp(start_time).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    log(f"Build started at: {start_time_formatted} for target: {component}...")

    try:
        build_result = await engine._build_with_options(
            component=component,
            incremental=incremental,
            multi_threaded=multi_threaded,
            silent=silent,
            build_subprojects=build_subprojects,
        )

        end_time = time.time()
        end_time_formatted = datetime.datetime.fromtimestamp(end_time).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        duration = end_time - start_time

        if build_result:
            log(
                f"Build completed successfully at: {end_time_formatted}. Duration: {duration:.2f} seconds."
            )
        else:
            error(f"Build failed after {duration:.2f} seconds.")

        return build_result
    except Exception as e:
        error(f"Build failed with exception: {str(e)}")
        return None


def build(project, config=None, options=None):
    """
    Build a project using configuration.

    Args:
        project: Either a project name or BuildEngine instance
        config: Project configuration dictionary (optional if project is a BuildEngine)
        options: Additional build options

    Returns:
        True if build successful, None if failed
    """
    options = options or []
    incremental = "--incremental" in options
    silent = "--silent" in options
    verbose = "--verbose" in options
    debug = "--debug" in options
    no_subprojects = "--no-subprojects" in options

    if verbose:
        silent = False

    try:
        if isinstance(project, BuildEngine):
            engine = project
            component = "all"
        else:
            # Project is a name, we need to create a BuildEngine
            project_dir = os.getcwd()

            if config is None:
                # Try to find project.yaml in current directory
                config_path = os.path.join(project_dir, "project.yaml")
                if os.path.exists(config_path):
                    config = load_config(config_path)
                else:
                    # If we don't find one in the current directory, 
                    # check if this is a sources directory with a parent containing project.yaml
                    parent_dir = os.path.dirname(project_dir)
                    parent_config_path = os.path.join(parent_dir, "project.yaml")
                    if os.path.exists(parent_config_path) and os.path.basename(project_dir) == "sources":
                        info(f"Found project.yaml in parent directory {parent_dir}")
                        project_dir = parent_dir
                        config = load_config(parent_config_path)
                    else:
                        error(f"No configuration provided for project: {project}")
                        return None

            engine = BuildEngine(project_dir)
            if config:
                engine.config = config  # Use provided config
            component = project

        if verbose:
            project_info = engine.get_project_info()
            log(f"Building project: {project_info['name']} v{project_info['version']}")
            if 'description' in project_info:
                log(f"Description: {project_info.get('description', 'No description')}")
            if "authors" in project_info and project_info["authors"]:
                if isinstance(project_info["authors"], list):
                    log(f"Authors: {', '.join(project_info['authors'])}")
                else:
                    log(f"Author: {project_info['authors']}")
            if "license" in project_info and project_info["license"]:
                log(f"License: {project_info['license']}")
            log(
                f"Language: {project_info['language']}, Compiler: {project_info['compiler']}"
            )
            log(f"Output: {project_info['output']}")
            if "subprojects" in project_info and project_info["subprojects"]:
                log(f"Subprojects: {', '.join(project_info['subprojects'])}")

        # Create an event loop and run the coroutine
        try:
            # Use asyncio.run for Python 3.7+ to properly manage the event loop
            result = asyncio.run(_build_async(
                engine,
                component,
                incremental,
                multi_threaded=True,  # Always multi-threaded
                silent=silent,
                build_subprojects=not no_subprojects,  # Build subprojects unless explicitly disabled
            ))
            return result
        except Exception as e:
            error(f"Error during asyncio execution: {str(e)}")
            return None

    except Exception as e:
        error(f"Error during build: {str(e)}")
        if debug:
            import traceback

            traceback.print_exc()
        return None


async def _clean_async(engine, clean_subprojects=True):
    """Internal async implementation of the clean process"""
    start_time = time.time()
    log(f"Cleaning build artifacts...")

    try:
        clean_result = await engine.clean(clean_subprojects)

        end_time = time.time()
        duration = end_time - start_time

        if clean_result:
            log(f"Clean completed successfully. Duration: {duration:.2f} seconds.")
        else:
            error(f"Clean failed after {duration:.2f} seconds.")

        return clean_result
    except Exception as e:
        error(f"Clean failed with exception: {str(e)}")
        return None


def clean(project=None, config=None, options=None):
    """
    Clean a project.

    Args:
        project: Either a project name, BuildEngine instance, or None (use current directory)
        config: Project configuration dictionary (optional)
        options: Additional options

    Returns:
        True if clean successful, None if failed
    """
    options = options or []
    no_subprojects = "--no-subprojects" in options

    try:
        # Determine the project to clean
        if isinstance(project, BuildEngine):
            engine = project
        else:
            project_dir = os.getcwd()
            engine = BuildEngine(project_dir)
            if config:
                engine.config = config

        # Create an event loop and run the coroutine
        try:
            # Use asyncio.run for Python 3.7+ to properly manage the event loop
            result = asyncio.run(_clean_async(
                engine,
                clean_subprojects=not no_subprojects,  # Clean subprojects unless explicitly disabled
            ))
            return result
        except Exception as e:
            error(f"Error during asyncio execution: {str(e)}")
            return None

    except Exception as e:
        error(f"Error during clean: {str(e)}")
        return None


def build_src_tree(args=None):
    """
    Build command handler that processes command line arguments.

    Args:
        args: Command line arguments

    Returns:
        True if build succeeded, False otherwise
    """
    args = args or []

    # Process arguments
    options = []
    for arg in args:
        if arg.startswith("--"):
            options.append(arg)

    # Get current directory as project directory
    project_dir = os.getcwd()

    # Try to find project.yaml
    config_path = os.path.join(project_dir, "project.yaml")
    if os.path.exists(config_path):
        config = load_config(config_path)
    else:
        error("No project.yaml found in current directory")
        return False

    # Build the project
    result = build("all", config, options)

    return result is True


# Helper function to ensure coroutines are properly handled in tests
def _ensure_coroutine_awaited(coro):
    """
    Helper function to ensure coroutines are properly handled.
    This prevents unhandled coroutine warnings in tests.
    
    Args:
        coro: Coroutine object
        
    Returns:
        Result from coroutine execution
    """
    import asyncio
    
    # If the coroutine is already a result (not a coroutine), return it
    if not asyncio.iscoroutine(coro):
        return coro
        
    # Try to use asyncio.run which handles the event loop properly
    try:
        return asyncio.run(coro)
    except (RuntimeError, ValueError):
        # If we're already in an event loop or there's an issue,
        # create a new loop in this thread and run it
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            loop.close()
            asyncio.set_event_loop(None)
