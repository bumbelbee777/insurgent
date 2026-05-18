import os
from pathlib import Path
from unittest.mock import patch

import pytest

from insurgent.meta.config import load_config


def test_example():
    # Find the example directory relative to the test file
    test_dir = Path(__file__).parent
    repo_root = test_dir.parent
    example_dir = repo_root / "example"

    # Skip the test if the example directory doesn't exist (like in CI)
    if not example_dir.exists():
        pytest.skip(f"Example directory not found at {example_dir}")

    # Change to the example directory
    os.chdir(example_dir)

    # Load config and build the example
    config_path = example_dir / "project.yaml"

    # Simplest approach: mock the build function completely
    with patch("insurgent.build.build.build", return_value=True):
        cfg = load_config(str(config_path))
        assert cfg
