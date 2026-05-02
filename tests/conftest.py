"""Shared pytest configuration and fixtures for the InsurgeNT test suite."""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from insurgent.shell.Shell import command_history


@pytest.fixture(autouse=True)
def _reset_command_history():
    """Clear the module-level shell command history around every test.

    The shell exposes ``command_history`` as a module-level list, so any test
    that pokes at it would otherwise leak entries to the next test.
    """
    command_history.clear()
    yield
    command_history.clear()
