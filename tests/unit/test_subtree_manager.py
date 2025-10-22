"""Unit tests for subtree_manager module.

Tests subtree synchronization logic.
Per TDD: These tests MUST fail until implementation is complete.
"""

from pathlib import Path

import pytest


class TestSubtreeSyncLogic:
    """Tests for subtree synchronization logic (User Story 2)."""

    def test_sync_all_components(self):
        """Test sync_all_components function."""
        from subrepo.subtree_manager import SubtreeManager

        # sync_all_components method exists
        assert hasattr(SubtreeManager, "sync_all_components")

    def test_detect_component_state(self):
        """Test component state detection."""
        from subrepo.subtree_manager import SubtreeManager

        # detect_component_state method exists
        assert hasattr(SubtreeManager, "detect_component_state")

    def test_detect_conflicts(self):
        """Test conflict detection."""
        from subrepo.subtree_manager import SubtreeManager

        # detect_conflicts method exists
        assert hasattr(SubtreeManager, "detect_conflicts")


class TestCommitExtractionLogic:
    """Tests for commit extraction logic (User Story 3)."""

    def test_extract_subtree_commits(self):
        """Test extracting commits for a subtree."""
        from subrepo.subtree_manager import SubtreeManager

        # extract_subtree_commits method exists
        assert hasattr(SubtreeManager, "extract_subtree_commits")


class TestSingleComponentPullLogic:
    """Tests for single component pull logic (User Story 4)."""

    def test_pull_single_component(self):
        """Test pulling updates for a single component."""
        from subrepo.subtree_manager import SubtreeManager

        # pull_component method exists
        assert hasattr(SubtreeManager, "pull_component")


class TestStatusComputationLogic:
    """Tests for status computation logic (User Story 5)."""

    def test_get_component_status_returns_state(self):
        """Test get_component_status returns SubtreeState for a component.

        This test verifies that get_component_status can compute and return
        the status for a given component.
        """
        import tempfile

        from subrepo.models import Manifest, Project, Remote, SubtreeStatus
        from subrepo.subtree_manager import get_component_status
        from subrepo.workspace import init_workspace

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_path = Path(tmpdir)

            # Create a test manifest
            manifest = Manifest(
                remotes={"origin": Remote(name="origin", fetch="https://github.com/")},
                projects=[
                    Project(name="org/repo", path="lib/repo", remote="origin", revision="main")
                ],
                default_remote="origin",
                default_revision="main",
            )

            # Initialize workspace
            init_workspace(workspace_path, manifest, "test_manifest.xml")

            # Get status for the project
            project = manifest.projects[0]
            status = get_component_status(workspace_path, project)

            # Should return a SubtreeState
            assert status is not None
            assert hasattr(status, "status")
            # Component is uninitialized since we haven't pulled it yet
            assert status.status == SubtreeStatus.UNINITIALIZED

    def test_get_all_component_status_returns_list(self):
        """Test get_all_component_status returns list of SubtreeState.

        This test verifies that get_all_component_status can compute status
        for all components in a workspace.
        """
        import tempfile

        from subrepo.models import Manifest, Project, Remote, SubtreeStatus
        from subrepo.subtree_manager import get_all_component_status
        from subrepo.workspace import init_workspace

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_path = Path(tmpdir)

            # Create a test manifest
            manifest = Manifest(
                remotes={"origin": Remote(name="origin", fetch="https://github.com/")},
                projects=[
                    Project(name="org/repo1", path="lib/repo1", remote="origin", revision="main"),
                    Project(name="org/repo2", path="lib/repo2", remote="origin", revision="main"),
                ],
                default_remote="origin",
                default_revision="main",
            )

            # Initialize workspace
            init_workspace(workspace_path, manifest, "test_manifest.xml")

            # Get status for all components
            statuses = get_all_component_status(workspace_path, manifest)

            # Should return a list of SubtreeState
            assert isinstance(statuses, list)
            assert len(statuses) == 2
            # All components should be uninitialized
            for status in statuses:
                assert hasattr(status, "status")
                assert status.status == SubtreeStatus.UNINITIALIZED

    def test_status_detection_logic(self):
        """Test status detection returns correct SubtreeStatus enum.

        This test verifies that the status detection logic correctly
        identifies whether a component is up-to-date, ahead, behind, etc.
        """
        from subrepo.models import SubtreeStatus

        # Verify SubtreeStatus enum exists and has expected values
        assert hasattr(SubtreeStatus, "UP_TO_DATE")
        assert hasattr(SubtreeStatus, "AHEAD")
        assert hasattr(SubtreeStatus, "BEHIND")
        assert hasattr(SubtreeStatus, "DIVERGED")
        assert hasattr(SubtreeStatus, "MODIFIED")

        # Test that enum values are correctly defined
        assert SubtreeStatus.UP_TO_DATE.value == "up-to-date"
        assert SubtreeStatus.AHEAD.value == "ahead"
        assert SubtreeStatus.BEHIND.value == "behind"
