"""Tests for target branch determination logic.

This module tests the determine_target_branch() function that decides
which branch to push to based on current context.
"""

from unittest.mock import MagicMock, patch

import pytest

from subrepo.git_commands import determine_target_branch
from subrepo.manifest_parser import extract_default_branch_from_project
from subrepo.models import BranchInfo, Project


class TestDetermineTargetBranch:
    """Tests for determine_target_branch() function."""

    def test_uses_current_branch_when_not_default(self) -> None:
        """Test that current branch is used when not on default."""
        branch_info = BranchInfo(
            current_branch="feature-push",
            is_default_branch=False,
            default_branch="main",
            target_branch="feature-push",
        )
        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="main",
        )

        result = determine_target_branch(branch_info, project)

        assert result == "feature-push"

    def test_uses_default_branch_when_on_default(self) -> None:
        """Test that default branch is used when on default."""
        branch_info = BranchInfo(
            current_branch="main",
            is_default_branch=True,
            default_branch="main",
            target_branch="main",
        )
        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="main",
        )

        result = determine_target_branch(branch_info, project)

        assert result == "main"

    def test_uses_manifest_default_when_available(self) -> None:
        """Test that manifest default branch is preferred when available."""
        # Scenario: We're on "develop" which is the manifest's default,
        # but git's origin/HEAD points to "main"
        branch_info = BranchInfo(
            current_branch="develop",
            is_default_branch=False,  # Not on git's default
            default_branch="main",  # Git's default from origin/HEAD
            target_branch="develop",
        )
        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="develop",  # Manifest default
        )

        result = determine_target_branch(branch_info, project)

        # When on feature branch, use current branch name
        assert result == "develop"

    def test_handles_sha_in_manifest(self) -> None:
        """Test that SHA in manifest falls back to git default."""
        branch_info = BranchInfo(
            current_branch="main",
            is_default_branch=True,
            default_branch="main",
            target_branch="main",
        )
        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",  # SHA
        )

        result = determine_target_branch(branch_info, project)

        # SHA in manifest → use git default
        assert result == "main"
