# Research: Git Subtree Repo Manager

**Feature**: Git Subtree Repo Manager
**Branch**: 001-git-subtree-repo
**Date**: 2025-10-18

## Overview

This document captures research findings and technical decisions for implementing a git-repo alternative using git subtrees. All decisions align with the constitution requirement for Python standard library only.

## Key Research Areas

### 1. Repo Manifest XML Format

**Decision**: Support standard repo manifest XML schema with core elements

**Rationale**:
- Repo manifest is a well-established format used by AOSP and other large projects
- XML parsing available via Python stdlib (xml.etree.ElementTree)
- Core elements are well-documented and stable

**Key Elements to Support**:
```xml
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <default remote="origin" revision="main" />
  <project name="org/repo" path="components/repo" remote="origin" revision="feature-branch" />
</manifest>
```

**Alternatives Considered**:
- TOML/YAML manifest: Rejected - would break compatibility with existing repo users
- JSON manifest: Rejected - not standard in repo ecosystem
- Custom format: Rejected - reduces adoption, no benefit over XML

**Implementation Notes**:
- Use xml.etree.ElementTree for parsing (stdlib)
- Validate required attributes (name, path for projects; name, fetch for remotes)
- Support optional attributes (revision, remote defaults)
- Handle manifest references to other manifests (include element) in future iteration

### 2. Git Subtree Operations

**Decision**: Wrap git subtree commands via subprocess module

**Rationale**:
- Git subtree is a standard git command available in all modern git installations
- Python subprocess module provides robust process execution (stdlib)
- No need to reimplement git logic - leverage existing, tested tool

**Core Operations**:
```python
# Add subtree (init)
git subtree add --prefix=<path> <repository> <ref> --squash

# Pull updates (sync, pull)
git subtree pull --prefix=<path> <repository> <ref> --squash

# Push changes (push)
git subtree push --prefix=<path> <repository> <ref>

# Split for examination
git subtree split --prefix=<path> --branch=<temp-branch>
```

**Alternatives Considered**:
- GitPython library: Rejected - external dependency, violates constitution
- Dulwich (pure Python git): Rejected - external dependency, doesn't support subtree commands
- Manual tree manipulation: Rejected - extremely complex, error-prone, reinvents git

**Implementation Notes**:
- Use subprocess.run() with capture_output=True for command execution
- Parse git command output for progress and error reporting
- Use --squash flag to avoid cluttering history with upstream commits
- Implement retry logic for network failures
- Validate git version ≥2.30 (subtree improvements)

### 3. CLI Architecture

**Decision**: Use argparse with subcommands pattern

**Rationale**:
- argparse is Python stdlib, provides excellent subcommand support
- Pattern matches git/repo command structure (init, sync, push, pull, status)
- Built-in help generation and argument validation

**Command Structure**:
```
subrepo init <manifest-url-or-path>
subrepo sync [--component=<name>] [--jobs=<n>]
subrepo push <component> [--branch=<name>]
subrepo pull <component>
subrepo status [--component=<name>]
```

**Alternatives Considered**:
- Click framework: Rejected - external dependency
- Custom argument parsing: Rejected - reinvents wheel, less robust
- Single-command with flags: Rejected - less intuitive, harder to extend

**Implementation Notes**:
- Use ArgumentParser.add_subparsers() for command routing
- Each command has dedicated handler function
- Common arguments (verbose, quiet) available globally
- Exit codes: 0=success, 1=user error, 2=system error

### 4. Workspace Metadata Storage

**Decision**: Store manifest and subtree mapping in .subrepo/ directory

**Rationale**:
- Hidden directory pattern familiar to developers (.git, .repo)
- Filesystem-based storage simple and inspectable
- No external database needed

**Metadata Structure**:
```
.subrepo/
├── manifest.xml          # Copy of active manifest
├── config.json           # Workspace configuration
└── subtrees/
    └── <component>.json  # Per-subtree metadata (last sync, commit hash)
```

**Alternatives Considered**:
- Git config: Rejected - pollutes git config namespace
- SQLite database: Rejected - overkill for simple key-value needs
- Single JSON file: Rejected - harder to update atomically per-component

**Implementation Notes**:
- Use json module (stdlib) for config serialization
- Atomic writes with tempfile + rename pattern
- .subrepo/ should be gitignored in created repositories
- Lock file pattern for concurrent operation safety

### 5. Error Handling Strategy

**Decision**: Custom exception hierarchy with actionable messages

**Rationale**:
- Constitution requires clear, actionable error messages
- Exception hierarchy enables specific error handling
- Better than generic RuntimeError

**Exception Hierarchy**:
```python
SubrepoError (base)
├── ManifestError
│   ├── ManifestParseError
│   ├── ManifestValidationError
│   └── ManifestNotFoundError
├── WorkspaceError
│   ├── WorkspaceNotInitializedError
│   ├── WorkspaceAlreadyExistsError
│   └── DirtyWorkspaceError
└── GitOperationError
    ├── GitCommandError
    ├── SubtreeConflictError
    └── RemoteNotAccessibleError
```

**Alternatives Considered**:
- Generic exceptions: Rejected - less specific error handling
- Error codes: Rejected - less Pythonic, harder to handle
- Result types: Rejected - not idiomatic Python

**Implementation Notes**:
- Each exception includes context (file path, component name, git output)
- User-facing messages explain what happened and how to fix
- Internal details in exception attributes for debugging
- logging module for debug-level detailed output

### 6. Concurrent Operations

**Decision**: Sequential operations in MVP, concurrent in future with --jobs flag

**Rationale**:
- YAGNI principle - simple sequential first
- Git operations are I/O bound (network, disk)
- Complexity of concurrent git operations high (locking, conflicts)

**MVP Approach**:
- Process components sequentially
- Clear progress reporting for each component
- Fail fast or continue with --continue-on-error flag

**Future Enhancement**:
```python
# Phase 2 or 3: concurrent operations
with ThreadPoolExecutor(max_workers=jobs) as executor:
    futures = [executor.submit(sync_component, c) for c in components]
```

**Alternatives Considered**:
- Concurrent by default: Rejected - premature optimization
- asyncio: Rejected - subprocess works better with threads
- multiprocessing: Rejected - overkill for I/O bound operations

**Implementation Notes**:
- Design with concurrency in mind (stateless operations)
- Use component-level locking when adding concurrency
- Progress reporting needs thread-safe updates

### 7. Testing Strategy

**Decision**: Three-tier testing per constitution requirements

**Contract Tests**:
- Test CLI interface end-to-end with real git repositories
- Validate command output format and exit codes
- Use temporary directories for isolation
- pytest fixtures for test repository setup

**Integration Tests**:
- Test git subtree operations with real git commands
- Test manifest parsing with real XML files
- Test workspace initialization and state management
- Slower tests (~5-10 seconds acceptable)

**Unit Tests**:
- Test data models (Manifest, Project, Remote classes)
- Test argument parsing logic
- Test validation functions
- Mock subprocess calls for git operations
- Fast tests (<1 second)

**Implementation Notes**:
- pytest fixtures for temporary git repositories
- Use unittest.mock for subprocess mocking in unit tests
- Test with various manifest formats (simple, complex, invalid)
- Coverage target ≥90% per constitution

## Technology Choices Summary

| Category | Choice | Rationale |
|----------|--------|-----------|
| Language | Python 3.14+ | Specified in project |
| XML Parsing | xml.etree.ElementTree | Python stdlib |
| Git Operations | subprocess + git CLI | Stdlib, leverages existing tool |
| CLI Framework | argparse | Python stdlib |
| Configuration | JSON + json module | Stdlib, simple, human-readable |
| Testing | pytest | Allowed dev dependency |
| Type Checking | mypy --strict | Allowed dev dependency |
| Formatting | black | Allowed dev dependency |
| Linting | ruff | Allowed dev dependency |

## Open Questions for Future Iterations

1. **Manifest includes**: How to handle `<include>` elements that reference other manifests?
   - Current: Not supported in MVP
   - Future: Recursive parsing with cycle detection

2. **Sync strategies**: Should sync support different merge strategies?
   - Current: Default git subtree merge behavior
   - Future: Add --squash, --rebase options

3. **History management**: How to handle git subtree merge commit clutter?
   - Current: Use --squash flag to minimize commits
   - Future: Add --prune-history option

4. **Large repositories**: How to optimize for large component repositories?
   - Current: Accept performance limitations
   - Future: Shallow clones, sparse checkouts

5. **Credential management**: How to handle authentication for private repositories?
   - Current: Rely on git credential helper
   - Future: Document credential setup in quickstart

## Next Steps

1. ✅ Complete Technical Context (done)
2. ✅ Pass Constitution Check (done)
3. → Proceed to Phase 1: Data Model design
4. → Proceed to Phase 1: Contract definitions
5. → Proceed to Phase 1: Quickstart guide
