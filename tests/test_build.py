import os
from unittest.mock import MagicMock, patch

import pytest
import yaml

from insurgent.build.BuildEngine import BuildEngine


@pytest.fixture
def project_dir(tmp_path):
    """Create a temporary project directory with basic structure."""
    project_path = tmp_path / "test_project"
    project_path.mkdir()

    # Create project.yaml
    config = {
        "name": "test_project",
        "version": "0.1.0",
        "description": "Test project",
        "type": "executable",
        "language": "c",
        "standard": "c99",
        "output": "bin/test_project",
        "project_dirs": ["src", "include", "test"],
        "compiler_flags": {
            "global": "-Wall -Wextra",
            "c": "-std=c99",
        },
    }

    with open(project_path / "project.yaml", "w") as f:
        yaml.dump(config, f)

    # Create source file
    src_dir = project_path / "src"
    src_dir.mkdir()
    with open(src_dir / "main.c", "w") as f:
        f.write(
            """#include <stdio.h>

int main(int argc, char** argv) {
    printf("Hello, InsurgeNT!\\n");
    return 0;
}
"""
        )

    return project_path


@pytest.fixture
def build_engine(project_dir):
    """Create a BuildEngine instance for testing."""
    return BuildEngine(str(project_dir))


def test_build_engine_initialization(build_engine):
    """Test BuildEngine initialization."""
    assert build_engine.project_path is not None
    assert build_engine.config is not None
    assert build_engine.build_dir is not None
    assert build_engine.cache_file is not None


def test_project_config_loading(build_engine):
    """Test project configuration loading."""
    assert build_engine.config["name"] == "test_project"
    assert build_engine.config["version"] == "0.1.0"
    assert build_engine.config["type"] == "executable"
    assert build_engine.config["language"] == "c"
    assert build_engine.config["standard"] == "c99"


def test_source_file_discovery(build_engine):
    """Test source file discovery."""
    source_files = build_engine._find_source_files()
    assert len(source_files) > 0
    assert any(f.endswith("main.c") for f in source_files)


def test_include_dir_discovery(build_engine):
    """Test include directory discovery."""
    # Create an include directory
    include_dir = os.path.join(build_engine.project_path, "include")
    os.makedirs(include_dir, exist_ok=True)

    include_dirs = build_engine._find_include_dirs()
    assert len(include_dirs) > 0
    assert any("include" in d for d in include_dirs)


def test_compiler_flags(build_engine):
    """Test compiler flags generation."""
    flags = build_engine._get_compiler_flags()
    assert "c" in flags
    assert "-Wall" in flags["c"]
    assert "-Wextra" in flags["c"]
    assert "-std=c99" in flags["c"]


def test_build_cache_operations(build_engine):
    """Test build cache operations."""
    # Test cache loading
    cache = build_engine._load_build_cache()
    assert isinstance(cache, dict)
    assert "file_hashes" in cache

    # Test cache saving
    build_engine._save_build_cache()
    assert os.path.exists(build_engine.cache_file)


def test_file_hash_operations(build_engine):
    """Test file hash operations."""
    source_file = os.path.join(build_engine.project_path, "src", "main.c")

    # Test hash update
    hash_value = build_engine._update_file_hash(source_file)
    assert hash_value is not None

    # Test file change detection - should be False since we just updated the hash
    assert build_engine._has_file_changed(source_file) is False

    # Modify the file to trigger a change
    with open(source_file, "a") as f:
        f.write("\n// Modified")

    # Now it should detect the change
    assert build_engine._has_file_changed(source_file) is True


@pytest.mark.asyncio
async def test_build_process(build_engine):
    """Test the build process."""
    with patch.object(build_engine, "_compile_file") as mock_compile:
        mock_compile.return_value = True

        with patch.object(build_engine, "_link_executable") as mock_link:
            mock_link.return_value = True

            success, _ = await build_engine.build()
            assert success is True
            mock_compile.assert_called()
            mock_link.assert_called()


@pytest.mark.asyncio
async def test_clean_process(build_engine):
    """Test the clean process."""
    # Create some build artifacts
    os.makedirs(build_engine.build_dir, exist_ok=True)
    with open(os.path.join(build_engine.build_dir, "test.o"), "w") as f:
        f.write("test")

    # Test cleaning
    success = await build_engine.clean()
    assert success is True
    assert not os.path.exists(os.path.join(build_engine.build_dir, "test.o"))


def test_project_info(build_engine):
    """Test project information retrieval."""
    info = build_engine.get_project_info()
    assert info["name"] == "test_project"
    assert info["version"] == "0.1.0"
    assert info["type"] == "executable"
    assert info["language"] == "c"
    assert "source_files" in info
    assert "include_dirs" in info
    assert "unit_tests" in info


def test_compiler_detection(build_engine):
    """Test compiler detection."""
    c_compiler, cxx_compiler = build_engine._detect_compilers()
    assert c_compiler is not None
    assert cxx_compiler is not None


def test_tool_detection(build_engine):
    """Test tool detection."""
    ar = build_engine._detect_tool("ar", "ar")
    as_tool = build_engine._detect_tool("as", "as")
    ld = build_engine._detect_tool("ld", build_engine.cxx_compiler)

    assert ar is not None
    assert as_tool is not None
    assert ld is not None


def test_language_standard_validation(build_engine):
    """Test language standard validation."""
    # Test valid standards
    build_engine.languages = ["c"]
    build_engine.standards = ["c99"]
    build_engine._validate_language_standards()  # Should not raise

    # Test invalid standards
    build_engine.languages = ["c", "c"]
    build_engine.standards = ["c99", "c11"]
    with pytest.raises(ValueError):
        build_engine._validate_language_standards()


@pytest.mark.asyncio
async def test_bootstrap_execution(build_engine):
    """Test bootstrap command execution."""
    # Add bootstrap commands to config
    build_engine.config["bootstrap"] = ["echo 'Bootstrap test'"]

    # Test bootstrap execution
    status, reason = await build_engine._run_bootstrap()
    assert status is True
    assert reason == "success"


@pytest.mark.asyncio
async def test_build_with_options(build_engine):
    """Test building with different options."""
    with patch.object(build_engine, "_build_with_options") as mock_build:
        mock_build.return_value = True

        # Test incremental build
        success, _ = await build_engine.build(incremental=True)
        assert success is True
        mock_build.assert_called_with(
            component=None,
            incremental=True,
            multi_threaded=True,
            silent=False,
            build_subprojects=False,
        )

        # Test full build
        success, _ = await build_engine.build(incremental=False)
        assert success is True
        mock_build.assert_called_with(
            component=None,
            incremental=False,
            multi_threaded=True,
            silent=False,
            build_subprojects=False,
        )
