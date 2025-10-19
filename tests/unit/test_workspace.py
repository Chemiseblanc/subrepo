"""Unit tests for workspace initialization logic.

Tests workspace management functions.
"""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from subrepo.exceptions import GitOperationError, WorkspaceError
from subrepo.models import Manifest, Project, Remote, WorkspaceConfig
from subrepo.workspace import (
    create_git_repo,
    init_workspace,
    load_workspace_config,
    save_workspace_config,
)


def create_test_manifest() -> Manifest:
    """Create a simple test manifest for testing."""
    return Manifest(
        remotes={"origin": Remote(name="origin", fetch="https://github.com/")},
        projects=[
            Project(
                name="test/repo",
                path="lib/repo",
                remote="origin",
                revision="main",
            )
        ],
        default_remote="origin",
        default_revision="main",
    )


class TestWorkspaceInitialization:
    """Tests for workspace initialization functions."""

    # Enabled test
    def test_init_workspace_creates_git_repo(self):
        """Test that init_workspace creates a git repository.

        This test will FAIL until init_workspace is implemented.
        """
        from subrepo.workspace import init_workspace

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_path = Path(tmpdir)
            manifest = create_test_manifest()

            init_workspace(workspace_path, manifest, "test_manifest.xml")

            # Should create .git directory
            assert (workspace_path / ".git").exists()

    # Enabled test
    def test_init_workspace_creates_metadata_directory(self):
        """Test that init_workspace creates .subrepo metadata directory.

        This test will FAIL until init_workspace is implemented.
        """
        from subrepo.workspace import init_workspace

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_path = Path(tmpdir)
            manifest = create_test_manifest()

            init_workspace(workspace_path, manifest, "test_manifest.xml")

            # Should create .subrepo directory
            assert (workspace_path / ".subrepo").exists()
            assert (workspace_path / ".subrepo").is_dir()

    # Enabled test
    def test_init_workspace_in_non_empty_directory_raises_error(self):
        """Test that init_workspace fails in non-empty directory.

        This test will FAIL until init_workspace is implemented.
        """
        from subrepo.exceptions import WorkspaceError
        from subrepo.workspace import init_workspace

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_path = Path(tmpdir)
            manifest = create_test_manifest()

            # Create a file to make directory non-empty
            (workspace_path / "existing.txt").write_text("content")

            with pytest.raises(WorkspaceError):
                init_workspace(workspace_path, manifest, "test_manifest.xml")

    # Enabled test
    def test_create_git_repo_initializes_repository(self):
        """Test that create_git_repo initializes a git repository.

        This test will FAIL until create_git_repo is implemented.
        """
        from subrepo.workspace import create_git_repo

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            result = create_git_repo(repo_path)

            assert result.success
            assert (repo_path / ".git").exists()

    # Enabled test
    def test_create_git_repo_with_initial_commit(self):
        """Test that create_git_repo creates an initial commit.

        This test will FAIL until create_git_repo is implemented.
        """
        import subprocess

        from subrepo.workspace import create_git_repo

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            create_git_repo(repo_path)

            # Check for commits
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )

            # Should have at least one commit (initial commit)
            commit_count = int(result.stdout.strip()) if result.returncode == 0 else 0
            assert commit_count >= 1, "Should have at least one initial commit"


class TestWorkspaceConfiguration:
    """Tests for WorkspaceConfig dataclass and persistence."""

    # Enabled test
    def test_workspace_config_to_json(self):
        """Test WorkspaceConfig serialization to JSON.

        This test will FAIL until WorkspaceConfig is implemented.
        """
        import json
        from datetime import datetime

        from subrepo.models import WorkspaceConfig

        config = WorkspaceConfig(
            manifest_path="https://example.com/manifest.xml",
            manifest_hash="abc123",
            initialized_at=datetime(2025, 10, 18, 10, 0, 0, tzinfo=UTC),
            git_version="2.43.0",
            subrepo_version="0.1.0",
        )

        json_str = config.to_json()
        parsed = json.loads(json_str)

        assert parsed["manifest_path"] == "https://example.com/manifest.xml"
        assert parsed["manifest_hash"] == "abc123"
        assert parsed["git_version"] == "2.43.0"
        assert parsed["subrepo_version"] == "0.1.0"

    # Enabled test
    def test_workspace_config_from_json(self):
        """Test WorkspaceConfig deserialization from JSON.

        This test will FAIL until WorkspaceConfig is implemented.
        """
        import json

        from subrepo.models import WorkspaceConfig

        json_str = json.dumps(
            {
                "manifest_path": "manifest.xml",
                "manifest_hash": "def456",
                "initialized_at": "2025-10-18T10:00:00Z",
                "git_version": "2.43.0",
                "subrepo_version": "0.1.0",
            }
        )

        config = WorkspaceConfig.from_json(json_str)

        assert config.manifest_path == "manifest.xml"
        assert config.manifest_hash == "def456"
        assert config.git_version == "2.43.0"
        assert config.subrepo_version == "0.1.0"

    # Enabled test
    def test_workspace_config_persistence(self):
        """Test WorkspaceConfig persistence to .subrepo/config.json.

        This test will FAIL until WorkspaceConfig persistence is implemented.
        """
        from datetime import datetime

        from subrepo.models import WorkspaceConfig
        from subrepo.workspace import load_workspace_config, save_workspace_config

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_path = Path(tmpdir)
            (workspace_path / ".subrepo").mkdir()

            # Create and save config
            config = WorkspaceConfig(
                manifest_path="manifest.xml",
                manifest_hash="hash123",
                initialized_at=datetime.now(UTC),
                git_version="2.43.0",
                subrepo_version="0.1.0",
            )

            save_workspace_config(workspace_path, config)

            # Load and verify
            loaded_config = load_workspace_config(workspace_path)

            assert loaded_config.manifest_path == config.manifest_path
            assert loaded_config.manifest_hash == config.manifest_hash
            assert loaded_config.git_version == config.git_version
