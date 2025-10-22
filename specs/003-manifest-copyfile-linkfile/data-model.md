# Data Model: Manifest Copyfile and Linkfile Support

**Feature**: 003-manifest-copyfile-linkfile
**Date**: 2025-10-21

## Overview

This document defines the data structures for copyfile and linkfile support, extending the existing manifest data model.

## Entity Definitions

### Copyfile

Represents a file copy directive that specifies copying a file from a project directory to the workspace root.

**Attributes**:
- `src: str` - Source path relative to project directory (e.g., "docs/README.md")
- `dest: str` - Destination path relative to workspace root (e.g., "README.md")

**Validation Rules**:
- Both `src` and `dest` MUST be non-empty strings
- `src` MUST NOT contain ".." path components (prevent directory traversal)
- `src` MUST NOT start with "/" (must be relative)
- `dest` MUST NOT contain ".." path components
- `dest` MUST NOT escape workspace root when resolved
- Intermediate path components in `dest` MUST NOT be symlinks (security)

**Implementation**:
```python
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
```

**State Transitions**: Immutable (no state changes)

**Relationships**:
- Belongs to exactly one `Project`
- Many `Copyfile` instances can belong to one `Project`

---

### Linkfile

Represents a symbolic link directive that specifies creating a symlink from the workspace root to a file or directory in a project.

**Attributes**:
- `src: str` - Source path relative to project directory (e.g., "scripts/build.sh")
- `dest: str` - Destination path relative to workspace root where symlink will be created (e.g., "build.sh")

**Validation Rules**:
- Both `src` and `dest` MUST be non-empty strings
- `src` MUST NOT contain ".." path components
- `src` MUST NOT start with "/"
- `dest` MUST NOT contain ".." path components
- `dest` MUST NOT escape workspace root when resolved
- Intermediate path components in `dest` MUST NOT be symlinks (security)
- `src` CAN point to either a file or directory

**Implementation**:
```python
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
```

**State Transitions**: Immutable (no state changes)

**Relationships**:
- Belongs to exactly one `Project`
- Many `Linkfile` instances can belong to one `Project`

---

### Project (Modified)

**New Attributes**:
- `copyfiles: list[Copyfile]` - List of file copy directives for this project (default: empty list)
- `linkfiles: list[Linkfile]` - List of symlink directives for this project (default: empty list)

**Modified Validation Rules**:
- Existing validation rules remain unchanged
- NEW: All `copyfile` and `linkfile` dest paths MUST be unique across ALL projects in the manifest
- NEW: Dest path conflicts MUST be detected during manifest validation and cause immediate failure

**Implementation Changes**:
```python
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
        copyfiles: List of file copy directives (NEW)
        linkfiles: List of symlink directives (NEW)
    """
    name: str
    path: str
    remote: str
    revision: str = "main"
    upstream: str | None = None
    clone_depth: int | None = None
    copyfiles: list[Copyfile] = field(default_factory=list)  # NEW
    linkfiles: list[Linkfile] = field(default_factory=list)  # NEW
```

---

### Manifest (Modified)

**Modified Validation Rules**:
- Existing validation rules remain unchanged
- NEW: MUST validate that all `copyfile` and `linkfile` dest paths are unique across all projects
- NEW: MUST fail validation if any dest path conflicts exist

**Implementation Changes**:
```python
def validate(self) -> list[str]:
    """Validate manifest and return list of validation errors.

    Returns:
        List of validation error messages (empty if valid)
    """
    errors: list[str] = []

    # Existing validation...

    # NEW: Validate copyfile/linkfile dest path uniqueness
    dest_paths: dict[str, str] = {}  # dest -> project name
    for project in self.projects:
        for copyfile in project.copyfiles:
            if copyfile.dest in dest_paths:
                errors.append(
                    f"Duplicate copyfile destination '{copyfile.dest}': "
                    f"conflicts between projects '{project.name}' and '{dest_paths[copyfile.dest]}'"
                )
            else:
                dest_paths[copyfile.dest] = project.name

        for linkfile in project.linkfiles:
            if linkfile.dest in dest_paths:
                errors.append(
                    f"Duplicate linkfile destination '{linkfile.dest}': "
                    f"conflicts between projects '{project.name}' and '{dest_paths[linkfile.dest]}'"
                )
            else:
                dest_paths[linkfile.dest] = project.name

    return errors
```

---

### FileOperationResult (New)

Represents the result of executing a copyfile or linkfile operation.

**Attributes**:
- `project_name: str` - Name of the project this operation belongs to
- `operation_type: str` - Either "copyfile" or "linkfile"
- `src: str` - Source path
- `dest: str` - Destination path
- `success: bool` - Whether operation succeeded
- `error_message: str | None` - Error message if operation failed
- `fallback_used: bool` - Whether fallback-to-copy was used for linkfile (default: False)

**Implementation**:
```python
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
```

---

### FileOperationSummary (New)

Aggregates results from multiple file operations during sync.

**Attributes**:
- `results: list[FileOperationResult]` - List of individual operation results
- `total_count: int` - Total operations attempted (computed property)
- `success_count: int` - Number of successful operations (computed property)
- `failed_count: int` - Number of failed operations (computed property)
- `fallback_count: int` - Number of linkfile operations that fell back to copy (computed property)

**Implementation**:
```python
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
            lines.append("\\nFailures:")
            for result in self.results:
                if not result.success:
                    lines.append(
                        f"  - {result.project_name} ({result.operation_type}): "
                        f"{result.src} → {result.dest}: {result.error_message}"
                    )

        return "\\n".join(lines)
```

---

## Entity Relationship Diagram

```
Manifest
  │
  ├──> Remote (1..n)
  │
  └──> Project (1..n)
         ├──> Copyfile (0..n) [NEW]
         └──> Linkfile (0..n) [NEW]

FileOperationSummary (used during sync)
  └──> FileOperationResult (0..n)
```

## Data Flow

### Manifest Parse Flow
1. Parse XML manifest
2. For each `<project>` element:
   - Parse project attributes (existing)
   - Find all `<copyfile>` child elements → create `Copyfile` instances
   - Find all `<linkfile>` child elements → create `Linkfile` instances
   - Add copyfiles/linkfiles lists to Project
3. Validate manifest (including dest path uniqueness check)
4. Return Manifest object or raise validation error

### Sync Flow with File Operations
1. Load and validate manifest
2. For each project:
   - Perform git subtree sync (existing)
   - Execute copyfile operations:
     - Validate src exists in project directory
     - Validate dest security (no escape, no symlinks in path)
     - Copy file with `shutil.copy2()` (preserve permissions)
     - Create `FileOperationResult`
   - Execute linkfile operations:
     - Validate dest security
     - Try to create symlink with `os.symlink()`
     - On failure (e.g., Windows without support):
       - Fall back to `shutil.copy2()`
       - Set `fallback_used=True` in result
       - Log warning
     - Create `FileOperationResult`
3. Aggregate results into `FileOperationSummary`
4. Display summary to user
5. Return non-zero exit code if any operations failed

## Validation Chain

```
XML Parse → Copyfile/Linkfile __post_init__
              ↓
         Project validation
              ↓
         Manifest.validate()
              ↓
         [Sync begins]
              ↓
         Runtime path security validation
              ↓
         File operation execution
              ↓
         Result collection
```

## Storage Format

### XML Manifest Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="github" fetch="https://github.com/" />
  <default remote="github" revision="main" />

  <project name="org/core" path="components/core">
    <copyfile src="docs/README.md" dest="README.md" />
    <copyfile src="config/Makefile" dest="Makefile" />
    <linkfile src="scripts/build.sh" dest="build.sh" />
  </project>

  <project name="org/docs" path="documentation">
    <linkfile src="." dest="docs" />
  </project>
</manifest>
```

### Runtime State (No Persistent Storage)

File operations are stateless and executed fresh on each sync. No persistent tracking of copyfile/linkfile state is maintained.
