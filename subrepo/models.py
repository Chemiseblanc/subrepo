"""Data models for subrepo.

This module defines the core data structures used throughout the application.
All models use dataclasses with full type hints for type safety.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


@dataclass(frozen=True)
class Copyfile:
    """File copy directive from project to workspace.

    Attributes:
        src: Source path relative to project directory
        dest: Destination path relative to workspace root
    """

    src: str
    dest: str

    def __post_init__(self) -> None:
        """Validate Copyfile attributes."""
        if not self.src or not self.dest:
            raise ValueError("Copyfile src and dest cannot be empty")
        if ".." in self.src or ".." in self.dest:
            raise ValueError(f"Path cannot contain '..': src={self.src}, dest={self.dest}")
        if self.src.startswith("/") or self.dest.startswith("/"):
            raise ValueError(f"Paths must be relative: src={self.src}, dest={self.dest}")


@dataclass(frozen=True)
class Linkfile:
    """Symbolic link directive from workspace to project.

    Attributes:
        src: Source path relative to project directory (target of symlink)
        dest: Destination path relative to workspace root (location of symlink)
    """

    src: str
    dest: str

    def __post_init__(self) -> None:
        """Validate Linkfile attributes."""
        if not self.src or not self.dest:
            raise ValueError("Linkfile src and dest cannot be empty")
        if ".." in self.src or ".." in self.dest:
            raise ValueError(f"Path cannot contain '..': src={self.src}, dest={self.dest}")
        if self.src.startswith("/") or self.dest.startswith("/"):
            raise ValueError(f"Paths must be relative: src={self.src}, dest={self.dest}")


@dataclass(frozen=True)
class Remote:
    """Represents a named git remote repository base URL.

    Attributes:
        name: Unique identifier for the remote (e.g., "origin", "github")
        fetch: Base URL for fetching repositories
        push_url: Optional separate URL for push operations
        review: Optional code review server URL (repo compatibility)
    """

    name: str
    fetch: str
    push_url: str | None = None
    review: str | None = None

    def __post_init__(self) -> None:
        """Validate Remote attributes."""
        if not self.name:
            raise ValueError("Remote name cannot be empty")
        if not self.name.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Invalid remote name: {self.name}")
        if not self.fetch:
            raise ValueError("Remote fetch URL cannot be empty")


@dataclass(frozen=True)
class Project:
    """Represents a component repository managed as a git subtree.

    Attributes:
        name: Repository identifier, typically "org/repo" format
        path: Local filesystem path where subtree will be located
        remote: Reference to Remote.name defining the git remote
        revision: Branch, tag, or commit hash to track
        upstream: Optional upstream branch for tracking
        clone_depth: Shallow clone depth (future optimization)
        copyfiles: List of file copy directives for this project
        linkfiles: List of symlink directives for this project
    """

    name: str
    path: str
    remote: str
    revision: str = "main"
    upstream: str | None = None
    clone_depth: int | None = None
    copyfiles: list[Copyfile] = field(default_factory=list)
    linkfiles: list[Linkfile] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate Project attributes."""
        if not self.name:
            raise ValueError("Project name cannot be empty")
        if not self.path:
            raise ValueError("Project path cannot be empty")
        if self.path.startswith("/") or self.path.endswith("/"):
            raise ValueError(
                f"Project path must be relative without leading/trailing slashes: {self.path}"
            )
        if ".." in self.path:
            raise ValueError(f"Project path cannot contain '..' components: {self.path}")
        if not self.remote:
            raise ValueError("Project remote reference cannot be empty")

    @property
    def full_url(self) -> str:
        """Compute full repository URL (requires manifest context for remote lookup)."""
        # This will be computed when manifest is available
        return f"{self.remote}/{self.name}"


@dataclass
class Manifest:
    """Represents the complete workspace configuration from manifest XML.

    Attributes:
        remotes: Map of remote name to Remote objects
        projects: List of all project components
        default_remote: Default remote name for projects
        default_revision: Default revision for projects
        notice: Optional copyright/notice text from manifest
    """

    remotes: dict[str, Remote]
    projects: list[Project]
    default_remote: str | None = None
    default_revision: str | None = None
    notice: str | None = None

    def __post_init__(self) -> None:
        """Validate Manifest attributes."""
        if not self.remotes:
            raise ValueError("Manifest must have at least one remote")
        if not self.projects:
            raise ValueError("Manifest must have at least one project")

        # Validate default_remote exists
        if self.default_remote and self.default_remote not in self.remotes:
            raise ValueError(f"Default remote '{self.default_remote}' not found in remotes")

        # Validate all project remotes exist
        for project in self.projects:
            if project.remote not in self.remotes:
                raise ValueError(
                    f"Project '{project.name}' references unknown remote '{project.remote}'"
                )

        # Validate unique paths
        paths = [p.path for p in self.projects]
        if len(paths) != len(set(paths)):
            duplicates = [p for p in paths if paths.count(p) > 1]
            raise ValueError(f"Duplicate project paths found: {set(duplicates)}")

    def get_project_by_name(self, name: str) -> Project | None:
        """Find project by name.

        Args:
            name: Project name to search for

        Returns:
            Project if found, None otherwise
        """
        return next((p for p in self.projects if p.name == name), None)

    def get_project_by_path(self, path: str) -> Project | None:
        """Find project by path.

        Args:
            path: Project path to search for

        Returns:
            Project if found, None otherwise
        """
        return next((p for p in self.projects if p.path == path), None)

    def validate(self) -> list[str]:
        """Validate manifest and return list of validation errors.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        # Validate copyfile/linkfile dest path uniqueness across all projects
        dest_paths: dict[str, str] = {}  # dest -> project name
        for project in self.projects:
            for copyfile in project.copyfiles:
                if copyfile.dest in dest_paths:
                    msg = f"Duplicate copyfile destination '{copyfile.dest}': "
                    msg += f"conflicts between projects '{project.name}' "
                    msg += f"and '{dest_paths[copyfile.dest]}'"
                    errors.append(msg)
                else:
                    dest_paths[copyfile.dest] = project.name

            for linkfile in project.linkfiles:
                if linkfile.dest in dest_paths:
                    msg = f"Duplicate linkfile destination '{linkfile.dest}': "
                    msg += f"conflicts between projects '{project.name}' "
                    msg += f"and '{dest_paths[linkfile.dest]}'"
                    errors.append(msg)
                else:
                    dest_paths[linkfile.dest] = project.name

        return errors


class SubtreeStatus(Enum):
    """Enumeration of possible subtree states."""

    UP_TO_DATE = "up-to-date"
    AHEAD = "ahead"
    BEHIND = "behind"
    DIVERGED = "diverged"
    MODIFIED = "modified"
    UNINITIALIZED = "uninitialized"
    ERROR = "error"


@dataclass
class SubtreeState:
    """Represents the current state of a subtree component.

    Attributes:
        project: Reference to the project definition
        last_sync_commit: Last synced commit SHA from upstream
        last_sync_time: Timestamp of last sync operation
        local_commits: Number of local commits not pushed upstream
        upstream_commits: Number of upstream commits not pulled locally
        has_local_changes: Whether working directory has uncommitted changes
        status: Current status enum
    """

    project: Project
    last_sync_commit: str | None = None
    last_sync_time: datetime | None = None
    local_commits: int = 0
    upstream_commits: int = 0
    has_local_changes: bool = False
    status: SubtreeStatus = SubtreeStatus.UNINITIALIZED

    def needs_sync(self) -> bool:
        """Check if subtree needs synchronization.

        Returns:
            True if BEHIND or DIVERGED
        """
        return self.status in (SubtreeStatus.BEHIND, SubtreeStatus.DIVERGED)

    def can_push(self) -> bool:
        """Check if subtree can be pushed.

        Returns:
            True if AHEAD or DIVERGED and no local changes
        """
        return (
            self.status in (SubtreeStatus.AHEAD, SubtreeStatus.DIVERGED)
            and not self.has_local_changes
        )

    def is_clean(self) -> bool:
        """Check if subtree is clean and up-to-date.

        Returns:
            True if UP_TO_DATE and no local changes
        """
        return self.status == SubtreeStatus.UP_TO_DATE and not self.has_local_changes


@dataclass
class WorkspaceConfig:
    """Workspace configuration stored in .subrepo/config.json.

    Attributes:
        manifest_path: Path or URL to the manifest file
        manifest_hash: SHA256 hash of manifest content
        initialized_at: When workspace was initialized
        git_version: Git version used for initialization
        subrepo_version: Subrepo tool version
    """

    manifest_path: str
    manifest_hash: str
    initialized_at: datetime
    git_version: str
    subrepo_version: str

    def to_json(self) -> str:
        """Serialize WorkspaceConfig to JSON string.

        Returns:
            JSON string representation
        """
        import json

        config_dict = {
            "manifest_path": self.manifest_path,
            "manifest_hash": self.manifest_hash,
            "initialized_at": self.initialized_at.isoformat(),
            "git_version": self.git_version,
            "subrepo_version": self.subrepo_version,
        }
        return json.dumps(config_dict, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "WorkspaceConfig":
        """Deserialize WorkspaceConfig from JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            WorkspaceConfig instance

        Raises:
            ValueError: If JSON is invalid or missing required fields
        """
        import json

        try:
            config_dict = json.loads(json_str)
            return cls(
                manifest_path=config_dict["manifest_path"],
                manifest_hash=config_dict["manifest_hash"],
                initialized_at=datetime.fromisoformat(config_dict["initialized_at"]),
                git_version=config_dict["git_version"],
                subrepo_version=config_dict["subrepo_version"],
            )
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid WorkspaceConfig JSON: {e}") from e


@dataclass
class GitOperationResult:
    """Result of a git command execution.

    Attributes:
        success: Whether command succeeded
        stdout: Standard output from command
        stderr: Standard error from command
        exit_code: Process exit code
        duration: Execution time in seconds
        command: The git command that was executed
    """

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration: float
    command: list[str]

    def raise_for_status(self) -> None:
        """Raise GitCommandError if command failed."""
        from .exceptions import GitCommandError

        if not self.success:
            raise GitCommandError(
                f"Git command failed with exit code {self.exit_code}",
                self.command,
                self.exit_code,
                self.stderr,
            )

    def get_output(self) -> str:
        """Get output from command.

        Returns:
            stdout if success, else stderr
        """
        return self.stdout if self.success else self.stderr


class PushStatus(Enum):
    """Status of a push operation."""

    SUCCESS = "success"
    FAILED = "failed"


class PushAction(Enum):
    """Action taken during push."""

    CREATED = "created"  # New branch created
    UPDATED = "updated"  # Existing branch updated
    SKIPPED = "skipped"  # Push skipped due to error


@dataclass(frozen=True)
class PushResult:
    """Result of pushing a single component.

    Attributes:
        project_name: Name of the project/component
        status: Success or failure status
        action: What action was taken (created/updated/skipped)
        branch_name: Name of the branch pushed to
        error_message: Optional error message if status is FAILED
    """

    project_name: str
    status: PushStatus
    action: PushAction
    branch_name: str
    error_message: str | None = None

    def __post_init__(self) -> None:
        """Validate PushResult attributes."""
        if self.status == PushStatus.FAILED and not self.error_message:
            raise ValueError("Failed push must include error_message")
        if self.status == PushStatus.SUCCESS and self.error_message:
            raise ValueError("Successful push should not have error_message")


@dataclass(frozen=True)
class BranchInfo:
    """Information about current and target branches.

    Attributes:
        current_branch: Name of the current local branch
        is_default_branch: Whether current branch is the default
        default_branch: Name of the default branch (from manifest or git)
        target_branch: Name of the branch to push to (may equal current or default)
    """

    current_branch: str
    is_default_branch: bool
    default_branch: str
    target_branch: str

    def __post_init__(self) -> None:
        """Validate BranchInfo attributes."""
        if not self.current_branch:
            raise ValueError("current_branch cannot be empty")
        if not self.default_branch:
            raise ValueError("default_branch cannot be empty")
        if not self.target_branch:
            raise ValueError("target_branch cannot be empty")

        # Consistency check
        if self.is_default_branch and self.current_branch != self.default_branch:
            raise ValueError(
                f"Inconsistent state: is_default_branch=True but "
                f"current_branch={self.current_branch} != default_branch={self.default_branch}"
            )


@dataclass(frozen=True)
class MultiPushSummary:
    """Summary of multi-component push operation.

    Attributes:
        results: List of individual push results
    """

    results: list[PushResult]

    @property
    def total_count(self) -> int:
        """Total number of components attempted."""
        return len(self.results)

    @property
    def success_count(self) -> int:
        """Number of successful pushes."""
        return sum(1 for r in self.results if r.status == PushStatus.SUCCESS)

    @property
    def failed_count(self) -> int:
        """Number of failed pushes."""
        return sum(1 for r in self.results if r.status == PushStatus.FAILED)

    @property
    def created_count(self) -> int:
        """Number of branches created."""
        return sum(1 for r in self.results if r.action == PushAction.CREATED)

    @property
    def updated_count(self) -> int:
        """Number of branches updated."""
        return sum(1 for r in self.results if r.action == PushAction.UPDATED)

    def format_summary(self) -> str:
        """Format a human-readable summary.

        Returns:
            Formatted summary string
        """
        lines = [
            f"Push Summary: {self.success_count}/{self.total_count} succeeded",
            f"  Created: {self.created_count}",
            f"  Updated: {self.updated_count}",
            f"  Failed: {self.failed_count}",
        ]

        if self.failed_count > 0:
            lines.append("\nFailures:")
            for result in self.results:
                if result.status == PushStatus.FAILED:
                    lines.append(f"  - {result.project_name}: {result.error_message}")

        return "\n".join(lines)


@dataclass(frozen=True)
class FileOperationResult:
    """Result of a copyfile or linkfile operation.

    Attributes:
        project_name: Name of the project
        operation_type: "copyfile" or "linkfile"
        src: Source path
        dest: Destination path
        success: Whether operation succeeded
        error_message: Error message if failed
        fallback_used: Whether linkfile fell back to copy
    """

    project_name: str
    operation_type: str
    src: str
    dest: str
    success: bool
    error_message: str | None = None
    fallback_used: bool = False

    def __post_init__(self) -> None:
        """Validate FileOperationResult attributes."""
        if self.operation_type not in ("copyfile", "linkfile"):
            raise ValueError(f"Invalid operation_type: {self.operation_type}")
        if not self.success and not self.error_message:
            raise ValueError("Failed operation must include error_message")
        if self.success and self.error_message:
            raise ValueError("Successful operation should not have error_message")


@dataclass(frozen=True)
class FileOperationSummary:
    """Summary of file operations during sync.

    Attributes:
        results: List of operation results
    """

    results: list[FileOperationResult]

    @property
    def total_count(self) -> int:
        """Total number of operations attempted."""
        return len(self.results)

    @property
    def success_count(self) -> int:
        """Number of successful operations."""
        return sum(1 for r in self.results if r.success)

    @property
    def failed_count(self) -> int:
        """Number of failed operations."""
        return sum(1 for r in self.results if not r.success)

    @property
    def fallback_count(self) -> int:
        """Number of linkfile operations that fell back to copy."""
        return sum(1 for r in self.results if r.fallback_used)

    def format_summary(self) -> str:
        """Format a human-readable summary."""
        lines = [f"File Operations: {self.success_count}/{self.total_count} succeeded"]

        if self.fallback_count > 0:
            lines.append(f"  Symlink fallbacks: {self.fallback_count} (copied instead)")

        if self.failed_count > 0:
            lines.append(f"  Failed: {self.failed_count}")
            lines.append("\nFailures:")
            for result in self.results:
                if not result.success:
                    lines.append(
                        f"  - {result.project_name} ({result.operation_type}): "
                        f"{result.src} → {result.dest}: {result.error_message}"
                    )

        return "\n".join(lines)
