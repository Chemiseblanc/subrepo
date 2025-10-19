"""Contract tests for 'subrepo status' command.

Tests verify CLI interface contract including:
- Command execution and argument parsing
- Output formats (text, JSON, compact)
- Exit codes for various scenarios
- Error messages and edge cases
"""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest


class TestStatusCommandSuccess:
    """Test status command success cases."""

    def test_status_text_output_all_up_to_date(self, initialized_workspace_simple: Path) -> None:
        """Test status command with text output when all components up-to-date."""
        result = subprocess.run(
            ["python", "-m", "subrepo", "status"],
            cwd=initialized_workspace_simple,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"
        assert "Workspace Status:" in result.stdout
        assert "Components:" in result.stdout
        assert "Summary:" in result.stdout
        assert "up-to-date" in result.stdout or "up_to_date" in result.stdout

    def test_status_json_output_format(self, initialized_workspace_simple: Path) -> None:
        """Test status command with JSON output format."""
        result = subprocess.run(
            ["python", "-m", "subrepo", "status", "--format", "json"],
            cwd=initialized_workspace_simple,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # Parse JSON output
        status_data: dict[str, Any] = json.loads(result.stdout)

        # Verify JSON structure
        assert "workspace" in status_data
        assert "manifest" in status_data
        assert "components" in status_data
        assert "summary" in status_data

        # Verify summary structure
        summary = status_data["summary"]
        assert "total" in summary
        assert "up_to_date" in summary
        assert isinstance(summary["total"], int)
        assert summary["total"] >= 0

        # Verify components structure
        if status_data["components"]:
            component = status_data["components"][0]
            assert "name" in component
            assert "path" in component
            assert "branch" in component or "revision" in component
            assert "status" in component

    def test_status_compact_output_format(self, initialized_workspace_simple: Path) -> None:
        """Test status command with compact output format."""
        result = subprocess.run(
            ["python", "-m", "subrepo", "status", "--format", "compact"],
            cwd=initialized_workspace_simple,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # Compact format: "<path> <status> [details]" per line
        lines = result.stdout.strip().split("\n")
        assert len(lines) >= 1

        # Each line should be component status
        for line in lines:
            parts = line.split()
            assert len(parts) >= 2  # path + status at minimum
            # First part should be a path
            assert "/" in parts[0] or parts[0].replace("_", "").replace("-", "").isalnum()

    def test_status_porcelain_flag(self, initialized_workspace_simple: Path) -> None:
        """Test status command with --porcelain flag (machine-readable)."""
        result = subprocess.run(
            ["python", "-m", "subrepo", "status", "--porcelain"],
            cwd=initialized_workspace_simple,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # Porcelain implies compact format
        lines = result.stdout.strip().split("\n")
        assert len(lines) >= 1

        # No color codes, no decorative text
        assert "\033[" not in result.stdout  # ANSI color codes
        assert "Workspace Status:" not in result.stdout
        assert "Summary:" not in result.stdout

    def test_status_specific_component(self, initialized_workspace_simple: Path) -> None:
        """Test status command with --component flag for specific component."""
        result = subprocess.run(
            ["python", "-m", "subrepo", "status", "--component", "lib/repo1"],
            cwd=initialized_workspace_simple,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"
        assert "lib/repo1" in result.stdout


class TestStatusCommandExitCodes:
    """Test status command exit codes for different scenarios."""

    def test_status_exit_0_when_all_clean(self, initialized_workspace_simple: Path) -> None:
        """Test exit code 0 when all components clean and up-to-date."""
        result = subprocess.run(
            ["python", "-m", "subrepo", "status"],
            cwd=initialized_workspace_simple,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "Exit code should be 0 for clean workspace"

    def test_status_exit_1_when_components_need_attention(
        self, initialized_workspace_with_changes: Path
    ) -> None:
        """Test exit code 1 when components have local changes or are behind/ahead.

        Per contract: exit 1 when components need attention (behind, ahead, modified).
        """
        # Make a local change
        test_file = initialized_workspace_with_changes / "lib" / "repo1" / "test.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("local change\n")

        result = subprocess.run(
            ["python", "-m", "subrepo", "status"],
            cwd=initialized_workspace_with_changes,
            capture_output=True,
            text=True,
        )

        # Exit code 1 indicates components need attention
        assert result.returncode == 1, "Exit code should be 1 when components have changes"

    def test_status_exit_2_when_not_in_workspace(self, tmp_path: Path) -> None:
        """Test exit code 2 when not in a subrepo workspace."""
        result = subprocess.run(
            ["python", "-m", "subrepo", "status"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2, "Exit code should be 2 for system error"
        assert "not" in result.stderr.lower()
        assert "workspace" in result.stderr.lower()


class TestStatusCommandErrors:
    """Test status command error handling."""

    def test_status_error_component_not_found(self, initialized_workspace_simple: Path) -> None:
        """Test error when requesting status for non-existent component."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "subrepo",
                "status",
                "--component",
                "nonexistent/component",
            ],
            cwd=initialized_workspace_simple,
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0, "Should fail for non-existent component"
        assert "not found" in result.stderr.lower() or "unknown" in result.stderr.lower()

    def test_status_error_invalid_format(self, initialized_workspace_simple: Path) -> None:
        """Test error when requesting invalid output format."""
        result = subprocess.run(
            ["python", "-m", "subrepo", "status", "--format", "invalid"],
            cwd=initialized_workspace_simple,
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0, "Should fail for invalid format"
        assert "invalid" in result.stderr.lower() or "format" in result.stderr.lower()


class TestStatusOutputDetails:
    """Test detailed output formatting and content."""

    def test_status_shows_component_states(self, initialized_workspace_multi_state: Path) -> None:
        """Test that status correctly shows different component states."""
        result = subprocess.run(
            ["python", "-m", "subrepo", "status"],
            cwd=initialized_workspace_multi_state,
            capture_output=True,
            text=True,
        )

        assert result.returncode in [0, 1], f"Unexpected exit code: {result.returncode}"

        # Should show various status indicators
        output = result.stdout.lower()

        # Check for status terminology (implementation may vary)
        status_terms = [
            "up-to-date",
            "up_to_date",
            "ahead",
            "behind",
            "modified",
            "diverged",
        ]
        assert any(
            term in output for term in status_terms
        ), "Output should contain status information"

    def test_status_json_includes_all_components(self, initialized_workspace_simple: Path) -> None:
        """Test that JSON output includes all workspace components."""
        result = subprocess.run(
            ["python", "-m", "subrepo", "status", "--format", "json"],
            cwd=initialized_workspace_simple,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        status_data: dict[str, Any] = json.loads(result.stdout)

        # Should have at least one component
        assert len(status_data["components"]) > 0

        # All components should have required fields
        for component in status_data["components"]:
            assert "name" in component or "path" in component
            assert "status" in component

    def test_status_summary_counts_match_components(
        self, initialized_workspace_simple: Path
    ) -> None:
        """Test that summary counts match actual component states."""
        result = subprocess.run(
            ["python", "-m", "subrepo", "status", "--format", "json"],
            cwd=initialized_workspace_simple,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        status_data: dict[str, Any] = json.loads(result.stdout)

        summary = status_data["summary"]
        components = status_data["components"]

        # Total should match number of components
        assert summary["total"] == len(components)

        # Sum of all status counts should equal total
        count_sum = sum(
            [
                summary.get("up_to_date", 0),
                summary.get("ahead", 0),
                summary.get("behind", 0),
                summary.get("diverged", 0),
                summary.get("modified", 0),
                summary.get("uninitialized", 0),
            ]
        )
        assert count_sum == summary["total"]


# Fixtures


@pytest.fixture
def initialized_workspace_simple(tmp_path: Path) -> Path:
    """Create a simple initialized workspace for testing.

    Returns path to workspace root.
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create a simple manifest
    manifest = workspace / "manifest.xml"
    manifest.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/test/" />
  <default remote="origin" revision="main" />
  <project name="org/repo1" path="lib/repo1" />
</manifest>
"""
    )

    # Initialize workspace (this will be implemented)
    # For now, create minimal structure for tests to run
    (workspace / ".subrepo").mkdir()
    (workspace / ".subrepo" / "config.json").write_text(
        json.dumps(
            {
                "manifest_path": str(manifest),
                "manifest_hash": "test",
                "initialized_at": "2025-10-18T00:00:00Z",
                "git_version": "2.43.0",
                "subrepo_version": "0.1.0",
            }
        )
    )
    (workspace / ".subrepo" / "manifest.xml").write_text(manifest.read_text())

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=workspace, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=workspace,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=workspace,
        capture_output=True,
        check=True,
    )

    return workspace


@pytest.fixture
def initialized_workspace_with_changes(tmp_path: Path) -> Path:
    """Create an initialized workspace with local changes.

    Returns path to workspace root.
    """
    workspace = tmp_path / "workspace_changes"
    workspace.mkdir()

    # Create minimal structure
    (workspace / ".subrepo").mkdir()
    (workspace / ".subrepo" / "config.json").write_text(
        json.dumps(
            {
                "manifest_path": "manifest.xml",
                "manifest_hash": "test",
                "initialized_at": "2025-10-18T00:00:00Z",
                "git_version": "2.43.0",
                "subrepo_version": "0.1.0",
            }
        )
    )

    # Create manifest file
    (workspace / ".subrepo" / "manifest.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/test/" />
  <default remote="origin" revision="main" />
  <project name="org/repo1" path="lib/repo1" />
</manifest>
"""
    )

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=workspace, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=workspace,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=workspace,
        capture_output=True,
        check=True,
    )

    return workspace


@pytest.fixture
def initialized_workspace_multi_state(tmp_path: Path) -> Path:
    """Create an initialized workspace with components in different states.

    Returns path to workspace root.
    """
    workspace = tmp_path / "workspace_multi"
    workspace.mkdir()

    # Create minimal structure
    (workspace / ".subrepo").mkdir()
    (workspace / ".subrepo" / "config.json").write_text(
        json.dumps(
            {
                "manifest_path": "manifest.xml",
                "manifest_hash": "test",
                "initialized_at": "2025-10-18T00:00:00Z",
                "git_version": "2.43.0",
                "subrepo_version": "0.1.0",
            }
        )
    )

    # Create manifest file
    (workspace / ".subrepo" / "manifest.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/test/" />
  <default remote="origin" revision="main" />
  <project name="org/repo1" path="lib/repo1" />
</manifest>
"""
    )

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=workspace, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=workspace,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=workspace,
        capture_output=True,
        check=True,
    )

    return workspace
