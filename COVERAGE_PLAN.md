# Test Coverage Improvement Plan

## Current Status

**Current Coverage**: 40.32%
**Target Coverage**: 85%
**Gap**: 467 statements need coverage (out of 1069 total)

### Module-by-Module Breakdown

| Module | Current | Target | Statements Missing |
|--------|---------|--------|--------------------|
| __init__.py | 100% | ✓ | 0 |
| exceptions.py | 100% | ✓ | 0 |
| models.py | 87% | 90% | 18 → 14 |
| git_commands.py | 78% | 90% | 28 → 13 |
| cli.py | 23% | 85% | 339 → 66 |
| subtree_manager.py | 23% | 85% | 126 → 25 |
| workspace.py | 22% | 85% | 52 → 10 |
| manifest_parser.py | 16% | 85% | 73 → 13 |
| __main__.py | 0% | 80% | 2 → 0 |

## Progress Made

### Fixed Issues
1. ✅ Fixed 7 failing CLI init tests by:
   - Correcting module name from `src` to `subrepo` in test commands
   - Fixing directory empty check to allow manifest file
   - Adding proper error messages to CLI functions
   - Using `--no-clone` flag to avoid GitHub access in tests

2. ✅ Created comprehensive unit tests for:
   - CLI logging and colorization functions
   - CLI init_command edge cases
   - Workspace initialization functions
   - Configuration save/load functionality

3. ✅ Improved coverage from 29% to 40%

### Current Test Results
- **Total Tests**: 269
- **Passed**: 146
- **Failed**: 26
- **Skipped**: 97

## Detailed Test Cases Needed to Reach 85%

### Priority 1: manifest_parser.py (16% → 85% = 60 statements)

**Missing Coverage**: Lines 58-154, 166-213

**Required Tests**:
1. `test_parse_manifest_basic_xml` - Test basic manifest parsing
2. `test_parse_manifest_with_multiple_remotes` - Multiple <remote> elements
3. `test_parse_manifest_with_default_element` - <default> parsing
4. `test_parse_manifest_project_inherits_defaults` - Default remote/revision applied
5. `test_parse_manifest_project_overrides` - Project-specific remote/revision
6. `test_parse_manifest_missing_name` - Error on missing project name
7. `test_parse_manifest_missing_path` - Path defaults to name
8. `test_parse_manifest_invalid_remote_reference` - Project references non-existent remote
9. `test_parse_manifest_no_projects_error` - Empty manifest fails validation
10. `test_parse_manifest_malformed_xml` - XML syntax errors
11. `test_parse_manifest_with_comments` - XML comments handled
12. `test_write_manifest` - Serialization back to XML
13. `test_validate_manifest_duplicate_paths` - Detect duplicate project paths
14. `test_validate_manifest_duplicate_names` - Detect duplicate project names

**Estimated Impact**: +60 statements = 76% total coverage

### Priority 2: workspace.py (22% → 85% = 42 statements)

**Missing Coverage**: Lines 34-82, 97-119, 129-154, 169-183, 198-216, 229-236, 245-258

**Required Tests**:
1. ✅ `test_init_workspace_empty_directory` - Already created
2. ✅ `test_init_workspace_with_manifest_file` - Already created
3. ✅ `test_init_workspace_non_empty_directory` - Already created
4. `test_init_workspace_git_repo_creation` - Verify git init called
5. `test_init_workspace_creates_subrepo_metadata` - .subrepo directory
6. `test_init_workspace_saves_manifest_copy` - manifest.xml in .subrepo
7. `test_init_workspace_computes_manifest_hash` - Hash calculation
8. `test_create_git_repo_configures_user` - Git user.name/email set
9. ✅ `test_create_git_repo_creates_initial_commit` - Already created
10. `test_create_git_repo_creates_readme` - README.md created
11. ✅ `test_save_workspace_config_atomic_write` - Already created
12. ✅ `test_load_workspace_config_missing_file` - Already created
13. ✅ `test_load_workspace_config_invalid_json` - Already created
14. `test_get_git_version` - Parse git --version output
15. `test_compute_manifest_hash_stable` - Same manifest = same hash

**Estimated Impact**: +42 statements = 80% total coverage

### Priority 3: subtree_manager.py (23% → 85% = 101 statements)

**Missing Coverage**: Lines 66-127, 139-155, 176-193, 209-217, 247-279, etc.

**Required Tests**:
1. `test_subtree_manager_init` - Constructor initialization
2. `test_pull_component_success` - Basic pull operation
3. `test_pull_component_with_branch` - Pull specific branch
4. `test_pull_component_with_squash` - Squash commits
5. `test_pull_component_not_found` - Component doesn't exist
6. `test_pull_component_up_to_date` - No changes to pull
7. `test_pull_component_with_conflicts` - Merge conflicts
8. `test_push_component_success` - Basic push operation
9. `test_push_component_dry_run` - Dry run mode
10. `test_push_component_no_changes` - Nothing to push
11. `test_push_component_upstream_diverged` - Non-fast-forward
12. `test_push_to_feature_branch` - Push to non-default branch
13. `test_get_component_status_up_to_date` - Status: clean
14. `test_get_component_status_ahead` - Local commits
15. `test_get_component_status_behind` - Remote ahead
16. `test_get_component_status_diverged` - Both have commits
17. `test_get_component_status_modified` - Uncommitted changes
18. `test_get_all_component_status` - Status for all components
19. `test_sync_component` - Sync operation
20. `test_find_subtree_prefix` - Locate subtree in repo

**Estimated Impact**: +101 statements = 90% total coverage

### Priority 4: cli.py (23% → 75% = 229 statements)

**Missing Coverage**: Large sections 242-328, 340-445, 457-530, 542-610, etc.

**Status Commands (242-328)**:
1. `test_status_command_all_components` - Default status output
2. `test_status_command_specific_component` - Status for one component
3. `test_status_command_json_format` - JSON output
4. `test_status_command_compact_format` - Compact output
5. `test_status_command_porcelain_format` - Machine-readable output
6. `test_status_command_not_in_workspace` - Error when not in workspace
7. `test_status_command_component_not_found` - Invalid component name

**Sync Commands (340-445)**:
8. `test_sync_command_all_components` - Sync all
9. `test_sync_command_specific_component` - Sync one
10. `test_sync_command_with_force` - Force sync with local changes
11. `test_sync_command_continue_on_error` - Don't stop on failure
12. `test_sync_command_not_in_workspace` - Error handling

**Pull Commands (457-530)**:
13. `test_pull_command_by_name` - Pull component by name
14. `test_pull_command_by_path` - Pull component by path
15. `test_pull_command_with_branch` - Pull from specific branch
16. `test_pull_command_with_squash` - Squash flag
17. `test_pull_command_component_not_found` - Error handling

**Push Commands (542-610)**:
18. `test_push_command_success` - Basic push
19. `test_push_command_dry_run` - Dry run mode
20. `test_push_command_with_branch` - Push to branch
21. `test_push_command_with_force` - Force push
22. `test_push_command_no_changes` - Nothing to push

**Main/Parser (753-776, 967-987)**:
23. `test_main_parses_verbose_flag` - Global flags
24. `test_main_parses_quiet_flag` - Output suppression
25. `test_main_routes_to_status` - Command routing
26. `test_main_routes_to_sync` - Command routing
27. `test_main_routes_to_pull` - Command routing
28. `test_main_routes_to_push` - Command routing
29. `test_handle_global_error` - Exception handling

**Estimated Impact**: +229 statements = 85%+ total coverage

### Priority 5: git_commands.py (78% → 90% = 15 statements)

**Missing Coverage**: Lines 93-94, 116, 180, 197-200, 363-366, 391-401, 422-425, 484

**Required Tests** (Error Paths):
1. `test_git_subtree_split_error` - Lines 93-94
2. `test_git_subtree_add_error` - Line 116
3. `test_git_push_error_non_fast_forward` - Lines 197-200
4. `test_git_fetch_remote_error` - Lines 363-366
5. `test_git_merge_error_conflicts` - Lines 391-401
6. `test_git_show_ref_commit_not_found` - Lines 422-425
7. `test_git_format_log_empty_range` - Line 484

**Estimated Impact**: +15 statements = 85% total coverage

### Priority 6: models.py (87% → 90% = 4 statements)

**Missing Coverage**: Lines 315, 317, 339, 341, 343, 366, 371, 376, 381, 386, 394-407

**Required Tests**:
1. `test_component_equality` - __eq__ method (315, 317)
2. `test_component_status_comparison` - Comparison operators (339, 341, 343)
3. `test_workspace_config_validation` - Validation methods (366, 371, 376, 381, 386)
4. `test_workspace_config_serialization` - to_dict/from_dict (394-407)

**Estimated Impact**: +4 statements = 90% total coverage

### Priority 7: __main__.py (0% → 80% = 2 statements)

**Required Tests**:
1. Integration test that runs `python -m subrepo --help`
2. This is automatically covered when contract tests run

**Estimated Impact**: +2 statements

## Implementation Strategy

### Phase 1 - Quick Wins (Target: 60% coverage)
1. ✅ Fix failing contract tests - **DONE**
2. ✅ Add basic unit tests for CLI and workspace - **DONE**
3. **TODO**: Add manifest_parser tests (Priority 1) - Would bring us to 76%

### Phase 2 - Core Functionality (Target: 80% coverage)
4. **TODO**: Complete workspace.py tests (Priority 2)
5. **TODO**: Add git_commands error path tests (Priority 5)
6. **TODO**: Add models edge case tests (Priority 6)

### Phase 3 - Full Coverage (Target: 85%+)
7. **TODO**: Add subtree_manager tests (Priority 3)
8. **TODO**: Add comprehensive CLI command tests (Priority 4)

## Summary

To reach 85% coverage:
- **Completed**: 40% (431 statements covered)
- **Remaining**: 45% (467 statements to cover)
- **Estimated test cases needed**: ~80-100 additional test functions

### Fastest Path to 85%
1. manifest_parser.py tests: +60 statements (→ 76%)
2. workspace.py tests: +42 statements (→ 80%)
3. git_commands.py error tests: +15 statements (→ 82%)
4. Partial subtree_manager tests: +35 statements (→ 85%)

**Total needed**: ~152 statements across ~40 test functions
