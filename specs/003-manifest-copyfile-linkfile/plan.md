# Implementation Plan: Manifest Copyfile and Linkfile Support

**Branch**: `003-manifest-copyfile-linkfile` | **Date**: 2025-10-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-manifest-copyfile-linkfile/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add support for `<copyfile>` and `<linkfile>` elements in git-repo manifest XML, enabling users to automatically copy files or create symbolic links from project directories to the workspace root during sync operations. This feature extends the existing manifest parsing and sync infrastructure with new file operation capabilities while maintaining security through path validation and providing graceful error handling with cross-platform symlink fallback.

## Technical Context

**Language/Version**: Python 3.14+ (as specified in pyproject.toml)
**Primary Dependencies**: Python standard library only (xml.etree.ElementTree, pathlib, shutil, os)
**Storage**: Filesystem (manifest XML, workspace directory structure)
**Testing**: pytest with >=90% coverage requirement, mypy --strict, ruff, black
**Target Platform**: Cross-platform (Linux, macOS, Windows with symlink fallback)
**Project Type**: Single CLI application
**Performance Goals**: File operations complete in <1s per 100 files, manifest validation in <100ms
**Constraints**: Standard library only (constitution requirement), security-focused path validation, cross-platform compatibility
**Scale/Scope**: Support manifests with 100+ projects, each with multiple copyfile/linkfile elements

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Standard Library Only
✅ **PASS** - Feature uses only Python standard library:
- `xml.etree.ElementTree` for XML parsing (already in use)
- `pathlib` for path manipulation and validation
- `shutil` for file copy operations
- `os` for symlink operations and filesystem checks

### II. Test-Driven Development
✅ **PASS** - TDD workflow will be followed:
- Unit tests for Copyfile/Linkfile models
- Unit tests for path validation logic
- Unit tests for file operation functions
- Integration tests for sync with copyfile/linkfile
- Contract tests for error messages and exit codes
- Target: >=90% coverage (matches project standard)

### III. Code Quality & Readability
✅ **PASS** - Complexity is bounded:
- New dataclasses: Copyfile, Linkfile (simple, immutable)
- New functions: validate_path_security, copy_file, create_symlink (single responsibility)
- Extension to existing: Project model (add copyfile/linkfile lists), manifest_parser (parse new elements)
- File operations isolated in dedicated module for testability
- Max function length: <50 lines maintained

### IV. Type Safety
✅ **PASS** - Full type hints will be provided:
- Copyfile/Linkfile dataclasses with frozen=True
- All function signatures with complete type hints
- mypy --strict compliance verified
- No use of `Any` type

### V. Minimal Complexity
✅ **PASS** - Simplest solution chosen:
- Extends existing Project model rather than creating separate registry
- Reuses existing manifest validation patterns
- No new abstraction layers
- File operations use standard library functions directly
- Fail-fast validation prevents complex error recovery

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
subrepo/
├── models.py                    # MODIFIED: Add Copyfile, Linkfile dataclasses; extend Project
├── manifest_parser.py           # MODIFIED: Parse <copyfile> and <linkfile> XML elements
├── file_operations.py           # NEW: File copy and symlink operations with validation
├── subtree_manager.py          # MODIFIED: Execute file operations during sync
├── exceptions.py                # MODIFIED: Add FileOperationError, PathSecurityError
└── cli.py                       # MODIFIED: Display file operation results and errors

tests/
├── unit/
│   ├── test_models.py           # MODIFIED: Test Copyfile, Linkfile models and validation
│   ├── test_manifest_parser.py  # MODIFIED: Test parsing copyfile/linkfile elements
│   ├── test_file_operations.py  # NEW: Test file copy, symlink, path validation
│   └── test_subtree_manager.py  # MODIFIED: Test sync with file operations
├── integration/
│   ├── test_manifest_workflow.py # MODIFIED: Test end-to-end sync with copyfile/linkfile
│   └── fixtures/
│       └── manifest_with_files.xml # NEW: Test manifest with copyfile/linkfile
└── contract/
    └── test_cli_sync.py          # MODIFIED: Test error messages and exit codes
```

**Structure Decision**: Single project structure (Option 1) is appropriate. This feature extends existing modules (models, manifest_parser, subtree_manager) and adds one new module (file_operations) for the file manipulation logic. The modular design keeps file operations isolated for testability while integrating cleanly with the existing sync workflow.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

No constitution violations. All requirements met with standard library and simple extensions to existing architecture.

---

## Planning Phase Complete

### Generated Artifacts

**Phase 0 - Research**:
- ✅ `research.md` - Technical research covering:
  - Path security validation patterns
  - Cross-platform symlink handling
  - File copy with permission preservation
  - Atomic file operations
  - XML parsing patterns

**Phase 1 - Design & Contracts**:
- ✅ `data-model.md` - Complete data model specification with:
  - Copyfile and Linkfile entities
  - FileOperationResult and FileOperationSummary
  - Modified Project and Manifest models
  - Entity relationships and validation rules
  - Data flow diagrams
- ✅ `contracts/cli-file-operations.md` - CLI contract with:
  - 10 success and error scenarios
  - Output format specifications
  - Exit code definitions
  - Testing requirements
- ✅ `quickstart.md` - Developer onboarding guide with:
  - Architecture overview
  - Module breakdown
  - 9-phase implementation plan
  - TDD workflow
  - Common pitfalls
  - Success criteria checklist
- ✅ Agent context updated (`CLAUDE.md`)

### Post-Design Constitution Check

All principles still satisfied after design phase:

- ✅ **Standard Library Only**: Uses xml.etree, pathlib, shutil, os only
- ✅ **Test-Driven Development**: Quickstart documents full TDD workflow with 9 phases
- ✅ **Code Quality**: Simple dataclasses, single-responsibility functions, isolated modules
- ✅ **Type Safety**: All entities fully typed with frozen dataclasses
- ✅ **Minimal Complexity**: Extends existing patterns, no new abstractions

### Key Design Decisions

1. **Security-First Path Validation**: Multi-layer validation (parse-time + runtime) prevents directory traversal attacks
2. **Continue-on-Error Pattern**: Sync processes all projects and reports all failures at end (better UX)
3. **Cross-Platform Graceful Degradation**: Automatic fallback from symlink to copy on unsupported platforms
4. **Fail-Fast Manifest Validation**: Duplicate dest paths caught at validation, not during sync
5. **Immutable Data Structures**: All models use frozen dataclasses for safety

### Implementation Readiness

**Ready to proceed with** `/speckit.tasks` command to generate task breakdown.

**What developers need**:
1. Start with `quickstart.md` for overview
2. Reference `data-model.md` for entity specifications
3. Follow `contracts/cli-file-operations.md` for expected behavior
4. Use `research.md` for implementation patterns
5. Follow TDD workflow: Red → Green → Refactor

### Next Command

```bash
/speckit.tasks
```

This will generate the dependency-ordered `tasks.md` file for implementation execution.

