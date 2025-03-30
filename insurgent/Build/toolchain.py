import asyncio
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from insurgent.Logging.logger import error, log
from insurgent.Logging.terminal import *

# Define default paths
DEFAULT_TOOLCHAIN_DIR = os.path.join(os.path.expanduser("~"), ".insurgent", "toolchain")
DEFAULT_BUILD_DIR = os.path.join(os.path.expanduser("~"), ".insurgent", "build")

# Define installation directories based on platform
if platform.system() == "Windows":
    DEFAULT_INSTALL_DIR = os.path.expandvars("%LOCALAPPDATA%\\InsurgeNT\\toolchain")
elif platform.system() == "Darwin":  # macOS
    DEFAULT_INSTALL_DIR = "/usr/local/bin"
else:  # Linux and others
    DEFAULT_INSTALL_DIR = "/usr/local/bin"

# Supported toolchains and versions
SUPPORTED_TOOLCHAINS = {
    "gcc": {
        "version": "13.2.0",
        "url": "https://ftp.gnu.org/gnu/gcc/gcc-13.2.0/gcc-13.2.0.tar.xz",
        "archive": "gcc-13.2.0.tar.xz",
        "dir": "gcc-13.2.0",
    },
    "clang": {
        "version": "18.1.1",
        "url": "https://github.com/llvm/llvm-project/releases/download/llvmorg-18.1.1/llvm-project-18.1.1.src.tar.xz",
        "archive": "llvm-project-18.1.1.src.tar.xz",
        "dir": "llvm-project-18.1.1.src",
    },
}


class ToolchainManager:
    """Manager for downloading, building, and installing compiler toolchains"""

    def __init__(
        self,
        toolchain_name: str = "gcc",
        toolchain_dir: Optional[str] = None,
        build_dir: Optional[str] = None,
        install_dir: Optional[str] = None,
        verbose: bool = False,
    ):
        """
        Initialize the toolchain manager.

        Args:
            toolchain_name: Name of the toolchain to manage (gcc, clang)
            toolchain_dir: Directory to store toolchain source
            build_dir: Directory to build the toolchain
            install_dir: Directory to install the toolchain
            verbose: Whether to show verbose output
        """
        if toolchain_name not in SUPPORTED_TOOLCHAINS:
            raise ValueError(
                f"Unsupported toolchain: {toolchain_name}. "
                f"Supported toolchains: {', '.join(SUPPORTED_TOOLCHAINS.keys())}"
            )

        self.toolchain_name = toolchain_name
        self.toolchain_info = SUPPORTED_TOOLCHAINS[toolchain_name]
        self.toolchain_dir = toolchain_dir or os.path.join(
            DEFAULT_TOOLCHAIN_DIR, toolchain_name
        )
        self.build_dir = build_dir or os.path.join(DEFAULT_BUILD_DIR, toolchain_name)
        self.install_dir = install_dir or DEFAULT_INSTALL_DIR
        self.verbose = verbose

        # Ensure directories exist
        os.makedirs(self.toolchain_dir, exist_ok=True)
        os.makedirs(self.build_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.install_dir), exist_ok=True)

    def get_version(self) -> Optional[str]:
        """
        Get the version of the installed toolchain.

        Returns:
            Version string if available, None otherwise
        """
        try:
            compiler = self.toolchain_name
            # For clang, use clang++ if checking for C++ compiler
            if compiler == "clang" and os.path.exists(shutil.which("clang++") or ""):
                compiler = "clang++"

            output = subprocess.check_output([compiler, "--version"], text=True)
            return output.split("\n")[0]
        except (FileNotFoundError, subprocess.CalledProcessError):
            return None

    async def run_command(
        self, cmd: Union[str, List[str]], cwd: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Run a command asynchronously.

        Args:
            cmd: Command to run (string or list of args)
            cwd: Working directory

        Returns:
            Tuple of (success, output)
        """
        if self.verbose:
            if isinstance(cmd, list):
                log(f"Running: {' '.join(cmd)}")
            else:
                log(f"Running: {cmd}")

        try:
            if isinstance(cmd, str):
                # Use shell=True for string commands
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    cwd=cwd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            else:
                # Use create_subprocess_exec for list of args
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=cwd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                if self.verbose and stdout:
                    log(stdout.decode().strip())
                return True, stdout.decode().strip()
            else:
                error_msg = stderr.decode().strip()
                error(f"Command failed with code {process.returncode}: {error_msg}")
                return False, error_msg

        except Exception as e:
            error(f"Error running command: {e}")
            return False, str(e)

    async def download_sources(self) -> bool:
        """
        Download toolchain sources.

        Returns:
            True if successful, False otherwise
        """
        log(f"{YELLOW}Checking for {self.toolchain_name} toolchain sources...{RESET}")

        # Check if sources already exist
        toolchain_src_dir = os.path.join(self.toolchain_dir, self.toolchain_info["dir"])
        if os.path.exists(toolchain_src_dir) and os.listdir(toolchain_src_dir):
            log(f"{GREEN}Toolchain sources already present. Skipping download.{RESET}")
            return True

        url = self.toolchain_info["url"]
        archive = self.toolchain_info["archive"]

        log(f"{YELLOW}Downloading toolchain from {url}...{RESET}")

        # Create a temporary directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = os.path.join(temp_dir, archive)

            # Download with curl or wget
            if shutil.which("curl"):
                cmd = f"curl -L {url} -o {archive_path}"
            elif shutil.which("wget"):
                cmd = f"wget {url} -O {archive_path}"
            else:
                error("Neither curl nor wget is installed! Cannot download toolchain.")
                return False

            success, _ = await self.run_command(cmd)
            if not success:
                return False

            log(f"{YELLOW}Download complete. Extracting...{RESET}")

            # Extract the archive
            if shutil.which("tar"):
                extract_cmd = f"tar -xf {archive_path} -C {self.toolchain_dir}"
                success, _ = await self.run_command(extract_cmd)
                if not success:
                    return False
            elif shutil.which("7z"):
                # 7z requires two steps: extract and move
                extract_dir = os.path.join(temp_dir, "extract")
                os.makedirs(extract_dir, exist_ok=True)

                extract_cmd = f"7z x {archive_path} -o{extract_dir}"
                success, _ = await self.run_command(extract_cmd)
                if not success:
                    return False

                # Move extracted directory to toolchain dir
                src_dir = os.path.join(extract_dir, self.toolchain_info["dir"])
                dst_dir = os.path.join(self.toolchain_dir, self.toolchain_info["dir"])

                try:
                    if os.path.exists(src_dir):
                        shutil.move(src_dir, dst_dir)
                    else:
                        # If extracted directory structure is different, move all contents
                        os.makedirs(dst_dir, exist_ok=True)
                        for item in os.listdir(extract_dir):
                            shutil.move(os.path.join(extract_dir, item), dst_dir)
                except Exception as e:
                    error(f"Error moving extracted files: {e}")
                    return False
            else:
                error("No extraction tools available! Install 'tar' or '7z'.")
                return False

        log(f"{GREEN}Toolchain extracted successfully!{RESET}")
        return True

    async def build_toolchain(self) -> bool:
        """
        Build the toolchain.

        Returns:
            True if successful, False otherwise
        """
        log(f"{YELLOW}Building {self.toolchain_name} toolchain...{RESET}")

        # Ensure build directory exists
        os.makedirs(self.build_dir, exist_ok=True)

        # Determine source directory
        source_dir = os.path.join(self.toolchain_dir, self.toolchain_info["dir"])
        if not os.path.exists(source_dir):
            error(f"Toolchain source directory not found: {source_dir}")
            return False

        # Configure and build based on toolchain type
        if self.toolchain_name == "gcc":
            return await self._build_gcc(source_dir)
        elif self.toolchain_name == "clang":
            return await self._build_clang(source_dir)
        else:
            error(f"Building {self.toolchain_name} is not implemented")
            return False

    async def _build_gcc(self, source_dir: str) -> bool:
        """
        Build GCC toolchain.

        Args:
            source_dir: Source directory

        Returns:
            True if successful, False otherwise
        """
        cpu_count = os.cpu_count() or 4

        # Configure
        configure_cmd = f"../gcc-{self.toolchain_info['version']}/configure --prefix={self.install_dir} --enable-languages=c,c++ --disable-multilib"
        success, _ = await self.run_command(configure_cmd, cwd=self.build_dir)
        if not success:
            return False

        # Make
        make_cmd = f"make -j{cpu_count}"
        success, _ = await self.run_command(make_cmd, cwd=self.build_dir)
        if not success:
            return False

        log(f"{GREEN}GCC toolchain built successfully!{RESET}")
        return True

    async def _build_clang(self, source_dir: str) -> bool:
        """
        Build Clang toolchain.

        Args:
            source_dir: Source directory

        Returns:
            True if successful, False otherwise
        """
        cpu_count = os.cpu_count() or 4

        # Create a separate build directory for LLVM
        llvm_build_dir = os.path.join(self.build_dir, "llvm-build")
        os.makedirs(llvm_build_dir, exist_ok=True)

        # Configure with CMake
        cmake_cmd = f"cmake -G 'Unix Makefiles' -DCMAKE_INSTALL_PREFIX={self.install_dir} -DLLVM_ENABLE_PROJECTS=clang -DCMAKE_BUILD_TYPE=Release {source_dir}/llvm"
        success, _ = await self.run_command(cmake_cmd, cwd=llvm_build_dir)
        if not success:
            return False

        # Build
        make_cmd = f"make -j{cpu_count}"
        success, _ = await self.run_command(make_cmd, cwd=llvm_build_dir)
        if not success:
            return False

        log(f"{GREEN}Clang toolchain built successfully!{RESET}")
        return True

    async def install_toolchain(self) -> bool:
        """
        Install the toolchain.

        Returns:
            True if successful, False otherwise
        """
        log(f"{YELLOW}Installing {self.toolchain_name} to {self.install_dir}...{RESET}")

        install_dir = Path(self.install_dir)

        if self.toolchain_name == "gcc":
            install_cmd = "make install"
            success, _ = await self.run_command(install_cmd, cwd=self.build_dir)
            if not success:
                return False
        elif self.toolchain_name == "clang":
            install_cmd = "make install"
            success, _ = await self.run_command(
                install_cmd, cwd=os.path.join(self.build_dir, "llvm-build")
            )
            if not success:
                return False
        else:
            error(f"Installing {self.toolchain_name} is not implemented")
            return False

        # Check if install directory is in PATH
        path_env = os.environ.get("PATH", "").split(os.pathsep)
        install_bin_dir = str(
            install_dir / "bin" if platform.system() != "Windows" else install_dir
        )

        if install_bin_dir not in path_env:
            log(f"{YELLOW}Adding {install_bin_dir} to PATH...{RESET}")

            # Add to current process PATH
            os.environ["PATH"] = os.pathsep.join(
                [install_bin_dir, os.environ.get("PATH", "")]
            )

            # Suggest permanent PATH addition based on platform
            if platform.system() == "Windows":
                log(
                    f"{YELLOW}To permanently add to PATH, run this in PowerShell as Administrator:{RESET}"
                )
                log(
                    f'[Environment]::SetEnvironmentVariable("PATH", "$env:PATH;{install_bin_dir}", "Machine")'
                )
            else:
                log(
                    f"{YELLOW}To permanently add to PATH, add this to your ~/.bashrc or ~/.zshrc:{RESET}"
                )
                log(f'export PATH="{install_bin_dir}:$PATH"')

        log(f"{GREEN}Toolchain installation complete!{RESET}")
        return True

    async def setup_toolchain(self) -> bool:
        """
        Download, build and install the toolchain.

        Returns:
            True if successful, False otherwise
        """
        log(
            f"{CYAN}🔨 InsurgeNT Toolchain Setup - {self.toolchain_name.upper()} 🔨{RESET}"
        )

        # Check if toolchain is already installed
        current_version = self.get_version()
        if current_version:
            log(f"{GREEN}Detected {self.toolchain_name}: {current_version}{RESET}")
            user_input = input(
                f"Found existing {self.toolchain_name} installation. "
                f"Continue with setup anyway? [y/N]: "
            ).lower()
            if user_input != "y":
                log("Setup cancelled.")
                return True

        # Download sources
        if not await self.download_sources():
            error("Failed to download toolchain sources")
            return False

        # Build toolchain
        if not await self.build_toolchain():
            error("Failed to build toolchain")
            return False

        # Install toolchain
        if not await self.install_toolchain():
            error("Failed to install toolchain")
            return False

        log(f"{GREEN}🚀 {self.toolchain_name.upper()} toolchain setup complete!{RESET}")
        log(f"{GREEN}May your project compile without errors!{RESET}")
        return True


def get_toolchain() -> str:
    """
    Get the first available supported toolchain.

    Returns:
        Toolchain name or empty string if none found
    """
    for compiler in SUPPORTED_TOOLCHAINS.keys():
        # Check for compiler existence in PATH
        if shutil.which(compiler):
            try:
                version = subprocess.check_output(
                    [compiler, "--version"], text=True
                ).split("\n")[0]
                log(f"Detected {compiler}: {version}")
                return compiler
            except (subprocess.SubprocessError, OSError):
                pass

    log(
        f"{YELLOW}No supported toolchains found. Available toolchains: {', '.join(SUPPORTED_TOOLCHAINS.keys())}{RESET}"
    )
    return ""


def setup_toolchain(toolchain_name=None, install_dir=None, verbose=False):
    """
    Synchronous wrapper for setting up a toolchain.

    Args:
        toolchain_name: Name of the toolchain to set up
        install_dir: Directory to install the toolchain
        verbose: Whether to show verbose output

    Returns:
        True if successful, False otherwise
    """
    # If no toolchain specified, use gcc as default
    if not toolchain_name:
        toolchain_name = "gcc"
        log(f"No toolchain specified, using {toolchain_name} as default")

    # Check if toolchain is supported
    if toolchain_name not in SUPPORTED_TOOLCHAINS:
        error(f"Unsupported toolchain: {toolchain_name}")
        error(f"Supported toolchains: {', '.join(SUPPORTED_TOOLCHAINS.keys())}")
        return False

    # Create and configure toolchain manager
    manager = ToolchainManager(
        toolchain_name=toolchain_name, install_dir=install_dir, verbose=verbose
    )

    # Create an event loop and run the setup_toolchain coroutine
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(manager.setup_toolchain())
    finally:
        if not loop.is_closed():
            loop.close()


# For backwards compatibility
def make_toolchain():
    """Legacy function for backwards compatibility"""
    return setup_toolchain(toolchain_name="gcc", verbose=True)
