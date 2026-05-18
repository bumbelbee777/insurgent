"""
Build engine for InsurgeNT.

Drives source discovery, incremental compilation, linking and bootstrap
commands for a single project (and its subprojects) described by a
``project.yaml`` file living in ``project_path``.
"""

import asyncio
import glob
import hashlib
import json
import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import yaml

from insurgent.logging.logger import error, log


class BuildEngine:
    """Project-aware build engine."""

    DEFAULT_LANGUAGE_STANDARDS = {
        "c": "c11",
        "cpp": "c++17",
        "c++": "c++17",
        "asm": "",
    }

    def __init__(self, project_path: Union[str, dict, None] = None):
        """
        Initialise the build engine for a project rooted at ``project_path``.

        ``project_path`` may also be a config dict for backwards compatibility
        with older callers; in that case the project root is taken from the
        ``project_path`` / ``_config_path`` keys, falling back to ``cwd``.
        """
        if isinstance(project_path, dict):
            cfg = project_path
            root = cfg.get("project_path") or cfg.get("_config_path") or os.getcwd()
            if os.path.isfile(root):
                root = os.path.dirname(root)
            self.project_path = os.path.abspath(root)
            self.config = dict(cfg)
        else:
            self.project_path = os.path.abspath(project_path or os.getcwd())
            self.config = self._load_project_config()

        self.jobs = os.cpu_count() or 1

        self._normalize_compiler_flags()

        # Comma-separated language/standard pairs (e.g. "c,cpp" / "c99,c++17").
        lang_field = str(self.config.get("language", "") or "")
        std_field = str(self.config.get("standard", "") or "")
        self.languages = [l.strip() for l in lang_field.split(",") if l.strip()]
        self.standards = [s.strip() for s in std_field.split(",") if s.strip()]

        self.c_compiler, self.cxx_compiler = self._detect_compilers()
        self.ar = self._detect_tool("ar", "ar")
        self.as_tool = self._detect_tool("as", "as")
        self.ld = self._detect_tool("ld", self.cxx_compiler)

        self.build_dir = os.path.join(self.project_path, ".build")
        self.cache_file = os.path.join(self.build_dir, "cache.json")
        os.makedirs(self.build_dir, exist_ok=True)

        self.build_cache = self._load_build_cache()

        if self.config.get("output"):
            output_dir = os.path.dirname(
                os.path.join(self.project_path, self.config["output"])
            )
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

        self.subproject_engines = self._initialize_subprojects()
        self._normalize_unit_tests_config()

    def _normalize_unit_tests_config(self) -> None:
        """Validate and normalise optional ``unit_tests`` from ``project.yaml``."""
        ut = self.config.get("unit_tests")
        if ut is None:
            return
        if not isinstance(ut, dict):
            log("unit_tests must be a dictionary; ignoring.")
            self.config["unit_tests"] = None
            return

        dirs = ut.get("project_dirs")
        if isinstance(dirs, str):
            dirs = [dirs]
        elif not isinstance(dirs, list):
            dirs = []
        dirs = [str(d).strip() for d in dirs if str(d).strip()]

        output = str(ut.get("output", "") or "").strip()
        if not dirs or not output:
            log("unit_tests requires non-empty project_dirs and output; ignoring.")
            self.config["unit_tests"] = None
            return

        link_project = ut.get("link_project")
        if link_project is not None and not isinstance(link_project, bool):
            log("unit_tests.link_project must be a boolean; ignoring unit_tests.")
            self.config["unit_tests"] = None
            return

        raw_libs = ut.get("libraries") or []
        if isinstance(raw_libs, str):
            raw_libs = [raw_libs]
        if not isinstance(raw_libs, list):
            log("unit_tests.libraries must be a string or list; ignoring unit_tests.")
            self.config["unit_tests"] = None
            return
        libraries = [str(p).strip() for p in raw_libs if str(p).strip()]

        self.config["unit_tests"] = {
            "project_dirs": dirs,
            "output": output,
            "link_project": link_project,
            "libraries": libraries,
        }

    # ------------------------------------------------------------------ config

    def _load_project_config(self) -> dict:
        """Read ``project.yaml`` from the project root (tolerant of missing fields)."""
        config_path = os.path.join(self.project_path, "project.yaml")
        if not os.path.exists(config_path):
            error(f"No `project.yaml` found in {self.project_path}.")
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            error(f"Error parsing YAML file: {e}")
            return {}
        except Exception as e:
            error(f"Error reading config file: {e}")
            return {}

        if not isinstance(cfg, dict):
            return {}

        cfg["_config_path"] = config_path

        # Accept both ``name``/``project`` and ``type``/``project_type`` schemas.
        if "name" not in cfg and "project" in cfg:
            cfg["name"] = cfg["project"]
        if "project" not in cfg and "name" in cfg:
            cfg["project"] = cfg["name"]
        if "type" not in cfg and "project_type" in cfg:
            cfg["type"] = cfg["project_type"]
        if "project_type" not in cfg and "type" in cfg:
            cfg["project_type"] = cfg["type"]

        cfg.setdefault("description", f"{cfg.get('name', 'Unknown')} project")
        cfg.setdefault("version", "0.0.1")
        cfg.setdefault("project_dirs", ["src"])
        cfg.setdefault("subprojects", [])
        cfg.setdefault("ignore", [])
        cfg.setdefault("supplementary_sources", [])
        cfg.setdefault("extra_sources", [])
        cfg.setdefault("output", "")

        authors = cfg.get("authors")
        if isinstance(authors, str):
            cfg["authors"] = [authors]
        elif not isinstance(authors, list):
            cfg["authors"] = [] if authors is None else [str(authors)]

        return cfg

    def _normalize_compiler_flags(self) -> None:
        """Massage ``compiler_flags`` into a flat dict of strings."""
        flags = self.config.get("compiler_flags", {})

        if isinstance(flags, str):
            flags = {"common": flags}
        elif isinstance(flags, list):
            merged: Dict[str, str] = {}
            for item in flags:
                if isinstance(item, dict):
                    merged.update(item)
            flags = merged
        elif not isinstance(flags, dict):
            flags = {}

        for key in ("global", "common", "c", "cpp", "ar", "ld", "as"):
            flags.setdefault(key, "")

        self.config["compiler_flags"] = flags

    # ---------------------------------------------------------------- toolchain

    def _detect_compilers(self) -> Tuple[str, str]:
        """Pick a (C, C++) compiler pair from config or sensible defaults."""
        compiler = str(self.config.get("compiler", "") or "").strip()

        languages = {l.lower() for l in self.languages}
        prefers_cpp = bool(languages & {"cpp", "c++"})

        if compiler:
            if prefers_cpp:
                cxx_compiler = compiler
                c_compiler = compiler
            else:
                c_compiler = compiler
                cxx_compiler = "g++" if compiler in ("gcc", "cc") else compiler
        else:
            c_compiler = "gcc"
            cxx_compiler = "g++"

        return c_compiler, cxx_compiler

    def _detect_tool(self, tool_name: str, default_tool: str) -> str:
        """Resolve a build tool by name from the config, with a default."""
        if tool_name in self.config and self.config[tool_name]:
            return str(self.config[tool_name])
        return default_tool

    # ------------------------------------------------------------- subprojects

    def _initialize_subprojects(self) -> Dict[str, "BuildEngine"]:
        """Recursively instantiate engines for every declared subproject."""
        subproject_engines: Dict[str, BuildEngine] = {}
        for subproject_dir in self.config.get("subprojects", []) or []:
            subproject_path = os.path.join(self.project_path, subproject_dir)
            if os.path.exists(os.path.join(subproject_path, "project.yaml")):
                subproject_engines[subproject_dir] = BuildEngine(subproject_path)
        return subproject_engines

    # ----------------------------------------------------------------- caching

    def _load_build_cache(self) -> dict:
        """Load the on-disk incremental build cache (or a fresh stub)."""
        default = {
            "file_hashes": {},
            "last_build_time": 0,
            "compiler_flags": "",
            "output_file": "",
        }

        if not os.path.exists(self.cache_file):
            return default

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return default
            data.setdefault("file_hashes", {})
            data.setdefault("last_build_time", 0)
            data.setdefault("compiler_flags", "")
            data.setdefault("output_file", "")
            return data
        except Exception as e:
            log(f"Warning: could not load build cache: {e}")
            return default

    def _save_build_cache(self) -> None:
        """Persist ``self.build_cache`` to disk."""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.build_cache, f, indent=2)
        except Exception as e:
            error(f"Warning: could not save build cache: {e}")

    def _update_file_hash(self, file_path: str) -> Optional[str]:
        """Hash ``file_path``, store it in the cache, and return the digest."""
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            self.build_cache.setdefault("file_hashes", {})[file_path] = file_hash
            return file_hash
        except Exception as e:
            error(f"Warning: could not hash file {file_path}: {e}")
            return None

    def _has_file_changed(self, file_path: str) -> bool:
        """``True`` if ``file_path`` differs from the cached hash."""
        hashes = self.build_cache.setdefault("file_hashes", {})
        if file_path not in hashes:
            return True

        old_hash = hashes[file_path]
        try:
            with open(file_path, "rb") as f:
                new_hash = hashlib.md5(f.read()).hexdigest()
        except Exception:
            return True

        return old_hash != new_hash

    # -------------------------------------------------------------- discovery

    _C_PATTERNS = ("**/*.c",)
    _CXX_PATTERNS = ("**/*.cpp", "**/*.cc", "**/*.cxx", "**/*.c++")
    _ASM_PATTERNS = ("**/*.s", "**/*.S", "**/*.asm")

    def _iter_project_dirs(self):
        for directory in self.config.get("project_dirs", []) or []:
            yield directory, os.path.join(self.project_path, directory)

    def _file_type(self, file_path: str) -> Optional[str]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".c":
            return "c"
        if ext in {".cpp", ".cc", ".cxx", ".c++"}:
            return "cpp"
        if ext in {".s", ".asm"} or ext == ".S".lower():
            return "asm"
        return None

    def _resolve_supplementary_source_paths(self) -> List[str]:
        """Paths from ``supplementary_sources`` / ``extra_sources`` in ``project.yaml``."""
        raw = (
            self.config.get("supplementary_sources")
            or self.config.get("extra_sources")
            or []
        )
        if isinstance(raw, str):
            raw = [raw]
        elif not isinstance(raw, list):
            return []
        out: List[str] = []
        for item in raw:
            if not item or not isinstance(item, str):
                continue
            joined = os.path.normpath(os.path.join(self.project_path, item.strip()))
            if "*" in item or "?" in item:
                for fp in glob.glob(joined, recursive=False):
                    ft = self._file_type(fp)
                    if ft and os.path.isfile(fp):
                        out.append(os.path.abspath(fp))
            elif os.path.isfile(joined):
                ft = self._file_type(joined)
                if ft:
                    out.append(os.path.abspath(joined))
        return out

    def _find_source_files(self) -> List[str]:
        """Collect every C/C++/ASM source file under the project's source dirs."""
        ignore_patterns = self.config.get("ignore", []) or []
        sources: List[str] = []

        for _, dir_path in self._iter_project_dirs():
            if not os.path.isdir(dir_path):
                continue
            for patterns in (self._C_PATTERNS, self._CXX_PATTERNS, self._ASM_PATTERNS):
                for pattern in patterns:
                    for file_path in glob.glob(
                        os.path.join(dir_path, pattern), recursive=True
                    ):
                        rel = os.path.relpath(file_path, self.project_path)
                        if any(ignored in rel for ignored in ignore_patterns):
                            continue
                        sources.append(file_path)

        skip = {(os.path.normpath(p)).lower() for p in sources}
        for fp in self._resolve_supplementary_source_paths():
            key = os.path.normpath(fp).lower()
            if key not in skip:
                rel = os.path.relpath(fp, self.project_path)
                if any(ignored in rel for ignored in ignore_patterns):
                    continue
                sources.append(fp)
                skip.add(key)

        return sorted(set(sources))

    def _find_include_dirs(self) -> List[str]:
        """Locate include directories for the project."""
        include_dirs: List[str] = []
        seen = set()

        def _add(path: str) -> None:
            abs_path = os.path.abspath(path)
            if abs_path not in seen and os.path.isdir(abs_path):
                seen.add(abs_path)
                include_dirs.append(abs_path)

        for directory, dir_path in self._iter_project_dirs():
            if "include" in directory.lower():
                _add(dir_path)

        # Common conventions: top-level include/ and inc/ folders.
        for candidate in ("include", "inc"):
            _add(os.path.join(self.project_path, candidate))

        for _, dir_path in self._iter_project_dirs():
            for root, dirs, _files in os.walk(dir_path):
                for name in dirs:
                    if name.lower() in ("include", "inc", "headers"):
                        _add(os.path.join(root, name))

        return include_dirs

    # -------------------------------------------------------------- unit tests

    def _iter_unit_test_dirs(self):
        ut = self.config.get("unit_tests") or {}
        for directory in ut.get("project_dirs", []) or []:
            yield directory, os.path.join(self.project_path, directory)

    def _find_unit_test_sources(self) -> List[str]:
        """Collect C/C++/ASM sources under configured unit test directories only."""
        if not self.config.get("unit_tests"):
            return []
        ignore_patterns = self.config.get("ignore", []) or []
        sources: List[str] = []

        for _, dir_path in self._iter_unit_test_dirs():
            if not os.path.isdir(dir_path):
                continue
            for patterns in (self._C_PATTERNS, self._CXX_PATTERNS, self._ASM_PATTERNS):
                for pattern in patterns:
                    for file_path in glob.glob(
                        os.path.join(dir_path, pattern), recursive=True
                    ):
                        rel = os.path.relpath(file_path, self.project_path)
                        if any(ignored in rel for ignored in ignore_patterns):
                            continue
                        sources.append(file_path)

        return sorted(set(sources))

    def _get_unit_test_object_path(self, source_file: str) -> str:
        """Object file under ``.build/unit_tests/`` (separate from the main target)."""
        rel_path = os.path.relpath(source_file, self.project_path)
        obj_dir = os.path.join(self.build_dir, "unit_tests", os.path.dirname(rel_path))
        os.makedirs(obj_dir, exist_ok=True)
        stem = os.path.splitext(os.path.basename(source_file))[0]
        return os.path.join(obj_dir, f"{stem}.o")

    def _resolve_test_executable_path(self, output_path: str) -> str:
        """Resolve the on-disk path for the test runner (e.g. ``.exe`` on Windows)."""
        if os.path.isfile(output_path):
            return output_path
        if os.name == "nt":
            exe = f"{output_path}.exe"
            if os.path.isfile(exe):
                return exe
        return output_path

    def _project_type_lower(self) -> str:
        return str(
            self.config.get("type") or self.config.get("project_type") or "executable"
        ).lower()

    def _should_link_project_library(self, ut: dict) -> bool:
        """Whether to link the main ``output`` archive when building the test executable."""
        explicit = ut.get("link_project")
        if explicit is False:
            return False
        if explicit is True:
            return True
        return self._project_type_lower() == "library"

    async def run_unit_tests(
        self,
        incremental: bool = True,
        silent: bool = False,
    ) -> Tuple[bool, str]:
        """
        Build the unit test executable (if configured) and run it.

        Returns ``(success, message)`` where ``success`` matches the subprocess exit code.
        """
        ut = self.config.get("unit_tests")
        if not ut:
            return False, "no unit_tests configured in project.yaml"

        bootstrap_ok, reason = await self._run_bootstrap()
        if not bootstrap_ok:
            return False, f"bootstrap failed: {reason}"

        source_files = self._find_unit_test_sources()
        if not source_files:
            return False, "no unit test sources found under unit_tests.project_dirs"

        link_main = self._should_link_project_library(ut)
        if ut.get("link_project") is True and self._project_type_lower() != "library":
            return (
                False,
                "unit_tests.link_project: true requires project_type: library "
                "(or omit link_project to use only unit_tests.libraries)",
            )

        if link_main:
            main_ok, main_reason = await self.build(
                incremental=incremental,
                silent=silent,
                build_subprojects=False,
            )
            if not main_ok:
                return False, f"main library build failed (needed for tests): {main_reason}"

            main_lib = os.path.join(
                self.project_path,
                self.config.get("output", "") or "",
            )
            if not os.path.isfile(main_lib):
                return False, (
                    f"main project output not found at {main_lib}; "
                    "check project_type and output"
                )

        obj_files: List[str] = []
        for source_file in source_files:
            file_type = self._file_type(source_file)
            if file_type is None:
                continue

            obj_file = self._get_unit_test_object_path(source_file)
            obj_files.append(obj_file)

            if (
                incremental
                and not self._has_file_changed(source_file)
                and os.path.exists(obj_file)
            ):
                if not silent:
                    log(
                        "Skipping unchanged unit test file: "
                        f"{os.path.relpath(source_file, self.project_path)}"
                    )
                continue

            ok = await self._compile_file(source_file, obj_file, file_type, silent)
            if not ok:
                return False, "unit test compilation failed"

        output_file = os.path.join(self.project_path, ut["output"])
        if obj_files:
            extra_libs: List[str] = []
            if link_main:
                extra_libs.append(
                    os.path.join(
                        self.project_path,
                        self.config.get("output", "") or "",
                    )
                )
            for rel in ut.get("libraries") or []:
                extra_libs.append(os.path.join(self.project_path, rel))

            if not await self._link_executable(
                obj_files, output_file, silent, extra_libs=extra_libs
            ):
                return False, "unit test link failed"

        self._save_build_cache()

        exe = self._resolve_test_executable_path(output_file)
        if not os.path.isfile(exe):
            return False, f"unit test executable not found at {exe}"

        if not silent:
            log(f"Running tests: {os.path.relpath(exe, self.project_path)}")

        try:
            proc = await asyncio.create_subprocess_exec(
                exe,
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_b, stderr_b = await proc.communicate()
            code = proc.returncode if proc.returncode is not None else 1
            out = (stdout_b or b"").decode(errors="replace").strip()
            err = (stderr_b or b"").decode(errors="replace").strip()
            detail = ""
            if out:
                detail += out
            if err:
                detail += ("\n" if detail else "") + err
            if code == 0:
                msg = detail if detail else "tests passed"
                return True, msg
            tail = detail if detail else f"exit code {code}"
            return False, tail
        except Exception as e:
            return False, str(e)

    # ------------------------------------------------------------- flags helpers

    def _get_compiler_flags(self) -> Dict[str, str]:
        """Compose the per-stage compiler/linker/archiver/assembler flag strings."""
        compiler_flags = self.config.get("compiler_flags", {}) or {}
        global_flags = compiler_flags.get("global", "")
        common_flags = compiler_flags.get("common", "")
        c_flags = compiler_flags.get("c", "")
        cpp_flags = compiler_flags.get("cpp", "")
        ld_flags = compiler_flags.get("ld", "")
        ar_flags = compiler_flags.get("ar", "")
        as_flags = compiler_flags.get("as", "")

        languages = [l.lower() for l in self.languages] or [
            str(self.config.get("language", "") or "").lower()
        ]
        standard = str(self.config.get("standard", "") or "").strip()

        c_std = ""
        cpp_std = ""
        if "c" in languages and standard and not standard.startswith("c++"):
            c_std = f"-std={standard}"
        if any(l in ("cpp", "c++") for l in languages) and standard.startswith("c++"):
            cpp_std = f"-std={standard}"

        if c_std and c_std not in c_flags:
            c_flags = f"{c_flags} {c_std}".strip()
        if cpp_std and cpp_std not in cpp_flags:
            cpp_flags = f"{cpp_flags} {cpp_std}".strip()

        return {
            "c": " ".join(s for s in (global_flags, common_flags, c_flags) if s).strip(),
            "cpp": " ".join(s for s in (global_flags, common_flags, cpp_flags) if s).strip(),
            "ld": ld_flags.strip(),
            "ar": ar_flags.strip(),
            "as": as_flags.strip(),
        }

    def _validate_language_standards(self) -> None:
        """Ensure each declared language has exactly one standard."""
        if len(self.languages) != len(self.standards):
            raise ValueError(
                "Number of languages and standards must match: "
                f"languages={self.languages}, standards={self.standards}"
            )

        seen_languages = set()
        for lang in self.languages:
            key = lang.lower()
            if key in seen_languages:
                raise ValueError(
                    f"Language '{lang}' declared more than once with conflicting standards"
                )
            seen_languages.add(key)

    # ------------------------------------------------------------- compile/link

    def _get_object_file_path(self, source_file: str) -> str:
        """Map a source path to its object file under ``.build/``."""
        rel_path = os.path.relpath(source_file, self.project_path)
        obj_dir = os.path.join(self.build_dir, os.path.dirname(rel_path))
        os.makedirs(obj_dir, exist_ok=True)
        stem = os.path.splitext(os.path.basename(source_file))[0]
        return os.path.join(obj_dir, f"{stem}.o")

    async def _run_subprocess(self, cmd: List[str]) -> Tuple[int, str, str]:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return (
            process.returncode if process.returncode is not None else 1,
            stdout.decode(errors="replace") if stdout else "",
            stderr.decode(errors="replace") if stderr else "",
        )

    async def _compile_file(
        self,
        source_file: str,
        obj_file: str,
        file_type: str,
        silent: bool = False,
    ) -> bool:
        """Compile a single source file into an object file."""
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

        os.makedirs(os.path.dirname(obj_file), exist_ok=True)

        cmd = [compiler, "-c", source_file, "-o", obj_file]
        if compiler_flags:
            cmd.extend(compiler_flags.split())
        for include_dir in self._find_include_dirs():
            cmd.append(f"-I{include_dir}")

        if not silent:
            log(f"Compiling {os.path.relpath(source_file, self.project_path)}")

        try:
            returncode, _stdout, stderr_str = await self._run_subprocess(cmd)
            if returncode != 0:
                error(f"Compilation failed for {source_file}: {stderr_str.strip()}")
                return False
            self._update_file_hash(source_file)
            return True
        except Exception as e:
            error(f"Error compiling {source_file}: {e}")
            return False

    async def _link_executable(
        self,
        obj_files: List[str],
        output_file: str,
        silent: bool = False,
        extra_libs: Optional[List[str]] = None,
    ) -> bool:
        """Link ``obj_files`` into the final executable at ``output_file``."""
        flags = self._get_compiler_flags()
        ld_flags = flags["ld"]

        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

        libs = [p for p in (extra_libs or []) if p]
        cmd = [self.ld, "-o", output_file, *obj_files, *libs]
        if ld_flags:
            cmd.extend(ld_flags.split())

        if not silent:
            log(f"Linking executable: {os.path.relpath(output_file, self.project_path)}")

        try:
            returncode, _stdout, stderr_str = await self._run_subprocess(cmd)
            if returncode != 0:
                error(f"Linking failed for {output_file}: {stderr_str.strip()}")
                return False
            return True
        except Exception as e:
            error(f"Error linking {output_file}: {e}")
            return False

    async def _create_library(
        self,
        obj_files: List[str],
        output_file: str,
        silent: bool = False,
    ) -> bool:
        """Bundle ``obj_files`` into a static library at ``output_file``."""
        flags = self._get_compiler_flags()
        ar_flags = flags["ar"]

        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

        # Incremental `ar r` replaces listed members but can leave *orphan* members
        # (same basename from moved paths, removed TUs, or toolchain quirks). The
        # linker may then bind stale object code → subtle crashes (e.g. tests pass
        # only after a clean .build). Rebuild the archive from scratch every time.
        if os.path.isfile(output_file):
            try:
                os.remove(output_file)
            except OSError:
                pass

        cmd = [self.ar, "rcs", output_file]
        if ar_flags:
            cmd.extend(ar_flags.split())
        cmd.extend(obj_files)

        if not silent:
            log(f"Creating library: {os.path.relpath(output_file, self.project_path)}")

        try:
            returncode, _stdout, stderr_str = await self._run_subprocess(cmd)
            if returncode != 0:
                error(f"Creating library failed for {output_file}: {stderr_str.strip()}")
                return False
            return True
        except Exception as e:
            error(f"Error creating library {output_file}: {e}")
            return False

    # --------------------------------------------------------------- bootstrap

    async def _run_bootstrap(self) -> Tuple[bool, str]:
        """Execute optional bootstrap commands defined in the config."""
        bootstrap = self.config.get("bootstrap")
        if not bootstrap:
            return True, "success"

        commands: List[str] = []
        if isinstance(bootstrap, dict):
            cmd = bootstrap.get("command")
            if cmd:
                commands.append(str(cmd))
        elif isinstance(bootstrap, list):
            for entry in bootstrap:
                if isinstance(entry, str):
                    commands.append(entry)
                elif isinstance(entry, dict):
                    cmd = entry.get("command")
                    if cmd:
                        commands.append(str(cmd))
        elif isinstance(bootstrap, str):
            commands.append(bootstrap)

        if not commands:
            return True, "success"

        for command in commands:
            try:
                process = await asyncio.create_subprocess_shell(
                    command,
                    cwd=self.project_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _stdout, stderr_bytes = await process.communicate()
                if process.returncode != 0:
                    return False, (
                        stderr_bytes.decode(errors="replace").strip()
                        or f"Bootstrap command failed: {command}"
                    )
            except Exception as e:
                return False, str(e)

        return True, "success"

    # -------------------------------------------------------------- build/clean

    async def _build_with_options(
        self,
        component: Optional[str] = None,
        incremental: bool = True,
        multi_threaded: bool = True,
        silent: bool = False,
        build_subprojects: bool = False,
    ) -> bool:
        """Run the full compile + link/archive pipeline."""
        bootstrap_ok, reason = await self._run_bootstrap()
        if not bootstrap_ok:
            error(f"Bootstrap failed: {reason}")
            return False

        current_flags = json.dumps(self._get_compiler_flags(), sort_keys=True)
        if current_flags != self.build_cache.get("compiler_flags", ""):
            incremental = False
            if not silent:
                log("Compiler flags changed, performing full rebuild")

        source_files = self._find_source_files()
        if not silent:
            log(f"Found {len(source_files)} source file(s)")

        obj_files: List[str] = []
        for source_file in source_files:
            file_type = self._file_type(source_file)
            if file_type is None:
                continue

            obj_file = self._get_object_file_path(source_file)
            obj_files.append(obj_file)

            if (
                incremental
                and not self._has_file_changed(source_file)
                and os.path.exists(obj_file)
            ):
                if not silent:
                    log(
                        f"Skipping unchanged file: "
                        f"{os.path.relpath(source_file, self.project_path)}"
                    )
                continue

            ok = await self._compile_file(source_file, obj_file, file_type, silent)
            if not ok:
                return False

        output_file = os.path.join(
            self.project_path, self.config.get("output", "") or ""
        )

        project_type = str(
            self.config.get("type") or self.config.get("project_type") or "executable"
        ).lower()

        if output_file and obj_files:
            if project_type == "executable":
                if not await self._link_executable(obj_files, output_file, silent):
                    return False
            else:
                if not await self._create_library(obj_files, output_file, silent):
                    return False

        self.build_cache["last_build_time"] = time.time()
        self.build_cache["compiler_flags"] = current_flags
        self.build_cache["output_file"] = output_file
        self._save_build_cache()

        if build_subprojects and self.subproject_engines:
            for name, engine in self.subproject_engines.items():
                if not silent:
                    log(f"Building subproject: {name}")
                if not await engine._build_with_options(
                    component=component,
                    incremental=incremental,
                    multi_threaded=multi_threaded,
                    silent=silent,
                    build_subprojects=True,
                ):
                    return False

        return True

    async def build(
        self,
        component: Optional[str] = None,
        incremental: bool = True,
        multi_threaded: bool = True,
        silent: bool = False,
        build_subprojects: bool = True,
    ) -> Tuple[bool, str]:
        """Public entry point. Returns ``(success, reason)``."""
        try:
            success = await self._build_with_options(
                component=component,
                incremental=incremental,
                multi_threaded=multi_threaded,
                silent=silent,
                build_subprojects=build_subprojects,
            )
            return bool(success), ("success" if success else "build failed")
        except Exception as e:
            error(f"Build failed with exception: {e}")
            return False, str(e)

    async def clean(self, clean_subprojects: bool = False) -> bool:
        """Remove build artefacts (and, optionally, subproject artefacts)."""
        try:
            if os.path.exists(self.build_dir):
                for item in Path(self.build_dir).glob("**/*"):
                    if item.is_file():
                        try:
                            item.unlink()
                        except Exception:
                            pass
                # Remove now-empty subdirectories.
                for item in sorted(
                    Path(self.build_dir).glob("**/*"),
                    key=lambda p: len(p.parts),
                    reverse=True,
                ):
                    if item.is_dir():
                        try:
                            item.rmdir()
                        except OSError:
                            pass

            output_value = self.config.get("output", "")
            if output_value:
                output_file = os.path.join(self.project_path, output_value)
                if os.path.isfile(output_file):
                    try:
                        os.remove(output_file)
                    except Exception:
                        pass

            ut = self.config.get("unit_tests")
            if isinstance(ut, dict) and ut.get("output"):
                ut_out = os.path.join(self.project_path, ut["output"])
                candidates = [ut_out]
                if os.name == "nt":
                    candidates.append(f"{ut_out}.exe")
                for p in candidates:
                    if os.path.isfile(p):
                        try:
                            os.remove(p)
                        except Exception:
                            pass

            ut_obj_root = os.path.join(self.build_dir, "unit_tests")
            if os.path.isdir(ut_obj_root):
                try:
                    shutil.rmtree(ut_obj_root)
                except Exception:
                    pass

            self.build_cache = {
                "file_hashes": {},
                "last_build_time": 0,
                "compiler_flags": "",
                "output_file": "",
            }

            if clean_subprojects and self.subproject_engines:
                for name, engine in self.subproject_engines.items():
                    log(f"Cleaning subproject: {name}")
                    await engine.clean(clean_subprojects=True)

            return True
        except Exception as e:
            error(f"Error during clean: {e}")
            return False

    # --------------------------------------------------------------- info

    def get_project_info(self) -> dict:
        """Return a dictionary describing the project for display/inspection."""
        return {
            "name": self.config.get("name") or self.config.get("project", "unknown"),
            "version": self.config.get("version", "0.0.1"),
            "description": self.config.get("description", ""),
            "type": self.config.get("type")
            or self.config.get("project_type", "executable"),
            "language": self.config.get("language", ""),
            "standard": self.config.get("standard", ""),
            "compiler": self.cxx_compiler,
            "output": self.config.get("output", ""),
            "source_files": self._find_source_files(),
            "include_dirs": self._find_include_dirs(),
            "subprojects": list(self.subproject_engines.keys())
            if self.subproject_engines
            else [],
            "unit_tests": self.config.get("unit_tests"),
        }
