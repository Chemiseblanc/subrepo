"""Regression tests for backward compatibility.

This module ensures that existing push behavior is preserved when
pushing from default branches, comparing old behavior to new behavior.
"""

import subprocess
from pathlib import Path
from typing import Iterator

import pytest

from subrepo.git_commands import create_branch_info, determine_target_branch
from subrepo.manifest_parser import Project


class TestBackwardCompatibility:
    """Tests that existing workflows continue to work unchanged."""

    @pytest.fixture
    def temp_git_repo(self, tmp_path: Path) -> Iterator[Path]:
        """Create a temporary git repository."""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

        # Create initial commit
        (repo_dir / "README.md").write_text("# Test\n")
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

        yield repo_dir

    def test_default_branch_push_uses_revision_from_manifest(self, temp_git_repo: Path) -> None:
        """Test that manifest revision is respected on default branch."""
        # Setup: Branch specified in manifest should be used
        project = Project(
            name="test/project",
            path="test/project",
            remote="origin",
            revision="develop",  # Manifest says develop
        )

        # Checkout develop branch
        subprocess.run(
            ["git", "checkout", "-b", "develop"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        # Create branch info
        branch_info = create_branch_info(cwd=temp_git_repo)

        # Determine target branch
        target = determine_target_branch(branch_info, project)

        # Should use the manifest revision (develop) since we're on it
        assert target == "develop"

    def test_main_branch_push_unchanged(self, temp_git_repo: Path) -> None:
        """Test that pushing from main works exactly as before."""
        # This is the most common case - should continue to work
        project = Project(
            name="test/project",
            path="test/project",
            remote="origin",
            revision="main",
        )

        # Ensure we're on main
        current_branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
            text=True,
        )
        current_branch = current_branch_result.stdout.strip()

        # Rename to main if needed
        if current_branch in ("master", ""):
            subprocess.run(
                ["git", "branch", "-M", "main"],
                cwd=temp_git_repo,
                check=True,
                capture_output=True,
            )

        # Create branch info
        branch_info = create_branch_info(cwd=temp_git_repo)

        # Determine target
        target = determine_target_branch(branch_info, project)

        # Should target main
        assert target == "main"

    def test_master_branch_push_unchanged(self, temp_git_repo: Path) -> None:
        """Test that legacy master branch behavior is preserved."""
        # Older repositories use master as default
        project = Project(
            name="test/project",
            path="test/project",
            remote="origin",
            revision="master",
        )

        # Get current branch
        current_branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
            text=True,
        )
        current_branch = current_branch_result.stdout.strip()

        # Rename to master
        if current_branch != "master":
            subprocess.run(
                ["git", "branch", "-M", "master"],
                cwd=temp_git_repo,
                check=True,
                capture_output=True,
            )

        # Create branch info
        branch_info = create_branch_info(cwd=temp_git_repo)

        # Determine target
        target = determine_target_branch(branch_info, project)

        # Should target master
        assert target == "master"

    def test_no_new_behavior_when_revision_is_sha(self, temp_git_repo: Path) -> None:
        """Test that SHA revisions fall back to git detection as before."""
        # When manifest has SHA (pinned commit), should use git default
        project = Project(
            name="test/project",
            path="test/project",
            remote="origin",
            revision="a" * 40,  # Full SHA
        )

        # Ensure we're on main/master
        current_branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
            text=True,
        )
        current_branch = current_branch_result.stdout.strip()

        if not current_branch:
            subprocess.run(
                ["git", "checkout", "-b", "main"],
                cwd=temp_git_repo,
                check=True,
                capture_output=True,
            )

        # Create branch info
        branch_info = create_branch_info(cwd=temp_git_repo)

        # Determine target - should fall back to current branch
        target = determine_target_branch(branch_info, project)

        # Should use the branch we're on (git detection)
        current_branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
            text=True,
        )
        expected = current_branch_result.stdout.strip()
        assert target == expected
