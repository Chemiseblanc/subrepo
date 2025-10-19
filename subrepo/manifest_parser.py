"""Manifest XML parsing and validation.

Provides functions to parse repo-style manifest XML files and convert them to
typed data structures with validation.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from .exceptions import ManifestError, ManifestValidationError
from .models import Manifest, Project, Remote

# Regular expression pattern for full git commit SHA (40 hexadecimal characters)
SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")


def is_commit_sha(revision: str) -> bool:
    """Check if revision string is a full git commit SHA.

    Args:
        revision: Revision string from manifest (branch name, tag, or SHA)

    Returns:
        True if revision is a 40-character hexadecimal SHA, False otherwise
    """
    return bool(SHA_PATTERN.match(revision))


def extract_default_branch_from_project(project: Project) -> str | None:
    """Extract default branch from manifest project, or None if revision is a SHA.

    Args:
        project: Project object from manifest

    Returns:
        Branch name if revision is not a SHA, None if revision is a commit SHA
    """
    if is_commit_sha(project.revision):
        return None  # Fall back to git detection
    return project.revision


def parse_manifest(manifest_path: Path) -> Manifest:
    """Parse a manifest XML file and return a Manifest object.

    Args:
        manifest_path: Path to the manifest XML file

    Returns:
        Parsed and validated Manifest object

    Raises:
        ManifestError: If file not found or XML parsing fails
        ManifestValidationError: If manifest fails validation rules
    """
    # Check file exists
    if not manifest_path.exists():
        raise ManifestError(f"Manifest file not found: {manifest_path}")

    # Parse XML
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ManifestError(f"Failed to parse manifest XML: {e}") from e
    except Exception as e:
        raise ManifestError(f"Error reading manifest file: {e}") from e

    # Verify root element
    if root.tag != "manifest":
        raise ManifestError(f"Expected <manifest> root element, got <{root.tag}>")

    # Parse remotes
    remotes: dict[str, Remote] = {}
    for remote_elem in root.findall("remote"):
        name = remote_elem.get("name")
        fetch = remote_elem.get("fetch")

        if not name:
            raise ManifestError("Remote element missing required 'name' attribute")
        if not fetch:
            raise ManifestError(f"Remote '{name}' missing required 'fetch' attribute")

        push_url = remote_elem.get("push")
        review = remote_elem.get("review")

        remotes[name] = Remote(
            name=name,
            fetch=fetch,
            push_url=push_url,
            review=review,
        )

    # Parse defaults
    default_remote = None
    default_revision = None
    default_elem = root.find("default")
    if default_elem is not None:
        default_remote = default_elem.get("remote")
        default_revision = default_elem.get("revision")

    # Parse projects
    projects: list[Project] = []
    for project_elem in root.findall("project"):
        name = project_elem.get("name")
        path = project_elem.get("path")

        if not name:
            raise ManifestError("Project element missing required 'name' attribute")
        if not path:
            raise ManifestError(f"Project '{name}' missing required 'path' attribute")

        # Use project-specific remote or default
        remote = project_elem.get("remote") or default_remote
        if not remote:
            raise ManifestError(f"Project '{name}' has no remote specified and no default remote")

        # Use project-specific revision or default
        revision = project_elem.get("revision") or default_revision or "main"

        # Parse optional attributes
        upstream = project_elem.get("upstream")
        clone_depth_str = project_elem.get("clone-depth")
        clone_depth = int(clone_depth_str) if clone_depth_str else None

        try:
            project = Project(
                name=name,
                path=path,
                remote=remote,
                revision=revision,
                upstream=upstream,
                clone_depth=clone_depth,
            )
            projects.append(project)
        except ValueError as e:
            # Convert ValueError from Project.__post_init__ to ManifestValidationError
            raise ManifestValidationError(str(e)) from e

    # Parse optional notice
    notice_elem = root.find("notice")
    notice = notice_elem.text if notice_elem is not None else None

    # Create manifest object
    try:
        manifest = Manifest(
            remotes=remotes,
            projects=projects,
            default_remote=default_remote,
            default_revision=default_revision,
            notice=notice,
        )
    except ValueError as e:
        # Convert ValueError from Manifest.__post_init__ to ManifestValidationError
        raise ManifestValidationError(str(e)) from e

    # Validate manifest
    validate_manifest(manifest)

    return manifest


def validate_manifest(manifest: Manifest) -> None:
    """Validate a manifest object according to specification rules.

    Args:
        manifest: Manifest object to validate

    Raises:
        ManifestValidationError: If validation fails
    """
    errors: list[str] = []

    # Rule: At least one remote must be defined
    if not manifest.remotes:
        errors.append("Manifest must define at least one remote")

    # Rule: At least one project must be defined
    if not manifest.projects:
        errors.append("Manifest must define at least one project")

    # Rule: All project remote references must exist
    for project in manifest.projects:
        if project.remote not in manifest.remotes:
            errors.append(
                f"Project '{project.name}' references non-existent remote '{project.remote}'"
            )

    # Rule: All project paths must be unique
    paths_seen = set()
    for project in manifest.projects:
        if project.path in paths_seen:
            errors.append(f"Duplicate project path: '{project.path}'")
        paths_seen.add(project.path)

    # Rule: Project paths must be relative (not absolute)
    for project in manifest.projects:
        if Path(project.path).is_absolute():
            errors.append(
                f"Project '{project.name}' has absolute path '{project.path}'. "
                "Paths must be relative."
            )

    # Rule: Project paths must not contain ".." components
    for project in manifest.projects:
        if ".." in Path(project.path).parts:
            errors.append(
                f"Project '{project.name}' path '{project.path}' contains '..' components. "
                "This is not allowed."
            )

    # Rule: If default_remote is specified, it must exist
    if manifest.default_remote and manifest.default_remote not in manifest.remotes:
        errors.append(f"Default remote '{manifest.default_remote}' not found in defined remotes")

    # Raise if any errors found
    if errors:
        error_msg = "Manifest validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ManifestValidationError(error_msg)
