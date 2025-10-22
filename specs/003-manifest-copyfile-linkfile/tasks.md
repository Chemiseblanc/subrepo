# Tasks: Manifest Copyfile and Linkfile Support

**Input**: Design documents from `/specs/003-manifest-copyfile-linkfile/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: This project follows Test-Driven Development (TDD) as a constitutional requirement. All test tasks are included and MUST be written before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions
- Single project structure: `subrepo/` for source, `tests/` for tests
- Paths follow plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and exception infrastructure

- [X] T001 [P] Add FileOperationError exception in subrepo/exceptions.py
- [X] T002 [P] Add PathSecurityError exception in subrepo/exceptions.py

**Checkpoint**: Exception infrastructure ready ✅

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and validation that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational Components

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T003 [P] Test Copyfile model validation (empty src/dest, ".." in paths, absolute paths) in tests/unit/test_models.py
- [X] T004 [P] Test Linkfile model validation (empty src/dest, ".." in paths, absolute paths) in tests/unit/test_models.py
- [X] T005 [P] Test Project model with copyfiles and linkfiles lists in tests/unit/test_models.py
- [X] T006 Test Manifest.validate() detects duplicate dest paths across projects in tests/unit/test_models.py

### Implementation for Foundational Components

- [X] T007 [P] Create Copyfile dataclass (frozen=True) with __post_init__ validation in subrepo/models.py
- [X] T008 [P] Create Linkfile dataclass (frozen=True) with __post_init__ validation in subrepo/models.py
- [X] T009 Extend Project model to add copyfiles and linkfiles list fields with default_factory in subrepo/models.py
- [X] T010 Extend Manifest.validate() to check dest path uniqueness across all projects in subrepo/models.py
- [X] T011 [P] Create FileOperationResult dataclass in subrepo/models.py
- [X] T012 [P] Create FileOperationSummary dataclass with computed properties in subrepo/models.py

**Checkpoint**: Foundation ready - all models defined and validated. User story implementation can now begin in parallel ✅

---

## Phase 3: User Story 1 - Copy Project Files to Workspace Root (Priority: P1) 🎯 MVP

**Goal**: Enable users to automatically copy files from project directories to workspace root during sync

**Independent Test**: Create manifest with copyfile elements, run sync, verify files copied from project to workspace with correct permissions

### Tests for User Story 1

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Test parse_project() extracts copyfile elements from XML in tests/unit/test_manifest_parser.py
- [X] T014 [P] [US1] Test parse_project() creates Copyfile objects with correct src/dest in tests/unit/test_manifest_parser.py
- [X] T015 [P] [US1] Test parse_project() handles multiple copyfile elements per project in tests/unit/test_manifest_parser.py
- [X] T016 [P] [US1] Test validate_path_security() rejects ".." components in tests/unit/test_file_operations.py
- [X] T017 [P] [US1] Test validate_path_security() rejects absolute paths in tests/unit/test_file_operations.py
- [X] T018 [P] [US1] Test validate_path_security() rejects paths escaping workspace in tests/unit/test_file_operations.py
- [X] T019 [P] [US1] Test validate_path_security() accepts valid relative paths in tests/unit/test_file_operations.py
- [X] T020 [P] [US1] Test copy_file() preserves permissions using shutil.copy2() in tests/unit/test_file_operations.py
- [X] T021 [P] [US1] Test copy_file() creates parent directories if missing in tests/unit/test_file_operations.py
- [X] T022 [P] [US1] Test copy_file() dereferences symlinks at source in tests/unit/test_file_operations.py
- [X] T023 [P] [US1] Test copy_file() overwrites existing dest files in tests/unit/test_file_operations.py
- [X] T024 [P] [US1] Test copy_file() handles missing source file error in tests/unit/test_file_operations.py
- [ ] T025 [P] [US1] Integration test: sync with copyfile creates files at dest in tests/integration/test_manifest_workflow.py
- [ ] T026 [P] [US1] Integration test: sync with multiple copyfiles in one project in tests/integration/test_manifest_workflow.py
- [ ] T027 [P] [US1] Contract test: CLI displays "Copied: src → dest" progress messages in tests/contract/test_cli_sync.py
- [ ] T028 [P] [US1] Contract test: CLI displays file operation summary at end in tests/contract/test_cli_sync.py

### Implementation for User Story 1

- [x] T029 [US1] Extend parse_project() in manifest_parser.py to find copyfile elements and create Copyfile objects
- [x] T030 [US1] Create file_operations.py module with validate_path_security() function using pathlib.Path.resolve() and is_relative_to()
- [x] T031 [US1] Implement copy_file() function in file_operations.py using shutil.copy2() for permission preservation
- [x] T032 [US1] Implement execute_copyfile_operations() function in file_operations.py to process all copyfiles for a project
- [x] T033 [US1] Extend SubtreeManager to call execute_copyfile_operations() after git subtree sync in subrepo/subtree_manager.py
- [x] T034 [US1] Update CLI to display copyfile progress messages during sync in subrepo/cli.py
- [x] T035 [US1] Update CLI to display FileOperationSummary at sync completion in subrepo/cli.py

**Checkpoint**: User Story 1 complete - copyfile functionality fully functional and independently testable

---

## Phase 4: User Story 2 - Create Symlinks to Project Files (Priority: P1)

**Goal**: Enable users to create symbolic links from workspace root to project files/directories

**Independent Test**: Create manifest with linkfile elements, run sync, verify symlinks created pointing to correct project locations, verify fallback to copy on unsupported filesystems

### Tests for User Story 2

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T036 [P] [US2] Test parse_project() extracts linkfile elements from XML in tests/unit/test_manifest_parser.py
- [X] T037 [P] [US2] Test parse_project() creates Linkfile objects with correct src/dest in tests/unit/test_manifest_parser.py
- [X] T038 [P] [US2] Test parse_project() handles multiple linkfile elements per project in tests/unit/test_manifest_parser.py
- [X] T039 [P] [US2] Test create_symlink() creates symlink using os.symlink() in tests/unit/test_file_operations.py
- [X] T040 [P] [US2] Test create_symlink() falls back to copy on OSError (unsupported filesystem) in tests/unit/test_file_operations.py
- [ ] T041 [P] [US2] Test create_symlink() logs warning when fallback occurs in tests/unit/test_file_operations.py
- [X] T042 [P] [US2] Test create_symlink() creates parent directories if missing in tests/unit/test_file_operations.py
- [X] T043 [P] [US2] Test create_symlink() handles symlink to directory in tests/unit/test_file_operations.py
- [ ] T044 [P] [US2] Integration test: sync with linkfile creates symlinks at dest in tests/integration/test_manifest_workflow.py
- [ ] T045 [P] [US2] Integration test: sync with linkfile fallback to copy shows warning in tests/integration/test_manifest_workflow.py
- [ ] T046 [P] [US2] Contract test: CLI displays "Linked: dest → src" for successful symlinks in tests/contract/test_cli_sync.py
- [ ] T047 [P] [US2] Contract test: CLI displays "Warning: Symlinks not supported, copying instead" for fallback in tests/contract/test_cli_sync.py

### Implementation for User Story 2

- [X] T048 [US2] Extend parse_project() in manifest_parser.py to find linkfile elements and create Linkfile objects
- [X] T049 [US2] Implement create_symlink() function in file_operations.py with try/except fallback to copy
- [X] T050 [US2] Implement execute_linkfile_operations() function in file_operations.py to process all linkfiles for a project
- [X] T051 [US2] Extend SubtreeManager to call execute_linkfile_operations() after copyfile operations in subrepo/subtree_manager.py
- [X] T052 [US2] Update CLI to display linkfile progress messages and warnings in subrepo/cli.py
- [X] T053 [US2] Update FileOperationSummary.format_summary() to show fallback count in subrepo/models.py

**Checkpoint**: User Story 2 complete - linkfile functionality fully functional with graceful degradation

---

## Phase 5: User Story 3 - Update Copied and Linked Files on Re-sync (Priority: P2)

**Goal**: Ensure file operations refresh on re-sync to reflect latest project content

**Independent Test**: Run initial sync, modify source files, run sync again, verify copied files updated and symlinks recreated

### Tests for User Story 3

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T054 [P] [US3] Test copy_file() overwrites existing dest file with new content in tests/unit/test_file_operations.py
- [ ] T055 [P] [US3] Test create_symlink() removes existing symlink before recreating in tests/unit/test_file_operations.py
- [ ] T056 [P] [US3] Integration test: re-sync overwrites previously copied files in tests/integration/test_manifest_workflow.py
- [ ] T057 [P] [US3] Integration test: re-sync recreates symlinks pointing to updated src in tests/integration/test_manifest_workflow.py
- [ ] T058 [P] [US3] Integration test: removed copyfile element leaves file in workspace in tests/integration/test_manifest_workflow.py

### Implementation for User Story 3

- [ ] T059 [US3] Verify copy_file() already overwrites existing files (shutil.copy2 default behavior) in subrepo/file_operations.py
- [ ] T060 [US3] Update create_symlink() to check if dest exists and remove before creating symlink in subrepo/file_operations.py

**Checkpoint**: User Story 3 complete - re-sync behavior validated

---

## Phase 6: User Story 4 - Handle File Operation Errors Gracefully (Priority: P2)

**Goal**: Provide clear error messages, continue processing on failures, report all errors at end with non-zero exit code

**Independent Test**: Create manifest with invalid copyfile/linkfile elements, run sync, verify sync continues processing all projects and reports all failures

### Tests for User Story 4

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T061 [P] [US4] Test validate_path_security() raises PathSecurityError for "../" in path in tests/unit/test_file_operations.py
- [ ] T062 [P] [US4] Test execute_copyfile_operations() catches errors and returns FileOperationResult with error_message in tests/unit/test_file_operations.py
- [ ] T063 [P] [US4] Test execute_linkfile_operations() catches errors and returns FileOperationResult with error_message in tests/unit/test_file_operations.py
- [ ] T064 [P] [US4] Test copy_file() raises FileOperationError when source missing in tests/unit/test_file_operations.py
- [ ] T065 [P] [US4] Test copy_file() raises FileOperationError when dest is existing directory in tests/unit/test_file_operations.py
- [ ] T066 [P] [US4] Test Manifest.validate() returns errors for duplicate dest paths in tests/unit/test_models.py
- [ ] T067 [P] [US4] Integration test: sync continues after copyfile error and processes remaining projects in tests/integration/test_manifest_workflow.py
- [ ] T068 [P] [US4] Integration test: sync collects multiple errors and reports summary at end in tests/integration/test_manifest_workflow.py
- [ ] T069 [P] [US4] Contract test: CLI exits with code 1 when file operations fail in tests/contract/test_cli_sync.py
- [ ] T070 [P] [US4] Contract test: CLI displays "Failures:" section listing all errors in tests/contract/test_cli_sync.py
- [ ] T071 [P] [US4] Contract test: manifest validation failure shows duplicate dest error in tests/contract/test_cli_sync.py

### Implementation for User Story 4

- [ ] T072 [US4] Update execute_copyfile_operations() to catch exceptions and create FileOperationResult with success=False in subrepo/file_operations.py
- [ ] T073 [US4] Update execute_linkfile_operations() to catch exceptions and create FileOperationResult with success=False in subrepo/file_operations.py
- [ ] T074 [US4] Update SubtreeManager to collect all FileOperationResult objects across projects in subrepo/subtree_manager.py
- [ ] T075 [US4] Update CLI to return non-zero exit code if FileOperationSummary.failed_count > 0 in subrepo/cli.py
- [ ] T076 [US4] Update CLI to handle Manifest.validate() errors and display before sync in subrepo/cli.py

**Checkpoint**: User Story 4 complete - error handling robust and user-friendly

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Quality assurance, documentation, and final validation

- [ ] T077 [P] Create test fixture manifest with copyfile/linkfile in tests/integration/fixtures/manifest_with_files.xml
- [X] T078 [P] Add module-level docstrings to file_operations.py
- [X] T079 [P] Run mypy --strict and fix any type errors
- [X] T080 [P] Run ruff check subrepo and fix any linting issues
- [X] T081 [P] Run black subrepo tests to format code
- [ ] T082 Verify test coverage ≥90% with pytest --cov
- [ ] T083 Run quickstart.md validation (verify all phases work)
- [ ] T084 [P] Update CLAUDE.md if any patterns changed
- [ ] T085 Final integration test across all user stories

**Checkpoint**: Feature complete, all quality gates passed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1): Independent, can start after Foundational
  - User Story 2 (P1): Independent, can start after Foundational (parallel with US1)
  - User Story 3 (P2): Depends on US1 and US2 completion (extends their functionality)
  - User Story 4 (P2): Depends on US1 and US2 completion (error handling for them)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - No dependencies on other stories (can run parallel with US1)
- **User Story 3 (P2)**: Depends on US1 and US2 - Extends re-sync behavior for both
- **User Story 4 (P2)**: Depends on US1 and US2 - Adds error handling for both

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD requirement)
- All tests for a story marked [P] can run in parallel
- Models/parsing before file operations
- File operations before integration with SubtreeManager
- SubtreeManager integration before CLI display
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
- T001 and T002 can run in parallel

**Phase 2 (Foundational) - Tests**:
- T003, T004, T005 can run in parallel
- T006 runs after T003-T005 (depends on Manifest.validate)

**Phase 2 (Foundational) - Implementation**:
- T007, T008, T011, T012 can run in parallel
- T009 runs after T007, T008 (depends on Copyfile/Linkfile)
- T010 runs after T009 (depends on Project extension)

**Phase 3 (US1) - Tests**:
- T013-T024 can all run in parallel (different test files/test functions)

**Phase 3 (US1) - Implementation**:
- T029, T030 can run in parallel
- T031 runs after T030 (depends on validate_path_security)
- T032 runs after T031 (depends on copy_file)
- T033-T035 run sequentially (modify same files)

**Phase 4 (US2) - Tests**:
- T036-T047 can all run in parallel

**Phase 4 (US2) - Implementation**:
- T048, T049 can run in parallel
- T050 runs after T049
- T051-T053 run sequentially

**Phase 5 (US3) - Tests**:
- T054-T058 can all run in parallel

**Phase 6 (US4) - Tests**:
- T061-T071 can all run in parallel

**Phase 7 (Polish)**:
- T077-T081, T084 can all run in parallel

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all tests for User Story 1 together:
Task: "Test parse_project() extracts copyfile elements from XML in tests/unit/test_manifest_parser.py"
Task: "Test parse_project() creates Copyfile objects with correct src/dest in tests/unit/test_manifest_parser.py"
Task: "Test validate_path_security() rejects '..' components in tests/unit/test_file_operations.py"
Task: "Test copy_file() preserves permissions using shutil.copy2() in tests/unit/test_file_operations.py"
# ... all 16 tests can be written in parallel
```

## Parallel Example: User Story 1 & 2 Together

```bash
# Once Foundational phase complete, these can proceed in parallel:
Team A: Complete all of Phase 3 (User Story 1 - copyfile)
Team B: Complete all of Phase 4 (User Story 2 - linkfile)
# Both teams work independently, then integrate in Phase 5
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup (exceptions)
2. Complete Phase 2: Foundational (models, validation) - CRITICAL BLOCKER
3. Complete Phase 3: User Story 1 (copyfile)
4. Complete Phase 4: User Story 2 (linkfile)
5. **STOP and VALIDATE**: Test both copyfile and linkfile independently
6. Deploy/demo MVP with both P1 stories

**Rationale**: Both US1 and US2 are P1 (equally important) and provide complete git-repo manifest compatibility.

### Incremental Delivery

1. Setup + Foundational → Foundation ready ✓
2. Add User Story 1 → Test independently → Copyfile works ✓
3. Add User Story 2 → Test independently → Linkfile works ✓
4. **MVP COMPLETE** - Both P1 stories delivered
5. Add User Story 3 → Test independently → Re-sync works ✓
6. Add User Story 4 → Test independently → Error handling robust ✓
7. Polish → Production ready ✓

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (4-6 hours)
2. Once Foundational complete:
   - Developer A: User Story 1 (copyfile) - 28 tests + 7 implementation tasks
   - Developer B: User Story 2 (linkfile) - 12 tests + 6 implementation tasks
3. After US1 & US2 complete:
   - Developer A: User Story 3 (re-sync) - 5 tests + 2 implementation tasks
   - Developer B: User Story 4 (error handling) - 11 tests + 5 implementation tasks
4. Team completes Polish together

**Estimated Effort**:
- Setup: 1 hour
- Foundational: 4-6 hours (blocking)
- User Story 1: 8-12 hours
- User Story 2: 6-8 hours
- User Story 3: 2-4 hours
- User Story 4: 4-6 hours
- Polish: 2-4 hours
- **Total: 27-41 hours** (single developer) or **15-25 hours** (two developers in parallel)

---

## Notes

- **TDD Required**: All tests MUST be written first and FAIL before implementation (constitutional requirement)
- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests must fail before implementing (red-green-refactor)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- mypy --strict, ruff, black must pass before completion
- Coverage ≥90% enforced by pytest configuration
