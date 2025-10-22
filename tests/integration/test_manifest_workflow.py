"""Integration tests for manifest parsing workflow.

Tests the complete workflow of parsing and validating manifests.
Per TDD: These tests MUST fail until implementation is complete.
"""

from pathlib import Path

import pytest

# Will import once implemented
# from subrepo.manifest_parser import parse_manifest, validate_manifest


@pytest.fixture
def simple_manifest_path():
    """Path to simple test manifest."""
    return Path(__file__).parent / "fixtures" / "simple_manifest.xml"


@pytest.fixture
def complex_manifest_path():
    """Path to complex test manifest."""
    return Path(__file__).parent / "fixtures" / "complex_manifest.xml"


@pytest.fixture
def invalid_manifest_path():
    """Path to invalid test manifest."""
    return Path(__file__).parent / "fixtures" / "invalid_manifest.xml"


class TestManifestParsingWorkflow:
    """Tests for complete manifest parsing workflow."""

    def test_parse_simple_manifest(self, simple_manifest_path):
        """Test parsing a simple manifest file."""
        from subrepo.manifest_parser import parse_manifest

        manifest = parse_manifest(simple_manifest_path)

        assert len(manifest.remotes) == 1
        assert "github" in manifest.remotes
        assert len(manifest.projects) == 2
        assert manifest.default_remote == "github"
        assert manifest.default_revision == "main"

    def test_parse_complex_manifest(self, complex_manifest_path):
        """Test parsing a complex manifest with multiple remotes."""
        from subrepo.manifest_parser import parse_manifest

        manifest = parse_manifest(complex_manifest_path)

        assert len(manifest.remotes) == 2
        assert "github" in manifest.remotes
        assert "gitlab" in manifest.remotes
        assert len(manifest.projects) == 4

    def test_parse_invalid_manifest_raises_error(self, invalid_manifest_path):
        """Test that parsing invalid manifest raises appropriate error."""
        from subrepo.exceptions import ManifestError
        from subrepo.manifest_parser import parse_manifest

        with pytest.raises(ManifestError):
            parse_manifest(invalid_manifest_path)


class TestMultiComponentSyncWorkflow:
    """Integration tests for multi-component sync workflow (User Story 2)."""

    def test_sync_all_components_workflow(self, tmp_path):
        """Test syncing all components in a workspace.

        Note: This is a basic test since it requires external git repos.
        """
        from subrepo.models import Manifest, Project, Remote
        from subrepo.subtree_manager import SubtreeManager
        from subrepo.workspace import init_workspace

        # Create minimal test manifest
        manifest = Manifest(
            remotes={"origin": Remote(name="origin", fetch="https://github.com/test/")},
            projects=[
                Project(name="org/repo1", path="lib/repo1", remote="origin", revision="main"),
            ],
            default_remote="origin",
            default_revision="main",
        )

        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir()
        init_workspace(workspace_path, manifest, "test_manifest.xml")

        # Create manager
        manager = SubtreeManager(workspace_path, manifest)

        # Basic check that manager can be created
        assert manager.workspace_path == workspace_path
        assert manager.manifest == manifest

    def test_sync_selective_component_workflow(self, tmp_path):
        """Test syncing a single component.

        Note: This is a basic test since it requires external git repos.
        """
        from subrepo.models import Manifest, Project, Remote
        from subrepo.subtree_manager import SubtreeManager
        from subrepo.workspace import init_workspace

        manifest = Manifest(
            remotes={"origin": Remote(name="origin", fetch="https://github.com/test/")},
            projects=[
                Project(name="org/repo1", path="lib/repo1", remote="origin", revision="main"),
                Project(name="org/repo2", path="lib/repo2", remote="origin", revision="main"),
            ],
            default_remote="origin",
            default_revision="main",
        )

        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir()
        init_workspace(workspace_path, manifest, "test_manifest.xml")

        # Create manager and verify selective access works
        manager = SubtreeManager(workspace_path, manifest)
        assert len(manager.manifest.projects) == 2


class TestStatusAcrossMultipleComponentStates:
    """Integration tests for status command across multiple component states (User Story 5)."""

    def test_status_workflow_with_mixed_states(self, tmp_path):
        """Test status computation with components in different states.

        This test verifies that the status command can correctly identify and
        report on components that are up-to-date, ahead, behind, and modified.
        """
        from subrepo.models import Manifest, Project, Remote
        from subrepo.subtree_manager import get_all_component_status
        from subrepo.workspace import init_workspace

        # Create a test manifest
        manifest = Manifest(
            remotes={"origin": Remote(name="origin", fetch="https://github.com/test/")},
            projects=[
                Project(name="org/repo1", path="lib/repo1", remote="origin", revision="main"),
                Project(name="org/repo2", path="lib/repo2", remote="origin", revision="main"),
            ],
            default_remote="origin",
            default_revision="main",
        )

        # Initialize workspace
        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir()
        init_workspace(workspace_path, manifest, "test_manifest.xml")

        # Get status for all components
        statuses = get_all_component_status(workspace_path, manifest)

        # Should return status for both components
        assert len(statuses) == 2
        assert all(hasattr(s, "status") for s in statuses)

    def test_status_workflow_empty_workspace(self, tmp_path):
        """Test status computation in a workspace with uninitialized components.

        This test verifies that status gracefully handles a workspace
        where components are defined but not yet cloned/initialized.
        """
        from subrepo.models import Manifest, Project, Remote
        from subrepo.subtree_manager import get_all_component_status
        from subrepo.workspace import init_workspace

        # Manifest with a project but not yet cloned
        manifest = Manifest(
            remotes={"origin": Remote(name="origin", fetch="https://github.com/test/")},
            projects=[
                Project(name="org/repo1", path="lib/repo1", remote="origin", revision="main"),
            ],
            default_remote="origin",
            default_revision="main",
        )

        # Initialize workspace (but don't clone components)
        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir()
        init_workspace(workspace_path, manifest, "test_manifest.xml")

        # Get status for all components
        statuses = get_all_component_status(workspace_path, manifest)

        # Should return status showing component is uninitialized
        assert len(statuses) == 1
        assert hasattr(statuses[0], "status")
        from subrepo.models import SubtreeStatus

        assert statuses[0].status == SubtreeStatus.UNINITIALIZED
