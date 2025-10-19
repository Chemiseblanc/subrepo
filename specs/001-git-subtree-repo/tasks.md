---
description: "Task list for Git Subtree Repo Manager implementation"
---

# Tasks: Git Subtree Repo Manager

**Input**: Design documents from `/specs/001-git-subtree-repo/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Per constitution requirement (TDD non-negotiable), all user stories include test tasks that MUST be written and fail before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- Paths shown below follow single project structure per plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure (src/, tests/{contract,integration,unit}/)
- [X] T002 [P] Initialize pyproject.toml with Python 3.14+ requirement and zero runtime dependencies
- [X] T003 [P] Create src/__init__.py with package metadata
- [X] T004 [P] Create tests/__init__.py and test fixtures directory structure
- [X] T005 [P] Configure pytest in pyproject.toml with coverage ≥90% requirement
- [X] T006 [P] Configure mypy in pyproject.toml with --strict mode
- [X] T007 [P] Configure black formatter in pyproject.toml (line length 100)
- [X] T008 [P] Configure ruff linter in pyproject.toml with strict rules
- [X] T009 [P] Create .gitignore with Python patterns, .subrepo/, __pycache__, etc.
- [X] T010 [P] Create tests/integration/fixtures/ directory for test manifest XML files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T011 Create custom exception hierarchy in src/exceptions.py (SubrepoError base, ManifestError, WorkspaceError, GitOperationError)
- [X] T012 [P] Write unit tests for exception classes in tests/unit/test_exceptions.py
- [X] T013 [P] Create data model classes in src/models.py (Remote, Project, Manifest dataclasses with full type hints)
- [X] T014 Write unit tests for Remote dataclass validation in tests/unit/test_models.py
- [X] T015 Write unit tests for Project dataclass validation in tests/unit/test_models.py
- [X] T016 Write unit tests for Manifest dataclass and methods in tests/unit/test_models.py
- [X] T017 Create git command wrapper module src/git_commands.py with GitOperationResult dataclass
- [X] T018 [P] Write unit tests for git command wrappers in tests/unit/test_git_commands.py (mock subprocess calls)
- [X] T019 [P] Create test fixture manifests in tests/integration/fixtures/ (simple_manifest.xml, complex_manifest.xml, invalid_manifest.xml)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Initialize Workspace from Manifest (Priority: P1) 🎯 MVP

**Goal**: Enable developers to initialize a workspace from a manifest XML file, creating a git repository with all components as subtrees

**Independent Test**: Provide a manifest XML, run init command, verify git repository created with all components as subtrees at correct paths

### Tests for User Story 1 (TDD - RED phase)

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T020 [P] [US1] Contract test for init command success case in tests/contract/test_cli_init.py
- [X] T021 [P] [US1] Contract test for init command with non-empty directory in tests/contract/test_cli_init.py
- [X] T022 [P] [US1] Contract test for init command with invalid manifest in tests/contract/test_cli_init.py
- [X] T023 [P] [US1] Contract test for init command exit codes in tests/contract/test_cli_init.py
- [X] T024 [P] [US1] Integration test for manifest parsing workflow in tests/integration/test_manifest_workflow.py
- [X] T025 [P] [US1] Integration test for git subtree add operations in tests/integration/test_subtree_operations.py
- [X] T026 [P] [US1] Unit test for XML parsing logic in tests/unit/test_manifest_parser.py
- [X] T027 [P] [US1] Unit test for manifest validation rules in tests/unit/test_manifest_parser.py
- [X] T028 [P] [US1] Unit test for workspace initialization logic in tests/unit/test_workspace.py

### Implementation for User Story 1 (GREEN phase)

- [X] T029 [P] [US1] Implement XML parsing in src/manifest_parser.py (parse_manifest function using xml.etree)
- [X] T030 [P] [US1] Implement manifest validation in src/manifest_parser.py (validate_manifest function)
- [X] T031 [US1] Implement workspace initialization in src/workspace.py (init_workspace function)
- [X] T032 [US1] Implement git repository creation in src/workspace.py (create_git_repo function)
- [X] T033 [US1] Implement WorkspaceConfig dataclass and persistence in src/models.py
- [X] T034 [US1] Implement .subrepo/ metadata directory creation in src/workspace.py
- [X] T035 [US1] Implement git subtree add wrapper in src/git_commands.py
- [X] T036 [US1] Implement init command handler in src/cli.py (init_command function with argparse)
- [X] T037 [US1] Create entry point in src/__main__.py with CLI routing to init command
- [X] T038 [US1] Add directory validation (empty check) to init command
- [X] T039 [US1] Add progress reporting for multi-component initialization
- [X] T040 [US1] Add error handling and user-friendly messages for init failures

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Synchronize Components (Priority: P2)

**Goal**: Enable developers to sync all component subtrees with their upstream repositories

**Independent Test**: Initialize workspace, make upstream commits, run sync, verify all subtrees updated to latest commits

### Tests for User Story 2 (TDD - RED phase)

- [X] T041 [P] [US2] Contract test for sync command success case in tests/contract/test_cli_sync.py
- [X] T042 [P] [US2] Contract test for sync command with local modifications in tests/contract/test_cli_sync.py
- [X] T043 [P] [US2] Contract test for sync command with network failures in tests/contract/test_cli_sync.py
- [X] T044 [P] [US2] Contract test for sync --force flag in tests/contract/test_cli_sync.py
- [X] T045 [P] [US2] Integration test for multi-component sync workflow in tests/integration/test_manifest_workflow.py
- [X] T046 [P] [US2] Integration test for git subtree pull operations in tests/integration/test_subtree_operations.py
- [X] T047 [P] [US2] Unit test for SubtreeState dataclass in tests/unit/test_models.py
- [X] T048 [P] [US2] Unit test for subtree sync logic in tests/unit/test_subtree_manager.py

### Implementation for User Story 2 (GREEN phase)

- [X] T049 [P] [US2] Create SubtreeState dataclass in src/models.py (with SubtreeStatus enum)
- [X] T050 [P] [US2] Create src/subtree_manager.py module with SubtreeManager class
- [X] T051 [US2] Implement git fetch wrapper in src/git_commands.py
- [X] T052 [US2] Implement git subtree pull wrapper in src/git_commands.py
- [X] T053 [US2] Implement sync_all_components function in src/subtree_manager.py
- [X] T054 [US2] Implement component state detection in src/subtree_manager.py
- [X] T055 [US2] Implement conflict detection and reporting in src/subtree_manager.py
- [X] T056 [US2] Implement sync command handler in src/cli.py (sync_command function)
- [X] T057 [US2] Add --force flag support (stash and reapply) to sync command
- [X] T058 [US2] Add --component flag for selective sync
- [X] T059 [US2] Add --continue-on-error flag for partial failure handling
- [X] T060 [US2] Add progress reporting with component-by-component status
- [X] T061 [US2] Implement SubtreeState persistence to .subrepo/subtrees/<component>.json

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Push Component Changes Upstream (Priority: P3)

**Goal**: Enable developers to push local commits from a subtree back to its upstream repository

**Independent Test**: Make commits in a subtree path, run push command, verify commits appear in upstream repository

### Tests for User Story 3 (TDD - RED phase)

- [X] T062 [P] [US3] Contract test for push command success case in tests/contract/test_cli_push.py
- [X] T063 [P] [US3] Contract test for push command with no changes in tests/contract/test_cli_push.py
- [X] T064 [P] [US3] Contract test for push command with conflicts in tests/contract/test_cli_push.py
- [X] T065 [P] [US3] Contract test for push --dry-run flag in tests/contract/test_cli_push.py
- [X] T066 [P] [US3] Integration test for git subtree split and push in tests/integration/test_push_operations.py
- [X] T067 [P] [US3] Unit test for commit extraction logic in tests/unit/test_subtree_manager.py

### Implementation for User Story 3 (GREEN phase)

- [X] T068 [P] [US3] Implement git subtree split wrapper in src/git_commands.py
- [X] T069 [P] [US3] Implement git push wrapper in src/git_commands.py
- [X] T070 [US3] Implement push_component function in src/subtree_manager.py
- [X] T071 [US3] Implement commit extraction for subtree in src/subtree_manager.py
- [X] T072 [US3] Implement upstream divergence detection in src/subtree_manager.py
- [X] T073 [US3] Implement push command handler in src/cli.py (push_command function)
- [X] T074 [US3] Add --branch flag support for pushing to different branch
- [X] T075 [US3] Add --dry-run flag to show what would be pushed
- [X] T076 [US3] Add --force flag for force push (with warning)
- [X] T077 [US3] Add push confirmation and result reporting

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Pull Component Changes from Upstream (Priority: P4)

**Goal**: Enable developers to pull updates for a specific component without syncing all components

**Independent Test**: Update upstream component, run pull command for that component only, verify only that subtree updated

### Tests for User Story 4 (TDD - RED phase)

- [X] T078 [P] [US4] Contract test for pull command success case in tests/contract/test_cli_pull.py
- [X] T079 [P] [US4] Contract test for pull command with component not found in tests/contract/test_cli_pull.py
- [X] T080 [P] [US4] Contract test for pull command with conflicts in tests/contract/test_cli_pull.py
- [X] T081 [P] [US4] Integration test for selective component pull in tests/integration/test_subtree_operations.py
- [X] T082 [P] [US4] Unit test for single component pull logic in tests/unit/test_subtree_manager.py

### Implementation for User Story 4 (GREEN phase)

- [X] T083 [P] [US4] Implement pull_component function in src/subtree_manager.py
- [X] T084 [US4] Implement component lookup by name or path in src/subtree_manager.py
- [X] T085 [US4] Implement pull command handler in src/cli.py (pull_command function)
- [X] T086 [US4] Add --branch flag for pulling from different branch
- [X] T087 [US4] Add --squash / --no-squash flags
- [X] T088 [US4] Add pull result reporting and conflict guidance

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: User Story 5 - Manage Manifest Configuration (Priority: P5)

**Goal**: Enable developers to view and validate manifest configuration

**Independent Test**: Run status command, verify display of all components with correct state information

### Tests for User Story 5 (TDD - RED phase)

- [X] T089 [P] [US5] Contract test for status command text output in tests/contract/test_cli_status.py
- [X] T090 [P] [US5] Contract test for status command JSON output in tests/contract/test_cli_status.py
- [X] T091 [P] [US5] Contract test for status command compact output in tests/contract/test_cli_status.py
- [X] T092 [P] [US5] Contract test for status --component flag in tests/contract/test_cli_status.py
- [X] T093 [P] [US5] Integration test for status across multiple component states in tests/integration/test_manifest_workflow.py
- [X] T094 [P] [US5] Unit test for status computation logic in tests/unit/test_subtree_manager.py

### Implementation for User Story 5 (GREEN phase)

- [X] T095 [P] [US5] Implement get_component_status function in src/subtree_manager.py
- [X] T096 [P] [US5] Implement get_all_component_status function in src/subtree_manager.py
- [X] T097 [US5] Implement status detection (up-to-date, ahead, behind, diverged, modified) in src/subtree_manager.py
- [X] T098 [US5] Implement status command handler in src/cli.py (status_command function)
- [X] T099 [US5] Implement text format output with color coding
- [X] T100 [US5] Implement JSON format output
- [X] T101 [US5] Implement compact/porcelain format output
- [X] T102 [US5] Add --component flag for selective status
- [X] T103 [US5] Add --format flag for output format selection
- [X] T104 [US5] Implement summary statistics (total, up-to-date, ahead, behind counts)

**Checkpoint**: All user stories complete - feature-complete CLI tool

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T105 [P] Add comprehensive docstrings (Google style) to all public functions in src/
- [X] T106 [P] Create README.md with installation, quickstart, usage examples
- [X] T107 [P] Add --verbose flag support with detailed logging in src/cli.py
- [X] T108 [P] Add --quiet flag support in src/cli.py
- [X] T109 [P] Add --no-color flag support for output formatting
- [X] T110 [P] Implement logging configuration in src/cli.py (using stdlib logging)
- [X] T111 [P] Add --version flag and version reporting
- [X] T112 Add global error handler with actionable messages in src/cli.py
- [X] T113 Validate all exit codes match contract specification
- [X] T114 [P] Add shell completion generation (bash/zsh) in src/cli.py
- [X] T115 Run mypy --strict and fix all type errors
- [X] T116 Run black formatter on all source files
- [X] T117 Run ruff linter and fix all issues
- [X] T118 Run pytest with coverage report, ensure ≥90% coverage
- [X] T119 [P] Create CHANGELOG.md with v0.1.0 release notes
- [X] T120 Verify quickstart.md examples work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4 → P5)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1 - Init)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2 - Sync)**: Can start after Foundational (Phase 2) - Extends US1 but independently testable
- **User Story 3 (P3 - Push)**: Can start after Foundational (Phase 2) - Uses US1 & US2 foundation but independently testable
- **User Story 4 (P4 - Pull)**: Can start after Foundational (Phase 2) - Uses US1 & US2 foundation but independently testable
- **User Story 5 (P5 - Status)**: Can start after Foundational (Phase 2) - Uses US1 & US2 foundation but independently testable

**Note**: While US2-5 extend US1 capabilities, each user story is independently testable. US1 provides the workspace initialization, but subsequent stories can be developed and tested in parallel once foundational phase completes.

### Within Each User Story

**TDD Cycle (NON-NEGOTIABLE per constitution)**:
1. **RED**: Write tests FIRST (contract, integration, unit tests for the story)
2. **Verify**: Ensure all tests FAIL (proving they actually test the missing functionality)
3. **GREEN**: Implement minimal code to pass tests
4. **REFACTOR**: Improve code while keeping tests green

**Task order within story**:
- Tests (contract → integration → unit) - ALL MUST FAIL before implementation
- Models/data structures
- Core business logic
- CLI command handlers
- Flags and options
- Error handling and reporting

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, user stories can be developed in parallel by different developers
- Within each story, tasks marked [P] can run in parallel (different files, no dependencies)
- Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1 (Init)

```bash
# RED Phase - Launch all test creation tasks together:
Task T020: "Contract test for init command success case in tests/contract/test_cli_init.py"
Task T021: "Contract test for init command with non-empty directory in tests/contract/test_cli_init.py"
Task T022: "Contract test for init command with invalid manifest in tests/contract/test_cli_init.py"
Task T023: "Contract test for init command exit codes in tests/contract/test_cli_init.py"
Task T024: "Integration test for manifest parsing workflow in tests/integration/test_manifest_workflow.py"
Task T025: "Integration test for git subtree add operations in tests/integration/test_subtree_operations.py"
Task T026: "Unit test for XML parsing logic in tests/unit/test_manifest_parser.py"
Task T027: "Unit test for manifest validation rules in tests/unit/test_manifest_parser.py"
Task T028: "Unit test for workspace initialization logic in tests/unit/test_workspace.py"

# Verify all tests FAIL

# GREEN Phase - Launch parallel implementation tasks:
Task T029: "Implement XML parsing in src/manifest_parser.py"
Task T030: "Implement manifest validation in src/manifest_parser.py"
# Then sequential tasks T031-T040 as they build on each other
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Init)
   - Write ALL tests (T020-T028)
   - Verify ALL tests FAIL
   - Implement (T029-T040)
   - Verify ALL tests PASS
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Ready for initial release or demo

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (sync capability)
4. Add User Story 3 → Test independently → Deploy/Demo (bidirectional workflow)
5. Add User Story 4 → Test independently → Deploy/Demo (granular control)
6. Add User Story 5 → Test independently → Deploy/Demo (status reporting)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Init)
   - Developer B: User Story 2 (Sync) - can start in parallel after foundational
   - Developer C: User Story 3 (Push) - can start in parallel after foundational
3. Stories complete and integrate independently
4. Each developer follows TDD: write tests → verify fail → implement → verify pass

---

## Notes

- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability
- **TDD NON-NEGOTIABLE**: Constitution requires red-green-refactor cycle
  - Write tests FIRST (T020-T028 before T029-T040)
  - Verify tests FAIL before implementation
  - Every public function/class MUST have tests
  - Test coverage MUST be ≥90%
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

## Test-First Examples

**User Story 1 - Init Command**:
1. Write test in `tests/contract/test_cli_init.py`:
   ```python
   def test_init_creates_git_repo_with_subtrees():
       # Arrange: create manifest
       # Act: run 'subrepo init manifest.xml'
       # Assert: .git exists, subtrees at correct paths
   ```
2. Run test → FAILS (command doesn't exist yet)
3. Implement init command in `src/cli.py`
4. Run test → PASSES
5. Refactor if needed, keeping tests green

**User Story 2 - Sync Command**:
1. Write test in `tests/contract/test_cli_sync.py`:
   ```python
   def test_sync_updates_all_subtrees():
       # Arrange: initialized workspace, make upstream commits
       # Act: run 'subrepo sync'
       # Assert: subtrees updated to latest commits
   ```
2. Run test → FAILS (sync command doesn't exist)
3. Implement sync command
4. Run test → PASSES
5. Refactor while keeping tests green

This ensures code is testable by design and provides living documentation of behavior.
