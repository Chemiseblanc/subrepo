"""Unit tests for CLI module."""

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from subrepo import cli
from subrepo.exceptions import GitOperationError, ManifestError, WorkspaceError
from subrepo.models import Manifest, Project, Remote


class TestSetupLogging:
    """Tests for logging setup."""

    def test_setup_logging_verbose(self):
        """Test logging setup with verbose mode."""
        cli.setup_logging(verbose=True, quiet=False)
        assert cli._verbose is True
        assert cli._quiet is False

    def test_setup_logging_quiet(self):
        """Test logging setup with quiet mode."""
        cli.setup_logging(verbose=False, quiet=True)
        assert cli._verbose is False
        assert cli._quiet is True

    def test_setup_logging_normal(self):
        """Test logging setup with normal mode."""
        cli.setup_logging(verbose=False, quiet=False)
        assert cli._verbose is False
        assert cli._quiet is False


class TestShouldPrint:
    """Tests for should_print function."""

    def test_should_print_not_quiet(self):
        """Test should_print when not in quiet mode."""
        cli._quiet = False
        assert cli.should_print("info") is True
        assert cli.should_print("error") is True
        assert cli.should_print("debug") is True

    def test_should_print_quiet_info(self):
        """Test should_print for info when quiet."""
        cli._quiet = True
        assert cli.should_print("info") is False

    def test_should_print_quiet_error(self):
        """Test should_print for error when quiet."""
        cli._quiet = True
        assert cli.should_print("error") is True


class TestColorize:
    """Tests for colorize function."""

    def test_colorize_with_color(self):
        """Test colorize adds color codes."""
        cli._no_color = False
        result = cli.colorize("text", "red")
        assert "\033[31m" in result
        assert "text" in result
        assert "\033[0m" in result

    def test_colorize_no_color_flag(self):
        """Test colorize respects no-color flag."""
        cli._no_color = True
        result = cli.colorize("text", "red")
        assert result == "text"

    @patch.dict("os.environ", {"NO_COLOR": "1"})
    def test_colorize_no_color_env(self):
        """Test colorize respects NO_COLOR environment variable."""
        cli._no_color = False
        result = cli.colorize("text", "red")
        assert result == "text"

    def test_colorize_invalid_color(self):
        """Test colorize with invalid color name."""
        cli._no_color = False
        result = cli.colorize("text", "invalid")
        assert result == "text"


class TestInitCommand:
    """Tests for init_command function."""

    @patch("subrepo.cli.parse_manifest")
    @patch("subrepo.cli.init_workspace")
    @patch("subrepo.cli.git_subtree_add")
    def test_init_command_no_clone(self, mock_add, mock_init_ws, mock_parse):
        """Test init command with --no-clone flag."""
        # Setup
        args = argparse.Namespace(
            manifest="manifest.xml",
            directory=None,
            no_clone=True,
        )

        project = Project(name="test/repo", path="lib/repo", remote="origin", revision="main")
        manifest = Manifest(
            remotes={"origin": Remote(name="origin", fetch="https://github.com/test/")},
            projects=[project],
            default_remote="origin",
            default_revision="main",
        )
        mock_parse.return_value = manifest

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.iterdir", return_value=[]):
                result = cli.init_command(args)

        assert result == 0
        mock_parse.assert_called_once()
        mock_init_ws.assert_not_called()
        mock_add.assert_not_called()

    @patch("subrepo.cli.parse_manifest")
    def test_init_command_manifest_not_found(self, mock_parse):
        """Test init command with missing manifest."""
        args = argparse.Namespace(
            manifest="nonexistent.xml",
            directory=None,
            no_clone=False,
        )

        with patch("pathlib.Path.exists", return_value=False):
            result = cli.init_command(args)

        assert result == 1
        mock_parse.assert_not_called()

    @patch("subrepo.cli.parse_manifest")
    def test_init_command_directory_not_empty(self, mock_parse):
        """Test init command with non-empty directory."""
        args = argparse.Namespace(
            manifest="manifest.xml",
            directory=None,
            no_clone=False,
        )

        # Create mock paths with resolve methods
        manifest_path = MagicMock(spec=Path)
        manifest_path.resolve.return_value = Path("/tmp/manifest.xml")
        manifest_path.name = "manifest.xml"

        other_file = MagicMock(spec=Path)
        other_file.resolve.return_value = Path("/tmp/other.txt")
        other_file.name = "other.txt"

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.iterdir", return_value=[manifest_path, other_file]):
                result = cli.init_command(args)

        assert result == 1

    @patch("subrepo.cli.parse_manifest")
    def test_init_command_manifest_parse_error(self, mock_parse):
        """Test init command with manifest parse error."""
        args = argparse.Namespace(
            manifest="manifest.xml",
            directory=None,
            no_clone=False,
        )

        mock_parse.side_effect = ManifestError("Parse error")

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.iterdir", return_value=[]):
                result = cli.init_command(args)

        assert result == 1

    @patch("subrepo.cli.parse_manifest")
    @patch("subrepo.cli.init_workspace")
    def test_init_command_workspace_error(self, mock_init_ws, mock_parse):
        """Test init command with workspace initialization error."""
        args = argparse.Namespace(
            manifest="manifest.xml",
            directory=None,
            no_clone=False,
        )

        project = Project(name="test/repo", path="lib/repo", remote="origin", revision="main")
        manifest = Manifest(
            remotes={"origin": Remote(name="origin", fetch="https://github.com/test/")},
            projects=[project],
            default_remote="origin",
            default_revision="main",
        )
        mock_parse.return_value = manifest
        mock_init_ws.side_effect = WorkspaceError("Init error")

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.iterdir", return_value=[]):
                result = cli.init_command(args)

        assert result == 1

    @patch("subrepo.cli.parse_manifest")
    @patch("subrepo.cli.init_workspace")
    @patch("subrepo.cli.git_subtree_add")
    def test_init_command_success_with_projects(self, mock_add, mock_init_ws, mock_parse):
        """Test successful init command with projects."""
        args = argparse.Namespace(
            manifest="manifest.xml",
            directory=None,
            no_clone=False,
        )

        project = Project(
            name="test/repo",
            path="lib/repo",
            remote="origin",
            revision="main",
        )
        manifest = Manifest(
            remotes={"origin": Remote(name="origin", fetch="https://github.com/")},
            projects=[project],
            default_remote="origin",
            default_revision="main",
        )
        mock_parse.return_value = manifest

        mock_result = Mock()
        mock_result.success = True
        mock_add.return_value = mock_result

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.iterdir", return_value=[]):
                result = cli.init_command(args)

        assert result == 0
        mock_init_ws.assert_called_once()
        mock_add.assert_called_once()

    @patch("subrepo.cli.parse_manifest")
    @patch("subrepo.cli.init_workspace")
    @patch("subrepo.cli.git_subtree_add")
    def test_init_command_git_add_failure(self, mock_add, mock_init_ws, mock_parse):
        """Test init command when git subtree add fails."""
        args = argparse.Namespace(
            manifest="manifest.xml",
            directory=None,
            no_clone=False,
        )

        project = Project(
            name="test/repo",
            path="lib/repo",
            remote="origin",
            revision="main",
        )
        manifest = Manifest(
            remotes={"origin": Remote(name="origin", fetch="https://github.com/")},
            projects=[project],
            default_remote="origin",
            default_revision="main",
        )
        mock_parse.return_value = manifest

        mock_result = Mock()
        mock_result.success = False
        mock_result.stderr = "Git error"
        mock_add.return_value = mock_result

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.iterdir", return_value=[]):
                result = cli.init_command(args)

        assert result == 2

    @patch("subrepo.cli.parse_manifest")
    @patch("subrepo.cli.init_workspace")
    @patch("subrepo.cli.git_subtree_add")
    def test_init_command_git_operation_exception(self, mock_add, mock_init_ws, mock_parse):
        """Test init command when git operation raises exception."""
        args = argparse.Namespace(
            manifest="manifest.xml",
            directory=None,
            no_clone=False,
        )

        project = Project(
            name="test/repo",
            path="lib/repo",
            remote="origin",
            revision="main",
        )
        manifest = Manifest(
            remotes={"origin": Remote(name="origin", fetch="https://github.com/")},
            projects=[project],
            default_remote="origin",
            default_revision="main",
        )
        mock_parse.return_value = manifest
        mock_add.side_effect = GitOperationError("Git failed")

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.iterdir", return_value=[]):
                result = cli.init_command(args)

        assert result == 2


class TestMain:
    """Tests for main function."""

    @patch("subrepo.cli.init_command")
    @patch("sys.argv", ["subrepo", "init", "manifest.xml", "--no-clone"])
    def test_main_init_command(self, mock_init):
        """Test main function routes to init command."""
        mock_init.return_value = 0
        result = cli.main()
        assert result == 0
        mock_init.assert_called_once()

    @patch("sys.argv", ["subrepo", "--version"])
    def test_main_version_flag(self, capsys):
        """Test main function with --version flag."""
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
        assert exc_info.value.code == 0

    @patch("sys.argv", ["subrepo"])
    def test_main_no_command(self, capsys):
        """Test main function without command."""
        result = cli.main()
        assert result == 1
