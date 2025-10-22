"""Subtree management operations.

Provides functions for managing git subtree components including sync, push, pull operations.
"""

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from .exceptions import GitOperationError, WorkspaceError
from .file_operations import (
    execute_copyfile_operations,
    execute_linkfile_operations,
)
from .git_commands import (
    create_branch_info,
    determine_target_branch,
    execute_git_push,
    git_fetch,
    git_log,
    git_rev_list,
    git_status,
    git_subtree_pull,
    git_subtree_push,
)
from .models import (
    FileOperationResult,
    GitOperationResult,
    Manifest,
    Project,
    PushResult,
    SubtreeState,
    SubtreeStatus,
)


class SubtreeManager:
    """Manager class for subtree operations."""

    def __init__(self, workspace_path: Path, manifest: Manifest) -> None:
        """Initialize SubtreeManager.

        Args:
            workspace_path: Path to workspace root
            manifest: Parsed manifest object
        """
        self.workspace_path = workspace_path
        self.manifest = manifest
        self.subtree_state_dir = workspace_path / ".subrepo" / "subtrees"
        self.subtree_state_dir.mkdir(parents=True, exist_ok=True)
        self.file_operation_results: list[FileOperationResult] = []

    def sync_all_components(
        self,
        force: bool = False,
        continue_on_error: bool = False,
    ) -> dict[str, GitOperationResult]:
        """Sync all components with their upstream repositories.

        Args:
            force: Whether to stash local changes and force sync
            continue_on_error: Whether to continue syncing other components if one fails

        Returns:
            Dictionary mapping component paths to sync results

        Raises:
            WorkspaceError: If workspace has uncommitted changes (when force=False)
            GitOperationError: If sync operation fails
        """
        results: dict[str, GitOperationResult] = {}

        # Check for uncommitted changes (unless force mode)
        if not force:
            status_result = git_status(self.workspace_path, short=True)
            if status_result.stdout.strip():
                raise WorkspaceError(
                    "Cannot sync with uncommitted changes in workspace.\n"
                    "Options:\n"
                    "  1. Commit your changes: git add . && git commit\n"
                    "  2. Stash your changes: git stash\n"
                    "  3. Force sync: subrepo sync --force (will stash and reapply)"
                )

        # If force mode and there are changes, stash them
        stashed = False
        if force:
            status_result = git_status(self.workspace_path, short=True)
            if status_result.stdout.strip():
                subprocess.run(
                    ["git", "stash", "push", "-m", "subrepo sync --force"],
                    cwd=self.workspace_path,
                    check=True,
                    capture_output=True,
                )
                stashed = True

        try:
            # Sync each component
            for project in self.manifest.projects:
                try:
                    result = self._sync_component(project)
                    results[project.path] = result

                    if not result.success and not continue_on_error:
                        raise GitOperationError(
                            f"Failed to sync component {project.path}: {result.stderr}"
                        )
                except GitOperationError as e:
                    if not continue_on_error:
                        raise
                    # Store error result
                    results[project.path] = GitOperationResult(
                        success=False,
                        stdout="",
                        stderr=str(e),
                        exit_code=1,
                        duration=0.0,
                        command=[],
                    )

        finally:
            # Reapply stash if we stashed changes
            if stashed:
                subprocess.run(
                    ["git", "stash", "pop"],
                    cwd=self.workspace_path,
                    check=False,  # Don't fail if stash pop has conflicts
                    capture_output=True,
                )

        return results

    def _sync_component(self, project: Project) -> GitOperationResult:
        """Sync a single component.

        Args:
            project: Project to sync

        Returns:
            GitOperationResult from the sync operation
        """
        # Get remote URL
        remote = self.manifest.remotes[project.remote]
        repository_url = f"{remote.fetch}{project.name}"

        # Pull latest changes using git subtree pull
        result = git_subtree_pull(
            path=self.workspace_path,
            prefix=project.path,
            repository=repository_url,
            ref=project.revision,
            squash=True,
        )

        # Update subtree state and execute file operations if successful
        if result.success:
            self._save_subtree_state(project)

            # Execute copyfile operations
            project_dir = self.workspace_path / project.path
            if project.copyfiles:
                copyfile_results = execute_copyfile_operations(
                    project=project,
                    workspace_root=self.workspace_path,
                    project_dir=project_dir,
                )
                self.file_operation_results.extend(copyfile_results)

            # Execute linkfile operations
            if project.linkfiles:
                linkfile_results = execute_linkfile_operations(
                    project=project,
                    workspace_root=self.workspace_path,
                    project_dir=project_dir,
                )
                self.file_operation_results.extend(linkfile_results)

        return result

    def get_file_operation_summary(self) -> list[FileOperationResult]:
        """Get summary of all file operations executed during sync.

        Returns:
            List of FileOperationResult objects
        """
        return self.file_operation_results

    def detect_component_state(self, project: Project) -> SubtreeState:
        """Detect the current state of a component.

        Args:
            project: Project to check

        Returns:
            SubtreeState with current status
        """
        component_path = self.workspace_path / project.path

        # Check if component exists
        if not component_path.exists():
            return SubtreeState(
                project=project,
                status=SubtreeStatus.UNINITIALIZED,
            )

        # Check for uncommitted changes
        status_result = git_status(self.workspace_path, short=True)
        has_changes = False
        if status_result.success:
            # Check if any changes affect this component
            # Git status output format: "XY filename" where XY is status code
            for line in status_result.stdout.split("\n"):
                if not line.strip():
                    continue
                # Extract the filename (skip first 3 characters which are status codes)
                if len(line) >= 3:
                    filename = line[3:].strip()
                    # Check if the file is within the component path
                    # Git may show parent directory for untracked files (e.g., "?? lib/")
                    # So we check both: file is in component OR component is in file
                    if filename.startswith(project.path) or project.path.startswith(
                        filename.rstrip("/")
                    ):
                        has_changes = True
                        break

        if has_changes:
            return SubtreeState(
                project=project,
                status=SubtreeStatus.MODIFIED,
                has_local_changes=True,
            )

        # For now, assume up-to-date (full implementation would check against remote)
        return SubtreeState(
            project=project,
            status=SubtreeStatus.UP_TO_DATE,
            has_local_changes=False,
        )

    def detect_conflicts(self, project: Project) -> bool:
        """Detect if a component has conflicts.

        Args:
            project: Project to check

        Returns:
            True if conflicts detected, False otherwise
        """
        # Check git status for conflict markers
        status_result = git_status(self.workspace_path, short=True)

        if status_result.success:
            # Look for conflict indicators (UU, AA, DD, etc. in git status --short)
            for line in status_result.stdout.split("\n"):
                if line.startswith(("UU", "AA", "DD")) and project.path in line:
                    return True

        return False

    def push_single_component(
        self,
        project: Project,
        force: bool = False,
        dry_run: bool = False,
    ) -> PushResult:
        """Push a single component to its remote repository.

        Detects the current branch and pushes to a matching branch in the component's
        remote repository. When on a feature branch, creates/updates a branch with the
        same name. When on the default branch, pushes to the default branch.

        Args:
            project: Project to push
            force: Whether to force push (allows non-fast-forward)
            dry_run: If True, only simulate the push without actually pushing

        Returns:
            PushResult with status and action taken

        Raises:
            DetachedHeadError: If HEAD is detached
            NonFastForwardError: If push rejected due to non-fast-forward (when force=False)
            BranchProtectionError: If branch is protected
            RepositoryNotFoundError: If remote repository doesn't exist
            PushError: For other push failures
        """
        # Get branch information
        branch_info = create_branch_info(cwd=self.workspace_path)

        # Determine target branch
        target_branch = determine_target_branch(branch_info, project)

        # Get remote URL
        remote = self.manifest.remotes[project.remote]
        # Use push URL if available, otherwise use fetch URL
        remote_url = remote.push_url if remote.push_url else f"{remote.fetch}{project.name}"

        # If dry-run, just return a simulated result
        if dry_run:
            from .models import PushAction, PushStatus

            return PushResult(
                project_name=project.name,
                status=PushStatus.SUCCESS,
                action=PushAction.UPDATED,  # Assume update for dry-run
                branch_name=target_branch,
                error_message=None,
            )

        # Execute the push
        result = execute_git_push(
            component_name=project.name,
            component_path=Path(project.path),
            remote_url=remote_url,
            branch_name=target_branch,
            force=force,
            cwd=self.workspace_path,
        )

        return result

    def _save_subtree_state(self, project: Project) -> None:
        """Save subtree state to .subrepo/subtrees/<component>.json.

        Args:
            project: Project whose state to save
        """
        state = SubtreeState(
            project=project,
            last_sync_time=datetime.now(UTC),
            status=SubtreeStatus.UP_TO_DATE,
        )

        # Create safe filename from project path
        safe_name = project.path.replace("/", "_").replace("\\", "_")
        state_file = self.subtree_state_dir / f"{safe_name}.json"

        # Serialize state
        state_dict = {
            "project_name": project.name,
            "project_path": project.path,
            "last_sync_time": state.last_sync_time.isoformat() if state.last_sync_time else None,
            "status": state.status.value,
        }

        # Write atomically
        temp_file = state_file.with_suffix(".json.tmp")
        temp_file.write_text(json.dumps(state_dict, indent=2))
        temp_file.rename(state_file)

    def load_subtree_state(self, project: Project) -> SubtreeState | None:
        """Load subtree state from .subrepo/subtrees/<component>.json.

        Args:
            project: Project whose state to load

        Returns:
            SubtreeState if found, None otherwise
        """
        safe_name = project.path.replace("/", "_").replace("\\", "_")
        state_file = self.subtree_state_dir / f"{safe_name}.json"

        if not state_file.exists():
            return None

        try:
            state_dict = json.loads(state_file.read_text())

            last_sync_time = None
            if state_dict.get("last_sync_time"):
                last_sync_time = datetime.fromisoformat(state_dict["last_sync_time"])

            return SubtreeState(
                project=project,
                last_sync_time=last_sync_time,
                status=SubtreeStatus(state_dict.get("status", "uninitialized")),
            )
        except (json.JSONDecodeError, ValueError, KeyError):
            return None

    def push_component(
        self,
        project: Project,
        branch: str | None = None,
        force: bool = False,
        dry_run: bool = False,
    ) -> GitOperationResult:
        """Push local changes in a component back to upstream.

        Args:
            project: Project to push
            branch: Target branch (defaults to project.revision)
            force: Whether to force push
            dry_run: Show what would be pushed without actually pushing

        Returns:
            GitOperationResult from the push operation

        Raises:
            WorkspaceError: If component has uncommitted changes
            GitOperationError: If push fails
        """
        # Check for uncommitted changes in this component
        status_result = git_status(self.workspace_path, short=True)
        if status_result.success:
            for line in status_result.stdout.split("\n"):
                if line.strip() and project.path in line:
                    raise WorkspaceError(
                        f"Cannot push component {project.path} with uncommitted changes.\n"
                        "Commit your changes first: git add . && git commit"
                    )

        # Extract commits for this subtree
        commits = self.extract_subtree_commits(project)
        if not commits:
            # No commits to push - return success
            return GitOperationResult(
                success=True,
                stdout="No local commits to push\nComponent is up-to-date with upstream",
                stderr="",
                exit_code=0,
                duration=0.0,
                command=[],
            )

        if dry_run:
            # Show what would be pushed
            commit_list = "\n".join(f"  {c}" for c in commits)
            return GitOperationResult(
                success=True,
                stdout=f"Would push {len(commits)} commit(s):\n{commit_list}",
                stderr="",
                exit_code=0,
                duration=0.0,
                command=[],
            )

        # Get remote URL and target branch
        remote = self.manifest.remotes[project.remote]
        repository_url = f"{remote.fetch}{project.name}"
        target_branch = branch or project.revision

        # Use git subtree push to push the changes
        return git_subtree_push(
            path=self.workspace_path,
            prefix=project.path,
            repository=repository_url,
            ref=target_branch,
        )

    def extract_subtree_commits(self, project: Project) -> list[str]:
        """Extract commits affecting a specific subtree.

        Args:
            project: Project to extract commits for

        Returns:
            List of commit SHAs/messages affecting this subtree
        """
        try:
            # Use git log to find commits affecting this path
            result = git_log(
                path=self.workspace_path,
                paths=[project.path],
                oneline=True,
            )

            if not result.success or not result.stdout.strip():
                return []

            # Parse commit list (format: "sha message")
            return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]

        except Exception:
            return []

    def detect_upstream_divergence(self, project: Project) -> tuple[int, int]:
        """Detect if local and upstream have diverged.

        Args:
            project: Project to check

        Returns:
            Tuple of (commits_ahead, commits_behind)

        Raises:
            GitOperationError: If detection fails
        """
        try:
            # Get remote URL
            remote = self.manifest.remotes[project.remote]
            repository_url = f"{remote.fetch}{project.name}"

            # Fetch latest from remote (don't update working tree)
            git_fetch(self.workspace_path, repository_url, project.revision)

            # Count commits ahead (local commits not in upstream)
            # This is a simplified implementation - full implementation would use FETCH_HEAD
            ahead_result = git_rev_list(
                path=self.workspace_path,
                revision_range="FETCH_HEAD..HEAD",
                count=True,
            )
            commits_ahead = int(ahead_result.stdout.strip()) if ahead_result.success else 0

            # Count commits behind (upstream commits not in local)
            behind_result = git_rev_list(
                path=self.workspace_path,
                revision_range="HEAD..FETCH_HEAD",
                count=True,
            )
            commits_behind = int(behind_result.stdout.strip()) if behind_result.success else 0

            return (commits_ahead, commits_behind)

        except Exception as e:
            raise GitOperationError(f"Failed to detect upstream divergence: {e}") from e

    def pull_component(
        self,
        project: Project,
        branch: str | None = None,
        squash: bool = True,
    ) -> GitOperationResult:
        """Pull upstream changes for a specific component.

        Args:
            project: Project to pull
            branch: Branch to pull from (defaults to project.revision)
            squash: Whether to squash upstream commits (default True)

        Returns:
            GitOperationResult from the pull operation

        Raises:
            WorkspaceError: If component has uncommitted changes
            GitOperationError: If pull fails
        """
        # Check for uncommitted changes in this component
        status_result = git_status(self.workspace_path, short=True)
        if status_result.success:
            for line in status_result.stdout.split("\n"):
                if line.strip() and project.path in line:
                    raise WorkspaceError(
                        f"Cannot pull component {project.path} with uncommitted changes.\n"
                        "Commit or stash your changes first: git add . && git commit"
                    )

        # Get remote URL and target branch
        remote = self.manifest.remotes[project.remote]
        repository_url = f"{remote.fetch}{project.name}"
        target_branch = branch or project.revision

        # Pull updates using git subtree pull
        result = git_subtree_pull(
            path=self.workspace_path,
            prefix=project.path,
            repository=repository_url,
            ref=target_branch,
            squash=squash,
        )

        # Update subtree state if successful
        if result.success:
            self._save_subtree_state(project)

        return result


def sync_all_components(
    workspace_path: Path,
    manifest: Manifest,
    force: bool = False,
    continue_on_error: bool = False,
) -> dict[str, GitOperationResult]:
    """Convenience function to sync all components.

    Args:
        workspace_path: Path to workspace root
        manifest: Parsed manifest object
        force: Whether to force sync with uncommitted changes
        continue_on_error: Whether to continue on errors

    Returns:
        Dictionary mapping component paths to sync results
    """
    manager = SubtreeManager(workspace_path, manifest)
    return manager.sync_all_components(force=force, continue_on_error=continue_on_error)


def get_component_status(workspace_path: Path, project: Project) -> SubtreeState:
    """Get status for a specific component.

    Args:
        workspace_path: Path to workspace root
        project: Project to get status for

    Returns:
        SubtreeState with current component status

    Raises:
        WorkspaceError: If workspace is not initialized
        GitOperationError: If git commands fail
    """
    # Create a minimal manifest with a dummy remote for the project
    from .models import Remote

    dummy_remote = Remote(
        name=project.remote,
        fetch="https://example.com/",  # Dummy URL, not used for status checks
    )
    manifest = Manifest(
        remotes={project.remote: dummy_remote},
        projects=[project],
        default_remote=project.remote,
        default_revision=project.revision,
    )
    manager = SubtreeManager(workspace_path, manifest)
    return manager.detect_component_state(project)


def get_all_component_status(workspace_path: Path, manifest: Manifest) -> list[SubtreeState]:
    """Get status for all components in the workspace.

    Args:
        workspace_path: Path to workspace root
        manifest: Parsed manifest object

    Returns:
        List of SubtreeState objects, one for each component

    Raises:
        WorkspaceError: If workspace is not initialized
        GitOperationError: If git commands fail
    """
    manager = SubtreeManager(workspace_path, manifest)
    statuses: list[SubtreeState] = []

    for project in manifest.projects:
        try:
            state = manager.detect_component_state(project)
            statuses.append(state)
        except Exception:
            # If we can't detect state for a component, mark it as ERROR
            statuses.append(
                SubtreeState(
                    project=project,
                    status=SubtreeStatus.ERROR,
                    has_local_changes=False,
                    local_commits=0,
                    upstream_commits=0,
                )
            )

    return statuses
