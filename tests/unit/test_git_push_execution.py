"""Tests for git push execution logic.

This module tests the execute_git_push() function that performs the actual
git push operation with error handling.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from subrepo.exceptions import (
    BranchProtectionError,
    NonFastForwardError,
    RepositoryNotFoundError,
)
from subrepo.git_commands import execute_git_push
from subrepo.models import PushAction, PushResult, PushStatus


class TestExecuteGitPush:
    """Tests for execute_git_push() function."""

    @patch("subrepo.git_commands.subprocess.run")
    def test_successful_push_to_new_branch(self, mock_run: MagicMock) -> None:
        """Test successful push that creates a new branch."""
        # Dry-run succeeds with "new branch" indicator
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="* [new branch]      feature -> feature",
        )

        result = execute_git_push(
            component_name="platform/core",
            component_path=Path("platform/core"),
            remote_url="git@github.com:org/core.git",
            branch_name="feature",
            force=False,
        )

        assert result.status == PushStatus.SUCCESS
        assert result.action == PushAction.CREATED
        assert result.branch_name == "feature"
        assert result.project_name == "platform/core"
        assert result.error_message is None

    @patch("subrepo.git_commands.subprocess.run")
    def test_successful_push_to_existing_branch(self, mock_run: MagicMock) -> None:
        """Test successful push that updates existing branch."""
        # Dry-run succeeds without "new branch" indicator
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="feature -> feature")

        result = execute_git_push(
            component_name="platform/auth",
            component_path=Path("platform/auth"),
            remote_url="git@github.com:org/auth.git",
            branch_name="feature",
            force=False,
        )

        assert result.status == PushStatus.SUCCESS
        assert result.action == PushAction.UPDATED
        assert result.branch_name == "feature"

    @patch("subrepo.git_commands.subprocess.run")
    def test_non_fast_forward_without_force(self, mock_run: MagicMock) -> None:
        """Test that non-fast-forward raises error when force=False."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="[rejected] non-fast-forward"
        )

        with pytest.raises(NonFastForwardError) as exc_info:
            execute_git_push(
                component_name="platform/core",
                component_path=Path("platform/core"),
                remote_url="git@github.com:org/core.git",
                branch_name="feature",
                force=False,
            )

        assert "feature" in str(exc_info.value)
        assert "platform/core" in str(exc_info.value)

    @patch("subrepo.git_commands.subprocess.run")
    def test_force_push_succeeds(self, mock_run: MagicMock) -> None:
        """Test that force push succeeds even with non-fast-forward."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="", stderr="+ feature...feature (forced update)"
        )

        result = execute_git_push(
            component_name="platform/core",
            component_path=Path("platform/core"),
            remote_url="git@github.com:org/core.git",
            branch_name="feature",
            force=True,
        )

        assert result.status == PushStatus.SUCCESS
        # Verify --force was used
        assert "--force" in mock_run.call_args[0][0]

    @patch("subrepo.git_commands.subprocess.run")
    def test_protected_branch_raises_error(self, mock_run: MagicMock) -> None:
        """Test that protected branch raises specific error."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="protected branch hook declined"
        )

        with pytest.raises(BranchProtectionError) as exc_info:
            execute_git_push(
                component_name="platform/core",
                component_path=Path("platform/core"),
                remote_url="git@github.com:org/core.git",
                branch_name="main",
                force=False,
            )

        assert "main" in str(exc_info.value)
        assert "protected" in str(exc_info.value).lower()

    @patch("subrepo.git_commands.subprocess.run")
    def test_missing_repository_raises_error(self, mock_run: MagicMock) -> None:
        """Test that missing repository raises specific error."""
        mock_run.return_value = MagicMock(
            returncode=128,
            stdout="",
            stderr="fatal: repository 'git@github.com:org/missing.git' not found",
        )

        with pytest.raises(RepositoryNotFoundError) as exc_info:
            execute_git_push(
                component_name="platform/missing",
                component_path=Path("platform/missing"),
                remote_url="git@github.com:org/missing.git",
                branch_name="feature",
                force=False,
            )

        assert "missing" in str(exc_info.value).lower()

    @patch("subrepo.git_commands.subprocess.run")
    def test_uses_subtree_push(self, mock_run: MagicMock) -> None:
        """Test that git subtree push command is used."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        execute_git_push(
            component_name="platform/core",
            component_path=Path("platform/core"),
            remote_url="git@github.com:org/core.git",
            branch_name="feature",
            force=False,
        )

        args = mock_run.call_args[0][0]
        assert "git" in args
        assert "subtree" in args
        assert "push" in args
