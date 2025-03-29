import os
import subprocess
import datetime
import time
import asyncio
from insurgent.Build.BuildEngine import BuildEngine
from insurgent.Meta.config import load_config
from insurgent.Logging.logger import *

async def _build_async(engine, component="all", incremental=False, multi_threaded=True, silent=False, build_subprojects=True):
    """Internal async implementation of the build process"""
    start_time = time.time()
    start_time_formatted = datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
    log(f"Build started at: {start_time_formatted} for target: {component}...")

    try:
        build_result = await engine._build_with_options(
            component=component, 
            incremental=incremental, 
            multi_threaded=multi_threaded, 
            silent=silent,
            build_subprojects=build_subprojects
        )

        end_time = time.time()
        end_time_formatted = datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
        duration = end_time - start_time
        
        if build_result:
            log(f"Build completed successfully at: {end_time_formatted}. Duration: {duration:.2f} seconds.")
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
                    error(f"No configuration provided for project: {project}")
                    return None

            engine = BuildEngine(project_dir)
            if config:
                engine.config = config  # Use provided config
            component = project

        if verbose:
            project_info = engine.get_project_info()
            log(f"Building project: {project_info['name']} v{project_info['version']}")
            log(f"Description: {project_info['description']}")
            log(f"Authors: {', '.join(project_info['authors'])}")
            log(f"License: {project_info['license']}")
            log(f"Language: {project_info['language']}, Compiler: {project_info['compiler']}")
            log(f"Output: {project_info['output']}")
            if project_info['subprojects']:
                log(f"Subprojects: {', '.join(project_info['subprojects'])}")

        return asyncio.run(_build_async(
            engine, 
            component, 
            incremental, 
            True,  # Always multi-threaded 
            silent,
            not no_subprojects  # Build subprojects unless explicitly disabled
        ))
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

        return asyncio.run(_clean_async(
            engine,
            not no_subprojects  # Clean subprojects unless explicitly disabled
        ))
    except Exception as e:
        error(f"Error during clean: {str(e)}")
        return None
