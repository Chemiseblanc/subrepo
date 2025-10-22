"""File operations for copyfile and linkfile support.

Provides secure file copying and symlink creation with proper validation and
error handling.
"""

import shutil
from pathlib import Path

from .exceptions import FileOperationError, PathSecurityError
from .models import FileOperationResult, Project


def validate_path_security(
    src_path: str,
    dest_path: str,
    workspace_root: Path,
    project_dir: Path,
) -> None:
    """Validate that file operation paths are safe and won't escape workspace.

    Args:
        src_path: Source path (relative to project directory)
        dest_path: Destination path (relative to workspace root)
        workspace_root: Absolute path to workspace root
        project_dir: Absolute path to project directory

    Raises:
        PathSecurityError: If paths fail security validation
    """
    # Check for ".." components (already validated in model, but double-check)
    if ".." in src_path or ".." in dest_path:
        raise PathSecurityError(
            f"Paths cannot contain '..' components: src={src_path}, dest={dest_path}"
        )

    # Check for absolute paths (already validated in model, but double-check)
    if src_path.startswith("/") or dest_path.startswith("/"):
        raise PathSecurityError(f"Paths must be relative: src={src_path}, dest={dest_path}")

    # Resolve destination path and ensure it stays within workspace
    dest_absolute = (workspace_root / dest_path).resolve()
    workspace_absolute = workspace_root.resolve()

    try:
        dest_absolute.relative_to(workspace_absolute)
    except ValueError:
        raise PathSecurityError(
            f"Destination path would escape workspace root: {dest_path} "
            f"resolves to {dest_absolute}, outside {workspace_absolute}"
        ) from None


def copy_file(src: Path, dest: Path) -> None:
    """Copy a file, preserving permissions and metadata.

    Uses shutil.copy2() to preserve file metadata including permissions.
    Creates parent directories if they don't exist. Dereferences symlinks at source.

    Args:
        src: Source file path (must exist)
        dest: Destination file path (will be overwritten if exists)

    Raises:
        FileOperationError: If copy operation fails
    """
    # Verify source exists
    if not src.exists():
        raise FileOperationError(f"Copy source file not found: {src}")

    # Create parent directories if needed
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Copy file with metadata preservation
    try:
        shutil.copy2(src, dest, follow_symlinks=True)
    except OSError as e:
        raise FileOperationError(f"Failed to copy {src} to {dest}: {e}") from e


def create_symlink(target: Path, link: Path) -> FileOperationResult:
    """Create a symbolic link, with fallback to copy on failure.

    Creates parent directories if needed. On platforms that don't support symlinks
    (e.g., Windows without admin), falls back to copying the file/directory.

    Args:
        target: Target path (what the symlink points to)
        link: Link path (where to create the symlink)

    Returns:
        FileOperationResult with fallback_used=True if copy fallback was used

    Raises:
        FileOperationError: If both symlink and copy fallback fail
    """
    # Create parent directories if needed
    link.parent.mkdir(parents=True, exist_ok=True)

    # Try to create symlink
    try:
        link.symlink_to(target)
        return FileOperationResult(
            project_name="",  # Will be filled by caller
            operation_type="linkfile",
            src=str(target),
            dest=str(link),
            success=True,
            fallback_used=False,
        )
    except OSError as symlink_error:
        # Symlink failed, try copy fallback
        try:
            if target.is_dir():
                shutil.copytree(target, link, symlinks=False)
            else:
                shutil.copy2(target, link, follow_symlinks=True)

            return FileOperationResult(
                project_name="",  # Will be filled by caller
                operation_type="linkfile",
                src=str(target),
                dest=str(link),
                success=True,
                fallback_used=True,
            )
        except OSError as copy_error:
            raise FileOperationError(
                f"Failed to create symlink and copy fallback: "
                f"symlink error: {symlink_error}, copy error: {copy_error}"
            ) from copy_error


def execute_copyfile_operations(
    project: Project,
    workspace_root: Path,
    project_dir: Path,
) -> list[FileOperationResult]:
    """Execute all copyfile operations for a project.

    Args:
        project: Project with copyfile directives
        workspace_root: Absolute path to workspace root
        project_dir: Absolute path to project directory

    Returns:
        List of FileOperationResult objects (one per copyfile)
    """
    results: list[FileOperationResult] = []

    for copyfile in project.copyfiles:
        try:
            # Validate path security
            validate_path_security(
                src_path=copyfile.src,
                dest_path=copyfile.dest,
                workspace_root=workspace_root,
                project_dir=project_dir,
            )

            # Resolve absolute paths
            src_absolute = project_dir / copyfile.src
            dest_absolute = workspace_root / copyfile.dest

            # Execute copy
            copy_file(src_absolute, dest_absolute)

            results.append(
                FileOperationResult(
                    project_name=project.name,
                    operation_type="copyfile",
                    src=copyfile.src,
                    dest=copyfile.dest,
                    success=True,
                )
            )

        except (PathSecurityError, FileOperationError) as e:
            results.append(
                FileOperationResult(
                    project_name=project.name,
                    operation_type="copyfile",
                    src=copyfile.src,
                    dest=copyfile.dest,
                    success=False,
                    error_message=str(e),
                )
            )

    return results


def execute_linkfile_operations(
    project: Project,
    workspace_root: Path,
    project_dir: Path,
) -> list[FileOperationResult]:
    """Execute all linkfile operations for a project.

    Args:
        project: Project with linkfile directives
        workspace_root: Absolute path to workspace root
        project_dir: Absolute path to project directory

    Returns:
        List of FileOperationResult objects (one per linkfile)
    """
    results: list[FileOperationResult] = []

    for linkfile in project.linkfiles:
        try:
            # Validate path security
            validate_path_security(
                src_path=linkfile.src,
                dest_path=linkfile.dest,
                workspace_root=workspace_root,
                project_dir=project_dir,
            )

            # Resolve absolute paths
            # For linkfile: src is in project, dest is in workspace
            # The symlink at dest points to src in project
            src_absolute = project_dir / linkfile.src
            dest_absolute = workspace_root / linkfile.dest

            # Execute symlink creation (with fallback)
            result = create_symlink(src_absolute, dest_absolute)

            # Update project name in result
            results.append(
                FileOperationResult(
                    project_name=project.name,
                    operation_type=result.operation_type,
                    src=linkfile.src,
                    dest=linkfile.dest,
                    success=result.success,
                    error_message=result.error_message,
                    fallback_used=result.fallback_used,
                )
            )

        except (PathSecurityError, FileOperationError) as e:
            results.append(
                FileOperationResult(
                    project_name=project.name,
                    operation_type="linkfile",
                    src=linkfile.src,
                    dest=linkfile.dest,
                    success=False,
                    error_message=str(e),
                )
            )

    return results
