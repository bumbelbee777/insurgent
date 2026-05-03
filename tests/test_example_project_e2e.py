"""End-to-end checks for the checked-in ``example`` C++ project."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ROOT = REPO_ROOT / "example"
PROJECT_YAML = EXAMPLE_ROOT / "project.yaml"


def _example_compiler_exe() -> Optional[str]:
    if not PROJECT_YAML.is_file():
        return None
    with PROJECT_YAML.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    compiler = str(cfg.get("compiler", "") or "").strip()
    if not compiler:
        return "g++"
    # project.yaml lists the driver first (e.g. "clang++").
    return compiler.split()[0]


requires_cxx = pytest.mark.skipif(
    not shutil.which(_example_compiler_exe() or ""),
    reason="C++ toolchain for example/project.yaml not on PATH",
)


pytestmark = pytest.mark.integration


def test_devshell_one_off_sh_pwd():
    """CLI path that exercises ShellInterface via ``insurgent sh``."""
    proc = subprocess.run(
        [sys.executable, "-m", "insurgent", "sh", "pwd"],
        cwd=EXAMPLE_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    hay = (proc.stdout or "").replace("/", os.sep)
    assert str(EXAMPLE_ROOT.resolve()) in hay


def test_devshell_interactive_repl_stdin_eof():
    """Non-interactive drive of the stdin REPL (welcome + pwd + exit)."""
    proc = subprocess.run(
        [sys.executable, "-m", "insurgent"],
        cwd=EXAMPLE_ROOT,
        input="pwd\nversion\nexit\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=120,
    )
    assert proc.returncode == 0
    out = proc.stdout or ""
    assert str(EXAMPLE_ROOT.resolve()) in out.replace("/", os.sep)
    assert "InsurgeNT" in out


@requires_cxx
def test_example_build_cli():
    cxx = _example_compiler_exe()
    assert cxx and shutil.which(cxx)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "insurgent",
            "build",
            "--silent",
        ],
        cwd=EXAMPLE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr


@requires_cxx
def test_example_unit_tests_cli():
    cxx = _example_compiler_exe()
    assert cxx and shutil.which(cxx)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "insurgent",
            "test",
            "--silent",
        ],
        cwd=EXAMPLE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr


@requires_cxx
def test_example_main_binary_runs():
    exe = EXAMPLE_ROOT / "binaries" / "insurgent-example"
    if sys.platform.startswith("win"):
        exe = exe.with_suffix(".exe")
    proc = subprocess.run(
        [str(exe)],
        cwd=EXAMPLE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "InsurgeNT" in (proc.stdout or "")
