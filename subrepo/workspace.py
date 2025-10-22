"""Workspace initialization and management.

Provides functions to initialize subrepo workspaces and manage workspace configuration.
"""

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from .exceptions import GitOperationError, WorkspaceError
from .git_commands import GitOperationResult
from .models import Manifest, WorkspaceConfig


def init_workspace(
    workspace_path: Path,
    manifest: Manifest,
    manifest_source: str,
) -> None:
    """Initialize a new subrepo workspace.

    Args:
        workspace_path: Path to workspace directory (must be empty or not exist)
        manifest: Parsed manifest object
        manifest_source: Original path/URL to manifest file

    Raises:
        WorkspaceError: If workspace cannot be initialized
        GitOperationError: If git operations fail
    """
    # Ensure workspace directory exists
    workspace_path.mkdir(parents=True, exist_ok=True)

    # Resolve manifest path for comparison (only if it exists)
    manifest_path = Path(manifest_source)
    if manifest_path.exists():
        manifest_path_resolved = manifest_path.resolve()
    else:
        # If manifest doesn't exist (e.g., URL), use absolute path
        manifest_path_resolved = manifest_path.absolute()

    # Check directory is empty (allow .git and manifest file)
    existing_files = list(workspace_path.iterdir())
    if existing_files:
        # Filter out allowed files
        non_init_files = [
            f for f in existing_files if f.name != ".git" and f.resolve() != manifest_path_resolved
        ]
        if non_init_files:
            raise WorkspaceError(
                f"Directory is not empty: {workspace_path}\n"
                f"Contains {len(non_init_files)} file(s). "
                "Use an empty directory or clean the current directory."
            )

    # Create git repository
    create_git_repo(workspace_path)

    # Create .subrepo metadata directory
    subrepo_dir = workspace_path / ".subrepo"
    subrepo_dir.mkdir(exist_ok=True)

    # Save manifest to .subrepo/manifest.xml
    # (For now, we'll save a placeholder - full manifest saving would serialize back to XML)
    manifest_copy_path = subrepo_dir / "manifest.xml"
    manifest_copy_path.write_text(f"<!-- Manifest from: {manifest_source} -->\n")

    # Create workspace config
    manifest_hash = _compute_manifest_hash(manifest)
    git_version = _get_git_version()

    config = WorkspaceConfig(
        manifest_path=manifest_source,
        manifest_hash=manifest_hash,
        initialized_at=datetime.now(UTC),
        git_version=git_version,
        subrepo_version="0.1.0",
    )

    # Save config to .subrepo/config.json
    save_workspace_config(workspace_path, config)

    # Create subtrees directory
    (subrepo_dir / "subtrees").mkdir(exist_ok=True)


def create_git_repo(repo_path: Path) -> GitOperationResult:
    """Initialize a git repository at the specified path.

    Args:
        repo_path: Path where git repository should be created

    Returns:
        GitOperationResult with command execution details

    Raises:
        GitOperationError: If git init fails
    """
    result = subprocess.run(
        ["git", "init"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    git_result = GitOperationResult(
        success=result.returncode == 0,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.returncode,
        duration=0.0,  # Not tracking duration for init
        command=["git", "init"],
    )

    if not git_result.success:
        raise GitOperationError(f"Failed to initialize git repository: {git_result.stderr}")

    # Create initial commit so we have a base for subtree operations
    _create_initial_commit(repo_path)

    return git_result


def _create_initial_commit(repo_path: Path) -> None:
    """Create an initial commit in the repository.

    Args:
        repo_path: Path to git repository
    """
    # Configure git user for this repo (required for commit)
    subprocess.run(
        ["git", "config", "user.name", "Subrepo"],
        cwd=repo_path,
        check=False,  # Don't fail if already configured
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "subrepo@local"],
        cwd=repo_path,
        check=False,
        capture_output=True,
    )

    # Create a README file
    readme_path = repo_path / "README.md"
    readme_path.write_text("# Subrepo Workspace\n\nInitialized by subrepo tool.\n")

    # Stage and commit
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )


def save_workspace_config(workspace_path: Path, config: WorkspaceConfig) -> None:
    """Save workspace configuration to .subrepo/config.json.

    Args:
        workspace_path: Path to workspace directory
        config: WorkspaceConfig object to save
    """
    config_path = workspace_path / ".subrepo" / "config.json"

    # Convert config to dict for JSON serialization
    config_dict = {
        "manifest_path": config.manifest_path,
        "manifest_hash": config.manifest_hash,
        "initialized_at": config.initialized_at.isoformat(),
        "git_version": config.git_version,
        "subrepo_version": config.subrepo_version,
    }

    # Write atomically using temp file + rename
    temp_path = config_path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(config_dict, indent=2))
    temp_path.rename(config_path)


def load_workspace_config(workspace_path: Path) -> WorkspaceConfig:
    """Load workspace configuration from .subrepo/config.json.

    Args:
        workspace_path: Path to workspace directory

    Returns:
        WorkspaceConfig object

    Raises:
        WorkspaceError: If config file not found or invalid
    """
    config_path = workspace_path / ".subrepo" / "config.json"

    if not config_path.exists():
        raise WorkspaceError(
            f"Not a subrepo workspace: {workspace_path}\nMissing .subrepo/config.json file."
        )

    try:
        config_dict = json.loads(config_path.read_text())

        return WorkspaceConfig(
            manifest_path=config_dict["manifest_path"],
            manifest_hash=config_dict["manifest_hash"],
            initialized_at=datetime.fromisoformat(config_dict["initialized_at"]),
            git_version=config_dict["git_version"],
            subrepo_version=config_dict["subrepo_version"],
        )
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        raise WorkspaceError(f"Invalid workspace config file: {e}") from e


def _compute_manifest_hash(manifest: Manifest) -> str:
    """Compute SHA256 hash of manifest for change detection.

    Args:
        manifest: Manifest object

    Returns:
        Hex-encoded SHA256 hash
    """
    # Create a stable string representation of the manifest
    manifest_str = (
        f"remotes={sorted(manifest.remotes.keys())}"
        f"projects={[(p.name, p.path, p.remote, p.revision) for p in manifest.projects]}"
        f"default_remote={manifest.default_remote}"
        f"default_revision={manifest.default_revision}"
    )

    return hashlib.sha256(manifest_str.encode()).hexdigest()


def _get_git_version() -> str:
    """Get the installed git version.

    Returns:
        Git version string (e.g., "2.43.0")
    """
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Output is like "git version 2.43.0"
        version_str = result.stdout.strip()
        if version_str.startswith("git version "):
            return version_str.replace("git version ", "")
        return version_str
    except Exception:
        return "unknown"
