"""Tests for default branch backward compatibility.

This module tests that when on the default branch, the push behavior is
unchanged from before the feature branch support was added.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from subrepo.git_commands import determine_target_branch
from subrepo.manifest_parser import Project
from subrepo.models import BranchInfo


class TestDefaultBranchCompatibility:
    """Tests for backward compatibility when on default branch."""

    def test_target_branch_equals_default_when_on_main(self) -> None:
        """Test that target branch is default when current equals default."""
        # Create BranchInfo for being on main branch
        branch_info = BranchInfo(
            current_branch="main",
            is_default_branch=True,
            default_branch="main",
            target_branch="main",
        )

        # When on default branch, target should be default
        assert branch_info.target_branch == branch_info.default_branch
        assert branch_info.is_default_branch is True

    def test_target_branch_equals_default_when_on_master(self) -> None:
        """Test backward compatibility with master as default branch."""
        branch_info = BranchInfo(
            current_branch="master",
            is_default_branch=True,
            default_branch="master",
            target_branch="master",
        )

        assert branch_info.target_branch == "master"
        assert branch_info.is_default_branch is True

    @patch("subrepo.manifest_parser.extract_default_branch_from_project")
    def test_determine_target_branch_returns_default_on_default(
        self,
        mock_manifest_default: MagicMock,
    ) -> None:
        """Test determine_target_branch when on default branch."""
        # Setup: manifest returns branch name
        mock_manifest_default.return_value = "main"

        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="main",
        )

        branch_info = BranchInfo(
            current_branch="main",
            is_default_branch=True,
            default_branch="main",
            target_branch="main",
        )

        result = determine_target_branch(branch_info, project)

        # Should return default branch
        assert result == "main"

    @patch("subrepo.manifest_parser.extract_default_branch_from_project")
    def test_determine_target_branch_uses_manifest_default_on_default(
        self,
        mock_manifest_default: MagicMock,
    ) -> None:
        """Test that manifest default is used when on default branch."""
        # Setup: manifest says develop
        mock_manifest_default.return_value = "develop"  # Manifest says develop

        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="develop",
        )

        branch_info = BranchInfo(
            current_branch="develop",
            is_default_branch=True,
            default_branch="develop",
            target_branch="develop",
        )

        result = determine_target_branch(branch_info, project)

        # Should use manifest default (develop)
        assert result == "develop"

    def test_branch_info_validation_for_default_branch(self) -> None:
        """Test that BranchInfo validates default branch consistency."""
        # This should work - consistent state
        branch_info = BranchInfo(
            current_branch="main",
            is_default_branch=True,
            default_branch="main",
            target_branch="main",
        )
        assert branch_info.is_default_branch

        # This should raise - inconsistent: says it's default but current != default
        with pytest.raises(ValueError, match="Inconsistent state"):
            BranchInfo(
                current_branch="feature-branch",
                is_default_branch=True,  # Says default
                default_branch="main",  # But current != default
                target_branch="feature-branch",
            )
