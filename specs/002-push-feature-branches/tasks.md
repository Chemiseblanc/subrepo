# Tasks: Feature Branch Push Synchronization

**Input**: Design documents from `/specs/002-push-feature-branches/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: This project follows TDD (constitution requirement). All tests MUST be written FIRST and verified to FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- Single Python CLI project: `src/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure (already exists, validate only)

- [ ] T001 Verify project structure matches plan.md (src/, tests/, pyproject.toml)
- [ ] T002 Verify Python 3.14+ and development dependencies (pytest, mypy, ruff, black)
- [ ] T003 [P] Run existing tests to ensure environment is working (pytest)
- [ ] T004 [P] Verify type checking works (mypy src --strict)
- [ ] T005 [P] Verify linting works (ruff check src)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core git operations and exception framework that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests (Write FIRST, verify they FAIL)

- [x] T006 [P] Write tests for `is_commit_sha()` in tests/unit/test_manifest_utils.py
- [x] T007 [P] Write tests for `DetachedHeadError` in tests/unit/test_exceptions.py
- [x] T008 [P] Write tests for `detect_current_branch()` in tests/unit/test_git_branch_detection.py
- [x] T009 [P] Write tests for `detect_default_branch()` in tests/unit/test_git_branch_detection.py
- [x] T010 [P] Write tests for `extract_default_branch_from_project()` in tests/unit/test_manifest_integration.py

### Implementation (After tests FAIL)

- [x] T011 [P] Add new exception types to src/exceptions.py (DetachedHeadError, BranchError, PushError, NonFastForwardError, BranchProtectionError, RepositoryNotFoundError)
- [x] T012 [P] Add `is_commit_sha()` function to src/manifest_parser.py
- [x] T013 [P] Add `PushResult` dataclass to src/models.py
- [x] T014 [P] Add `BranchInfo` dataclass to src/models.py
- [x] T015 [P] Add `PushStatus` and `PushAction` enums to src/models.py
- [x] T016 Add `detect_current_branch()` to src/git_commands.py (depends on T011)
- [x] T017 Add `detect_default_branch()` to src/git_commands.py (depends on T011)
- [x] T018 Add `extract_default_branch_from_project()` to src/manifest_parser.py (depends on T012, T013, T014)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Push Component from Feature Branch (Priority: P1) 🎯 MVP

**Goal**: Enable pushing a single component to a matching feature branch in its remote repository, creating the branch if necessary

**Independent Test**: Create a feature branch locally, modify a component, run `subrepo push <component>`, verify the remote has a branch with the same name containing the changes

### Tests for User Story 1 (Write FIRST, verify they FAIL)

- [x] T019 [P] [US1] Write contract test for basic push command in tests/contract/test_cli_push_contract.py
- [x] T020 [P] [US1] Write unit tests for `create_branch_info()` in tests/unit/test_branch_info_creation.py
- [x] T021 [P] [US1] Write unit tests for `determine_target_branch()` in tests/unit/test_target_branch_logic.py
- [x] T022 [P] [US1] Write unit tests for `execute_git_push()` in tests/unit/test_git_push_execution.py
- [x] T023 [P] [US1] Write integration test for feature branch push in tests/integration/test_push_feature_branch.py

### Implementation for User Story 1 (After tests FAIL)

- [x] T024 [P] [US1] Implement `create_branch_info()` in src/git_commands.py (depends on T016, T017)
- [x] T025 [P] [US1] Implement `determine_target_branch()` in src/git_commands.py (depends on T018, T024)
- [x] T026 [US1] Implement `execute_git_push()` in src/git_commands.py (depends on T025)
- [x] T027 [US1] Implement `push_single_component()` in src/subtree_manager.py (depends on T026, T013)
- [x] T028 [US1] Add `--dry-run` flag support to CLI in src/cli.py
- [x] T029 [US1] Update push command in src/cli.py to use branch-aware logic (depends on T027, T028)
- [x] T030 [US1] Add success output formatting for branch creation in src/cli.py

**Checkpoint**: At this point, User Story 1 should be fully functional - can push single component from feature branch to matching remote branch

---

## Phase 4: User Story 2 - Default Branch Behavior Unchanged (Priority: P2)

**Goal**: Ensure pushing from default branch continues to work exactly as before (backward compatibility)

**Independent Test**: Checkout default branch, modify a component, run `subrepo push <component>`, verify it pushes to the default branch as it did before this feature

### Tests for User Story 2 (Write FIRST, verify they FAIL)

- [x] T031 [P] [US2] Write unit tests for default branch detection logic in tests/unit/test_default_branch_compatibility.py
- [x] T032 [P] [US2] Write integration test for default branch push in tests/integration/test_push_default_branch.py
- [x] T033 [P] [US2] Write regression tests comparing old vs new behavior in tests/integration/test_backward_compatibility.py

### Implementation for User Story 2 (After tests FAIL)

- [x] T034 [US2] Add backward compatibility check in `determine_target_branch()` in subrepo/git_commands.py
- [x] T035 [US2] Verify existing push logic is preserved when on default branch in subrepo/subtree_manager.py
- [x] T036 [US2] Add integration test validation for default branch push behavior

**Checkpoint**: At this point, both User Stories 1 AND 2 should work independently - feature branch push works, default branch push unchanged

---

## Phase 5: User Story 3 - Multi-Component Feature Branch Push (Priority: P2)

**Goal**: Enable pushing multiple components at once, with each going to matching feature branches, continuing on failure

**Independent Test**: Create feature branch, modify multiple components, run `subrepo push comp1 comp2 comp3`, verify all component repos have matching feature branches

### Tests for User Story 3 (Write FIRST, verify they FAIL)

- [ ] T037 [P] [US3] Write unit tests for `MultiPushSummary` dataclass in tests/unit/test_multi_push_result.py
- [ ] T038 [P] [US3] Write unit tests for continue-on-error logic in tests/unit/test_push_error_handling.py
- [ ] T039 [P] [US3] Write integration test for multi-component push in tests/integration/test_multi_component_push.py
- [ ] T040 [P] [US3] Write integration test for partial failure scenario in tests/integration/test_multi_push_partial_failure.py

### Implementation for User Story 3 (After tests FAIL)

- [ ] T041 [P] [US3] Add `MultiPushSummary` dataclass to src/models.py
- [ ] T042 [US3] Implement `push_multiple_components()` in src/subtree_manager.py (depends on T027, T041)
- [ ] T043 [US3] Add error collection and continue-on-failure logic in src/subtree_manager.py (depends on T042)
- [ ] T044 [US3] Implement summary report formatting in src/subtree_manager.py (depends on T041, T043)
- [ ] T045 [US3] Update CLI to support multi-component push in src/cli.py (depends on T042)
- [ ] T046 [US3] Add summary output to CLI push command in src/cli.py (depends on T044)

**Checkpoint**: All three user stories should now be independently functional - single push, default branch, and multi-component push all work

---

## Phase 6: Error Handling & Edge Cases

**Purpose**: Handle error scenarios identified in specification

### Tests for Error Handling (Write FIRST, verify they FAIL)

- [ ] T047 [P] Write tests for non-fast-forward detection in tests/unit/test_non_fast_forward.py
- [ ] T048 [P] Write tests for protected branch detection in tests/unit/test_protected_branch.py
- [ ] T049 [P] Write tests for missing repository detection in tests/unit/test_missing_repository.py
- [ ] T050 [P] Write tests for detached HEAD error in tests/unit/test_detached_head.py
- [ ] T051 [P] Write integration test for --force flag in tests/integration/test_force_push.py

### Implementation for Error Handling (After tests FAIL)

- [ ] T052 [P] Implement non-fast-forward detection via dry-run in src/git_commands.py
- [ ] T053 [P] Implement protected branch error parsing in src/git_commands.py
- [ ] T054 [P] Implement missing repository error parsing in src/git_commands.py
- [ ] T055 Add --force flag to CLI in src/cli.py
- [ ] T056 Add force push logic to `execute_git_push()` in src/git_commands.py (depends on T055)
- [ ] T057 Add error message formatting for all error types in src/cli.py

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T058 [P] Add comprehensive docstrings to all new functions in src/
- [ ] T059 [P] Add logging for all push operations in src/subtree_manager.py
- [ ] T060 [P] Update CLI help text for push command in src/cli.py
- [ ] T061 [P] Add exit code handling per contract in src/cli.py
- [ ] T062 Run mypy --strict on all src/ files and fix any type errors
- [ ] T063 Run ruff check and fix any linting errors
- [ ] T064 Run black to format all code
- [ ] T065 Verify test coverage is ≥90% (pytest --cov=src --cov-report=term-missing)
- [ ] T066 Run full integration test suite from quickstart.md
- [ ] T067 Update CLAUDE.md if any new patterns or commands were added

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-5)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational
  - User Story 2 (P2): Can start after Foundational (no dependency on US1)
  - User Story 3 (P2): Depends on User Story 1 completion (uses push_single_component)
- **Error Handling (Phase 6)**: Can start after US1 is complete (extends push logic)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends only on Foundational (Phase 2) - Independent of US1, US3
- **User Story 3 (P2)**: Depends on Foundational (Phase 2) AND User Story 1 (uses push_single_component)

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD requirement)
- Models before services
- Git operations before subtree manager operations
- Core implementation before CLI integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: All tasks can run in parallel (verification only)
- **Phase 2 Tests**: T006-T010 can all run in parallel
- **Phase 2 Implementation**: T011-T015 can run in parallel, T016-T018 must be sequential
- **User Story 1 Tests**: T019-T023 can all run in parallel
- **User Story 1 Implementation**: T024-T025 parallel, then T026-T030 sequential
- **User Story 2**: Can run in parallel with User Story 1 implementation (independent)
- **User Story 3**: Cannot start until US1 complete
- **Error Handling Tests**: T047-T051 can all run in parallel
- **Error Handling Implementation**: T052-T054 parallel, T055-T057 sequential
- **Polish**: T058-T061 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Write contract test for basic push command in tests/contract/test_cli_push_contract.py"
Task: "Write unit tests for create_branch_info() in tests/unit/test_branch_info_creation.py"
Task: "Write unit tests for determine_target_branch() in tests/unit/test_target_branch_logic.py"
Task: "Write unit tests for execute_git_push() in tests/unit/test_git_push_execution.py"
Task: "Write integration test for feature branch push in tests/integration/test_push_feature_branch.py"

# After tests fail, launch first wave of implementation:
Task: "Implement create_branch_info() in src/git_commands.py"
Task: "Implement determine_target_branch() in src/git_commands.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005) - ~15 minutes
2. Complete Phase 2: Foundational (T006-T018) - ~4 hours
   - **CRITICAL CHECKPOINT**: Verify all foundation tests pass
3. Complete Phase 3: User Story 1 (T019-T030) - ~6 hours
   - **STOP and VALIDATE**: Test User Story 1 independently
   - Run integration test: `pytest tests/integration/test_push_feature_branch.py -v`
   - Manual test: Create feature branch, push component, verify remote
4. If MVP validates successfully → Deploy/demo

**Estimated MVP Completion**: ~10 hours of focused development

### Incremental Delivery

1. Complete Setup + Foundational (Phases 1-2) → Foundation ready (~4 hours)
2. Add User Story 1 (Phase 3) → Test independently → First deployable increment (MVP!) (~6 hours)
3. Add User Story 2 (Phase 4) → Test independently → Backward compatibility proven (~2 hours)
4. Add User Story 3 (Phase 5) → Test independently → Multi-component feature complete (~4 hours)
5. Add Error Handling (Phase 6) → Production-ready error scenarios (~3 hours)
6. Add Polish (Phase 7) → Code quality finalization (~2 hours)

**Estimated Total**: ~21 hours for complete feature

### Parallel Team Strategy

With 2 developers:

1. Both complete Setup + Foundational together (Phases 1-2)
2. Once Foundational is done:
   - Developer A: User Story 1 (Phase 3)
   - Developer B: User Story 2 (Phase 4) in parallel
3. After US1 complete:
   - Developer A: User Story 3 (Phase 5)
   - Developer B: Error Handling (Phase 6) in parallel
4. Both: Polish (Phase 7) together

**Estimated with 2 developers**: ~12 hours wall-clock time

---

## Notes

- [P] tasks = different files, no dependencies - safe to parallelize
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **TDD CRITICAL**: Verify tests fail (RED) before implementing (GREEN)
- Test coverage must be ≥90% (constitution requirement)
- All code must pass mypy --strict (constitution requirement)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- User Story 3 depends on User Story 1 (not independent due to code reuse)
