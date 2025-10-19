"""Git command wrappers for subrepo.

This module provides wrapper functions for executing git commands via subprocess.
All git operations are isolated here for easier testing and maintenance.
"""

import subprocess
import time
from pathlib import Path

from .exceptions import (
    BranchProtectionError,
    DetachedHeadError,
    GitCommandError,
    NonFastForwardError,
    PushError,
    RepositoryNotFoundError,
)
from .models import BranchInfo, GitOperationResult, Project, PushAction, PushResult, PushStatus

__all__ = [
    "GitOperationResult",
    "run_git_command",
    "git_subtree_add",
    "git_subtree_pull",
    "git_subtree_push",
    "git_subtree_split",
    "git_fetch",
    "detect_current_branch",
    "detect_default_branch",
    "create_branch_info",
    "determine_target_branch",
    "execute_git_push",
]


def run_git_command(
    args: list[str],
    cwd: Path | None = None,
    check: bool = True,
    timeout: int = 300,
) -> GitOperationResult:
    """Execute a git command and return the result.

    Args:
        args: Git command arguments (e.g., ["status", "--short"])
        cwd: Working directory for command execution
        check: Whether to raise exception on failure
        timeout: Command timeout in seconds

    Returns:
        GitOperationResult with command output and status

    Raises:
        GitCommandError: If check=True and command fails
    """
    command = ["git", *args]
    start_time = time.time()

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,  # We handle errors ourselves
        )

        duration = time.time() - start_time
        success = result.returncode == 0

        git_result = GitOperationResult(
            success=success,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            duration=duration,
            command=command,
        )

        if check and not success:
            raise GitCommandError(
                f"Git command failed: {' '.join(command)}",
                command,
                result.returncode,
                result.stderr,
            )

        return git_result

    except subprocess.TimeoutExpired as e:
        duration = time.time() - start_time
        raise GitCommandError(
            f"Git command timed out after {timeout}s: {' '.join(command)}",
            command,
            -1,
            str(e),
        ) from e


def git_version() -> str:
    """Get git version string.

    Returns:
        Git version (e.g., "2.43.0")

    Raises:
        GitCommandError: If git is not available
    """
    result = run_git_command(["--version"])
    # Output format: "git version 2.43.0"
    version_str = result.stdout.strip()
    if version_str.startswith("git version "):
        return version_str[len("git version ") :]
    return version_str


def git_init(path: Path) -> GitOperationResult:
    """Initialize a new git repository.

    Args:
        path: Directory to initialize

    Returns:
        GitOperationResult

    Raises:
        GitCommandError: If initialization fails
    """
    return run_git_command(["init"], cwd=path)


def git_add(path: Path, files: list[str]) -> GitOperationResult:
    """Add files to git staging area.

    Args:
        path: Repository directory
        files: List of file paths to add

    Returns:
        GitOperationResult

    Raises:
        GitCommandError: If add fails
    """
    return run_git_command(["add", *files], cwd=path)


def git_commit(path: Path, message: str) -> GitOperationResult:
    """Create a git commit.

    Args:
        path: Repository directory
        message: Commit message

    Returns:
        GitOperationResult

    Raises:
        GitCommandError: If commit fails
    """
    return run_git_command(["commit", "-m", message], cwd=path)


def git_remote_add(path: Path, name: str, url: str) -> GitOperationResult:
    """Add a git remote.

    Args:
        path: Repository directory
        name: Remote name
        url: Remote URL

    Returns:
        GitOperationResult

    Raises:
        GitCommandError: If remote add fails
    """
    return run_git_command(["remote", "add", name, url], cwd=path)


def git_fetch(path: Path, remote: str, ref: str | None = None) -> GitOperationResult:
    """Fetch from a remote repository.

    Args:
        path: Repository directory
        remote: Remote name
        ref: Optional specific ref to fetch

    Returns:
        GitOperationResult

    Raises:
        GitCommandError: If fetch fails
    """
    args = ["fetch", remote]
    if ref:
        args.append(ref)
    return run_git_command(args, cwd=path)


def git_subtree_add(
    path: Path,
    prefix: str,
    repository: str,
    ref: str,
    squash: bool = True,
) -> GitOperationResult:
    """Add a git subtree.

    Args:
        path: Repository directory
        prefix: Subtree prefix path
        repository: Repository URL or remote name
        ref: Branch, tag, or commit to add
        squash: Whether to squash commits (default True)

    Returns:
        GitOperationResult

    Raises:
        GitCommandError: If subtree add fails
    """
    args = ["subtree", "add", f"--prefix={prefix}", repository, ref]
    if squash:
        args.append("--squash")
    return run_git_command(args, cwd=path, timeout=600)  # Longer timeout for subtree ops


def git_subtree_pull(
    path: Path,
    prefix: str,
    repository: str,
    ref: str,
    squash: bool = True,
) -> GitOperationResult:
    """Pull updates to a git subtree.

    Args:
        path: Repository directory
        prefix: Subtree prefix path
        repository: Repository URL or remote name
        ref: Branch, tag, or commit to pull
        squash: Whether to squash commits (default True)

    Returns:
        GitOperationResult

    Raises:
        GitCommandError: If subtree pull fails
    """
    args = ["subtree", "pull", f"--prefix={prefix}", repository, ref]
    if squash:
        args.append("--squash")
    return run_git_command(args, cwd=path, timeout=600)


def git_subtree_push(
    path: Path,
    prefix: str,
    repository: str,
    ref: str,
) -> GitOperationResult:
    """Push subtree changes to upstream.

    Args:
        path: Repository directory
        prefix: Subtree prefix path
        repository: Repository URL or remote name
        ref: Branch to push to

    Returns:
        GitOperationResult

    Raises:
        GitCommandError: If subtree push fails
    """
    args = ["subtree", "push", f"--prefix={prefix}", repository, ref]
    return run_git_command(args, cwd=path, timeout=600)


def git_subtree_split(
    path: Path,
    prefix: str,
    branch: str | None = None,
) -> GitOperationResult:
    """Split out a subtree into a separate branch.

    Args:
        path: Repository directory
        prefix: Subtree prefix path
        branch: Optional branch name to create

    Returns:
        GitOperationResult with commit SHA in stdout

    Raises:
        GitCommandError: If subtree split fails
    """
    args = ["subtree", "split", f"--prefix={prefix}"]
    if branch:
        args.extend(["--branch", branch])
    return run_git_command(args, cwd=path, timeout=600)


def git_status(path: Path, short: bool = False) -> GitOperationResult:
    """Get git status.

    Args:
        path: Repository directory
        short: Whether to use short format

    Returns:
        GitOperationResult with status output

    Raises:
        GitCommandError: If status check fails
    """
    args = ["status"]
    if short:
        args.append("--short")
    return run_git_command(args, cwd=path)


def git_rev_parse(path: Path, ref: str) -> str:
    """Get commit SHA for a ref.

    Args:
        path: Repository directory
        ref: Reference (branch, tag, HEAD, etc.)

    Returns:
        Commit SHA

    Raises:
        GitCommandError: If rev-parse fails
    """
    result = run_git_command(["rev-parse", ref], cwd=path)
    return result.stdout.strip()


def git_push(
    path: Path,
    repository: str,
    refspec: str,
    force: bool = False,
) -> GitOperationResult:
    """Push commits to a remote repository.

    Args:
        path: Repository directory
        repository: Repository URL or remote name
        refspec: Refspec to push (e.g., "main", "HEAD:refs/heads/main")
        force: Whether to force push

    Returns:
        GitOperationResult

    Raises:
        GitCommandError: If push fails
    """
    args = ["push", repository, refspec]
    if force:
        args.insert(1, "--force")
    return run_git_command(args, cwd=path, timeout=600)


def git_log(
    path: Path,
    revision_range: str | None = None,
    paths: list[str] | None = None,
    oneline: bool = False,
    limit: int | None = None,
) -> GitOperationResult:
    """Get git log.

    Args:
        path: Repository directory
        revision_range: Revision range (e.g., "HEAD~5..HEAD", "main..develop")
        paths: Optional list of paths to filter
        oneline: Whether to use oneline format
        limit: Maximum number of commits to show

    Returns:
        GitOperationResult with log output

    Raises:
        GitCommandError: If log fails
    """
    args = ["log"]
    if oneline:
        args.append("--oneline")
    if limit:
        args.extend(["-n", str(limit)])
    if revision_range:
        args.append(revision_range)
    if paths:
        args.append("--")
        args.extend(paths)
    return run_git_command(args, cwd=path)


def git_rev_list(
    path: Path,
    revision_range: str,
    count: bool = False,
) -> GitOperationResult:
    """List commits in a revision range.

    Args:
        path: Repository directory
        revision_range: Revision range (e.g., "HEAD~5..HEAD")
        count: Whether to count commits instead of listing

    Returns:
        GitOperationResult

    Raises:
        GitCommandError: If rev-list fails
    """
    args = ["rev-list", revision_range]
    if count:
        args.append("--count")
    return run_git_command(args, cwd=path)


def detect_current_branch(cwd: Path | None = None) -> str:
    """Detect the current git branch name.

    Args:
        cwd: Working directory for git command (default: current directory)

    Returns:
        Current branch name

    Raises:
        DetachedHeadError: If HEAD is detached (not on a branch)
        GitCommandError: If git command fails for other reasons
    """
    result = subprocess.run(
        ["git", "symbolic-ref", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
    )

    if result.returncode != 0:
        raise DetachedHeadError()

    return result.stdout.strip()


def detect_default_branch(cwd: Path | None = None) -> str:
    """Detect the default branch name from remote.

    Queries git for the symbolic ref of origin/HEAD to determine the default branch.
    Falls back to "main" if the symbolic ref cannot be determined.

    Args:
        cwd: Working directory for git command (default: current directory)

    Returns:
        Default branch name (e.g., "main", "master", "develop")
    """
    result = subprocess.run(
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
    )

    if result.returncode != 0:
        # Fallback to "main" if symbolic-ref fails
        return "main"

    # Output format: "origin/branch-name" -> extract "branch-name"
    branch_with_remote = result.stdout.strip()
    if branch_with_remote.startswith("origin/"):
        return branch_with_remote[len("origin/") :]

    return branch_with_remote


def create_branch_info(cwd: Path | None = None) -> BranchInfo:
    """Create BranchInfo object from git branch detection.

    Args:
        cwd: Working directory for git commands (default: current directory)

    Returns:
        BranchInfo with current, default, and target branch information

    Raises:
        DetachedHeadError: If HEAD is detached
    """
    current = detect_current_branch(cwd=cwd)
    default = detect_default_branch(cwd=cwd)

    is_default = current == default
    target = default if is_default else current

    return BranchInfo(
        current_branch=current,
        is_default_branch=is_default,
        default_branch=default,
        target_branch=target,
    )


def determine_target_branch(branch_info: BranchInfo, project: Project) -> str:
    """Determine which branch to push to based on current context.

    Args:
        branch_info: Current branch information
        project: Project being pushed

    Returns:
        Target branch name to push to
    """
    from .manifest_parser import extract_default_branch_from_project

    if branch_info.is_default_branch:
        # On default branch - use manifest default if available, otherwise git default
        manifest_default = extract_default_branch_from_project(project)
        return manifest_default if manifest_default else branch_info.default_branch
    # On feature branch - push to matching feature branch
    return branch_info.current_branch


def execute_git_push(
    component_name: str,
    component_path: Path,
    remote_url: str,
    branch_name: str,
    force: bool = False,
    cwd: Path | None = None,
) -> PushResult:
    """Execute git subtree push to remote repository.

    Args:
        component_name: Name of the component (for error messages)
        component_path: Local path to component subtree
        remote_url: Remote repository URL
        branch_name: Branch name to push to
        force: Whether to force push
        cwd: Working directory for git command (default: current directory)

    Returns:
        PushResult with status and action taken

    Raises:
        NonFastForwardError: If push rejected due to non-fast-forward
        BranchProtectionError: If branch is protected
        RepositoryNotFoundError: If remote repository doesn't exist
        PushError: For other push failures
    """
    # Build git subtree push command
    cmd = ["git", "subtree", "push", f"--prefix={component_path}", remote_url, branch_name]
    if force:
        cmd.insert(3, "--force")  # Insert after "push"

    # Execute push
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=cwd, timeout=600)

    if result.returncode != 0:
        stderr_lower = result.stderr.lower()

        # Check for specific error conditions
        if "protected branch" in stderr_lower or "permission denied" in stderr_lower:
            raise BranchProtectionError(branch=branch_name, component=component_name)

        if "repository" in stderr_lower and "not found" in stderr_lower:
            raise RepositoryNotFoundError(repository=remote_url)

        if "non-fast-forward" in stderr_lower or "[rejected]" in result.stderr:
            raise NonFastForwardError(branch=branch_name, component=component_name)

        # Generic push error
        raise PushError(f"Push failed for {component_name}: {result.stderr}")

    # Determine action based on output
    action = PushAction.CREATED if "[new branch]" in result.stderr else PushAction.UPDATED

    return PushResult(
        project_name=component_name,
        status=PushStatus.SUCCESS,
        action=action,
        branch_name=branch_name,
        error_message=None,
    )
