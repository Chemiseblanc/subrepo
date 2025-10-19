"""Custom exceptions for subrepo.

This module defines the exception hierarchy used throughout the subrepo tool.
All exceptions inherit from SubrepoError base class for easy catching.
"""


class SubrepoError(Exception):
    """Base exception for all subrepo errors."""


class ManifestError(SubrepoError):
    """Base exception for manifest-related errors."""


class ManifestParseError(ManifestError):
    """Raised when manifest XML cannot be parsed."""


class ManifestValidationError(ManifestError):
    """Raised when manifest content fails validation rules."""


class ManifestNotFoundError(ManifestError):
    """Raised when manifest file cannot be found."""


class WorkspaceError(SubrepoError):
    """Base exception for workspace-related errors."""


class WorkspaceNotInitializedError(WorkspaceError):
    """Raised when operation requires initialized workspace but none exists."""


class WorkspaceAlreadyExistsError(WorkspaceError):
    """Raised when attempting to initialize in already-initialized directory."""


class DirtyWorkspaceError(WorkspaceError):
    """Raised when workspace has uncommitted changes that prevent operation."""


class GitOperationError(SubrepoError):
    """Base exception for git operation errors."""


class GitCommandError(GitOperationError):
    """Raised when a git command fails."""

    def __init__(self, message: str, command: list[str], exit_code: int, stderr: str) -> None:
        """Initialize git command error.

        Args:
            message: Human-readable error message
            command: The git command that failed
            exit_code: Exit code from git process
            stderr: Standard error output from git
        """
        super().__init__(message)
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr


class SubtreeConflictError(GitOperationError):
    """Raised when git subtree operation encounters conflicts."""


class RemoteNotAccessibleError(GitOperationError):
    """Raised when remote repository cannot be accessed."""


class BranchError(GitOperationError):
    """Base exception for branch-related errors."""


class DetachedHeadError(BranchError):
    """Raised when attempting to push from detached HEAD state."""

    def __init__(self) -> None:
        """Initialize detached HEAD error."""
        super().__init__(
            "Cannot push from detached HEAD state. "
            "Check out a branch before pushing:\n"
            "  git checkout main\n"
            "  git checkout -b new-feature-branch"
        )


class PushError(GitOperationError):
    """Base exception for push operation errors."""


class NonFastForwardError(PushError):
    """Raised when push would not be fast-forward."""

    def __init__(self, branch: str, component: str) -> None:
        """Initialize non-fast-forward error.

        Args:
            branch: Branch name that cannot be pushed
            component: Component name being pushed
        """
        super().__init__(
            f"Push to {component}:{branch} rejected (non-fast-forward). "
            f"Remote branch has diverged from local. Use --force to override."
        )
        self.branch = branch
        self.component = component


class BranchProtectionError(PushError):
    """Raised when pushing to a protected branch."""

    def __init__(self, branch: str, component: str) -> None:
        """Initialize branch protection error.

        Args:
            branch: Protected branch name
            component: Component name being pushed
        """
        super().__init__(
            f"Branch '{branch}' is protected in {component}. "
            f"Contact repository administrator to modify protection rules."
        )
        self.branch = branch
        self.component = component


class RepositoryNotFoundError(PushError):
    """Raised when remote repository does not exist."""

    def __init__(self, repository: str) -> None:
        """Initialize repository not found error.

        Args:
            repository: Repository URL or name that doesn't exist
        """
        super().__init__(
            f"Remote repository '{repository}' does not exist. "
            f"Create the repository before pushing."
        )
        self.repository = repository
