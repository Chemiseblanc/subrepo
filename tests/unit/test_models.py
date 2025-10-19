"""Unit tests for data model classes."""

import pytest

from subrepo.exceptions import GitCommandError
from subrepo.models import (
    GitOperationResult,
    Manifest,
    Project,
    Remote,
    SubtreeState,
    SubtreeStatus,
)


class TestRemote:
    """Tests for Remote dataclass."""

    def test_remote_creation_with_valid_data(self):
        """Test creating a Remote with valid data."""
        remote = Remote(name="origin", fetch="https://github.com/")
        assert remote.name == "origin"
        assert remote.fetch == "https://github.com/"
        assert remote.push_url is None
        assert remote.review is None

    def test_remote_with_push_url(self):
        """Test Remote with separate push URL."""
        remote = Remote(
            name="origin",
            fetch="https://github.com/",
            push_url="git@github.com:",
        )
        assert remote.push_url == "git@github.com:"

    def test_remote_validation_empty_name(self):
        """Test Remote validation fails for empty name."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Remote(name="", fetch="https://github.com/")

    def test_remote_validation_invalid_name(self):
        """Test Remote validation fails for invalid name characters."""
        with pytest.raises(ValueError, match="Invalid remote name"):
            Remote(name="origin@invalid", fetch="https://github.com/")

    def test_remote_validation_empty_fetch(self):
        """Test Remote validation fails for empty fetch URL."""
        with pytest.raises(ValueError, match="fetch URL cannot be empty"):
            Remote(name="origin", fetch="")

    def test_remote_is_frozen(self):
        """Test that Remote is immutable."""
        remote = Remote(name="origin", fetch="https://github.com/")
        with pytest.raises(Exception):  # FrozenInstanceError  # noqa: B017, PT011
            remote.name = "changed"


class TestProject:
    """Tests for Project dataclass."""

    def test_project_creation_with_valid_data(self):
        """Test creating a Project with valid data."""
        project = Project(
            name="org/repo",
            path="components/repo",
            remote="origin",
            revision="main",
        )
        assert project.name == "org/repo"
        assert project.path == "components/repo"
        assert project.remote == "origin"
        assert project.revision == "main"

    def test_project_default_revision(self):
        """Test Project uses 'main' as default revision."""
        project = Project(name="org/repo", path="lib/repo", remote="origin")
        assert project.revision == "main"

    def test_project_validation_empty_name(self):
        """Test Project validation fails for empty name."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Project(name="", path="lib/repo", remote="origin")

    def test_project_validation_empty_path(self):
        """Test Project validation fails for empty path."""
        with pytest.raises(ValueError, match="path cannot be empty"):
            Project(name="org/repo", path="", remote="origin")

    def test_project_validation_absolute_path(self):
        """Test Project validation fails for absolute path."""
        with pytest.raises(ValueError, match="must be relative"):
            Project(name="org/repo", path="/abs/path", remote="origin")

    def test_project_validation_trailing_slash(self):
        """Test Project validation fails for trailing slash."""
        with pytest.raises(ValueError, match="must be relative"):
            Project(name="org/repo", path="lib/repo/", remote="origin")

    def test_project_validation_dotdot_in_path(self):
        """Test Project validation fails for '..' in path."""
        with pytest.raises(ValueError, match="cannot contain '..' components"):
            Project(name="org/repo", path="lib/../repo", remote="origin")

    def test_project_validation_empty_remote(self):
        """Test Project validation fails for empty remote."""
        with pytest.raises(ValueError, match="remote reference cannot be empty"):
            Project(name="org/repo", path="lib/repo", remote="")

    def test_project_is_frozen(self):
        """Test that Project is immutable."""
        project = Project(name="org/repo", path="lib/repo", remote="origin")
        with pytest.raises(Exception):  # FrozenInstanceError  # noqa: B017, PT011
            project.name = "changed"


class TestManifest:
    """Tests for Manifest dataclass."""

    def test_manifest_creation_with_valid_data(self):
        """Test creating a Manifest with valid data."""
        remote = Remote(name="origin", fetch="https://github.com/")
        project = Project(name="org/repo", path="lib/repo", remote="origin")

        manifest = Manifest(
            remotes={"origin": remote},
            projects=[project],
        )

        assert len(manifest.remotes) == 1
        assert manifest.remotes["origin"] == remote
        assert len(manifest.projects) == 1
        assert manifest.projects[0] == project

    def test_manifest_with_defaults(self):
        """Test Manifest with default remote and revision."""
        remote = Remote(name="origin", fetch="https://github.com/")
        project = Project(name="org/repo", path="lib/repo", remote="origin")

        manifest = Manifest(
            remotes={"origin": remote},
            projects=[project],
            default_remote="origin",
            default_revision="develop",
        )

        assert manifest.default_remote == "origin"
        assert manifest.default_revision == "develop"

    def test_manifest_validation_no_remotes(self):
        """Test Manifest validation fails without remotes."""
        project = Project(name="org/repo", path="lib/repo", remote="origin")

        with pytest.raises(ValueError, match="at least one remote"):
            Manifest(remotes={}, projects=[project])

    def test_manifest_validation_no_projects(self):
        """Test Manifest validation fails without projects."""
        remote = Remote(name="origin", fetch="https://github.com/")

        with pytest.raises(ValueError, match="at least one project"):
            Manifest(remotes={"origin": remote}, projects=[])

    def test_manifest_validation_invalid_default_remote(self):
        """Test Manifest validation fails for non-existent default remote."""
        remote = Remote(name="origin", fetch="https://github.com/")
        project = Project(name="org/repo", path="lib/repo", remote="origin")

        with pytest.raises(ValueError, match="Default remote.*not found"):
            Manifest(
                remotes={"origin": remote},
                projects=[project],
                default_remote="invalid",
            )

    def test_manifest_validation_project_unknown_remote(self):
        """Test Manifest validation fails for project with unknown remote."""
        remote = Remote(name="origin", fetch="https://github.com/")
        project = Project(name="org/repo", path="lib/repo", remote="unknown")

        with pytest.raises(ValueError, match="references unknown remote"):
            Manifest(remotes={"origin": remote}, projects=[project])

    def test_manifest_validation_duplicate_paths(self):
        """Test Manifest validation fails for duplicate project paths."""
        remote = Remote(name="origin", fetch="https://github.com/")
        project1 = Project(name="org/repo1", path="lib/repo", remote="origin")
        project2 = Project(name="org/repo2", path="lib/repo", remote="origin")

        with pytest.raises(ValueError, match="Duplicate project paths"):
            Manifest(remotes={"origin": remote}, projects=[project1, project2])

    def test_manifest_get_project_by_name(self):
        """Test getting project by name."""
        remote = Remote(name="origin", fetch="https://github.com/")
        project = Project(name="org/repo", path="lib/repo", remote="origin")
        manifest = Manifest(remotes={"origin": remote}, projects=[project])

        found = manifest.get_project_by_name("org/repo")
        assert found == project

        not_found = manifest.get_project_by_name("org/other")
        assert not_found is None

    def test_manifest_get_project_by_path(self):
        """Test getting project by path."""
        remote = Remote(name="origin", fetch="https://github.com/")
        project = Project(name="org/repo", path="lib/repo", remote="origin")
        manifest = Manifest(remotes={"origin": remote}, projects=[project])

        found = manifest.get_project_by_path("lib/repo")
        assert found == project

        not_found = manifest.get_project_by_path("lib/other")
        assert not_found is None

    def test_manifest_validate_returns_empty_list_when_valid(self):
        """Test validate() returns empty list for valid manifest."""
        remote = Remote(name="origin", fetch="https://github.com/")
        project = Project(name="org/repo", path="lib/repo", remote="origin")
        manifest = Manifest(remotes={"origin": remote}, projects=[project])

        errors = manifest.validate()
        assert errors == []


class TestSubtreeState:
    """Tests for SubtreeState dataclass."""

    def test_subtree_state_creation(self):
        """Test creating SubtreeState."""
        project = Project(name="org/repo", path="lib/repo", remote="origin")
        state = SubtreeState(project=project)

        assert state.project == project
        assert state.status == SubtreeStatus.UNINITIALIZED
        assert state.local_commits == 0
        assert state.upstream_commits == 0
        assert not state.has_local_changes

    def test_subtree_state_needs_sync(self):
        """Test needs_sync() method."""
        project = Project(name="org/repo", path="lib/repo", remote="origin")

        state_behind = SubtreeState(project=project, status=SubtreeStatus.BEHIND)
        assert state_behind.needs_sync()

        state_diverged = SubtreeState(project=project, status=SubtreeStatus.DIVERGED)
        assert state_diverged.needs_sync()

        state_up_to_date = SubtreeState(project=project, status=SubtreeStatus.UP_TO_DATE)
        assert not state_up_to_date.needs_sync()

    def test_subtree_state_can_push(self):
        """Test can_push() method."""
        project = Project(name="org/repo", path="lib/repo", remote="origin")

        state_ahead = SubtreeState(project=project, status=SubtreeStatus.AHEAD)
        assert state_ahead.can_push()

        state_ahead_dirty = SubtreeState(
            project=project, status=SubtreeStatus.AHEAD, has_local_changes=True
        )
        assert not state_ahead_dirty.can_push()

        state_up_to_date = SubtreeState(project=project, status=SubtreeStatus.UP_TO_DATE)
        assert not state_up_to_date.can_push()

    def test_subtree_state_is_clean(self):
        """Test is_clean() method."""
        project = Project(name="org/repo", path="lib/repo", remote="origin")

        state_clean = SubtreeState(project=project, status=SubtreeStatus.UP_TO_DATE)
        assert state_clean.is_clean()

        state_dirty = SubtreeState(
            project=project,
            status=SubtreeStatus.UP_TO_DATE,
            has_local_changes=True,
        )
        assert not state_dirty.is_clean()

        state_ahead = SubtreeState(project=project, status=SubtreeStatus.AHEAD)
        assert not state_ahead.is_clean()


class TestGitOperationResult:
    """Tests for GitOperationResult dataclass."""

    def test_git_operation_result_success(self):
        """Test successful git operation result."""
        result = GitOperationResult(
            success=True,
            stdout="Success output",
            stderr="",
            exit_code=0,
            duration=1.5,
            command=["git", "status"],
        )

        assert result.success
        assert result.stdout == "Success output"
        assert result.exit_code == 0

    def test_git_operation_result_get_output_on_success(self):
        """Test get_output() returns stdout on success."""
        result = GitOperationResult(
            success=True,
            stdout="Success output",
            stderr="",
            exit_code=0,
            duration=1.0,
            command=["git", "status"],
        )

        assert result.get_output() == "Success output"

    def test_git_operation_result_get_output_on_failure(self):
        """Test get_output() returns stderr on failure."""
        result = GitOperationResult(
            success=False,
            stdout="",
            stderr="Error output",
            exit_code=1,
            duration=1.0,
            command=["git", "status"],
        )

        assert result.get_output() == "Error output"

    def test_git_operation_result_raise_for_status_success(self):
        """Test raise_for_status() does nothing on success."""
        result = GitOperationResult(
            success=True,
            stdout="Success",
            stderr="",
            exit_code=0,
            duration=1.0,
            command=["git", "status"],
        )

        result.raise_for_status()  # Should not raise

    def test_git_operation_result_raise_for_status_failure(self):
        """Test raise_for_status() raises on failure."""
        result = GitOperationResult(
            success=False,
            stdout="",
            stderr="fatal: error",
            exit_code=1,
            duration=1.0,
            command=["git", "status"],
        )

        with pytest.raises(GitCommandError) as exc_info:
            result.raise_for_status()

        error = exc_info.value
        assert error.command == ["git", "status"]
        assert error.exit_code == 1
        assert error.stderr == "fatal: error"
