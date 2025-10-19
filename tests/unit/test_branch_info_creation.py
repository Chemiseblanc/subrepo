"""Tests for BranchInfo creation logic.

This module tests the create_branch_info() function that builds BranchInfo
objects from git branch detection.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from subrepo.git_commands import create_branch_info
from subrepo.models import BranchInfo


class TestCreateBranchInfo:
    """Tests for create_branch_info() function."""

    @patch("subrepo.git_commands.detect_current_branch")
    @patch("subrepo.git_commands.detect_default_branch")
    def test_creates_info_on_feature_branch(
        self, mock_default: MagicMock, mock_current: MagicMock
    ) -> None:
        """Test creating BranchInfo when on a feature branch."""
        mock_current.return_value = "feature-auth"
        mock_default.return_value = "main"

        result = create_branch_info()

        assert result.current_branch == "feature-auth"
        assert result.default_branch == "main"
        assert result.is_default_branch is False
        assert result.target_branch == "feature-auth"

    @patch("subrepo.git_commands.detect_current_branch")
    @patch("subrepo.git_commands.detect_default_branch")
    def test_creates_info_on_default_branch(
        self, mock_default: MagicMock, mock_current: MagicMock
    ) -> None:
        """Test creating BranchInfo when on the default branch."""
        mock_current.return_value = "main"
        mock_default.return_value = "main"

        result = create_branch_info()

        assert result.current_branch == "main"
        assert result.default_branch == "main"
        assert result.is_default_branch is True
        assert result.target_branch == "main"

    @patch("subrepo.git_commands.detect_current_branch")
    @patch("subrepo.git_commands.detect_default_branch")
    def test_handles_master_as_default(
        self, mock_default: MagicMock, mock_current: MagicMock
    ) -> None:
        """Test with 'master' as the default branch."""
        mock_current.return_value = "develop"
        mock_default.return_value = "master"

        result = create_branch_info()

        assert result.current_branch == "develop"
        assert result.default_branch == "master"
        assert result.is_default_branch is False
        assert result.target_branch == "develop"

    @patch("subrepo.git_commands.detect_current_branch")
    @patch("subrepo.git_commands.detect_default_branch")
    def test_passes_cwd_to_detection_functions(
        self, mock_default: MagicMock, mock_current: MagicMock
    ) -> None:
        """Test that cwd parameter is passed to git detection functions."""
        mock_current.return_value = "main"
        mock_default.return_value = "main"
        test_path = Path("/tmp/test-repo")

        create_branch_info(cwd=test_path)

        mock_current.assert_called_once_with(cwd=test_path)
        mock_default.assert_called_once_with(cwd=test_path)
