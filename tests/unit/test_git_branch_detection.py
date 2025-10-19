"""Tests for git branch detection functions.

This module tests functions that detect the current branch and default branch
using git commands.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from subrepo.exceptions import DetachedHeadError
from subrepo.git_commands import detect_current_branch, detect_default_branch


class TestDetectCurrentBranch:
    """Tests for detect_current_branch() function."""

    @patch("subrepo.git_commands.subprocess.run")
    def test_returns_branch_name(self, mock_run: MagicMock) -> None:
        """Test that detect_current_branch returns the current branch name."""
        mock_run.return_value = MagicMock(returncode=0, stdout="feature-branch\n", stderr="")

        result = detect_current_branch()

        assert result == "feature-branch"
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["git", "symbolic-ref", "--short", "HEAD"]

    @patch("subrepo.git_commands.subprocess.run")
    def test_strips_whitespace(self, mock_run: MagicMock) -> None:
        """Test that returned branch name has whitespace stripped."""
        mock_run.return_value = MagicMock(returncode=0, stdout="  main  \n", stderr="")

        result = detect_current_branch()

        assert result == "main"

    @patch("subrepo.git_commands.subprocess.run")
    def test_handles_branch_with_slashes(self, mock_run: MagicMock) -> None:
        """Test that branch names with slashes are handled correctly."""
        mock_run.return_value = MagicMock(returncode=0, stdout="feature/auth/oauth2\n", stderr="")

        result = detect_current_branch()

        assert result == "feature/auth/oauth2"

    @patch("subrepo.git_commands.subprocess.run")
    def test_raises_on_detached_head(self, mock_run: MagicMock) -> None:
        """Test that DetachedHeadError is raised when HEAD is detached."""
        mock_run.return_value = MagicMock(
            returncode=128,
            stdout="",
            stderr="fatal: ref HEAD is not a symbolic ref",
        )

        with pytest.raises(DetachedHeadError):
            detect_current_branch()

    @patch("subrepo.git_commands.subprocess.run")
    def test_uses_text_mode(self, mock_run: MagicMock) -> None:
        """Test that subprocess.run is called with text=True."""
        mock_run.return_value = MagicMock(returncode=0, stdout="main\n", stderr="")

        detect_current_branch()

        assert mock_run.call_args[1]["text"] is True

    @patch("subrepo.git_commands.subprocess.run")
    def test_captures_output(self, mock_run: MagicMock) -> None:
        """Test that subprocess.run captures output."""
        mock_run.return_value = MagicMock(returncode=0, stdout="main\n", stderr="")

        detect_current_branch()

        assert mock_run.call_args[1]["capture_output"] is True


class TestDetectDefaultBranch:
    """Tests for detect_default_branch() function."""

    @patch("subrepo.git_commands.subprocess.run")
    def test_returns_default_branch(self, mock_run: MagicMock) -> None:
        """Test that detect_default_branch returns default branch name."""
        mock_run.return_value = MagicMock(returncode=0, stdout="origin/main\n", stderr="")

        result = detect_default_branch()

        assert result == "main"

    @patch("subrepo.git_commands.subprocess.run")
    def test_strips_origin_prefix(self, mock_run: MagicMock) -> None:
        """Test that origin/ prefix is stripped from branch name."""
        mock_run.return_value = MagicMock(returncode=0, stdout="origin/develop\n", stderr="")

        result = detect_default_branch()

        assert result == "develop"

    @patch("subrepo.git_commands.subprocess.run")
    def test_queries_symbolic_ref(self, mock_run: MagicMock) -> None:
        """Test that git symbolic-ref refs/remotes/origin/HEAD is used."""
        mock_run.return_value = MagicMock(returncode=0, stdout="origin/main\n", stderr="")

        detect_default_branch()

        args = mock_run.call_args[0][0]
        assert args == [
            "git",
            "symbolic-ref",
            "--short",
            "refs/remotes/origin/HEAD",
        ]

    @patch("subrepo.git_commands.subprocess.run")
    def test_strips_whitespace(self, mock_run: MagicMock) -> None:
        """Test that whitespace is stripped from result."""
        mock_run.return_value = MagicMock(returncode=0, stdout="  origin/main  \n", stderr="")

        result = detect_default_branch()

        assert result == "main"

    @patch("subrepo.git_commands.subprocess.run")
    def test_fallback_to_main_on_error(self, mock_run: MagicMock) -> None:
        """Test fallback to 'main' when symbolic-ref fails."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="fatal: ref does not exist"
        )

        result = detect_default_branch()

        assert result == "main"

    @patch("subrepo.git_commands.subprocess.run")
    def test_uses_text_mode(self, mock_run: MagicMock) -> None:
        """Test that subprocess.run is called with text=True."""
        mock_run.return_value = MagicMock(returncode=0, stdout="origin/main\n", stderr="")

        detect_default_branch()

        assert mock_run.call_args[1]["text"] is True
