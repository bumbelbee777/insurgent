import asyncio
import glob
import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

import yaml

from insurgent.Logging.logger import error, log, info, warning, success
from insurgent.Logging.terminal import *
from insurgent.Meta.config import load_config, validate_config
from insurgent.TUI.box import Box
from insurgent.TUI.text import Text
from insurgent.TUI.table import Table


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
            self.config["_config_path"] = os.path.join(
                self.project_path, "project.yaml"
            )

        if self.config and not validate_config(self.config):
            warning("Configuration validation failed. Build may fail.", use_box=True)

        self.c_compiler, self.cxx_compiler = self._detect_compilers()
        self.ar = self._detect_tool("ar", "ar")
        self.as_tool = self._detect_tool("as", "as")
        self.ld = self._detect_tool("ld", self.cxx_compiler)

        self.build_dir = os.path.join(self.project_path, "obj")
        self.cache_file = os.path.join(self.build_dir, "cache.json")
        os.makedirs(self.build_dir, exist_ok=True)

        # Load build cache for incremental builds
        self.build_cache = self._load_build_cache()

        # Create output directory if it doesn't exist
        if self.config and "output" in self.config:
            output_dir = os.path.dirname(
                os.path.join(self.project_path, self.config["output"])
            )
            os.makedirs(output_dir, exist_ok=True)

        self.subproject_engines = self._initialize_subprojects()

    def _load_project_config(self):
        """Load project configuration from project.yaml"""
        config_path = os.path.join(self.project_path, "project.yaml")
        if not os.path.exists(config_path):
            error(f"No `project.yaml` found in {self.project_path}.")
            return {}

        info(f"Loading project configuration from {config_path}...")
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
        if not self.config:
            return {}

        subproject_engines = {}

        # First handle explicitly declared subprojects
        if "subprojects" in self.config:
            for subproject_dir in self.config["subprojects"]:
                subproject_path = os.path.join(self.project_path, subproject_dir)
                if os.path.exists(subproject_path):
                    info(f"Initializing declared subproject in {subproject_dir}...")
                    subproject_engines[subproject_dir] = BuildEngine(subproject_path)
                else:
                    error(f"Subproject directory {subproject_dir} not found.")

        # Now check project_dirs for auto-discovery of nested projects
        # that have their own project.yaml but weren't explicitly declared as subprojects
        project_dirs = self.config.get("project_dirs", [])
        for project_dir in project_dirs:
            dir_path = os.path.join(self.project_path, project_dir)
            if not os.path.exists(dir_path):
                continue

            # Skip if this is already a declared subproject
            if project_dir in subproject_engines:
                continue

            # Check if this directory has a project.yaml file
            subdir_project_yaml = os.path.join(dir_path, "project.yaml")
            if os.path.exists(subdir_project_yaml):
                info(
                    f"Auto-discovered nested project in {project_dir}, adding as subproject..."
                )
                subproject_engines[project_dir] = BuildEngine(dir_path)

        return subproject_engines

    def _load_build_cache(self):
        """Load the build cache for incremental builds"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                warning(f"Could not load build cache: {e}")

        return {
            "file_hashes": {},
            "last_build_time": 0,
            "compiler_flags": "",
            "output_file": "",
        }

    def _save_build_cache(self):
        """Save the build cache to disk"""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.build_cache, f, indent=2)
        except Exception as e:
            error(f"Could not save build cache: {e}")

    def _update_file_hash(self, file_path):
        """Update the hash of a file in the build cache"""
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
                self.build_cache["file_hashes"][file_path] = file_hash
                return file_hash
        except Exception as e:
            error(f"Could not hash file {file_path}: {e}")
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

        if self.config.get("language", "").lower() in ["c++", "cpp"]:
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
            "as": as_flags.strip(),
        }

    def _find_source_files(self):
        """Find all source files for the project"""
        project_dirs = self.config.get("project_dirs", [])
        ignore_patterns = self.config.get("ignore", [])

        # If no project dirs specified, use all sub directories
        if not project_dirs:
            project_dirs = ["."]

        # Normalize project dirs to paths
        project_dirs = [
            os.path.normpath(os.path.join(self.project_path, d)) for d in project_dirs
        ]

        # Find all source files in project directories
        source_files = []
        for d in project_dirs:
            # First check if the directory exists
            if not os.path.exists(d):
                warning(
                    f"Project directory {d} does not exist, skipping.", use_box=True
                )
                continue

            # Check if this directory has its own project.yaml
            subdir_project_yaml = os.path.join(d, "project.yaml")
            if os.path.exists(subdir_project_yaml) and d != self.project_path:
                # This is a nested project with its own config file, but it's not a declared subproject
                # Skip it to avoid processing it as part of the parent project
                warning(
                    f"Directory {d} contains a project.yaml file but was not declared as a subproject. Skipping.",
                    use_box=True,
                )
                continue

            for ext in [".c", ".cpp", ".cc", ".cxx", ".s", ".asm"]:
                pattern = os.path.join(d, f"**/*{ext}")
                source_files.extend(glob.glob(pattern, recursive=True))

        # Filter out ignored files
        if ignore_patterns:
            for pattern in ignore_patterns:
                source_files = [
                    f
                    for f in source_files
                    if not os.path.basename(f).startswith(pattern)
                ]

        return source_files

    def _get_object_file_path(self, source_file):
        """Get the path to the object file for a source file"""
        rel_path = os.path.relpath(source_file, self.project_path)
        obj_path = os.path.join(self.build_dir, rel_path + ".o")
        os.makedirs(os.path.dirname(obj_path), exist_ok=True)
        return obj_path

    async def _compile_file(self, source_file, obj_file, file_type, silent=False):
        """Compile a source file to an object file"""
        if not os.path.exists(source_file):
            error(f"Source file {source_file} not found!")
            return False

        compiler_flags = self._get_compiler_flags()

        # Choose the appropriate compiler and flags
        if file_type == "c":
            compiler = self.c_compiler
            flags = compiler_flags["c"]
        elif file_type == "cpp":
            compiler = self.cxx_compiler
            flags = compiler_flags["cpp"]
        elif file_type == "asm":
            compiler = self.as_tool
            flags = compiler_flags["as"]
        else:
            error(f"Unknown file type: {file_type}")
            return False

        # Add include directories
        include_dirs = self.config.get("include_dirs", [])
        include_flags = " ".join(f"-I{dir}" for dir in include_dirs)

        # Add defines
        defines = self.config.get("defines", [])
        define_flags = " ".join(f"-D{define}" for define in defines)

        # Construct the compiler command
        cmd = f"{compiler} {flags} {include_flags} {define_flags} -c {source_file} -o {obj_file}"

        if not silent:
            # Display compilation progress using styled text
            rel_path = os.path.relpath(source_file, self.project_path)
            info(f"Compiling {Text.style(rel_path, color='cyan')}...")

        # Execute the compilation command
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                if stderr:
                    error_msg = stderr.decode()
                    error(f"Compilation failed:\n{error_msg}", use_box=True)
                else:
                    error("Compilation failed with no error message.", use_box=True)
                return False

            if not silent and stdout:
                stdout_str = stdout.decode()
                if stdout_str.strip():
                    print(stdout_str)

            return True
        except Exception as e:
            error(f"Compilation error: {e}", use_box=True)
            return False

    async def _link_executable(self, obj_files, output_file, silent=False):
        """Link object files into an executable"""
        if not obj_files:
            error("No object files to link!")
            return False

        # Prepare library flags
        lib_dirs = self.config.get("lib_dirs", [])
        lib_dir_flags = " ".join(f"-L{dir}" for dir in lib_dirs)

        libs = self.config.get("libs", [])
        lib_flags = " ".join(f"-l{lib}" for lib in libs)

        # Get linker flags
        compiler_flags = self._get_compiler_flags()
        linker_flags = compiler_flags["ld"]

        # Use C++ compiler for linking by default, or specified linker
        linker = self.ld

        # Construct the linker command
        obj_files_str = " ".join(obj_files)
        cmd = f"{linker} {obj_files_str} -o {output_file} {lib_dir_flags} {lib_flags} {linker_flags}"

        if not silent:
            # Display linking progress with styled output
            output_name = os.path.basename(output_file)
            info(f"Linking {Text.style(output_name, color='cyan', bold=True)}...")

        # Execute the linking command
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                if stderr:
                    error_msg = stderr.decode()
                    error(f"Linking failed:\n{error_msg}", use_box=True)
                else:
                    error("Linking failed with no error message.", use_box=True)
                return False

            if not silent and stdout:
                stdout_str = stdout.decode()
                if stdout_str.strip():
                    print(stdout_str)

            return True
        except Exception as e:
            error(f"Linking error: {e}", use_box=True)
            return False

    async def _create_library(self, obj_files, output_file, silent=False):
        """Create a static library from object files"""
        if not obj_files:
            error("No object files for library!")
            return False

        # Get archiver flags
        compiler_flags = self._get_compiler_flags()
        ar_flags = compiler_flags["ar"] or "rcs"

        # Construct the archiver command
        obj_files_str = " ".join(obj_files)
        cmd = f"{self.ar} {ar_flags} {output_file} {obj_files_str}"

        if not silent:
            # Display library creation progress with styled output
            output_name = os.path.basename(output_file)
            info(
                f"Creating library {Text.style(output_name, color='cyan', bold=True)}..."
            )

        # Execute the archiver command
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                if stderr:
                    error_msg = stderr.decode()
                    error(f"Library creation failed:\n{error_msg}", use_box=True)
                else:
                    error(
                        "Library creation failed with no error message.", use_box=True
                    )
                return False

            if not silent and stdout:
                stdout_str = stdout.decode()
                if stdout_str.strip():
                    print(stdout_str)

            return True
        except Exception as e:
            error(f"Library creation error: {e}", use_box=True)
            return False

    async def _run_bootstrap(self):
        """Run bootstrap commands if any"""
        bootstrap_commands = self.config.get("bootstrap", [])
        if not bootstrap_commands:
            return True

        info("Running bootstrap commands...", use_box=True)

        for cmd in bootstrap_commands:
            try:
                # Format command with variables
                cmd = cmd.format(
                    PROJECT_DIR=self.project_path,
                    BUILD_DIR=self.build_dir,
                    C_COMPILER=self.c_compiler,
                    CXX_COMPILER=self.cxx_compiler,
                )

                # Display the command
                print(Text.style(f"$ {cmd}", color="blue"))

                # Execute the command
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.project_path,
                )

                stdout, stderr = await process.communicate()
                if process.returncode != 0:
                    if stderr:
                        error_msg = stderr.decode()
                        error(f"Bootstrap command failed:\n{error_msg}", use_box=True)
                    else:
                        error(
                            f"Bootstrap command '{cmd}' failed with no error message.",
                            use_box=True,
                        )
                    return False

                if stdout:
                    stdout_str = stdout.decode()
                    if stdout_str.strip():
                        print(stdout_str)

            except Exception as e:
                error(f"Bootstrap error: {e}", use_box=True)
                return False

        return True

    async def _build_with_options(
        self,
        component="all",
        incremental=False,
        multi_threaded=True,
        silent=False,
        build_subprojects=True,
    ):
        """
        Build the project with the specified options.

        Args:
            component: Component to build (all, clean, specific component)
            incremental: Whether to perform an incremental build
            multi_threaded: Whether to use multi-threading
            silent: Whether to suppress output
            build_subprojects: Whether to build subprojects

        Returns:
            True if build was successful, False otherwise
        """
        if not self.config:
            error("No project configuration found!")
            return False

        # Build subprojects first if needed
        if build_subprojects and self.subproject_engines:
            for name, engine in self.subproject_engines.items():
                if not silent:
                    subproject_box = Box(style="light", title="Subproject")
                    subproject_content = [
                        f"Building subproject: {Text.style(name, color='cyan', bold=True)}"
                    ]
                    for line in subproject_box.draw(subproject_content):
                        print(line)

                success = await engine._build_with_options(
                    component, incremental, multi_threaded, silent, False
                )
                if not success:
                    error(f"Subproject {name} build failed!", use_box=True)
                    return False
                else:
                    info(f"Subproject {name} built successfully", use_box=True)

        # Run bootstrap commands if any
        bootstrap_success = await self._run_bootstrap()
        if not bootstrap_success:
            return False

        # Get the output file
        output_file = self.config.get("output", "")
        if not output_file:
            error("No output file specified in project configuration!")
            return False

        # Make the output path absolute
        output_file = os.path.join(self.project_path, output_file)

        # Find source files
        source_files = self._find_source_files()
        if not source_files:
            warning("No source files found for the project!", use_box=True)
            return False

        # Display build summary
        if not silent:
            # Create a table showing the build configuration
            build_table = Table(
                headers=["Setting", "Value"], alignments=["left", "left"], style="light"
            )

            # Add rows to the table
            build_table.add_rows(
                [
                    ["Project", os.path.basename(self.project_path)],
                    ["Output", os.path.basename(output_file)],
                    ["Sources", str(len(source_files))],
                    [
                        "Compiler",
                        (
                            self.cxx_compiler
                            if self.config.get("language", "").lower() in ["cpp", "c++"]
                            else self.c_compiler
                        ),
                    ],
                    ["Build Type", "Incremental" if incremental else "Full"],
                    ["Threads", str(self.jobs if multi_threaded else 1)],
                ]
            )

            # Display the build summary
            summary_box = Box(style="light", title="Build Summary")
            summary_content = []
            for line in build_table.draw():
                summary_content.append(line)
            for line in summary_box.draw(summary_content):
                print(line)
            print()

        # Determine files that need to be compiled
        obj_files = []
        files_to_compile = []

        for source_file in source_files:
            obj_file = self._get_object_file_path(source_file)
            obj_files.append(obj_file)

            # Determine if we need to compile this file
            need_compile = True
            if incremental and os.path.exists(obj_file):
                if not self._has_file_changed(source_file):
                    need_compile = False

            if need_compile:
                file_type = (
                    "cpp" if source_file.endswith((".cpp", ".cc", ".cxx")) else "c"
                )
                if source_file.endswith((".s", ".asm")):
                    file_type = "asm"
                files_to_compile.append((source_file, obj_file, file_type))

        # Start build timer
        start_time = time.time()

        # Compile the files
        if files_to_compile:
            if not silent:
                compile_box = Box(style="light", title="Compilation")
                compile_content = [
                    f"Compiling {Text.style(str(len(files_to_compile)), color='cyan', bold=True)} of {len(source_files)} files..."
                ]
                for line in compile_box.draw(compile_content):
                    print(line)

            if multi_threaded:
                # Compile files in parallel
                tasks = []
                for source_file, obj_file, file_type in files_to_compile:
                    task = asyncio.create_task(
                        self._compile_file(source_file, obj_file, file_type, silent)
                    )
                    tasks.append(task)

                # Wait for all compilation tasks to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Check for compilation errors
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        error(f"Compilation error: {result}", use_box=True)
                        return False
                    elif result is False:
                        # _compile_file already printed the error
                        return False
            else:
                # Compile files sequentially
                for source_file, obj_file, file_type in files_to_compile:
                    result = await self._compile_file(
                        source_file, obj_file, file_type, silent
                    )
                    if not result:
                        return False

        # Check if any object file is missing (can happen if compilation was aborted)
        for obj_file in obj_files:
            if not os.path.exists(obj_file):
                error(f"Object file {obj_file} is missing!", use_box=True)
                return False

        # Create the output file (executable or library)
        output_type = self.config.get("type", "executable").lower()
        if output_type == "library" or output_type == "static_library":
            result = await self._create_library(obj_files, output_file, silent)
        else:
            result = await self._link_executable(obj_files, output_file, silent)

        # Save the build cache
        self._save_build_cache()

        # Calculate build time
        build_time = time.time() - start_time
        self.build_cache["last_build_time"] = time.time()
        self.build_cache["output_file"] = output_file

        if result and not silent:
            # Show build success message with styling
            output_name = os.path.basename(output_file)
            output_size = os.path.getsize(output_file) / 1024  # KB

            success_box = Box(style="double", title="Build Completed")
            success_content = [
                f"Output: {Text.style(output_name, color='green', bold=True)}",
                f"Size: {Text.style(f'{output_size:.2f} KB', color='cyan')}",
                f"Time: {Text.style(f'{build_time:.2f} seconds', color='yellow')}",
                f"Files: {Text.style(str(len(source_files)), color='blue')}",
            ]
            for line in success_box.draw(success_content):
                print(line)

        return result

    async def build(
        self,
        component="all",
        incremental=True,
        multi_threaded=True,
        silent=False,
        build_subprojects=True,
    ):
        """
        Build the project.

        Args:
            component: Component to build (all, clean, specific component)
            incremental: Whether to perform an incremental build
            multi_threaded: Whether to use multi-threading
            silent: Whether to suppress output
            build_subprojects: Whether to build subprojects

        Returns:
            True if build was successful, False otherwise
        """
        try:
            if component == "clean":
                return await self.clean(clean_subprojects=build_subprojects)
            else:
                return await self._build_with_options(
                    component, incremental, multi_threaded, silent, build_subprojects
                )
        except Exception as e:
            error(f"Build error: {e}", use_box=True)
            return False

    async def clean(self, clean_subprojects=True):
        """
        Clean the build artifacts.

        Args:
            clean_subprojects: Whether to clean subprojects

        Returns:
            True if cleaning was successful, False otherwise
        """
        try:
            # Clean build directory
            if os.path.exists(self.build_dir):
                shutil.rmtree(self.build_dir)
                os.makedirs(self.build_dir, exist_ok=True)
                info(f"Cleaned build directory: {self.build_dir}")

            # Clean output file
            output_file = ""
            if self.config and "output" in self.config:
                output_file = os.path.join(self.project_path, self.config["output"])
                if os.path.exists(output_file):
                    os.remove(output_file)
                    info(f"Removed output file: {output_file}")

            # Clean subprojects if requested
            if clean_subprojects and self.subproject_engines:
                for name, engine in self.subproject_engines.items():
                    info(f"Cleaning subproject: {name}")
                    await engine.clean(clean_subprojects=False)

            # Reset build cache
            self.build_cache = {
                "file_hashes": {},
                "last_build_time": 0,
                "compiler_flags": "",
                "output_file": "",
            }
            self._save_build_cache()

            # Display cleaning summary
            clean_box = Box(style="light", title="Clean Completed")
            clean_content = [
                f"Removed build directory: {Text.style(self.build_dir, color='cyan')}",
            ]
            if output_file:
                clean_content.append(
                    f"Removed output file: {Text.style(output_file, color='cyan')}"
                )

            for line in clean_box.draw(clean_content):
                print(line)

            return True
        except Exception as e:
            error(f"Clean error: {e}", use_box=True)
            return False

    def get_project_info(self):
        """
        Get information about the project.

        Returns:
            Dictionary with project information
        """
        if not self.config:
            return {}

        source_files = self._find_source_files()

        # Create project information
        info = {
            "name": self.config.get("name", os.path.basename(self.project_path)),
            "version": self.config.get("version", "0.1.0"),
            "type": self.config.get("type", "executable"),
            "language": self.config.get("language", "c++"),
            "compiler": self.cxx_compiler,
            "source_files": len(source_files),
            "include_dirs": self.config.get("include_dirs", []),
            "libs": self.config.get("libs", []),
            "output": self.config.get("output", ""),
            "project_path": self.project_path,
        }

        return info
