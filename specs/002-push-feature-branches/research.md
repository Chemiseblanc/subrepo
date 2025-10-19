# Technical Research: Feature Branch Push Synchronization

**Feature**: 002-push-feature-branches
**Date**: 2025-10-18
**Purpose**: Document technical decisions and research findings for implementing branch-aware component pushing

## Research Questions Resolved

### 1. Git Branch Detection Methods

**Question**: How to reliably detect the current branch name and default branch in git repositories?

**Decision**: Use `git symbolic-ref` for current branch, `git symbolic-ref refs/remotes/origin/HEAD` for default branch detection

**Rationale**:
- `git symbolic-ref HEAD` returns full ref name (refs/heads/branch-name) which is unambiguous
- More reliable than parsing `git branch` output (which is porcelain, subject to format changes)
- Handles detached HEAD state explicitly (raises error, as expected)
- Standard approach used by git-aware tools

**Implementation**:
```python
# Current branch
result = subprocess.run(
    ["git", "symbolic-ref", "--short", "HEAD"],
    capture_output=True, text=True, check=False
)
if result.returncode != 0:
    raise DetachedHeadError("Cannot push from detached HEAD")
current_branch = result.stdout.strip()

# Default branch (from remote)
result = subprocess.run(
    ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
    capture_output=True, text=True, check=False
)
default_branch = result.stdout.strip().replace("origin/", "")
```

**Alternatives Considered**:
- `git branch --show-current`: Simpler but requires Git 2.22+ (June 2019)
- `git rev-parse --abbrev-ref HEAD`: Similar to symbolic-ref but less explicit about failure modes
- Parsing `.git/HEAD` file directly: Too implementation-dependent, breaks with worktrees

**References**:
- Git documentation: https://git-scm.com/docs/git-symbolic-ref
- Stack Overflow canonical answer on branch detection

---

### 2. Non-Fast-Forward Detection

**Question**: How to detect when a push would require force (non-fast-forward scenario)?

**Decision**: Use `git push --dry-run` with stderr parsing to detect rejection before actual push

**Rationale**:
- Dry-run allows detection without side effects
- Git's rejection message is consistent: `[rejected]` and `non-fast-forward`
- Prevents accidental data loss from automatic force pushes
- Aligns with constitution principle of minimal complexity (no custom git graph analysis)

**Implementation**:
```python
result = subprocess.run(
    ["git", "push", "--dry-run", remote_url, f"{local_branch}:{remote_branch}"],
    capture_output=True, text=True, check=False
)
if result.returncode != 0:
    if "non-fast-forward" in result.stderr or "[rejected]" in result.stderr:
        raise NonFastForwardError(
            f"Branch {remote_branch} has diverged. Use --force to push"
        )
    elif "does not exist" in result.stderr:
        raise RepositoryNotFoundError(f"Remote repository {remote_url} not found")
    else:
        raise PushError(f"Push failed: {result.stderr}")
```

**Alternatives Considered**:
- `git push --force-with-lease`: Safer than --force but still automatic, violates requirement for explicit user action
- `git rev-list --count origin/branch..HEAD`: Requires fetch first, adds complexity
- Custom merge-base analysis: Overengineering, git already provides this check

---

### 3. Protected Branch Detection

**Question**: How to detect protected branch patterns before attempting push?

**Decision**: Rely on remote's push rejection and parse error message for protected branch indicators

**Rationale**:
- Protected branch rules are server-side (GitHub, GitLab, etc.), not locally detectable
- No standard git command to query protection status
- API calls would require authentication, violate standard-library-only principle
- Best we can do is provide clear error messages when push is rejected

**Implementation**:
```python
# In push error handling
if "protected branch" in result.stderr.lower() or "permission denied" in result.stderr.lower():
    raise BranchProtectionError(
        f"Branch {remote_branch} is protected on remote. "
        f"Contact repository administrator to modify protection rules."
    )
```

**Limitations Accepted**:
- Cannot prevent push attempt proactively
- Relies on parsing error messages (not ideal but pragmatic)
- Different git hosting services may have slightly different messages

**Alternatives Considered**:
- GitHub/GitLab API calls: Requires external dependencies (requests) and authentication management
- Configuration file for protected patterns: Adds maintenance burden, can get out of sync
- No detection at all: Provides worse user experience with cryptic git errors

---

### 4. Manifest Revision Parsing

**Question**: How to distinguish between branch names and commit SHAs in manifest revision field?

**Decision**: Use regex pattern matching to detect SHA-like strings (40 hex characters)

**Rationale**:
- Git commit SHAs are always 40 hexadecimal characters (full form)
- Branch names cannot be pure 40-character hex strings (git rejects them as ambiguous)
- Simple pattern matching is reliable and fast
- Falls back to git detection when SHA detected, as specified in requirements

**Implementation**:
```python
import re

SHA_PATTERN = re.compile(r'^[0-9a-f]{40}$')

def is_commit_sha(revision: str) -> bool:
    """Check if revision string is a full git commit SHA."""
    return bool(SHA_PATTERN.match(revision.lower()))

def get_default_branch_from_manifest(project: Project) -> str | None:
    """Extract default branch from manifest, or None if revision is a SHA."""
    if is_commit_sha(project.revision):
        return None  # Fall back to git detection
    return project.revision
```

**Edge Cases Handled**:
- Short SHAs (7-8 chars): Treated as branch names (ambiguous, but rare in manifests)
- Tags: Treated same as branches (acceptable - git push handles both)
- Empty/None revision: Falls back to git detection

**Alternatives Considered**:
- `git cat-file -t`: Would require cloning repo first, defeats purpose of early detection
- Length check only (>=40 chars): Too crude, could match odd branch names
- No distinction: Would try to push to SHA as branch name, fail confusingly

---

### 5. Multi-Component Push Ordering

**Question**: Should components be pushed serially or in parallel?

**Decision**: Serial execution with continue-on-error semantics

**Rationale**:
- Simpler implementation (no thread/process management)
- Easier error reporting and logging
- Push operations are I/O-bound (network), parallel gains minimal
- Serial execution makes debugging easier
- Meets performance requirement: "complete in same time as sequential" (no slowdown introduced)

**Implementation**:
```python
def push_components(
    projects: list[Project],
    branch: str,
    force: bool = False
) -> list[PushResult]:
    """Push multiple components sequentially, continuing on failure."""
    results: list[PushResult] = []
    for project in projects:
        try:
            result = push_single_component(project, branch, force)
            results.append(result)
        except PushError as e:
            # Log error but continue with remaining components
            results.append(PushResult(
                project=project.name,
                success=False,
                error_message=str(e)
            ))
    return results
```

**Alternatives Considered**:
- Parallel with ThreadPoolExecutor: Adds complexity, minimal benefit for network I/O
- Stop-on-first-failure: Violates requirement FR-010 (continue on failure)
- Async/await: Overkill for subprocess calls, adds complexity

---

## Best Practices Applied

### Git Operations with subprocess
- Always use `check=False` and explicitly handle return codes
- Capture both stdout and stderr for error diagnostics
- Use `text=True` to get str instead of bytes
- Set `cwd` parameter for operations in specific repos
- Use `--` separator before file paths to prevent argument injection

### Error Message Design
- Include specific component name in error messages
- Suggest remediation steps (e.g., "Use --force", "Create repository manually")
- Distinguish between different failure modes (missing repo vs permission vs conflict)
- Quote branch names in messages to handle spaces/special chars

### Backward Compatibility
- Default branch behavior unchanged when flag not present
- Existing push command works identically on default branch
- New --force flag is opt-in only
- No changes to manifest XML format required

---

## Technology Stack Confirmation

**Language**: Python 3.14+
**Runtime Dependencies**: None (standard library only)
**Development Dependencies**:
- pytest (testing framework)
- mypy (type checking)
- ruff (linting)
- black (formatting)
- pytest-cov (coverage reporting)

**Standard Library Modules Used**:
- `subprocess`: Git command execution
- `xml.etree.ElementTree`: Manifest parsing (existing)
- `pathlib`: File path operations (existing)
- `argparse`: CLI argument parsing (existing)
- `logging`: Error and debug logging
- `dataclasses`: Data model definitions (existing)
- `re`: Regular expressions for SHA pattern matching
- `enum`: Enum types for status codes

**Constitution Compliance**: ✅ Zero external runtime dependencies

---

## Performance Considerations

### Expected Performance
- Branch detection: <10ms (single git command)
- Manifest parsing: <100ms for 1000 projects (existing)
- Push operation: Network-bound (same as manual git push)
- Multi-component: N × (single push time), no added overhead

### Optimization Opportunities (YAGNI - not implementing)
- Caching branch detection results
- Parallel push execution
- Incremental manifest parsing
- Connection pooling

**Decision**: Start simple, optimize only if performance issues observed in practice

---

## Risk Mitigation

### Data Loss Prevention
- No automatic force push (requires explicit --force flag)
- Dry-run detection before actual push
- Clear error messages for diverged histories
- Non-transactional model documented (failed pushes don't rollback successful ones)

### Security
- No credential storage or management
- Delegates authentication to git's existing mechanisms
- No parsing of sensitive git config
- No execution of user-provided commands (fixed command set)

### Compatibility
- Works with any git hosting service (GitHub, GitLab, Bitbucket, self-hosted)
- No assumptions about remote git version
- Handles both SSH and HTTPS remotes
- Compatible with git 2.17+ (Ubuntu 18.04 LTS baseline)

---

## Open Questions (None Remaining)

All research questions have been resolved. Implementation can proceed.
