"""Tests for optional native unit_tests support in BuildEngine."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import yaml

from insurgent.build.BuildEngine import BuildEngine


def _write_project_yaml(root: Path, **extras) -> None:
    data = {
        "project": "p",
        "authors": ["a"],
        "license": "MIT",
        "language": "c",
        "standard": "c99",
        "compiler": "gcc",
        "project_dirs": ["src"],
        "project_type": "executable",
        "output": "bin/p",
    }
    data.update(extras)
    with open(root / "project.yaml", "w", encoding="utf-8") as f:
        yaml.dump(data, f)


def test_unit_tests_invalid_shape_removed(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    _write_project_yaml(root, unit_tests="not-a-mapping")
    (root / "src").mkdir()
    engine = BuildEngine(str(root))
    assert engine.config.get("unit_tests") is None


def test_unit_tests_requires_dirs_and_output(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    _write_project_yaml(root, unit_tests={"project_dirs": [], "output": "bin/x"})
    (root / "src").mkdir()
    engine = BuildEngine(str(root))
    assert engine.config.get("unit_tests") is None


def test_unit_tests_single_project_dir_normalized(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    _write_project_yaml(
        root,
        unit_tests={"project_dirs": "tests", "output": "bin/run_tests"},
    )
    (root / "src").mkdir()
    (root / "tests").mkdir()
    engine = BuildEngine(str(root))
    ut = engine.config["unit_tests"]
    assert ut["project_dirs"] == ["tests"]
    assert ut["output"] == "bin/run_tests"


def test_find_unit_test_sources_respects_ignore(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    _write_project_yaml(
        root,
        unit_tests={"project_dirs": ["tests"], "output": "bin/t"},
        ignore=["skipme"],
    )
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "tests" / "good.c").write_text("void g() {}\n")
    skipped = root / "tests" / "skipme"
    skipped.mkdir()
    (skipped / "bad.c").write_text("int main(){return 1;}\n")

    engine = BuildEngine(str(root))
    paths = engine._find_unit_test_sources()
    assert len(paths) == 1
    assert paths[0].endswith(f"good.c")


@pytest.mark.asyncio
async def test_run_unit_tests_not_configured(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    _write_project_yaml(root)
    (root / "src").mkdir()

    ok, msg = await BuildEngine(str(root)).run_unit_tests()
    assert ok is False
    assert "no unit_tests configured" in msg


@pytest.mark.asyncio
async def test_run_unit_tests_no_sources(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    _write_project_yaml(
        root,
        unit_tests={"project_dirs": ["tests"], "output": "bin/x"},
    )
    (root / "src").mkdir()
    (root / "tests").mkdir()

    ok, msg = await BuildEngine(str(root)).run_unit_tests()
    assert ok is False
    assert "no unit test sources" in msg


@pytest.mark.asyncio
async def test_run_unit_tests_build_and_invoke_mocked(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    _write_project_yaml(
        root,
        unit_tests={"project_dirs": ["tests"], "output": "bin/run_tests"},
    )
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "tests" / "t.c").write_text("int main(void) { return 0; }\n")

    engine = BuildEngine(str(root))

    fake_proc = AsyncMock()
    fake_proc.communicate = AsyncMock(return_value=(b"", b""))
    fake_proc.returncode = 0

    async def touch_link(obj_files, output_file, silent=False, extra_libs=None):
        out = Path(output_file)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"")
        return True

    with patch.object(
        engine, "_run_bootstrap", AsyncMock(return_value=(True, "success"))
    ):
        with patch.object(engine, "_compile_file", AsyncMock(return_value=True)):
            with patch.object(
                engine, "_link_executable", AsyncMock(side_effect=touch_link)
            ):
                with patch(
                    "asyncio.create_subprocess_exec", AsyncMock(return_value=fake_proc)
                ) as cpe:
                    ok, msg = await engine.run_unit_tests(silent=True)
                    assert ok is True
                    assert cpe.await_count >= 1


@pytest.mark.asyncio
async def test_run_unit_tests_subprocess_failure(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    _write_project_yaml(
        root,
        unit_tests={"project_dirs": ["tests"], "output": "bin/run_tests"},
    )
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "tests" / "t.c").write_text("int main(void) { return 1; }\n")

    engine = BuildEngine(str(root))

    fake_proc = AsyncMock()
    fake_proc.communicate = AsyncMock(return_value=(b"", b"nope"))
    fake_proc.returncode = 42

    async def touch_link(obj_files, output_file, silent=False, extra_libs=None):
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        Path(output_file).write_bytes(b"")
        return True

    with patch.object(
        engine, "_run_bootstrap", AsyncMock(return_value=(True, "success"))
    ):
        with patch.object(engine, "_compile_file", AsyncMock(return_value=True)):
            with patch.object(
                engine, "_link_executable", AsyncMock(side_effect=touch_link)
            ):
                with patch(
                    "asyncio.create_subprocess_exec", AsyncMock(return_value=fake_proc)
                ):
                    ok, msg = await engine.run_unit_tests(silent=True)
                    assert ok is False
                    assert "nope" in msg


def test_unit_tests_invalid_libraries_type_removed(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    _write_project_yaml(
        root,
        unit_tests={
            "project_dirs": ["tests"],
            "output": "bin/x",
            "libraries": {"not": "a list"},
        },
    )
    (root / "src").mkdir()
    assert BuildEngine(str(root)).config.get("unit_tests") is None


def test_unit_tests_nonbool_link_project_removed(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    _write_project_yaml(
        root,
        unit_tests={
            "project_dirs": ["tests"],
            "output": "bin/x",
            "link_project": "yes",
        },
    )
    (root / "src").mkdir()
    assert BuildEngine(str(root)).config.get("unit_tests") is None


@pytest.mark.asyncio
async def test_run_unit_tests_link_project_true_requires_library(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    _write_project_yaml(
        root,
        project_type="executable",
        unit_tests={
            "project_dirs": ["tests"],
            "output": "bin/run_tests",
            "link_project": True,
        },
    )
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "tests" / "t.c").write_text("int main(void){return 0;}\n")

    ok, msg = await BuildEngine(str(root)).run_unit_tests(silent=True)
    assert ok is False
    assert "link_project" in msg and "library" in msg


@pytest.mark.asyncio
async def test_run_unit_tests_links_main_static_library(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    _write_project_yaml(
        root,
        project_type="library",
        output="lib/libdemo.a",
        unit_tests={"project_dirs": ["tests"], "output": "bin/run_tests"},
    )
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "tests" / "t.c").write_text("int main(void){return 0;}\n")
    (root / "lib").mkdir()
    (root / "lib" / "libdemo.a").write_bytes(b"!")

    engine = BuildEngine(str(root))
    captured_libs: list = []

    fake_proc = AsyncMock()
    fake_proc.communicate = AsyncMock(return_value=(b"", b""))
    fake_proc.returncode = 0

    async def touch_link(obj_files, output_file, silent=False, extra_libs=None):
        captured_libs.append(list(extra_libs or []))
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        Path(output_file).write_bytes(b"")
        return True

    with patch.object(engine, "build", AsyncMock(return_value=(True, "success"))):
        with patch.object(
            engine, "_run_bootstrap", AsyncMock(return_value=(True, "success"))
        ):
            with patch.object(engine, "_compile_file", AsyncMock(return_value=True)):
                with patch.object(
                    engine, "_link_executable", AsyncMock(side_effect=touch_link)
                ):
                    with patch(
                        "asyncio.create_subprocess_exec",
                        AsyncMock(return_value=fake_proc),
                    ):
                        ok, msg = await engine.run_unit_tests(silent=True)
                        assert ok is True
                        assert captured_libs and any(
                            p.replace("\\", "/").endswith("lib/libdemo.a")
                            for p in captured_libs[0]
                        )


@pytest.mark.asyncio
async def test_run_unit_tests_link_project_false_skips_main_build(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    _write_project_yaml(
        root,
        project_type="library",
        output="lib/libdemo.a",
        unit_tests={
            "project_dirs": ["tests"],
            "output": "bin/run_tests",
            "link_project": False,
        },
    )
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "tests" / "t.c").write_text("int main(void){return 0;}\n")

    engine = BuildEngine(str(root))
    fake_proc = AsyncMock()
    fake_proc.communicate = AsyncMock(return_value=(b"", b""))
    fake_proc.returncode = 0

    async def touch_link(obj_files, output_file, silent=False, extra_libs=None):
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        Path(output_file).write_bytes(b"")
        assert not (extra_libs or [])
        return True

    mock_build = AsyncMock(return_value=(True, "success"))
    with patch.object(engine, "build", mock_build):
        with patch.object(
            engine, "_run_bootstrap", AsyncMock(return_value=(True, "success"))
        ):
            with patch.object(engine, "_compile_file", AsyncMock(return_value=True)):
                with patch.object(
                    engine, "_link_executable", AsyncMock(side_effect=touch_link)
                ):
                    with patch(
                        "asyncio.create_subprocess_exec",
                        AsyncMock(return_value=fake_proc),
                    ):
                        ok, _ = await engine.run_unit_tests(silent=True)
                        assert ok is True
    mock_build.assert_not_called()


@pytest.mark.asyncio
async def test_run_unit_tests_extra_libraries(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    _write_project_yaml(
        root,
        unit_tests={
            "project_dirs": ["tests"],
            "output": "bin/run_tests",
            "libraries": ["extras/libx.a"],
        },
    )
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "tests" / "t.c").write_text("int main(void){return 0;}\n")
    (root / "extras").mkdir()
    (root / "extras" / "libx.a").write_bytes(b"!")

    engine = BuildEngine(str(root))
    captured_libs: list = []

    fake_proc = AsyncMock()
    fake_proc.communicate = AsyncMock(return_value=(b"", b""))
    fake_proc.returncode = 0

    async def touch_link(obj_files, output_file, silent=False, extra_libs=None):
        captured_libs.append(list(extra_libs or []))
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        Path(output_file).write_bytes(b"")
        return True

    with patch.object(
        engine, "_run_bootstrap", AsyncMock(return_value=(True, "success"))
    ):
        with patch.object(engine, "_compile_file", AsyncMock(return_value=True)):
            with patch.object(
                engine, "_link_executable", AsyncMock(side_effect=touch_link)
            ):
                with patch(
                    "asyncio.create_subprocess_exec",
                    AsyncMock(return_value=fake_proc),
                ):
                    ok, _ = await engine.run_unit_tests(silent=True)
                    assert ok is True
                    assert captured_libs and any(
                        p.replace("\\", "/").endswith("extras/libx.a")
                        for p in captured_libs[0]
                    )
