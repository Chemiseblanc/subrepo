"""Tests for manifest integration functions.

This module tests functions that integrate manifest parsing with git operations,
specifically extract_default_branch_from_project().
"""

import pytest

from subrepo.manifest_parser import extract_default_branch_from_project
from subrepo.models import Project


class TestExtractDefaultBranchFromProject:
    """Tests for extract_default_branch_from_project() function."""

    def test_returns_branch_name_when_not_sha(self) -> None:
        """Test that branch name is returned when revision is not a SHA."""
        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="develop",
        )

        result = extract_default_branch_from_project(project)

        assert result == "develop"

    def test_returns_none_when_full_sha(self) -> None:
        """Test that None is returned when revision is a full commit SHA."""
        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
        )

        result = extract_default_branch_from_project(project)

        assert result is None

    def test_handles_main_branch(self) -> None:
        """Test that 'main' branch name is returned correctly."""
        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="main",
        )

        result = extract_default_branch_from_project(project)

        assert result == "main"

    def test_handles_master_branch(self) -> None:
        """Test that 'master' branch name is returned correctly."""
        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="master",
        )

        result = extract_default_branch_from_project(project)

        assert result == "master"

    def test_handles_branch_with_slashes(self) -> None:
        """Test that branch names with slashes are handled correctly."""
        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="release/v1.0",
        )

        result = extract_default_branch_from_project(project)

        assert result == "release/v1.0"

    def test_handles_tag_names(self) -> None:
        """Test that tag names are treated as branch names (not SHAs)."""
        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="v1.0.0",
        )

        result = extract_default_branch_from_project(project)

        assert result == "v1.0.0"

    def test_handles_short_sha_as_branch(self) -> None:
        """Test that short SHAs (7-8 chars) are treated as branch names."""
        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="a1b2c3d",
        )

        result = extract_default_branch_from_project(project)

        # Short SHAs are treated as branch names (ambiguous but rare in manifests)
        assert result == "a1b2c3d"

    def test_mixed_case_sha_returns_none(self) -> None:
        """Test that mixed-case SHAs are recognized and return None."""
        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="A1B2c3d4E5F6a7b8C9D0e1F2a3B4c5D6e7F8a9B0",
        )

        result = extract_default_branch_from_project(project)

        assert result is None

    def test_all_zeros_sha_returns_none(self) -> None:
        """Test that all-zeros SHA (valid hex) returns None."""
        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="0" * 40,
        )

        result = extract_default_branch_from_project(project)

        assert result is None

    def test_all_f_sha_returns_none(self) -> None:
        """Test that all-F SHA (valid hex) returns None."""
        project = Project(
            name="platform/core",
            path="platform/core",
            remote="origin",
            revision="F" * 40,
        )

        result = extract_default_branch_from_project(project)

        assert result is None
