# Quick Start: Manifest Copyfile and Linkfile Support

**Feature**: 003-manifest-copyfile-linkfile
**For**: Developers implementing this feature

## Overview

This feature adds `<copyfile>` and `<linkfile>` element support to git-repo manifest XML, allowing automatic file copying and symlinking from projects to workspace root during sync operations.

## What You're Building

**User Story**: Users want to place files from component repositories (like README, Makefile, build scripts) into the workspace root automatically during sync.

**Solution**: Parse `<copyfile>` and `<linkfile>` XML elements, validate paths for security, execute file operations during sync with graceful error handling.

## Architecture at a Glance

```
┌─────────────────┐
│  Manifest XML   │ <copyfile src="..." dest="..." />
└────────┬────────┘
         │ parse
         ▼
┌─────────────────┐
│ ManifestParser  │ → Copyfile/Linkfile objects
└────────┬────────┘
         │ validate (security + uniqueness)
         ▼
┌─────────────────┐
│    Manifest     │ → Project.copyfiles[], Project.linkfiles[]
└────────┬────────┘
         │ during sync
         ▼
┌─────────────────┐
│ SubtreeManager  │ → execute file operations
└────────┬────────┘
         │ call
         ▼
┌─────────────────┐
│ FileOperations  │ → validate_path, copy_file, create_symlink
└────────┬────────┘
         │ results
         ▼
┌─────────────────┐
│FileOperationSum │ → report to user
└─────────────────┘
```

## Key Modules

### 1. `subrepo/models.py`
**What**: Data structures
**Changes**:
- Add `Copyfile` dataclass
- Add `Linkfile` dataclass
- Add `FileOperationResult` dataclass
- Add `FileOperationSummary` dataclass
- Extend `Project` with `copyfiles` and `linkfiles` lists
- Extend `Manifest.validate()` to check dest path uniqueness

### 2. `subrepo/manifest_parser.py`
**What**: XML parsing
**Changes**:
- Parse `<copyfile>` elements → create `Copyfile` objects
- Parse `<linkfile>` elements → create `Linkfile` objects
- Attach to `Project` during parsing

### 3. `subrepo/file_operations.py` *(NEW MODULE)*
**What**: File manipulation with security validation
**Functions**:
- `validate_path_security()` - Check for "..", symlinks in path, escape attempts
- `copy_file()` - Copy with permission preservation using `shutil.copy2()`
- `create_symlink()` - Create symlink with fallback to copy on Windows/unsupported FS
- `execute_file_operations()` - Orchestrate all file ops for a project

### 4. `subrepo/subtree_manager.py`
**What**: Sync orchestration
**Changes**:
- After syncing each project's subtree, call `execute_file_operations()`
- Collect `FileOperationResult` objects
- Continue processing on failures (don't abort)

### 5. `subrepo/cli.py`
**What**: User interface
**Changes**:
- Display file operation progress during sync
- Display `FileOperationSummary` at completion
- Return non-zero exit code if any operations failed

### 6. `subrepo/exceptions.py`
**What**: Error types
**Changes**:
- Add `FileOperationError` exception
- Add `PathSecurityError` exception

## Implementation Phases

### Phase 1: Data Model (TDD Red)
1. Write tests for `Copyfile` model validation
2. Write tests for `Linkfile` model validation
3. Write tests for `Project` with copyfiles/linkfiles
4. Write tests for `Manifest.validate()` with dest conflicts
5. Run tests → **ALL FAIL** ✓

### Phase 2: Data Model (TDD Green)
1. Implement `Copyfile` dataclass in `models.py`
2. Implement `Linkfile` dataclass in `models.py`
3. Extend `Project` with new fields
4. Extend `Manifest.validate()` for uniqueness check
5. Run tests → **ALL PASS** ✓

### Phase 3: XML Parsing (TDD Red)
1. Write tests for parsing `<copyfile>` elements
2. Write tests for parsing `<linkfile>` elements
3. Write tests for multiple file elements per project
4. Run tests → **ALL FAIL** ✓

### Phase 4: XML Parsing (TDD Green)
1. Extend `parse_project()` in `manifest_parser.py`
2. Find child `<copyfile>` elements → create `Copyfile` objects
3. Find child `<linkfile>` elements → create `Linkfile` objects
4. Attach to `Project`
5. Run tests → **ALL PASS** ✓

### Phase 5: File Operations (TDD Red)
1. Write tests for `validate_path_security()` (good/bad paths)
2. Write tests for `copy_file()` with various scenarios
3. Write tests for `create_symlink()` with fallback
4. Write tests for `execute_file_operations()`
5. Run tests → **ALL FAIL** ✓

### Phase 6: File Operations (TDD Green)
1. Create `file_operations.py` module
2. Implement `validate_path_security()` using `pathlib`
3. Implement `copy_file()` using `shutil.copy2()`
4. Implement `create_symlink()` with try/except fallback
5. Implement `execute_file_operations()` orchestration
6. Run tests → **ALL PASS** ✓

### Phase 7: Integration (TDD Red)
1. Write integration tests for sync with copyfile/linkfile
2. Write contract tests for CLI output format
3. Run tests → **ALL FAIL** ✓

### Phase 8: Integration (TDD Green)
1. Modify `subtree_manager.py` to call file operations
2. Modify `cli.py` to display results
3. Add exception types to `exceptions.py`
4. Run tests → **ALL PASS** ✓

### Phase 9: Refactor
1. Review code for readability
2. Extract magic strings to constants
3. Improve error messages
4. Run tests → **STILL ALL PASS** ✓

## Critical Path Validations

### Security Checks (Non-Negotiable)
- ✅ Reject paths with ".." components
- ✅ Reject absolute paths (starting with "/")
- ✅ Verify resolved dest path stays within workspace root
- ✅ Check for symlinks in intermediate directories
- ✅ Validate source exists before operations

### Error Handling (Non-Negotiable)
- ✅ Continue processing on file operation failures
- ✅ Collect all errors and report at end
- ✅ Return non-zero exit code if any failure
- ✅ Provide actionable error messages (include project name, paths, reason)

### Cross-Platform (Required)
- ✅ Detect symlink support via try/except
- ✅ Fall back to copy on Windows/unsupported FS
- ✅ Log warning when fallback occurs
- ✅ Preserve file permissions during copy

## Testing Strategy

### Unit Tests (Isolated)
- `test_models.py`: Copyfile/Linkfile validation, Project extension, Manifest validation
- `test_manifest_parser.py`: XML parsing for copyfile/linkfile elements
- `test_file_operations.py`: Path validation, copy, symlink, fallback logic

### Integration Tests (End-to-End)
- `test_manifest_workflow.py`: Full sync with copyfile/linkfile operations
- Test fixtures with real manifest XML and mock file systems

### Contract Tests (CLI Behavior)
- `test_cli_sync.py`: Exit codes, output format, error messages

### Coverage Target
- ≥90% for all new code (enforced by pytest --cov-fail-under=90)
- 100% for security-critical path validation code

## Development Workflow

### Before Writing Any Code
1. Read `spec.md` - understand requirements
2. Read `data-model.md` - understand data structures
3. Read `contracts/cli-file-operations.md` - understand expected behavior
4. Read `research.md` - understand technical approaches

### Red-Green-Refactor Cycle
1. **RED**: Write test for next smallest piece of functionality
2. Verify test fails (proves test works)
3. **GREEN**: Write minimal code to pass test
4. Verify test passes
5. **REFACTOR**: Improve code quality while keeping tests green
6. Repeat

### Git Workflow
1. Make small, focused commits
2. Commit message format: `<area>: <what changed and why>`
3. Examples:
   - `models: add Copyfile and Linkfile dataclasses for manifest file operations`
   - `manifest_parser: parse copyfile and linkfile XML elements`
   - `file_operations: implement secure path validation and copy operations`

### Quality Gates (Must Pass Before Commit)
```bash
# Run tests
pytest

# Type checking
mypy subrepo --strict

# Linting
ruff check subrepo

# Formatting
black subrepo tests

# All must pass ✓
```

## Common Pitfalls to Avoid

### ❌ DON'T: Use os.path for path manipulation
**Why**: Doesn't resolve paths securely, harder to validate
**DO**: Use `pathlib.Path` for all path operations

### ❌ DON'T: Assume symlinks work everywhere
**Why**: Windows requires special permissions, some filesystems don't support
**DO**: Use try/except with fallback to copy

### ❌ DON'T: Abort sync on first file operation failure
**Why**: User loses all subsequent work, can't see all problems at once
**DO**: Collect errors, continue processing, report all failures at end

### ❌ DON'T: Trust user-provided paths
**Why**: Security vulnerability (directory traversal attacks)
**DO**: Validate all paths with `validate_path_security()`

### ❌ DON'T: Use `shutil.copy()` for file copies
**Why**: Doesn't preserve permissions
**DO**: Use `shutil.copy2()` to preserve metadata

### ❌ DON'T: Create ambiguous error messages
**Why**: User can't fix the problem
**DO**: Include project name, src/dest paths, and specific reason in all errors

## Success Criteria Checklist

Before marking feature complete:
- [ ] All tests pass (pytest)
- [ ] Type checking passes (mypy --strict)
- [ ] Linting passes (ruff check)
- [ ] Code formatted (black)
- [ ] Coverage ≥90%
- [ ] All functional requirements from spec.md implemented
- [ ] All contract test scenarios pass
- [ ] Documentation updated (README if needed)
- [ ] Constitution compliance verified (no violations)

## Getting Help

### Key Reference Documents
- `spec.md` - Requirements and user stories
- `data-model.md` - Data structures and relationships
- `contracts/cli-file-operations.md` - Expected CLI behavior
- `research.md` - Technical implementation patterns
- `.specify/memory/constitution.md` - Project principles

### When Stuck
1. Re-read the spec - is the requirement clear?
2. Check research.md - is there a pattern for this?
3. Look at existing code - how is similar functionality handled?
4. Write a simpler test - can you break it down further?
5. Ask for help - include what you've tried and what's failing

## Next Steps

After reading this quickstart:
1. Read `data-model.md` for detailed entity specifications
2. Read `contracts/cli-file-operations.md` for CLI behavior examples
3. Read `research.md` for code patterns and best practices
4. Look at existing `models.py` and `manifest_parser.py` to understand patterns
5. Start with Phase 1: Write tests for `Copyfile` dataclass
6. Follow TDD workflow: Red → Green → Refactor

**Remember**: Tests first, code second. No exceptions. 🚦
