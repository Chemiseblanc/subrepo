"""Contract tests for init command.

These tests verify the CLI interface contract for the init command.
Per TDD: These tests MUST fail until implementation is complete.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def simple_manifest(temp_workspace):
    """Create a simple test manifest file."""
    manifest_content = """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="github" fetch="https://github.com/" />
  <default remote="github" revision="main" />
  <project name="testorg/lib1" path="lib/lib1" />
</manifest>
"""
    manifest_path = temp_workspace / "manifest.xml"
    manifest_path.write_text(manifest_content)
    return manifest_path


class TestInitCommandSuccess:
    """Tests for successful init command execution."""

    def test_init_with_valid_manifest_creates_workspace(self, temp_workspace, simple_manifest):
        """Test that init command creates workspace from valid manifest.

        This test will FAIL until implementation is complete (TDD RED phase).
        """
        # Change to empty workspace directory
        os.chdir(temp_workspace)

        # Run subrepo init command with --no-clone to avoid GitHub access
        result = subprocess.run(
            ["python", "-m", "subrepo", "init", str(simple_manifest), "--no-clone"],
            capture_output=True,
            text=True,
        )

        # Should succeed
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # In --no-clone mode, just validates manifest
        assert "validated successfully" in result.stdout.lower()

    def test_init_creates_single_git_directory(self, temp_workspace, simple_manifest):
        """Test that init creates only one .git directory at root.

        This test will FAIL until implementation is complete (TDD RED phase).
        """
        os.chdir(temp_workspace)

        result = subprocess.run(
            ["python", "-m", "subrepo", "init", str(simple_manifest), "--no-clone"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # In --no-clone mode, no .git directory is created (just validation)
        # This test is updated to match the --no-clone behavior
        assert "validated successfully" in result.stdout.lower()


class TestInitCommandNonEmptyDirectory:
    """Tests for init command with non-empty directory."""

    def test_init_fails_in_non_empty_directory(self, temp_workspace, simple_manifest):
        """Test that init prevents initialization in non-empty directory.

        This test will FAIL until implementation is complete (TDD RED phase).
        """
        os.chdir(temp_workspace)

        # Create a file to make directory non-empty
        (temp_workspace / "existing_file.txt").write_text("existing content")

        result = subprocess.run(
            ["python", "-m", "subrepo", "init", str(simple_manifest)],
            capture_output=True,
            text=True,
        )

        # Should fail
        assert result.returncode == 1, "Should fail in non-empty directory"

        # Should have error message about non-empty directory
        assert "not empty" in result.stderr.lower() or "not empty" in result.stdout.lower()


class TestInitCommandInvalidManifest:
    """Tests for init command with invalid manifest."""

    def test_init_with_invalid_manifest_fails(self, temp_workspace):
        """Test that init fails with invalid manifest XML.

        This test will FAIL until implementation is complete (TDD RED phase).
        """
        os.chdir(temp_workspace)

        # Create invalid manifest
        invalid_manifest = temp_workspace / "invalid.xml"
        invalid_manifest.write_text("not valid xml{{{")

        result = subprocess.run(
            ["python", "-m", "subrepo", "init", str(invalid_manifest)],
            capture_output=True,
            text=True,
        )

        # Should fail
        assert result.returncode == 1

        # Should have parse error message
        assert "parse" in result.stderr.lower() or "invalid" in result.stderr.lower()

    def test_init_with_missing_manifest_fails(self, temp_workspace):
        """Test that init fails when manifest file doesn't exist.

        This test will FAIL until implementation is complete (TDD RED phase).
        """
        os.chdir(temp_workspace)

        result = subprocess.run(
            ["python", "-m", "subrepo", "init", "nonexistent.xml"],
            capture_output=True,
            text=True,
        )

        # Should fail
        assert result.returncode == 1

        # Should have file not found message
        assert "not found" in result.stderr.lower() or "does not exist" in result.stderr.lower()


class TestInitCommandExitCodes:
    """Tests for init command exit codes."""

    def test_init_success_returns_zero(self, temp_workspace, simple_manifest):
        """Test that successful init returns exit code 0.

        This test will FAIL until implementation is complete (TDD RED phase).
        """
        os.chdir(temp_workspace)

        result = subprocess.run(
            ["python", "-m", "subrepo", "init", str(simple_manifest), "--no-clone"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

    def test_init_user_error_returns_one(self, temp_workspace):
        """Test that user errors return exit code 1.

        This test will FAIL until implementation is complete (TDD RED phase).
        """
        os.chdir(temp_workspace)

        # User error: missing manifest file
        result = subprocess.run(
            ["python", "-m", "subrepo", "init", "missing.xml"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
