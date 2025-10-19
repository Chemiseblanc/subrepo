# Data Model: Git Subtree Repo Manager

**Feature**: Git Subtree Repo Manager
**Branch**: 001-git-subtree-repo
**Date**: 2025-10-18

## Overview

This document defines the data structures used in the subrepo tool. All entities are implemented as Python dataclasses with full type hints per constitution requirements.

## Core Entities

### Remote

Represents a named git remote repository base URL.

**Attributes**:
- `name: str` - Unique identifier for the remote (e.g., "origin", "github")
- `fetch: str` - Base URL for fetching repositories (e.g., "https://github.com/")
- `push_url: Optional[str]` - Optional separate URL for push operations (defaults to fetch URL)
- `review: Optional[str]` - Optional code review server URL (for repo compatibility, not used in MVP)

**Validation Rules**:
- `name` must be non-empty, alphanumeric with hyphens/underscores
- `fetch` must be valid URL or git-compatible path
- If `push_url` provided, must be valid URL or git-compatible path

**Example**:
```python
Remote(
    name="origin",
    fetch="https://github.com/",
    push_url=None,
    review=None
)
```

**XML Mapping**:
```xml
<remote name="origin" fetch="https://github.com/" />
```

---

### Project

Represents a component repository to be managed as a git subtree.

**Attributes**:
- `name: str` - Repository identifier, typically "org/repo" format
- `path: str` - Local filesystem path where subtree will be located
- `remote: str` - Reference to Remote.name defining the git remote
- `revision: str` - Branch, tag, or commit hash to track (default from manifest or "main")
- `upstream: Optional[str]` - Optional upstream branch for tracking (repo compatibility)
- `clone_depth: Optional[int]` - Shallow clone depth (future optimization)

**Validation Rules**:
- `name` must be non-empty
- `path` must be relative path, no leading/trailing slashes, no ".." components
- `remote` must reference an existing Remote.name in manifest
- `revision` must be valid git ref format
- `path` must be unique across all projects in manifest

**Derived Properties**:
- `full_url: str` - Computed from remote.fetch + name (e.g., "https://github.com/org/repo")

**Example**:
```python
Project(
    name="myorg/myrepo",
    path="components/myrepo",
    remote="origin",
    revision="main",
    upstream=None,
    clone_depth=None
)
```

**XML Mapping**:
```xml
<project name="myorg/myrepo" path="components/myrepo"
         remote="origin" revision="main" />
```

---

### Manifest

Represents the complete workspace configuration parsed from manifest XML.

**Attributes**:
- `remotes: Dict[str, Remote]` - Map of remote name to Remote objects
- `projects: List[Project]` - List of all project components
- `default_remote: Optional[str]` - Default remote name for projects (if not specified)
- `default_revision: Optional[str]` - Default revision for projects (if not specified)
- `notice: Optional[str]` - Optional copyright/notice text from manifest

**Validation Rules**:
- At least one remote must be defined
- At least one project must be defined
- All project.remote values must reference existing remotes
- All project.path values must be unique
- If default_remote specified, must reference existing remote

**Methods**:
- `get_project_by_name(name: str) -> Optional[Project]` - Find project by name
- `get_project_by_path(path: str) -> Optional[Project]` - Find project by path
- `validate() -> List[str]` - Return list of validation errors

**Example**:
```python
Manifest(
    remotes={
        "origin": Remote(name="origin", fetch="https://github.com/")
    },
    projects=[
        Project(name="org/repo1", path="lib/repo1", remote="origin", revision="main"),
        Project(name="org/repo2", path="lib/repo2", remote="origin", revision="v2.0")
    ],
    default_remote="origin",
    default_revision="main",
    notice=None
)
```

**XML Mapping**:
```xml
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <default remote="origin" revision="main" />
  <project name="org/repo1" path="lib/repo1" />
  <project name="org/repo2" path="lib/repo2" revision="v2.0" />
</manifest>
```

---

### SubtreeState

Represents the current state of a subtree component in the workspace.

**Attributes**:
- `project: Project` - Reference to the project definition
- `last_sync_commit: Optional[str]` - Last synced commit SHA from upstream
- `last_sync_time: Optional[datetime]` - Timestamp of last sync operation
- `local_commits: int` - Number of local commits not pushed upstream
- `upstream_commits: int` - Number of upstream commits not pulled locally
- `has_local_changes: bool` - Whether working directory has uncommitted changes
- `status: SubtreeStatus` - Current status enum

**Status Enum**:
```python
class SubtreeStatus(Enum):
    UP_TO_DATE = "up-to-date"      # In sync with upstream
    AHEAD = "ahead"                 # Local commits to push
    BEHIND = "behind"               # Upstream commits to pull
    DIVERGED = "diverged"           # Both ahead and behind
    MODIFIED = "modified"           # Local uncommitted changes
    UNINITIALIZED = "uninitialized" # Subtree not yet added
    ERROR = "error"                 # Unable to determine status
```

**Methods**:
- `needs_sync() -> bool` - Returns True if BEHIND or DIVERGED
- `can_push() -> bool` - Returns True if AHEAD or DIVERGED and no local changes
- `is_clean() -> bool` - Returns True if UP_TO_DATE and no local changes

**Example**:
```python
SubtreeState(
    project=project_obj,
    last_sync_commit="abc123def456...",
    last_sync_time=datetime(2025, 10, 18, 10, 30),
    local_commits=2,
    upstream_commits=0,
    has_local_changes=False,
    status=SubtreeStatus.AHEAD
)
```

---

### WorkspaceConfig

Represents the workspace configuration stored in .subrepo/config.json.

**Attributes**:
- `manifest_path: str` - Path or URL to the manifest file
- `manifest_hash: str` - SHA256 hash of manifest content (detect changes)
- `initialized_at: datetime` - When workspace was initialized
- `git_version: str` - Git version used for initialization
- `subrepo_version: str` - Subrepo tool version

**Methods**:
- `to_json() -> str` - Serialize to JSON
- `from_json(json_str: str) -> WorkspaceConfig` - Deserialize from JSON
- `manifest_changed(current_manifest: Manifest) -> bool` - Detect manifest modifications

**Example**:
```python
WorkspaceConfig(
    manifest_path="https://example.com/manifest.xml",
    manifest_hash="a1b2c3d4e5f6...",
    initialized_at=datetime(2025, 10, 18, 9, 0),
    git_version="2.43.0",
    subrepo_version="0.1.0"
)
```

**JSON Storage** (.subrepo/config.json):
```json
{
  "manifest_path": "https://example.com/manifest.xml",
  "manifest_hash": "a1b2c3d4e5f6...",
  "initialized_at": "2025-10-18T09:00:00Z",
  "git_version": "2.43.0",
  "subrepo_version": "0.1.0"
}
```

---

### GitOperationResult

Represents the result of a git command execution.

**Attributes**:
- `success: bool` - Whether command succeeded
- `stdout: str` - Standard output from command
- `stderr: str` - Standard error from command
- `exit_code: int` - Process exit code
- `duration: float` - Execution time in seconds
- `command: List[str]` - The git command that was executed

**Methods**:
- `raise_for_status() -> None` - Raise GitCommandError if not successful
- `get_output() -> str` - Return stdout if success, else stderr

**Example**:
```python
GitOperationResult(
    success=True,
    stdout="Successfully added subtree 'components/lib'",
    stderr="",
    exit_code=0,
    duration=2.34,
    command=["git", "subtree", "add", "--prefix=components/lib", "..."]
)
```

---

## Entity Relationships

```
Manifest
├── remotes: Dict[str, Remote]
│   └── Remote (name, fetch, push_url)
└── projects: List[Project]
    └── Project (name, path, remote, revision)
        └── remote → references Remote.name

WorkspaceConfig
└── manifest_path → references Manifest source

SubtreeState
└── project → references Project instance
```

## Data Validation

All entities implement validation at construction and modification:

1. **Type Safety**: Full type hints with mypy --strict compliance
2. **Value Validation**: Enforce constraints (non-empty strings, valid URLs, unique paths)
3. **Referential Integrity**: Ensure remote references exist in manifest
4. **Immutability**: Use frozen dataclasses where appropriate to prevent modification
5. **Serialization**: Provide to_dict/from_dict methods for JSON persistence

## State Transitions

### SubtreeStatus State Machine

```
                    init
                     ↓
              UNINITIALIZED
                     ↓ add subtree
              UP_TO_DATE ←→ MODIFIED (local changes)
                  ↓ ↑
         local commits │ sync
                  ↓    │
                AHEAD  │
                  ↓    │
             push succeeds
                  ↓
              UP_TO_DATE

              UP_TO_DATE
                  ↓
          upstream commits
                  ↓
               BEHIND
                  ↓ pull
              UP_TO_DATE

         AHEAD + upstream commits → DIVERGED
         DIVERGED + pull → UP_TO_DATE or MODIFIED
```

## Persistence Strategy

### Manifest Storage
- **Location**: `.subrepo/manifest.xml`
- **Format**: XML (copy of original manifest)
- **Updates**: On init, or when manifest URL changes

### Workspace Config
- **Location**: `.subrepo/config.json`
- **Format**: JSON
- **Updates**: On init, version changes

### Subtree State Cache
- **Location**: `.subrepo/subtrees/<component-name>.json`
- **Format**: JSON (SubtreeState serialized)
- **Updates**: After sync, push, pull operations

### Git Metadata
- **Location**: `.git/` (standard git repository)
- **Content**: Subtree merge commits, refs, objects
- **Management**: Via git commands, not direct manipulation

## Implementation Notes

1. **Dataclasses**: Use `@dataclass` decorator with frozen=True for immutable entities
2. **Type Hints**: All attributes fully typed, no `Any` types
3. **Validation**: Use `__post_init__` for validation in dataclasses
4. **Serialization**: Implement custom JSON encoder/decoder for datetime, enums
5. **File I/O**: Atomic writes using tempfile + rename pattern
6. **Error Handling**: ValidationError for constraint violations

## Example Usage

```python
from subrepo.models import Manifest, Remote, Project
from subrepo.manifest_parser import parse_manifest

# Parse manifest from XML
manifest = parse_manifest("manifest.xml")

# Access entities
for project in manifest.projects:
    remote = manifest.remotes[project.remote]
    full_url = f"{remote.fetch}{project.name}"
    print(f"Project: {project.name} at {full_url}")

# Validate
errors = manifest.validate()
if errors:
    raise ManifestValidationError(errors)
```
