# CLI Contract: Push Command

**Feature**: 002-push-feature-branches
**Command**: `subrepo push`
**Date**: 2025-10-18

## Command Signature

```
subrepo push [OPTIONS] [COMPONENT...]
```

## Description

Push local changes for one or more components to their remote repositories. When on a feature branch, pushes to a branch with the same name in the component's remote repository (creating it if necessary). When on the default branch, pushes to the default branch (backward compatible behavior).

## Arguments

### COMPONENT (optional, variadic)

**Type**: String (path or name)
**Required**: No
**Default**: All components with local changes

**Description**: One or more component paths or names to push. If omitted, pushes all components that have local changes.

**Examples**:
```bash
subrepo push platform/core              # Push single component
subrepo push platform/core platform/auth  # Push multiple components
subrepo push                             # Push all changed components
```

**Validation**:
- Must match a component defined in manifest.xml
- Can be either project name (e.g., "org/repo") or local path (e.g., "platform/core")

## Options

### --force / -f

**Type**: Boolean flag
**Default**: False

**Description**: Allow non-fast-forward pushes (force push). Required when the remote branch has diverged from the local branch.

**Examples**:
```bash
subrepo push --force platform/core       # Force push to remote
subrepo push -f platform/core platform/auth  # Short form
```

**Warning**: Force pushing can overwrite remote changes. Use with caution.

### --dry-run / -n

**Type**: Boolean flag
**Default**: False

**Description**: Perform all checks and show what would be pushed without actually pushing to remote repositories.

**Examples**:
```bash
subrepo push --dry-run                   # Check what would be pushed
subrepo push -n platform/core           # Short form
```

### --verbose / -v

**Type**: Boolean flag
**Default**: False

**Description**: Show detailed output including git commands executed and their results.

**Examples**:
```bash
subrepo push --verbose platform/core     # Detailed output
subrepo push -v                         # Short form
```

## Exit Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| 0 | Success | All requested pushes completed successfully |
| 1 | Partial failure | Some components pushed successfully, others failed |
| 2 | Complete failure | All push operations failed |
| 3 | Configuration error | Invalid manifest, missing components, detached HEAD |
| 4 | Permission error | Authentication failure, protected branch |

## Output Format

### Success (Default Branch)

```
Pushing platform/core to origin/main... ✓
Pushing platform/auth to origin/main... ✓

Successfully pushed 2 components to main
```

### Success (Feature Branch)

```
Current branch: 002-push-feature-branches
Default branch: main

Pushing platform/core to origin/002-push-feature-branches... created ✓
Pushing platform/auth to origin/002-push-feature-branches... updated ✓

Push Summary: 2/2 succeeded
  Created: 1
  Updated: 1
  Failed: 0
```

### Partial Failure

```
Current branch: 002-push-feature-branches
Default branch: main

Pushing platform/core to origin/002-push-feature-branches... created ✓
Pushing platform/auth to origin/002-push-feature-branches... failed ✗
Pushing platform/ui to origin/002-push-feature-branches... updated ✓

Push Summary: 2/3 succeeded
  Created: 1
  Updated: 1
  Failed: 1

Failures:
  - platform/auth: Remote repository does not exist. Create the repository before pushing.

Exit code: 1
```

### Error: Non-Fast-Forward

```
Current branch: 002-push-feature-branches

Pushing platform/core to origin/002-push-feature-branches... failed ✗

Error: Push to platform/core:002-push-feature-branches rejected (non-fast-forward).
Remote branch has diverged from local. Use --force to override.

Suggestion: Run 'git pull' or use 'subrepo push --force' to force push.

Exit code: 2
```

### Error: Protected Branch

```
Current branch: release-1.0

Pushing platform/core to origin/release-1.0... failed ✗

Error: Branch 'release-1.0' is protected in platform/core.
Contact repository administrator to modify protection rules.

Exit code: 4
```

### Error: Detached HEAD

```
Error: Cannot push from detached HEAD state.
Check out a branch before pushing:
  git checkout main
  git checkout -b new-feature-branch

Exit code: 3
```

## Behavior Specification

### Scenario 1: Push Single Component on Feature Branch

**Given**: User is on feature branch "feature-auth"
**When**: User runs `subrepo push platform/core`
**Then**:
- Detect current branch: "feature-auth"
- Detect default branch from manifest or git
- Compare: "feature-auth" != default → feature branch mode
- Push to `origin/feature-auth` in platform/core repository
- Create branch if doesn't exist, update if exists
- Report: "created" or "updated" status

### Scenario 2: Push All Components on Default Branch

**Given**: User is on default branch "main"
**When**: User runs `subrepo push`
**Then**:
- Detect current branch: "main"
- Detect default branch: "main"
- Compare: "main" == default → default branch mode
- Push all changed components to their default branches
- Maintain existing behavior (backward compatible)

### Scenario 3: Non-Fast-Forward Without Force

**Given**: Remote branch "feature-auth" has commits not in local
**When**: User runs `subrepo push platform/core`
**Then**:
- Detect non-fast-forward via dry-run
- Display error message explaining divergence
- Suggest using --force or pulling first
- Exit with code 2 without pushing

### Scenario 4: Multi-Component Push with Failures

**Given**: User is pushing 3 components, 1 has errors
**When**: User runs `subrepo push comp1 comp2 comp3`
**Then**:
- Attempt push for comp1 → success
- Attempt push for comp2 → failure (continue anyway)
- Attempt push for comp3 → success
- Display summary with 2 successes, 1 failure
- List failure details
- Exit with code 1 (partial failure)

### Scenario 5: Dry Run Mode

**Given**: User wants to see what would be pushed
**When**: User runs `subrepo push --dry-run`
**Then**:
- Perform all checks (branch detection, manifest parsing)
- Run git push --dry-run for each component
- Display what would happen without actually pushing
- Exit with code 0 if all checks pass

## Backward Compatibility

**Guarantee**: All existing `subrepo push` invocations continue to work identically when on the default branch.

**Examples**:
```bash
# Before and after this feature - identical behavior on main
subrepo push platform/core          # Pushes to default branch
subrepo push                        # Pushes all to default branch
subrepo push --force platform/core  # Force push to default branch
```

## Dependencies

**Required**:
- Git installed and in PATH
- Git repository initialized (`.git` directory)
- Valid manifest.xml file
- Network connectivity to remote repositories

**Optional**:
- SSH keys configured (for SSH remotes)
- HTTPS credentials cached (for HTTPS remotes)

## Error Messages

All error messages follow this format:
```
Error: <what went wrong>
<explanation of why it happened>

<suggested remediation steps>
```

**Examples**:
- `Error: Cannot push from detached HEAD state.`
- `Error: Remote repository 'platform/new' does not exist.`
- `Error: Push rejected (non-fast-forward).`
- `Error: Branch 'release' is protected.`

## Performance

**Expected Latency**:
- Branch detection: <10ms
- Manifest parsing: <100ms (1000 projects)
- Single push: network-bound (same as git push)
- Multi-push: N × single push time (serial execution)

**Throughput**: Not applicable (interactive CLI tool)

## Security

**Authentication**: Delegates to git's credential management (SSH keys, credential cache, etc.)
**Authorization**: Enforced by remote git server
**No Stored Credentials**: Command does not store or manage credentials

## Testing Contract

Test cases must verify:
1. ✅ Push on default branch uses default branch
2. ✅ Push on feature branch creates remote feature branch
3. ✅ Push on feature branch updates existing remote feature branch
4. ✅ Non-fast-forward without --force raises error
5. ✅ Non-fast-forward with --force succeeds
6. ✅ Protected branch raises specific error
7. ✅ Missing remote repository raises specific error
8. ✅ Detached HEAD raises specific error
9. ✅ Multi-component push continues on failure
10. ✅ Summary report shows correct counts
11. ✅ Dry-run doesn't actually push
12. ✅ Exit codes match specifications

---

**Version**: 1.0
**Status**: Final
**Approved**: Ready for implementation
