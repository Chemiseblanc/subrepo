"""Integration tests for pushing from default branch.

This module tests that the default branch push behavior remains unchanged
and backward compatible after adding feature branch support.
"""

import subprocess
from pathlib import Path
from typing import Iterator

import pytest

from subrepo.git_commands import detect_current_branch, execute_git_push
from subrepo.manifest_parser import Project
from subrepo.models import BranchInfo, PushAction, PushStatus


class TestPushDefaultBranch:
    """Integration tests for default branch push behavior."""

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

    @pytest.fixture
    def temp_remote_repo(self, tmp_path: Path) -> Iterator[Path]:
        """Create a temporary bare git repository to act as remote."""
        remote_dir = tmp_path / "remote.git"
        remote_dir.mkdir()

        # Initialize bare repo
        subprocess.run(["git", "init", "--bare"], cwd=remote_dir, check=True, capture_output=True)

        yield remote_dir

    def test_push_from_main_branch_pushes_to_main(
        self, temp_git_repo: Path, temp_remote_repo: Path
    ) -> None:
        """Test that pushing from main branch pushes to main in remote."""
        # Setup: Add remote
        subprocess.run(
            ["git", "remote", "add", "origin", str(temp_remote_repo)],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        # Verify we're on main branch
        current_branch = detect_current_branch(cwd=temp_git_repo)
        assert current_branch in ("main", "master")

        # Create a subtree directory with some content
        subtree_path = temp_git_repo / "test" / "project"
        subtree_path.mkdir(parents=True)
        (subtree_path / "README.md").write_text("# Test Project\n")

        # Commit the subtree content
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add test project"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        # Create a project object
        project = Project(
            name="test/project",
            path="test/project",
            remote="origin",
            revision=current_branch,
        )

        # Create branch info for default branch
        branch_info = BranchInfo(
            current_branch=current_branch,
            is_default_branch=True,
            default_branch=current_branch,
            target_branch=current_branch,
        )

        # Execute push
        result = execute_git_push(
            component_name=project.name,
            component_path=Path(project.path),
            remote_url=str(temp_remote_repo),
            branch_name=branch_info.target_branch,
            force=False,
            cwd=temp_git_repo,
        )

        # Verify result
        assert result.status == PushStatus.SUCCESS
        assert result.branch_name == current_branch
        assert result.action in (PushAction.CREATED, PushAction.UPDATED)

    def test_push_from_master_branch_backward_compatible(
        self, temp_git_repo: Path, temp_remote_repo: Path
    ) -> None:
        """Test backward compatibility with repositories using 'master' as default."""
        # Setup: Rename main to master (older git default)
        current_branch = detect_current_branch(cwd=temp_git_repo)
        if current_branch == "main":
            subprocess.run(
                ["git", "branch", "-M", "master"],
                cwd=temp_git_repo,
                check=True,
                capture_output=True,
            )

        # Add remote
        subprocess.run(
            ["git", "remote", "add", "origin", str(temp_remote_repo)],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        # Verify we're on master
        current_branch = detect_current_branch(cwd=temp_git_repo)
        assert current_branch == "master"

        # Create a subtree directory with some content
        subtree_path = temp_git_repo / "test" / "project"
        subtree_path.mkdir(parents=True)
        (subtree_path / "README.md").write_text("# Test Project\n")

        # Commit the subtree content
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add test project"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        # Create project and branch info
        project = Project(
            name="test/project",
            path="test/project",
            remote="origin",
            revision="master",
        )

        branch_info = BranchInfo(
            current_branch="master",
            is_default_branch=True,
            default_branch="master",
            target_branch="master",
        )

        # Execute push
        result = execute_git_push(
            component_name=project.name,
            component_path=Path(project.path),
            remote_url=str(temp_remote_repo),
            branch_name=branch_info.target_branch,
            force=False,
            cwd=temp_git_repo,
        )

        # Should push to master successfully
        assert result.status == PushStatus.SUCCESS
        assert result.branch_name == "master"
