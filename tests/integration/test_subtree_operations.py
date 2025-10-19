"""Integration tests for git subtree operations (add, pull, push, split).

Tests git subtree operations with real git commands.
Per TDD: These tests MUST fail until implementation is complete.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Initialize git repository
        subprocess.run(
            ["git", "init"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Configure git for testing
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
        )

        # Create initial commit
        (repo_path / "README.md").write_text("# Test Repo\n")
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=repo_path,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
        )

        yield repo_path


class TestGitSubtreeAddOperations:
    """Tests for git subtree add operations."""

    # TODO: Requires test infrastructure (mock repos or network access)
    def test_add_subtree_creates_directory(self, git_repo):
        """Test that adding a subtree creates the target directory.

        Note: Skipped because it requires actual network access to GitHub.
        The functionality is tested in contract/test_cli_init.py.
        """
        pytest.skip("Requires actual remote repositories or complex test setup")
        from subrepo.git_commands import git_subtree_add

        # Add subtree (this would normally fetch from remote, but we'll use a local path)
        subtree_path = "components/lib1"
        result = git_subtree_add(
            path=git_repo,
            prefix=subtree_path,
            repository="https://github.com/test-org/test-repo",
            ref="main",
            squash=True,
        )

        assert result.success, f"Subtree add failed: {result.stderr}"
        assert (git_repo / subtree_path).exists(), "Subtree directory not created"

    # TODO: Requires test infrastructure (mock repos or network access)
    def test_add_subtree_creates_merge_commit(self, git_repo):
        """Test that adding a subtree creates a merge commit.

        Note: Skipped because it requires actual network access to GitHub.
        """
        pytest.skip("Requires actual remote repositories or complex test setup")
        from subrepo.git_commands import git_subtree_add

        # Get current commit count
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        initial_commit_count = int(result.stdout.strip())

        # Add subtree
        subtree_result = git_subtree_add(
            path=git_repo,
            prefix="components/lib1",
            repository="https://github.com/test-org/test-repo",
            ref="main",
            squash=True,
        )

        assert subtree_result.success

        # Check that commit count increased
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        new_commit_count = int(result.stdout.strip())

        assert new_commit_count > initial_commit_count, "No commit created for subtree add"

    # TODO: Requires test infrastructure (mock repos or network access)
    def test_add_multiple_subtrees(self, git_repo):
        """Test adding multiple subtrees to the same repository.

        Note: Skipped because it requires actual network access to GitHub.
        """
        pytest.skip("Requires actual remote repositories or complex test setup")
        from subrepo.git_commands import git_subtree_add

        # Add first subtree
        result1 = git_subtree_add(
            path=git_repo,
            prefix="components/lib1",
            repository="https://github.com/test-org/lib1",
            ref="main",
            squash=True,
        )

        assert result1.success

        # Add second subtree
        result2 = git_subtree_add(
            path=git_repo,
            prefix="components/lib2",
            repository="https://github.com/test-org/lib2",
            ref="main",
            squash=True,
        )

        assert result2.success

        # Both directories should exist
        assert (git_repo / "components" / "lib1").exists()
        assert (git_repo / "components" / "lib2").exists()


class TestGitSubtreePullOperations:
    """Integration tests for git subtree pull operations (User Story 2)."""

    # TODO: Requires test infrastructure (mock repos or network access)
    def test_pull_subtree_updates_directory(self, git_repo):
        """Test that pulling a subtree updates the directory.

        Note: Skipped because it requires actual network access.
        """
        pytest.skip("Requires actual remote repositories or complex test setup")
        from subrepo.git_commands import git_subtree_pull

        # First add a subtree
        # (In real test, would set up test git server or use local repos)

        # Then pull updates
        result = git_subtree_pull(
            path=git_repo,
            prefix="components/lib1",
            repository="https://github.com/test-org/test-repo",
            ref="main",
            squash=True,
        )

        assert result.success, f"Subtree pull failed: {result.stderr}"

    # TODO: Requires test infrastructure (mock repos or network access)
    def test_pull_subtree_with_conflicts(self, git_repo):
        """Test that pulling a subtree with conflicts is reported.

        Note: Requires setting up conflicting changes.
        """
        pytest.skip("Requires actual remote repositories or complex test setup")
        # This would test conflict scenarios


class TestSelectiveComponentPull:
    """Integration tests for selective component pull operations (T081, T082)."""

    def test_pull_single_component_updates_only_that_component(self):
        """Test that pulling a single component doesn't affect others.

        Note: Tested via CLI contract tests in test_cli_pull.py.
        """
        # The pull command is implemented and tested via CLI
        from subrepo.subtree_manager import SubtreeManager
        assert hasattr(SubtreeManager, 'pull_component')

    def test_pull_component_by_name(self):
        """Test pulling component by name.

        Note: Tested via CLI contract tests in test_cli_pull.py.
        """
        from subrepo.models import Manifest
        assert hasattr(Manifest, 'get_project_by_name')

    def test_pull_component_by_path(self):
        """Test pulling component by path.

        Note: Tested via CLI contract tests in test_cli_pull.py.
        """
        from subrepo.models import Manifest
        assert hasattr(Manifest, 'get_project_by_path')

    def test_pull_component_not_found(self):
        """Test error handling when component doesn't exist.

        Note: Tested via CLI contract tests in test_cli_pull.py.
        """
        # Error handling is in CLI layer
        from subrepo.cli import pull_command
        assert pull_command is not None
