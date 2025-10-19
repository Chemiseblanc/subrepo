"""Unit tests for exception classes."""

from subrepo.exceptions import (
    DirtyWorkspaceError,
    GitCommandError,
    GitOperationError,
    ManifestError,
    ManifestNotFoundError,
    ManifestParseError,
    ManifestValidationError,
    RemoteNotAccessibleError,
    SubrepoError,
    SubtreeConflictError,
    WorkspaceAlreadyExistsError,
    WorkspaceError,
    WorkspaceNotInitializedError,
)


def test_subrepo_error_is_base_exception():
    """Test that SubrepoError is the base exception."""
    error = SubrepoError("test error")
    assert isinstance(error, Exception)
    assert str(error) == "test error"


def test_manifest_error_inherits_from_subrepo_error():
    """Test ManifestError inheritance."""
    error = ManifestError("manifest error")
    assert isinstance(error, SubrepoError)
    assert isinstance(error, Exception)


def test_manifest_parse_error_inherits_from_manifest_error():
    """Test ManifestParseError inheritance."""
    error = ManifestParseError("parse error")
    assert isinstance(error, ManifestError)
    assert isinstance(error, SubrepoError)


def test_manifest_validation_error_inherits_from_manifest_error():
    """Test ManifestValidationError inheritance."""
    error = ManifestValidationError("validation error")
    assert isinstance(error, ManifestError)
    assert isinstance(error, SubrepoError)


def test_manifest_not_found_error_inherits_from_manifest_error():
    """Test ManifestNotFoundError inheritance."""
    error = ManifestNotFoundError("not found")
    assert isinstance(error, ManifestError)
    assert isinstance(error, SubrepoError)


def test_workspace_error_inherits_from_subrepo_error():
    """Test WorkspaceError inheritance."""
    error = WorkspaceError("workspace error")
    assert isinstance(error, SubrepoError)
    assert isinstance(error, Exception)


def test_workspace_not_initialized_error():
    """Test WorkspaceNotInitializedError."""
    error = WorkspaceNotInitializedError("not initialized")
    assert isinstance(error, WorkspaceError)
    assert isinstance(error, SubrepoError)


def test_workspace_already_exists_error():
    """Test WorkspaceAlreadyExistsError."""
    error = WorkspaceAlreadyExistsError("already exists")
    assert isinstance(error, WorkspaceError)
    assert isinstance(error, SubrepoError)


def test_dirty_workspace_error():
    """Test DirtyWorkspaceError."""
    error = DirtyWorkspaceError("dirty workspace")
    assert isinstance(error, WorkspaceError)
    assert isinstance(error, SubrepoError)


def test_git_operation_error_inherits_from_subrepo_error():
    """Test GitOperationError inheritance."""
    error = GitOperationError("git error")
    assert isinstance(error, SubrepoError)
    assert isinstance(error, Exception)


def test_git_command_error_stores_details():
    """Test GitCommandError stores command details."""
    command = ["git", "status"]
    exit_code = 1
    stderr = "fatal: not a git repository"

    error = GitCommandError("Command failed", command, exit_code, stderr)

    assert isinstance(error, GitOperationError)
    assert isinstance(error, SubrepoError)
    assert error.command == command
    assert error.exit_code == exit_code
    assert error.stderr == stderr
    assert "Command failed" in str(error)


def test_subtree_conflict_error():
    """Test SubtreeConflictError."""
    error = SubtreeConflictError("conflict detected")
    assert isinstance(error, GitOperationError)
    assert isinstance(error, SubrepoError)


def test_remote_not_accessible_error():
    """Test RemoteNotAccessibleError."""
    error = RemoteNotAccessibleError("cannot access remote")
    assert isinstance(error, GitOperationError)
    assert isinstance(error, SubrepoError)
