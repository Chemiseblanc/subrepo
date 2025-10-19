# Implementation Plan: Git Subtree Repo Manager

**Branch**: `001-git-subtree-repo` | **Date**: 2025-10-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-git-subtree-repo/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a command-line tool that reimplements git-repo functionality using git subtrees instead of multiple independent checkouts. The tool enables developers to manage multi-repository projects in a single unified git repository by parsing repo manifest XML files and transparently handling git subtree operations for initialization, synchronization, and bidirectional component updates.

## Technical Context

**Language/Version**: Python 3.14+ (as specified in pyproject.toml)
**Primary Dependencies**: Python standard library only (xml.etree, subprocess, pathlib, argparse, logging)
**Storage**: Filesystem-based (manifest XML, git repository metadata)
**Testing**: pytest with ≥90% coverage requirement
**Target Platform**: Cross-platform CLI (Linux, macOS, Windows with git installed)
**Project Type**: Single project (CLI application)
**Performance Goals**: Initialize 10+ component workspace in <2 minutes (network excluded), git operations complete with minimal overhead
**Constraints**: Zero runtime dependencies, must use only Python stdlib, CLI-only interface
**Scale/Scope**: Handle manifests with 50+ components, support standard repo manifest XML format

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Standard Library Only ✅ PASS

- **Requirement**: All functionality using Python standard library only
- **Status**: COMPLIANT
- **Evidence**: Technical context specifies xml.etree, subprocess, pathlib, argparse, logging - all stdlib modules
- **Note**: Git operations executed via subprocess calls to system git binary (external dependency on git installation is acceptable as it's a system tool, not a Python package)

### II. Test-Driven Development (NON-NEGOTIABLE) ✅ PASS

- **Requirement**: TDD with red-green-refactor cycle, ≥90% coverage
- **Status**: COMPLIANT
- **Evidence**: Testing framework pytest specified, coverage requirement ≥90% documented
- **Plan**: Contract tests for CLI commands, integration tests for git subtree operations, unit tests for manifest parsing and validation

### III. Code Quality & Readability ✅ PASS

- **Requirement**: Clear documentation, descriptive naming, single responsibility, max 50 lines/function, max 500 lines/file
- **Status**: COMPLIANT
- **Evidence**: CLI application architecture promotes clear separation (parsing, git operations, command handlers)
- **Plan**: Google-style docstrings for all public APIs, descriptive module structure (manifest_parser, subtree_manager, cli_commands)

### IV. Type Safety ✅ PASS

- **Requirement**: Full type hints, mypy --strict mode
- **Status**: COMPLIANT
- **Evidence**: Python 3.14+ supports full type hint capabilities
- **Plan**: Type hints for all functions, dataclasses for manifest entities (Remote, Project), strict mypy configuration

### V. Minimal Complexity ✅ PASS

- **Requirement**: YAGNI, no premature optimization/abstraction
- **Status**: COMPLIANT
- **Evidence**: Single project structure, CLI-only interface, focused on core repo commands (init, sync, push, pull)
- **Plan**: Start with basic manifest parsing, add features incrementally per user story priority

### Quality Standards ✅ PASS

- **Code Style**: Black formatter, Ruff linter, 100 char line length
- **Error Handling**: Custom exceptions for domain errors (ManifestError, SubtreeOperationError, GitCommandError)
- **Documentation**: README with quickstart, docstring-generated API docs
- **Testing**: Pytest fixtures, isolated tests, <1s unit tests, <10s integration tests

### Gate Status: ✅ ALL PASSED

No constitution violations. All principles satisfied by current design.

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
src/
├── __init__.py
├── __main__.py           # Entry point for python -m subrepo
├── cli.py                # CLI argument parsing and command routing
├── models.py             # Data classes (Manifest, Remote, Project, Subtree)
├── manifest_parser.py    # XML parsing and validation
├── subtree_manager.py    # Git subtree operations (add, pull, push, split)
├── workspace.py          # Workspace initialization and management
├── git_commands.py       # Git subprocess wrappers
└── exceptions.py         # Custom exception classes

tests/
├── contract/
│   ├── test_cli_init.py      # CLI contract tests for init command
│   ├── test_cli_sync.py      # CLI contract tests for sync command
│   ├── test_cli_push.py      # CLI contract tests for push command
│   ├── test_cli_pull.py      # CLI contract tests for pull command
│   └── test_cli_status.py    # CLI contract tests for status command
├── integration/
│   ├── test_manifest_workflow.py     # End-to-end manifest workflows
│   ├── test_subtree_operations.py    # Git subtree integration tests
│   └── fixtures/                     # Test manifest XML files
│       ├── simple_manifest.xml
│       ├── complex_manifest.xml
│       └── invalid_manifest.xml
└── unit/
    ├── test_manifest_parser.py       # Unit tests for XML parsing
    ├── test_models.py                # Unit tests for data classes
    ├── test_git_commands.py          # Unit tests for git wrappers
    └── test_workspace.py             # Unit tests for workspace management
```

**Structure Decision**: Single project structure selected. This is a CLI application with clear separation of concerns:
- **CLI layer** (cli.py, __main__.py): Command routing and user interface
- **Domain layer** (models.py, workspace.py): Business logic and entities
- **Infrastructure layer** (manifest_parser.py, subtree_manager.py, git_commands.py): External system interactions
- **Test structure** mirrors the three testing levels required by constitution (contract, integration, unit)

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

No violations. Constitution fully satisfied.

