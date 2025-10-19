"""Shared test fixtures and configuration."""

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def reset_cli_globals():
    """Reset CLI global variables before and after each test."""
    from subrepo import cli

    # Save original values
    original_verbose = cli._verbose
    original_quiet = cli._quiet
    original_no_color = cli._no_color

    # Reset to defaults
    cli._verbose = False
    cli._quiet = False
    cli._no_color = False

    yield

    # Restore original values
    cli._verbose = original_verbose
    cli._quiet = original_quiet
    cli._no_color = original_no_color


@pytest.fixture(autouse=True)
def preserve_cwd():
    """Preserve and restore the current working directory for each test."""
    original_cwd = os.getcwd()

    yield

    # Restore original working directory
    # Handle case where the directory might have been deleted
    try:
        os.chdir(original_cwd)
    except (FileNotFoundError, OSError):
        # If original directory was deleted, change to a safe location
        os.chdir(Path(__file__).parent.parent)
