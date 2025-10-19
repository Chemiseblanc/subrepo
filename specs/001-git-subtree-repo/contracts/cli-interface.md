# CLI Interface Contract

**Feature**: Git Subtree Repo Manager
**Version**: 0.1.0
**Date**: 2025-10-18

## Overview

This document defines the command-line interface contract for the `subrepo` tool. All commands, arguments, options, output formats, and exit codes are specified here to ensure consistent behavior and enable contract testing.

## Invocation

```bash
subrepo <command> [options] [arguments]
python -m subrepo <command> [options] [arguments]
```

## Global Options

Available for all commands:

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--help` | `-h` | flag | - | Show help message and exit |
| `--version` | `-V` | flag | - | Show version and exit |
| `--verbose` | `-v` | flag | false | Enable verbose output |
| `--quiet` | `-q` | flag | false | Suppress non-error output |
| `--no-color` | - | flag | false | Disable colored output |

## Commands

### init

Initialize a new workspace from a manifest file.

**Synopsis**:
```bash
subrepo init <manifest> [options]
```

**Arguments**:
- `<manifest>`: Path or URL to manifest XML file (required)

**Options**:

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--name` | `-n` | string | current directory name | Workspace name |
| `--directory` | `-d` | string | `.` | Directory to initialize (must be empty) |
| `--no-clone` | - | flag | false | Validate manifest without cloning repositories |

**Exit Codes**:
- `0`: Success - workspace initialized
- `1`: User error - invalid manifest, non-empty directory, invalid arguments
- `2`: System error - git command failed, network error, permission denied

**Output** (success):
```
Initializing workspace in /path/to/workspace
Parsing manifest from https://example.com/manifest.xml
Found 3 remotes, 12 projects

Adding subtrees:
  [1/12] components/lib1 ... done (2.3s)
  [2/12] components/lib2 ... done (1.8s)
  ...
  [12/12] tools/helper ... done (0.9s)

Workspace initialized successfully
Total time: 23.4s
```

**Output** (error):
```
Error: Directory is not empty
  /path/to/workspace contains 5 files

Use --directory to specify an empty directory or clean the current directory.
```

**Examples**:
```bash
# Initialize from local manifest
subrepo init manifest.xml

# Initialize from URL
subrepo init https://example.com/manifests/default.xml

# Initialize in specific directory
subrepo init manifest.xml --directory /path/to/workspace

# Validate manifest without cloning
subrepo init manifest.xml --no-clone
```

---

### sync

Synchronize all or specific components with their upstream repositories.

**Synopsis**:
```bash
subrepo sync [options]
```

**Arguments**: None (operates on current workspace)

**Options**:

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--component` | `-c` | string | all | Sync specific component only (by name or path) |
| `--force` | `-f` | flag | false | Force sync even with local changes (stash and reapply) |
| `--no-fetch` | - | flag | false | Use cached refs without fetching from remotes |
| `--continue-on-error` | - | flag | false | Continue syncing other components if one fails |

**Exit Codes**:
- `0`: Success - all components synchronized
- `1`: User error - not in workspace, component not found, conflicts detected
- `2`: System error - git command failed, network error

**Output** (success):
```
Syncing workspace components

Fetching remotes:
  origin ... done
  upstream ... done

Syncing components:
  [1/12] components/lib1 (main) ... up-to-date
  [2/12] components/lib2 (main) ... updated (3 commits)
  [3/12] components/lib3 (dev) ... updated (1 commit)
  ...
  [12/12] tools/helper (main) ... up-to-date

Summary:
  Up-to-date: 8 components
  Updated: 4 components (7 commits pulled)
  Skipped: 0 components
  Failed: 0 components

Total time: 8.2s
```

**Output** (with conflicts):
```
Syncing workspace components

  [1/3] components/lib1 ... CONFLICT
    Local changes detected in components/lib1:
      modified: src/main.py
      added: src/new_file.py

    Options:
      1. Commit your changes: git add . && git commit
      2. Stash your changes: git stash
      3. Force sync: subrepo sync --force (will stash and reapply)

Error: Cannot sync with uncommitted changes
Use --force to stash changes automatically
```

**Examples**:
```bash
# Sync all components
subrepo sync

# Sync specific component by name
subrepo sync --component myorg/myrepo

# Sync specific component by path
subrepo sync --component components/lib1

# Force sync with local changes
subrepo sync --force

# Sync without fetching (use cached refs)
subrepo sync --no-fetch
```

---

### push

Push local changes in a component back to its upstream repository.

**Synopsis**:
```bash
subrepo push <component> [options]
```

**Arguments**:
- `<component>`: Component name or path (required)

**Options**:

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--branch` | `-b` | string | component's revision | Target branch for push |
| `--force` | `-f` | flag | false | Force push (use with caution) |
| `--dry-run` | `-n` | flag | false | Show what would be pushed without pushing |

**Exit Codes**:
- `0`: Success - changes pushed
- `1`: User error - no changes to push, component not found, conflicts
- `2`: System error - git command failed, network error, permission denied

**Output** (success):
```
Pushing component: components/lib1

Extracting subtree commits ...
Found 3 local commits:
  abc1234 feat: add new feature
  def5678 fix: resolve bug
  789abcd docs: update README

Pushing to https://github.com/myorg/lib1 (branch: main) ...
  remote: Resolving deltas: 100%
  remote:
  To https://github.com/myorg/lib1
     old1234..new5678  main -> main

Push successful
```

**Output** (nothing to push):
```
Pushing component: components/lib1

No local commits to push
Component is up-to-date with upstream
```

**Output** (conflicts):
```
Error: Push rejected by remote

Upstream has diverged from your local changes.

Suggested resolution:
  1. Pull latest changes: subrepo pull components/lib1
  2. Resolve any conflicts
  3. Try pushing again: subrepo push components/lib1

Or force push (destructive): subrepo push components/lib1 --force
```

**Examples**:
```bash
# Push component by name
subrepo push myorg/myrepo

# Push component by path
subrepo push components/lib1

# Push to different branch
subrepo push components/lib1 --branch feature-x

# Dry run to see what would be pushed
subrepo push components/lib1 --dry-run

# Force push (destructive)
subrepo push components/lib1 --force
```

---

### pull

Pull upstream changes for a specific component.

**Synopsis**:
```bash
subrepo pull <component> [options]
```

**Arguments**:
- `<component>`: Component name or path (required)

**Options**:

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--branch` | `-b` | string | component's revision | Branch to pull from |
| `--squash` | `-s` | flag | true | Squash upstream commits (default) |
| `--no-squash` | - | flag | false | Preserve individual upstream commits |

**Exit Codes**:
- `0`: Success - changes pulled
- `1`: User error - component not found, conflicts detected
- `2`: System error - git command failed, network error

**Output** (success):
```
Pulling component: components/lib1

Fetching from https://github.com/myorg/lib1 (branch: main) ...
  remote: Counting objects: 15, done.
  remote: Compressing objects: 100% (12/12), done.

Merging upstream changes ...
  5 files changed, 124 insertions(+), 37 deletions(-)

Pull successful (2 upstream commits merged)
```

**Output** (already up-to-date):
```
Pulling component: components/lib1

Already up-to-date
No upstream changes
```

**Examples**:
```bash
# Pull component by name
subrepo pull myorg/myrepo

# Pull component by path
subrepo pull components/lib1

# Pull from different branch
subrepo pull components/lib1 --branch dev

# Pull without squashing
subrepo pull components/lib1 --no-squash
```

---

### status

Show the status of workspace components.

**Synopsis**:
```bash
subrepo status [options]
```

**Arguments**: None

**Options**:

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--component` | `-c` | string | all | Show status for specific component only |
| `--format` | `-f` | string | `text` | Output format: text, json, compact |
| `--porcelain` | - | flag | false | Machine-readable output (implies --format=compact) |

**Exit Codes**:
- `0`: Success (all components clean and up-to-date)
- `1`: Warning (components need attention: behind, ahead, modified)
- `2`: System error - not in workspace, git command failed

**Output** (text format):
```
Workspace Status: /path/to/workspace
Manifest: https://example.com/manifest.xml

Components:
  ✓ components/lib1 (main)
    Status: up-to-date

  ↑ components/lib2 (main)
    Status: ahead by 2 commits
    Local commits ready to push

  ↓ components/lib3 (main)
    Status: behind by 3 commits
    Upstream changes available

  ⚠ components/lib4 (dev)
    Status: modified (uncommitted changes)
    Files changed: 2 modified, 1 added

  ⇅ components/lib5 (main)
    Status: diverged (ahead 1, behind 2)
    Pull required before push

Summary:
  Total: 12 components
  Up-to-date: 7
  Ahead: 2 (can push)
  Behind: 2 (should pull)
  Diverged: 1 (needs merge)
  Modified: 0
```

**Output** (compact format):
```
components/lib1 up-to-date
components/lib2 ahead 2
components/lib3 behind 3
components/lib4 modified
components/lib5 diverged 1 2
...
```

**Output** (JSON format):
```json
{
  "workspace": "/path/to/workspace",
  "manifest": "https://example.com/manifest.xml",
  "components": [
    {
      "name": "myorg/lib1",
      "path": "components/lib1",
      "branch": "main",
      "status": "up-to-date",
      "ahead": 0,
      "behind": 0,
      "modified": false
    },
    {
      "name": "myorg/lib2",
      "path": "components/lib2",
      "branch": "main",
      "status": "ahead",
      "ahead": 2,
      "behind": 0,
      "modified": false
    }
  ],
  "summary": {
    "total": 12,
    "up_to_date": 7,
    "ahead": 2,
    "behind": 2,
    "diverged": 1,
    "modified": 0
  }
}
```

**Examples**:
```bash
# Show status of all components
subrepo status

# Show status of specific component
subrepo status --component components/lib1

# JSON output for scripting
subrepo status --format json

# Compact machine-readable output
subrepo status --porcelain
```

---

## Exit Code Summary

All commands use consistent exit codes:

| Code | Meaning | Examples |
|------|---------|----------|
| `0` | Success | Operation completed successfully |
| `1` | User Error | Invalid arguments, precondition not met, conflicts |
| `2` | System Error | Git failure, network error, I/O error, permission denied |

## Output Formatting

### Color Codes (when terminal supports color and --no-color not set)

- **Green**: Success, up-to-date status
- **Yellow**: Warnings, needs attention (ahead, behind, modified)
- **Red**: Errors, failures
- **Blue**: Informational messages
- **Cyan**: Progress indicators

### Progress Indicators

For long-running operations:
```
[1/12] components/lib1 ... done (2.3s)
[2/12] components/lib2 ... done (1.8s)
```

For streaming operations:
```
Fetching from remote ... ⠋
```

### Verbosity Levels

**Default**: Summary information, progress, results
```
Syncing 12 components ...
  [1/12] lib1 ... done
  ...
Total time: 8.2s
```

**Quiet** (`--quiet`): Errors only
```
Error: Component not found: invalid/path
```

**Verbose** (`--verbose`): Detailed command output
```
Syncing components/lib1
  Executing: git fetch https://github.com/org/lib1 main
  remote: Counting objects: 15, done.
  ...
  Executing: git subtree pull --prefix=components/lib1 ...
  ...
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SUBREPO_MANIFEST` | Default manifest path/URL | None |
| `SUBREPO_JOBS` | Number of parallel operations | 1 (sequential) |
| `NO_COLOR` | Disable colored output | Not set |
| `GIT_EXEC_PATH` | Path to git binary | System default |

## Configuration Files

### Workspace Config

**Location**: `.subrepo/config.json` (created by init)

**Not user-editable** - managed by tool

### Git Config Integration

**Optional** - users can set git config for defaults:

```bash
# Set default manifest
git config subrepo.manifest https://example.com/manifest.xml

# Set verbosity
git config subrepo.verbose true
```

## Shell Completion

Bash completion script available:
```bash
source <(subrepo completion bash)
```

Zsh completion:
```bash
source <(subrepo completion zsh)
```

## Scripting Examples

### Check if sync needed

```bash
#!/bin/bash
if ! subrepo status --porcelain | grep -q 'behind\|diverged'; then
  echo "All components up-to-date"
  exit 0
fi

echo "Syncing components..."
subrepo sync
```

### Automated push workflow

```bash
#!/bin/bash
# Push all components that have local commits

for component in $(subrepo status --porcelain | awk '/^.*ahead/ {print $1}'); do
  echo "Pushing $component"
  subrepo push "$component" || {
    echo "Failed to push $component"
    exit 1
  }
done
```

### JSON parsing for monitoring

```bash
#!/bin/bash
# Check for components that need attention

status_json=$(subrepo status --format json)
needs_sync=$(echo "$status_json" | jq '.summary.behind + .summary.diverged')

if [ "$needs_sync" -gt 0 ]; then
  echo "Warning: $needs_sync components need syncing"
  exit 1
fi
```

## Contract Test Requirements

All contract tests must verify:

1. **Command Execution**: All commands execute with expected arguments
2. **Exit Codes**: Correct exit code for success/error scenarios
3. **Output Format**: Output matches specified format (text/JSON/compact)
4. **Error Messages**: Error messages are actionable and match examples
5. **Idempotency**: Running same command twice produces expected behavior
6. **State Changes**: File system and git state changes are correct
7. **Edge Cases**: Empty workspace, single component, large workspace (50+ components)
