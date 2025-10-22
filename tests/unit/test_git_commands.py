"""Unit tests for git command wrappers."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from subrepo.exceptions import GitCommandError
from subrepo.git_commands import (
    git_add,
    git_commit,
    git_fetch,
    git_init,
    git_log,
    git_remote_add,
    git_rev_list,
    git_rev_parse,
    git_status,
    git_subtree_add,
    git_subtree_pull,
    git_subtree_push,
    git_subtree_split,
    git_version,
    run_git_command,
)
from subrepo.models import GitOperationResult


class TestRunGitCommand:
    """Tests for run_git_command function."""

    @patch("subprocess.run")
    def test_run_git_command_success(self, mock_run):
        """Test successful git command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "success output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = run_git_command(["status"])

        assert result.success
        assert result.stdout == "success output"
        assert result.exit_code == 0
        assert result.command == ["git", "status"]
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_git_command_failure_with_check(self, mock_run):
        """Test git command failure with check=True raises exception."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "fatal: error"
        mock_run.return_value = mock_result

        with pytest.raises(GitCommandError) as exc_info:
            run_git_command(["invalid"], check=True)

        error = exc_info.value
        assert error.exit_code == 1
        assert error.stderr == "fatal: error"

    @patch("subprocess.run")
    def test_run_git_command_failure_without_check(self, mock_run):
        """Test git command failure with check=False returns result."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "fatal: error"
        mock_run.return_value = mock_result

        result = run_git_command(["invalid"], check=False)

        assert not result.success
        assert result.exit_code == 1
        assert result.stderr == "fatal: error"

    @patch("subprocess.run")
    def test_run_git_command_with_cwd(self, mock_run):
        """Test git command with working directory."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        run_git_command(["status"], cwd=path)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["cwd"] == path


class TestGitVersion:
    """Tests for git_version function."""

    @patch("subrepo.git_commands.run_git_command")
    def test_git_version_returns_version_string(self, mock_run):
        """Test git_version extracts version from output."""
        mock_result = GitOperationResult(
            success=True,
            stdout="git version 2.43.0\n",
            stderr="",
            exit_code=0,
            duration=0.1,
            command=["git", "--version"],
        )
        mock_run.return_value = mock_result

        version = git_version()

        assert version == "2.43.0"
        mock_run.assert_called_once_with(["--version"])


class TestGitInit:
    """Tests for git_init function."""

    @patch("subrepo.git_commands.run_git_command")
    def test_git_init_calls_command(self, mock_run):
        """Test git_init calls git init command."""
        mock_result = GitOperationResult(
            success=True,
            stdout="Initialized empty Git repository",
            stderr="",
            exit_code=0,
            duration=0.1,
            command=["git", "init"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        result = git_init(path)

        assert result.success
        mock_run.assert_called_once_with(["init"], cwd=path)


class TestGitAdd:
    """Tests for git_add function."""

    @patch("subrepo.git_commands.run_git_command")
    def test_git_add_single_file(self, mock_run):
        """Test adding a single file."""
        mock_result = GitOperationResult(
            success=True,
            stdout="",
            stderr="",
            exit_code=0,
            duration=0.1,
            command=["git", "add", "file.txt"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        git_add(path, ["file.txt"])

        mock_run.assert_called_once_with(["add", "file.txt"], cwd=path)

    @patch("subrepo.git_commands.run_git_command")
    def test_git_add_multiple_files(self, mock_run):
        """Test adding multiple files."""
        mock_result = GitOperationResult(
            success=True,
            stdout="",
            stderr="",
            exit_code=0,
            duration=0.1,
            command=["git", "add", "file1.txt", "file2.txt"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        git_add(path, ["file1.txt", "file2.txt"])

        mock_run.assert_called_once_with(["add", "file1.txt", "file2.txt"], cwd=path)


class TestGitCommit:
    """Tests for git_commit function."""

    @patch("subrepo.git_commands.run_git_command")
    def test_git_commit(self, mock_run):
        """Test creating a commit."""
        mock_result = GitOperationResult(
            success=True,
            stdout="[main abc1234] commit message",
            stderr="",
            exit_code=0,
            duration=0.1,
            command=["git", "commit", "-m", "commit message"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        result = git_commit(path, "commit message")

        assert result.success
        mock_run.assert_called_once_with(["commit", "-m", "commit message"], cwd=path)


class TestGitSubtree:
    """Tests for git subtree functions."""

    @patch("subrepo.git_commands.run_git_command")
    def test_git_subtree_add_with_squash(self, mock_run):
        """Test adding a subtree with squash."""
        mock_result = GitOperationResult(
            success=True,
            stdout="Added subtree",
            stderr="",
            exit_code=0,
            duration=5.0,
            command=["git", "subtree", "add"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        git_subtree_add(path, "lib/component", "https://example.com/repo", "main")

        args = mock_run.call_args[0][0]
        assert "subtree" in args
        assert "add" in args
        assert "--prefix=lib/component" in args
        assert "--squash" in args
        assert "main" in args

    @patch("subrepo.git_commands.run_git_command")
    def test_git_subtree_add_without_squash(self, mock_run):
        """Test adding a subtree without squash."""
        mock_result = GitOperationResult(
            success=True,
            stdout="Added subtree",
            stderr="",
            exit_code=0,
            duration=5.0,
            command=["git", "subtree", "add"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        git_subtree_add(path, "lib/component", "https://example.com/repo", "main", squash=False)

        args = mock_run.call_args[0][0]
        assert "--squash" not in args

    @patch("subrepo.git_commands.run_git_command")
    def test_git_subtree_pull(self, mock_run):
        """Test pulling subtree updates."""
        mock_result = GitOperationResult(
            success=True,
            stdout="Subtree pulled",
            stderr="",
            exit_code=0,
            duration=5.0,
            command=["git", "subtree", "pull"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        git_subtree_pull(path, "lib/component", "origin", "main")

        args = mock_run.call_args[0][0]
        assert "subtree" in args
        assert "pull" in args
        assert "--prefix=lib/component" in args
        assert "--squash" in args

    @patch("subrepo.git_commands.run_git_command")
    def test_git_subtree_push(self, mock_run):
        """Test pushing subtree changes."""
        mock_result = GitOperationResult(
            success=True,
            stdout="Subtree pushed",
            stderr="",
            exit_code=0,
            duration=5.0,
            command=["git", "subtree", "push"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        git_subtree_push(path, "lib/component", "origin", "main")

        args = mock_run.call_args[0][0]
        assert "subtree" in args
        assert "push" in args
        assert "--prefix=lib/component" in args

    @patch("subrepo.git_commands.run_git_command")
    def test_git_subtree_split_with_branch(self, mock_run):
        """Test splitting subtree with branch creation."""
        mock_result = GitOperationResult(
            success=True,
            stdout="abc123def456",
            stderr="",
            exit_code=0,
            duration=3.0,
            command=["git", "subtree", "split"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        git_subtree_split(path, "lib/component", branch="temp-split")

        args = mock_run.call_args[0][0]
        assert "subtree" in args
        assert "split" in args
        assert "--prefix=lib/component" in args
        assert "--branch" in args
        assert "temp-split" in args


class TestGitStatus:
    """Tests for git_status function."""

    @patch("subrepo.git_commands.run_git_command")
    def test_git_status_default(self, mock_run):
        """Test git status with default format."""
        mock_result = GitOperationResult(
            success=True,
            stdout="On branch main",
            stderr="",
            exit_code=0,
            duration=0.1,
            command=["git", "status"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        git_status(path)

        mock_run.assert_called_once_with(["status"], cwd=path)

    @patch("subrepo.git_commands.run_git_command")
    def test_git_status_short(self, mock_run):
        """Test git status with short format."""
        mock_result = GitOperationResult(
            success=True,
            stdout=" M file.txt",
            stderr="",
            exit_code=0,
            duration=0.1,
            command=["git", "status", "--short"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        git_status(path, short=True)

        mock_run.assert_called_once_with(["status", "--short"], cwd=path)


class TestGitRevParse:
    """Tests for git_rev_parse function."""

    @patch("subrepo.git_commands.run_git_command")
    def test_git_rev_parse_returns_sha(self, mock_run):
        """Test rev-parse returns commit SHA."""
        mock_result = GitOperationResult(
            success=True,
            stdout="abc123def456789\n",
            stderr="",
            exit_code=0,
            duration=0.1,
            command=["git", "rev-parse", "HEAD"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        sha = git_rev_parse(path, "HEAD")

        assert sha == "abc123def456789"
        mock_run.assert_called_once_with(["rev-parse", "HEAD"], cwd=path)


class TestGitCommandTimeout:
    """Tests for git command timeout handling."""

    @patch("subprocess.run")
    def test_run_git_command_timeout(self, mock_run):
        """Test git command timeout raises GitCommandError."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["git", "fetch"], timeout=30
        )

        with pytest.raises(GitCommandError, match="timed out"):
            run_git_command(["fetch"], timeout=30)


class TestGitVersion:
    """Additional tests for git_version function."""

    @patch("subrepo.git_commands.run_git_command")
    def test_git_version_without_prefix(self, mock_run):
        """Test git_version handles output without 'git version' prefix."""
        mock_result = GitOperationResult(
            success=True,
            stdout="2.43.0\n",
            stderr="",
            exit_code=0,
            duration=0.1,
            command=["git", "--version"],
        )
        mock_run.return_value = mock_result

        version = git_version()

        # Should return the raw string if it doesn't start with "git version"
        assert version == "2.43.0"


class TestGitRemoteAdd:
    """Tests for git_remote_add function."""

    @patch("subrepo.git_commands.run_git_command")
    def test_git_remote_add_success(self, mock_run):
        """Test adding a git remote."""
        mock_result = GitOperationResult(
            success=True,
            stdout="",
            stderr="",
            exit_code=0,
            duration=0.1,
            command=["git", "remote", "add", "origin", "https://example.com/repo"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        result = git_remote_add(path, "origin", "https://example.com/repo")

        assert result.success
        mock_run.assert_called_once_with(
            ["remote", "add", "origin", "https://example.com/repo"], cwd=path
        )


class TestGitFetch:
    """Tests for git_fetch function."""

    @patch("subrepo.git_commands.run_git_command")
    def test_git_fetch_without_ref(self, mock_run):
        """Test fetching from remote without specific ref."""
        mock_result = GitOperationResult(
            success=True,
            stdout="From origin...",
            stderr="",
            exit_code=0,
            duration=2.0,
            command=["git", "fetch", "origin"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        result = git_fetch(path, "origin")

        assert result.success
        mock_run.assert_called_once_with(["fetch", "origin"], cwd=path)

    @patch("subrepo.git_commands.run_git_command")
    def test_git_fetch_with_ref(self, mock_run):
        """Test fetching specific ref from remote."""
        mock_result = GitOperationResult(
            success=True,
            stdout="From origin...",
            stderr="",
            exit_code=0,
            duration=2.0,
            command=["git", "fetch", "origin", "main"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        result = git_fetch(path, "origin", "main")

        assert result.success
        mock_run.assert_called_once_with(["fetch", "origin", "main"], cwd=path)


class TestGitLog:
    """Tests for git_log function."""

    @patch("subrepo.git_commands.run_git_command")
    def test_git_log_oneline(self, mock_run):
        """Test git log with oneline format."""
        mock_result = GitOperationResult(
            success=True,
            stdout="abc123 commit message\n",
            stderr="",
            exit_code=0,
            duration=0.5,
            command=["git", "log", "--oneline"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        result = git_log(path, oneline=True)

        assert result.success
        mock_run.assert_called_once_with(["log", "--oneline"], cwd=path)

    @patch("subrepo.git_commands.run_git_command")
    def test_git_log_with_paths(self, mock_run):
        """Test git log for specific paths."""
        mock_result = GitOperationResult(
            success=True,
            stdout="abc123 commit message\n",
            stderr="",
            exit_code=0,
            duration=0.5,
            command=["git", "log", "--", "lib/component"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        result = git_log(path, paths=["lib/component"])

        assert result.success
        args = mock_run.call_args[0][0]
        assert "--" in args
        assert "lib/component" in args

    @patch("subrepo.git_commands.run_git_command")
    def test_git_log_with_limit_and_revision(self, mock_run):
        """Test git log with limit and revision range."""
        mock_result = GitOperationResult(
            success=True,
            stdout="abc123 commit message\n",
            stderr="",
            exit_code=0,
            duration=0.5,
            command=["git", "log", "-n", "10", "HEAD~5..HEAD"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        result = git_log(path, revision_range="HEAD~5..HEAD", limit=10)

        assert result.success
        args = mock_run.call_args[0][0]
        assert "-n" in args
        assert "10" in args
        assert "HEAD~5..HEAD" in args


class TestGitRevList:
    """Tests for git_rev_list function."""

    @patch("subrepo.git_commands.run_git_command")
    def test_git_rev_list_basic(self, mock_run):
        """Test git rev-list with basic revision range."""
        mock_result = GitOperationResult(
            success=True,
            stdout="abc123\ndef456\n",
            stderr="",
            exit_code=0,
            duration=0.3,
            command=["git", "rev-list", "HEAD"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        result = git_rev_list(path, "HEAD")

        assert result.success
        mock_run.assert_called_once_with(["rev-list", "HEAD"], cwd=path)

    @patch("subrepo.git_commands.run_git_command")
    def test_git_rev_list_with_count(self, mock_run):
        """Test counting commits with git rev-list."""
        mock_result = GitOperationResult(
            success=True,
            stdout="5\n",
            stderr="",
            exit_code=0,
            duration=0.3,
            command=["git", "rev-list", "HEAD", "--count"],
        )
        mock_run.return_value = mock_result

        path = Path("/tmp/repo")
        result = git_rev_list(path, "HEAD", count=True)

        assert result.success
        assert "5" in result.stdout
        args = mock_run.call_args[0][0]
        assert "rev-list" in args
        assert "HEAD" in args
        assert "--count" in args
