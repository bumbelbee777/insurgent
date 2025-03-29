import os
import subprocess
import asyncio
import time
import yaml
import shutil
import glob
import hashlib
import json
from datetime import datetime
from pathlib import Path
from insurgent.Meta.config import load_config, validate_config
from insurgent.Logging.logger import error, log
from insurgent.Logging.terminal import *

class BuildEngine:
    def __init__(self, project_path: str):
        """
        Initialize the build engine for a project.
        
        Args:
            project_path: Path to the project directory containing project.yaml
        """
        self.project_path = os.path.abspath(project_path)
        self.jobs = os.cpu_count() or 1
        self.config = self._load_project_config()
        
        # Add the config_path to the config for later reference
        if self.config:
            self.config["_config_path"] = os.path.join(self.project_path, "project.yaml")

        if self.config and not validate_config(self.config):
            log(f"WARNING: Configuration validation failed. Build may fail.")

        self.c_compiler, self.cxx_compiler = self._detect_compilers()
        self.ar = self._detect_tool("ar", "ar")
        self.as_tool = self._detect_tool("as", "as")
        self.ld = self._detect_tool("ld", self.cxx_compiler)  # Default to using C++ compiler for linking

        self.build_dir = os.path.join(self.project_path, ".build")
        self.cache_file = os.path.join(self.build_dir, "cache.json")
        os.makedirs(self.build_dir, exist_ok=True)
        
        # Load build cache for incremental builds
        self.build_cache = self._load_build_cache()
        
        # Create output directory if it doesn't exist
        if self.config and 'output' in self.config:
            output_dir = os.path.dirname(os.path.join(self.project_path, self.config['output']))
            os.makedirs(output_dir, exist_ok=True)

        self.subproject_engines = self._initialize_subprojects()

    def _load_project_config(self):
        """Load project configuration from project.yaml"""
        config_path = os.path.join(self.project_path, "project.yaml")
        if not os.path.exists(config_path):
            error(f"No `project.yaml` found in {self.project_path}.")
            return {}

        log(f"Loading project configuration from {config_path}...")
        return load_config(config_path)

    def _detect_compilers(self):
        """Detect the compilers to use based on the configuration"""
        if not self.config:
            return "cc", "c++"
        
        # Use specific compiler from config
        compiler = self.config.get("compiler", "")
        
        # For C++ projects, use the specified compiler for both C and C++
        if self.config.get("language", "").lower() in ["cpp", "c++"]:
            c_compiler = compiler
            cxx_compiler = compiler
        else:
            # For C projects
            c_compiler = compiler
            cxx_compiler = "c++"  # default C++ compiler
        
        # If compiler not specified, use defaults
        if not c_compiler:
            c_compiler = "gcc"
        if not cxx_compiler:
            cxx_compiler = "g++"
        
        return c_compiler, cxx_compiler
    
    def _detect_tool(self, tool_name, default_tool):
        """Detect system tools based on configuration"""
        if not self.config:
            return default_tool
        
        # Check if the tool is specified in the config
        if tool_name in self.config:
            return self.config[tool_name]

        return default_tool

    def _initialize_subprojects(self):
        """Initialize build engines for all subprojects"""
        if not self.config or 'subprojects' not in self.config:
            return {}
        
        subproject_engines = {}
        for subproject_dir in self.config['subprojects']:
            subproject_path = os.path.join(self.project_path, subproject_dir)
            if os.path.exists(subproject_path):
                log(f"Initializing subproject in {subproject_dir}...")
                subproject_engines[subproject_dir] = BuildEngine(subproject_path)
            else:
                error(f"Subproject directory {subproject_dir} not found.")
        
        return subproject_engines
    
    def _load_build_cache(self):
        """Load the build cache for incremental builds"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                log(f"Warning: Could not load build cache: {e}")

        return {
            "file_hashes": {},
            "last_build_time": 0,
            "compiler_flags": "",
            "output_file": ""
        }
    
    def _save_build_cache(self):
        """Save the build cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.build_cache, f, indent=2)
        except Exception as e:
            error(f"Warning: Could not save build cache: {e}")
    
    def _update_file_hash(self, file_path):
        """Update the hash of a file in the build cache"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
                self.build_cache["file_hashes"][file_path] = file_hash
                return file_hash
        except Exception as e:
            error(f"Warning: Could not hash file {file_path}: {e}")
            return None
    
    def _has_file_changed(self, file_path):
        """Check if a file has changed since the last build"""
        if file_path not in self.build_cache["file_hashes"]:
            return True
        
        old_hash = self.build_cache["file_hashes"][file_path]
        new_hash = self._update_file_hash(file_path)
        
        return old_hash != new_hash
    
    def _get_compiler_flags(self):
        """Get the appropriate compiler flags from the configuration"""
        compiler_flags = self.config.get("compiler_flags", {})
        global_flags = compiler_flags.get("global", "")
        common_flags = compiler_flags.get("common", "")
        c_flags = compiler_flags.get("c", "")
        cpp_flags = compiler_flags.get("cpp", "")
        ld_flags = compiler_flags.get("ld", "")
        ar_flags = compiler_flags.get("ar", "")
        as_flags = compiler_flags.get("as", "")

        std_flag = f"-std={self.config.get('standard', 'c++20')}"
        
        if self.config.get('language', '').lower() in ['c++', 'cpp']:
            all_cxx_flags = f"{global_flags} {common_flags} {cpp_flags} {std_flag}"
            all_c_flags = f"{global_flags} {common_flags} {c_flags}"
        else:
            all_c_flags = f"{global_flags} {common_flags} {c_flags} {std_flag}"
            all_cxx_flags = f"{global_flags} {common_flags} {cpp_flags}"
        
        return {
            "c": all_c_flags.strip(),
            "cpp": all_cxx_flags.strip(),
            "ld": ld_flags.strip(),
            "ar": ar_flags.strip(),
            "as": as_flags.strip()
        }
    
    def _find_source_files(self):
        """Find all source files for the project"""
        project_dirs = self.config.get("project_dirs", [])
        ignore_patterns = self.config.get("ignore", [])
        
        c_files = []
        cpp_files = []
        asm_files = []
        
        for directory in project_dirs:
            dir_path = os.path.join(self.project_path, directory)
            if not os.path.exists(dir_path):
                log(f"Warning: Project directory '{directory}' does not exist.")
                continue

            for pattern in ["**/*.c"]:
                for file_path in glob.glob(os.path.join(dir_path, pattern), recursive=True):
                    rel_path = os.path.relpath(file_path, self.project_path)
                    if not any(ignore in rel_path for ignore in ignore_patterns):
                        c_files.append(file_path)

            for pattern in ["**/*.cpp", "**/*.cc", "**/*.cxx", "**/*.c++"]:
                for file_path in glob.glob(os.path.join(dir_path, pattern), recursive=True):
                    rel_path = os.path.relpath(file_path, self.project_path)
                    if not any(ignore in rel_path for ignore in ignore_patterns):
                        cpp_files.append(file_path)

            for pattern in ["**/*.s", "**/*.S", "**/*.asm"]:
                for file_path in glob.glob(os.path.join(dir_path, pattern), recursive=True):
                    rel_path = os.path.relpath(file_path, self.project_path)
                    if not any(ignore in rel_path for ignore in ignore_patterns):
                        asm_files.append(file_path)
        
        return {
            "c": c_files,
            "cpp": cpp_files,
            "asm": asm_files
        }
    
    def _get_object_file_path(self, source_file):
        """Get the path to the object file for a source file"""
        rel_path = os.path.relpath(source_file, self.project_path)
        obj_dir = os.path.join(self.build_dir, os.path.dirname(rel_path))
        os.makedirs(obj_dir, exist_ok=True)
        return os.path.join(obj_dir, f"{os.path.splitext(os.path.basename(source_file))[0]}.o")
    
    async def _compile_file(self, source_file, obj_file, file_type, silent=False):
        """Compile a single source file to an object file"""
        flags = self._get_compiler_flags()
        
        if file_type == "c":
            compiler = self.c_compiler
            compiler_flags = flags["c"]
        elif file_type == "cpp":
            compiler = self.cxx_compiler
            compiler_flags = flags["cpp"]
        elif file_type == "asm":
            compiler = self.as_tool
            compiler_flags = flags["as"]
        else:
            error(f"Unknown file type: {file_type}")
            return False

        if not self._has_file_changed(source_file) and os.path.exists(obj_file):
            if not silent:
                log(f"Skipping unchanged file: {os.path.relpath(source_file, self.project_path)}")
            return True
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(obj_file), exist_ok=True)

        cmd = [compiler, "-c", source_file, "-o", obj_file]

        if compiler_flags:
            cmd.extend(compiler_flags.split())
        
        if not silent:
            log(f"Compiling {os.path.relpath(source_file, self.project_path)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error(f"Compilation failed for {source_file}:")
                error(stderr.decode().strip())
                return False

            self._update_file_hash(source_file)
            
            return True
        except Exception as e:
            error(f"Error compiling {source_file}: {e}")
            return False
    
    async def _link_executable(self, obj_files, output_file, silent=False):
        """Link object files into an executable"""
        flags = self._get_compiler_flags()
        ld_flags = flags["ld"]

        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        cmd = [self.ld, "-o", output_file]
        cmd.extend(obj_files)

        if ld_flags:
            cmd.extend(ld_flags.split())
        
        if not silent:
            log(f"Linking executable: {os.path.relpath(output_file, self.project_path)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error(f"Linking failed for {output_file}:")
                error(stderr.decode().strip())
                return False
            
            return True
        except Exception as e:
            error(f"Error linking {output_file}: {e}")
            return False
    
    async def _create_library(self, obj_files, output_file, silent=False):
        """Create a static library from object files"""
        flags = self._get_compiler_flags()
        ar_flags = flags["ar"]

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Build the archive command
        cmd = [self.ar, "rcs", output_file]
        if ar_flags:
            cmd.extend(ar_flags.split())
        cmd.extend(obj_files)
        
        if not silent:
            log(f"Creating library: {os.path.relpath(output_file, self.project_path)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error(f"Creating library failed for {output_file}:")
                error(stderr.decode().strip())
                return False
            
            return True
        except Exception as e:
            error(f"Error creating library {output_file}: {e}")
            return False

    async def _run_bootstrap(self):
        """Run bootstrap command if defined"""
        if "bootstrap" in self.config and self.config["bootstrap"].get("command"):
            bootstrap_cmd = self.config["bootstrap"]["command"]
            task_name = self.config["bootstrap"]["task"]
            
            log(f"Running bootstrap task: {task_name}")
            
            try:
                if os.name == 'nt':  # Windows
                    # Use shell=True for Windows
                    process = await asyncio.create_subprocess_shell(
                        bootstrap_cmd,
                        cwd=self.project_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        shell=True
                    )
                else:  # Unix
                    # Split the command into arguments for subprocess
                    cmd_args = bootstrap_cmd.split()
                    process = await asyncio.create_subprocess_exec(
                        *cmd_args,
                        cwd=self.project_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    if stdout:
                        log(stdout.decode().strip())
                    log(f"Bootstrap task {task_name} completed successfully")
                    return True
                else:
                    error(f"Bootstrap task {task_name} failed: {stderr.decode().strip()}")
                    return False
            except Exception as e:
                error(f"Bootstrap task {task_name} failed: {e}")
                return False
        
        return True  # If no bootstrap, consider it successful

    async def _build_with_options(self, component="all", incremental=False, multi_threaded=True, silent=False, build_subprojects=True):
        """
        Build the project with the specified options.
        
        Args:
            component: The build target, defaults to "all"
            incremental: Whether to do an incremental build
            multi_threaded: Whether to use multiple threads
            silent: Whether to suppress output
            build_subprojects: Whether to build subprojects
        """
        # Run bootstrap if defined
        bootstrap_success = await self._run_bootstrap()
        if not bootstrap_success:
            error("Bootstrap failed, aborting build")
            return False

        current_flags = str(self._get_compiler_flags())
        if current_flags != self.build_cache.get("compiler_flags", ""):
            incremental = False  # Force full rebuild if flags changed
            if not silent:
                log("Compiler flags changed, performing full rebuild")
        
        # Find all source files
        source_files = self._find_source_files()
        
        if not silent:
            log(f"Found {len(source_files['c'])} C files, {len(source_files['cpp'])} C++ files, and {len(source_files['asm'])} ASM files")

        obj_files = []

        for c_file in source_files["c"]:
            obj_file = self._get_object_file_path(c_file)
            obj_files.append(obj_file)

            if incremental and not self._has_file_changed(c_file) and os.path.exists(obj_file):
                if not silent:
                    log(f"Skipping unchanged file: {os.path.relpath(c_file, self.project_path)}")
                continue
            
            compile_success = await self._compile_file(c_file, obj_file, "c", silent)
            if not compile_success:
                return False
        
        # Compile C++ files
        for cpp_file in source_files["cpp"]:
            obj_file = self._get_object_file_path(cpp_file)
            obj_files.append(obj_file)
            
            # Skip if incremental and file hasn't changed
            if incremental and not self._has_file_changed(cpp_file) and os.path.exists(obj_file):
                if not silent:
                    log(f"Skipping unchanged file: {os.path.relpath(cpp_file, self.project_path)}")
                continue
            
            compile_success = await self._compile_file(cpp_file, obj_file, "cpp", silent)
            if not compile_success:
                return False

        for asm_file in source_files["asm"]:
            obj_file = self._get_object_file_path(asm_file)
            obj_files.append(obj_file)

            if incremental and not self._has_file_changed(asm_file) and os.path.exists(obj_file):
                if not silent:
                    log(f"Skipping unchanged file: {os.path.relpath(asm_file, self.project_path)}")
                continue
            
            compile_success = await self._compile_file(asm_file, obj_file, "asm", silent)
            if not compile_success:
                return False

        output_file = os.path.join(self.project_path, self.config.get("output", "output"))

        if self.config.get("project_type", "").lower() == "executable":
            if not await self._link_executable(obj_files, output_file, silent):
                return False
        else:
            if not await self._create_library(obj_files, output_file, silent):
                return False

        self.build_cache["last_build_time"] = time.time()
        self.build_cache["compiler_flags"] = current_flags
        self.build_cache["output_file"] = output_file
        self._save_build_cache()
        
        if not silent:
            log(f"Build completed successfully: {os.path.relpath(output_file, self.project_path)}")

        if build_subprojects and self.subproject_engines:
            for subproj_name, subproj_engine in self.subproject_engines.items():
                if not silent:
                    log(f"Building subproject: {subproj_name}")
                
                subproj_success = await subproj_engine._build_with_options(
                    component="all",
                    incremental=incremental,
                    multi_threaded=multi_threaded,
                    silent=silent,
                    build_subprojects=True
                )
                
                if not subproj_success:
                    error(f"Subproject build failed: {subproj_name}")
                    return False
        
        return True

    async def clean(self, clean_subprojects=True):
        """Clean the project and optionally subprojects"""
        try:
            if os.path.exists(self.build_dir):
                shutil.rmtree(self.build_dir)
                log(f"Removed build directory: {os.path.relpath(self.build_dir, self.project_path)}")

            output_file = os.path.join(self.project_path, self.config.get("output", "output"))
            if os.path.exists(output_file):
                os.remove(output_file)
                log(f"Removed output file: {os.path.relpath(output_file, self.project_path)}")
            
            # Reset build cache
            self.build_cache = {
                "file_hashes": {},
                "last_build_time": 0,
                "compiler_flags": "",
                "output_file": ""
            }
            
            # Clean subprojects if requested
            if clean_subprojects and self.subproject_engines:
                for subproj_name, subproj_engine in self.subproject_engines.items():
                    log(f"Cleaning subproject: {subproj_name}")
                    await subproj_engine.clean(clean_subprojects=True)
            
            return True
        except Exception as e:
            error(f"Error during clean: {e}")
            return False

    def get_project_info(self):
        """Get information about the project"""
        return {
            "name": self.config.get("project", "unknown"),
            "version": self.config.get("version", "0.0.1"),
            "description": self.config.get("description", ""),
            "language": self.config.get("language", ""),
            "compiler": self.cxx_compiler,
            "output": self.config.get("output", ""),
            "subprojects": list(self.subproject_engines.keys()) if self.subproject_engines else []
        }
