# Data Model: Feature Branch Push Synchronization

**Feature**: 002-push-feature-branches
**Date**: 2025-10-18

## Overview

This document defines the data structures and git workflow for branch-aware component pushing. All models use Python dataclasses with full type annotations for type safety.

## Core Data Structures

### PushResult (New)

Represents the outcome of a single component push operation.

```python
from dataclasses import dataclass
from enum import Enum

class PushStatus(Enum):
    """Status of a push operation."""
    SUCCESS = "success"
    FAILED = "failed"

class PushAction(Enum):
    """Action taken during push."""
    CREATED = "created"      # New branch created
    UPDATED = "updated"      # Existing branch updated
    SKIPPED = "skipped"      # Push skipped due to error

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
```

**Validation Rules**:
- Failed status requires error_message
- Success status must not have error_message
- project_name and branch_name cannot be empty
- action must be SKIPPED if status is FAILED

**Usage**:
```python
# Successful push that created a new branch
result = PushResult(
    project_name="platform/core",
    status=PushStatus.SUCCESS,
    action=PushAction.CREATED,
    branch_name="002-push-feature-branches"
)

# Failed push with error details
result = PushResult(
    project_name="platform/auth",
    status=PushStatus.FAILED,
    action=PushAction.SKIPPED,
    branch_name="002-push-feature-branches",
    error_message="Remote repository does not exist"
)
```

---

### BranchInfo (New)

Represents branch metadata for push operations.

```python
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
```

**State Invariants**:
- If `is_default_branch` is True, `current_branch` must equal `default_branch`
- `target_branch` equals `current_branch` when not on default branch (feature branch mode)
- `target_branch` equals `default_branch` when on default branch (backward compatible mode)

---

## Exception Hierarchy (New)

Extended exception types for branch-aware push operations:

```python
class SubrepoError(Exception):
    """Base exception for all subrepo errors."""
    pass

class GitError(SubrepoError):
    """Base exception for git operation errors."""
    pass

class BranchError(GitError):
    """Base exception for branch-related errors."""
    pass

class DetachedHeadError(BranchError):
    """Raised when attempting to push from detached HEAD state."""
    pass

class PushError(GitError):
    """Base exception for push operation errors."""
    pass

class NonFastForwardError(PushError):
    """Raised when push would not be fast-forward."""
    def __init__(self, branch: str, component: str):
        super().__init__(
            f"Push to {component}:{branch} rejected (non-fast-forward). "
            f"Remote branch has diverged from local. Use --force to override."
        )
        self.branch = branch
        self.component = component

class BranchProtectionError(PushError):
    """Raised when pushing to a protected branch."""
    def __init__(self, branch: str, component: str):
        super().__init__(
            f"Branch '{branch}' is protected in {component}. "
            f"Contact repository administrator to modify protection rules."
        )
        self.branch = branch
        self.component = component

class RepositoryNotFoundError(PushError):
    """Raised when remote repository does not exist."""
    def __init__(self, repository: str):
        super().__init__(
            f"Remote repository '{repository}' does not exist. "
            f"Create the repository before pushing."
        )
        self.repository = repository
```

**Exception Design Principles**:
- Specific exception types for each error category
- Clear, actionable error messages
- Include context (branch name, component name)
- Suggest remediation steps where appropriate

---

## Git Workflow State Machine

The push operation follows this state machine:

```
┌─────────────────┐
│ Detect Current  │
│ Branch          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐        Yes    ┌──────────────────┐
│ Is Detached     │───────────────▶│ Raise            │
│ HEAD?           │                │ DetachedHeadError│
└────────┬────────┘                └──────────────────┘
         │ No
         ▼
┌─────────────────┐
│ Load Manifest   │
│ Get Project     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Determine       │
│ Default Branch  │ (manifest → git fallback)
└────────┬────────┘
         │
         ▼
┌─────────────────┐        Yes    ┌──────────────────┐
│ Current ==      │───────────────▶│ Push to Default  │
│ Default?        │                │ (existing flow)  │
└────────┬────────┘                └──────────────────┘
         │ No
         ▼
┌─────────────────┐
│ Dry Run Push    │
│ to Feature      │
│ Branch          │
└────────┬────────┘
         │
         ├──────▶ Success ──────▶ Actual Push ──────▶ Return SUCCESS
         │
         ├──────▶ Non-Fast-Forward ──▶ force? ───Yes─▶ Force Push
         │                                    │
         │                                    └─No──▶ Raise NonFastForwardError
         │
         ├──────▶ Protected Branch ─────────────────▶ Raise BranchProtectionError
         │
         └──────▶ Repo Not Found ───────────────────▶ Raise RepositoryNotFoundError
```

**State Transitions**:
1. **Detect** → DETACHED: Error state, cannot push
2. **Detect** → LOAD: Normal flow
3. **LOAD** → DETERMINE: Get default branch
4. **DETERMINE** → ON_DEFAULT: Use existing push logic
5. **DETERMINE** → ON_FEATURE: New branch-aware logic
6. **ON_FEATURE** → DRY_RUN: Test push viability
7. **DRY_RUN** → PUSH: Success path
8. **DRY_RUN** → FORCE_CHECK: Non-fast-forward detected
9. **FORCE_CHECK** → FORCE_PUSH: User provided --force
10. **FORCE_CHECK** → ERROR: User didn't provide --force
11. **DRY_RUN** → ERROR: Protected branch or missing repo

---

## Manifest Data Flow

```
manifest.xml
     │
     ▼
┌─────────────────┐
│ parse_manifest()│
│ (existing)      │
└────────┬────────┘
         │
         ▼
    Manifest object
    {remotes, projects, defaults}
         │
         ▼
┌──────────────────────────┐
│ get_project_by_path()    │
│ (existing)               │
└────────┬─────────────────┘
         │
         ▼
    Project object
    {name, path, remote, revision}
         │
         ▼
┌──────────────────────────┐
│ extract_default_branch() │
│ (new)                    │
└────────┬─────────────────┘
         │
         ├──────▶ is_commit_sha(revision)? ──Yes─▶ return None (fallback to git)
         │
         └──────▶ No ──────────────────────────────▶ return revision as branch name
```

**Data Transformations**:
1. XML string → Manifest object (existing parser)
2. Manifest + path → Project object (existing lookup)
3. Project.revision → branch name or None (new logic)
4. None → git detection (new fallback)
5. branch name → BranchInfo (new structure)

---

## Multi-Component Push Aggregation

When pushing multiple components, results are aggregated:

```python
@dataclass(frozen=True)
class MultiPushSummary:
    """Summary of multi-component push operation.

    Attributes:
        results: List of individual push results
        total_count: Total number of components attempted
        success_count: Number of successful pushes
        failed_count: Number of failed pushes
        created_count: Number of branches created
        updated_count: Number of branches updated
    """
    results: list[PushResult]

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.status == PushStatus.SUCCESS)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.status == PushStatus.FAILED)

    @property
    def created_count(self) -> int:
        return sum(1 for r in self.results if r.action == PushAction.CREATED)

    @property
    def updated_count(self) -> int:
        return sum(1 for r in self.results if r.action == PushAction.UPDATED)

    def format_summary(self) -> str:
        """Format a human-readable summary."""
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
```

**Aggregation Properties**:
- Computed properties for counts (no redundant storage)
- Immutable structure (frozen dataclass)
- Formatted output for CLI display
- Failures listed with error details

---

## Type Aliases and Constants

```python
from typing import TypeAlias

# Type aliases for clarity
ComponentName: TypeAlias = str
BranchName: TypeAlias = str
RemoteUrl: TypeAlias = str
ErrorMessage: TypeAlias = str

# Constants
DEFAULT_REMOTE_NAME = "origin"
SHA_PATTERN = r'^[0-9a-f]{40}$'
MAX_BRANCH_NAME_LENGTH = 255  # Git limitation

# Git command constants
GIT_SYMBOLIC_REF_HEAD = ["git", "symbolic-ref", "--short", "HEAD"]
GIT_SYMBOLIC_REF_DEFAULT = ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"]
```

---

## Data Validation Rules

### Branch Names
- Must not be empty
- Must not exceed 255 characters (git limit)
- Must not contain characters: `~`, `^`, `:`, `?`, `*`, `[`, `\`
- Must not start or end with `.` or `/`
- Must not contain `..` or `@{`
- Must not be `@` alone

### Project Names
- Validated by existing Project model
- Already enforced: non-empty, no leading/trailing slashes, no `..`

### Push Results
- Status and action must be consistent (FAILED → SKIPPED)
- Error message required if and only if status is FAILED
- All string fields must be non-empty except error_message

---

## Database/Storage

**None Required** - All state is transient:
- Branch information queried from git on demand
- Manifest parsed from XML file on demand
- Push results collected in memory and displayed
- No persistent storage of push history (git log serves this purpose)

**Constitution Compliance**: ✅ No database dependencies, maintains standard-library-only principle
