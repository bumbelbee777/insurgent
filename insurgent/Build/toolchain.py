import os
import shutil
import subprocess
import sys
import platform
from insurgent.Logging.logger import log, error

TOOLCHAIN_DIR = os.path.abspath("toolchain")
BUILD_DIR = os.path.abspath("build")

if platform.system() == "Windows":
    INSTALL_DIR = os.path.expandvars("%LOCALAPPDATA%\\InsurgeNT\\toolchain")
elif platform.system() == "Darwin":
    INSTALL_DIR = "/usr/local/bin"
else:
    INSTALL_DIR = "/usr/bin"

SUPPORTED_TOOLCHAINS = ["gcc", "clang"]
TOOLCHAIN_URL = "https://ftp.gnu.org/gnu/gcc/gcc-13.2.0/gcc-14.2.0.tar.xz"
ARCHIVE_NAME = "gcc-14.2.0.tar.xz"
EXTRACTED_DIR = "gcc-14.2.0"

def get_toolchain_version(compiler="gcc"):
    try:
        output = subprocess.check_output([compiler, "--version"], text=True)
        return output.split("\n")[0]
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

def get_toolchain():
    for compiler in SUPPORTED_TOOLCHAINS:
        version = get_toolchain_version(compiler)
        if version:
            log(f"Detected {compiler}: {version}")
            return compiler
    error("No supported toolchains found!")
    sys.exit(1)

def run_command(cmd, cwd=None, show_output=False):
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if show_output:
            log(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        error(f"Command '{cmd}' failed.\n{e.stderr.strip()}")
        sys.exit(1)

def download_sources():
    log("Checking for toolchain sources...")
    if os.path.exists(TOOLCHAIN_DIR):
        log("Toolchain sources already present. Skipping download.")
        return

    log(f"Downloading toolchain from {TOOLCHAIN_URL}...")

    if shutil.which("curl"):
        run_command(f"curl -L {TOOLCHAIN_URL} -o {ARCHIVE_NAME}")
    elif shutil.which("wget"):
        run_command(f"wget {TOOLCHAIN_URL} -O {ARCHIVE_NAME}")
    else:
        error("Neither curl nor wget is installed! Cannot download toolchain.")
        sys.exit(1)

    log("Download complete. Extracting...")

    if shutil.which("tar"):
        run_command(f"tar -xvf {ARCHIVE_NAME}")
    elif shutil.which("7z"):
        run_command(f"7z x {ARCHIVE_NAME}")
    else:
        error("No extraction tools available! Install `tar` or `7z`.")
        sys.exit(1)

    os.rename(EXTRACTED_DIR, TOOLCHAIN_DIR)
    log("Toolchain extracted successfully!")

def build_toolchain():
    os.makedirs(BUILD_DIR, exist_ok=True)
    log("Building Toolchain...")

    cpu_count = os.cpu_count() or 4
    configure_cmd = f"../configure --prefix={INSTALL_DIR} --enable-languages=c,c++ --disable-multilib"
    make_cmd = f"make -j{cpu_count}"

    run_command(configure_cmd, cwd=BUILD_DIR, show_output=True)
    run_command(make_cmd, cwd=BUILD_DIR, show_output=True)

    log("Toolchain build completed!")

def install_toolchain():
    log(f"Installing toolchain to {INSTALL_DIR}...")

    if platform.system() != "Windows":
        run_command("make install", cwd=BUILD_DIR, show_output=True)
    else:
        error("Windows installation requires manual setup!")

    if INSTALL_DIR not in os.environ["PATH"]:
        log(f"Adding {INSTALL_DIR}/bin to PATH...")
        os.environ["PATH"] += os.pathsep + os.path.join(INSTALL_DIR, "bin")
        log("Toolchain added to PATH! Restart your shell or add it manually.")

def make_toolchain():
    log("🔥 InsurgeNT Toolchain Builder 🔥")
    
    download_sources()
    build_toolchain()
    install_toolchain()

    log("🚀 Toolchain setup complete! May your project compile without errors!")
