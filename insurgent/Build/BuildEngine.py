import os
import subprocess
import asyncio
import time
from datetime import datetime
from insurgent.Meta.config import load_config
from insurgent.Logging.logger import error, log
from insurgent.Logging.terminal import *
from insurgent.Build.toolchain import get_toolchain

class BuildEngine:
    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(project_path)
        self.jobs = os.cpu_count() or 1
        self.config = self._load_project_config()
        self.c_compiler, self.cxx_compiler = self._detect_compilers()

    def _load_project_config(self):
        config_path = os.path.join(self.project_path, "project.yaml")
        if not os.path.exists(config_path):
            error(f"No `project.yaml` found in {self.project_path}.")
            return {}

        log(f"{INFO} Loading project configuration from {config_path}...")
        return load_config(config_path)

    def _detect_compilers(self):
        toolchain = get_toolchain(self.config.get("toolchain", "default"))
        return toolchain.get("c_compiler", "gcc"), toolchain.get("cxx_compiler", "g++")

    async def _run_command(self, cmd, cwd=None, silent=False):
        if not silent:
            log(f"[BUILD] Running command: {' '.join(cmd)}")

        process = await asyncio.create_subprocess_exec(
            *cmd, cwd=cwd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            if not silent:
                log(stdout.decode().strip())
        else:
            error(stderr.decode().strip())
            raise subprocess.CalledProcessError(process.returncode, cmd)

    async def _build_with_options(self, component, incremental=False, multi_threaded=True, silent=False):
        make_cmd = ["make", f"CXX={self.cxx_compiler}", f"CC={self.c_compiler}", component]

        if not incremental:
            make_cmd.append("-B")
        if multi_threaded:
            make_cmd.append(f"-j{self.jobs}")
        if silent:
            make_cmd.append("silent")

        await self._run_command(make_cmd, cwd=self.project_path, silent=silent)
