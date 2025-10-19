# Quickstart Guide: Subrepo

Get started with subrepo, the git-subtree-based alternative to git-repo.

## What is Subrepo?

Subrepo is a command-line tool that manages multi-repository projects using git subtrees instead of multiple independent checkouts. It reads repo-style manifest XML files and transparently handles git subtree operations, giving you:

- **Single repository**: One `.git` directory instead of many (40-60% disk space savings)
- **Unified commits**: All components in one git history for atomic changes
- **Bidirectional sync**: Pull updates from upstream and push changes back
- **Familiar workflow**: Compatible with existing repo manifest files

## Prerequisites

- Python 3.14 or later
- Git 2.30 or later
- Basic familiarity with git and command-line tools

## Installation

### From PyPI (when published)

```bash
pip install subrepo
```

### From Source

```bash
git clone https://github.com/yourorg/subrepo
cd subrepo
pip install -e .
```

### Verify Installation

```bash
subrepo --version
# Output: subrepo 0.1.0
```

## Your First Workspace

### 1. Create a Manifest

Create a file `manifest.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="github" fetch="https://github.com/" />
  <default remote="github" revision="main" />

  <project name="libfoo/core" path="lib/core" />
  <project name="libfoo/utils" path="lib/utils" revision="v2.0" />
  <project name="libfoo/cli" path="tools/cli" />
</manifest>
```

This manifest defines:
- A remote named "github" pointing to GitHub
- Default branch "main" for all projects
- Three projects from the `libfoo` organization

### 2. Initialize Workspace

```bash
# Create and enter a new directory
mkdir my-project && cd my-project

# Initialize from manifest
subrepo init manifest.xml
```

**What happens**:
1. Creates a git repository in the current directory
2. Parses the manifest
3. Adds each project as a git subtree at its specified path
4. Creates `.subrepo/` metadata directory

**Output**:
```
Initializing workspace in /path/to/my-project
Parsing manifest from manifest.xml
Found 1 remote, 3 projects

Adding subtrees:
  [1/3] lib/core ... done (2.1s)
  [2/3] lib/utils ... done (1.8s)
  [3/3] tools/cli ... done (0.9s)

Workspace initialized successfully
Total time: 4.8s
```

### 3. Check Status

```bash
subrepo status
```

**Output**:
```
Workspace Status: /path/to/my-project
Manifest: manifest.xml

Components:
  ✓ lib/core (main)
    Status: up-to-date

  ✓ lib/utils (v2.0)
    Status: up-to-date

  ✓ tools/cli (main)
    Status: up-to-date

Summary:
  Total: 3 components
  Up-to-date: 3
```

### 4. Make Changes

Edit files in any component:

```bash
# Make changes to a component
echo "// New feature" >> lib/core/src/feature.py

# Regular git workflow
git add lib/core/src/feature.py
git commit -m "feat(core): add new feature"
```

Check status again:

```bash
subrepo status --component lib/core
```

**Output**:
```
  ↑ lib/core (main)
    Status: ahead by 1 commit
    Local commits ready to push
```

### 5. Push Changes Upstream

```bash
subrepo push lib/core
```

**What happens**:
1. Extracts commits affecting `lib/core` subtree
2. Pushes them to `https://github.com/libfoo/core`
3. Updates tracking information

**Output**:
```
Pushing component: lib/core

Extracting subtree commits ...
Found 1 local commit:
  abc1234 feat(core): add new feature

Pushing to https://github.com/libfoo/core (branch: main) ...
  To https://github.com/libfoo/core
     old1234..new5678  main -> main

Push successful
```

### 6. Sync with Upstream

When teammates make changes to upstream components:

```bash
subrepo sync
```

**What happens**:
1. Fetches latest changes from all remotes
2. Updates each subtree to latest commit
3. Reports what was updated

**Output**:
```
Syncing workspace components

Fetching remotes:
  github ... done

Syncing components:
  [1/3] lib/core (main) ... up-to-date
  [2/3] lib/utils (v2.0) ... updated (2 commits)
  [3/3] tools/cli (main) ... updated (1 commit)

Summary:
  Up-to-date: 1 component
  Updated: 2 components (3 commits pulled)

Total time: 3.2s
```

## Common Workflows

### Sync Specific Component

```bash
# By path
subrepo sync --component lib/core

# By name
subrepo sync --component libfoo/core
```

### Pull Single Component

```bash
# Pull latest changes for one component without syncing others
subrepo pull lib/utils
```

### Handle Conflicts

If you have local changes when syncing:

```bash
$ subrepo sync
Error: Cannot sync with uncommitted changes in lib/core

Options:
  1. Commit: git add . && git commit
  2. Stash: git stash
  3. Force (auto-stash): subrepo sync --force
```

Force sync with auto-stash:

```bash
subrepo sync --force
# Stashes changes, syncs, then reapplies stash
```

### Work with Different Branches

```bash
# Pull from a different branch
subrepo pull lib/core --branch develop

# Push to a different branch
subrepo push lib/core --branch feature-x
```

### Dry Run

```bash
# See what would be pushed without actually pushing
subrepo push lib/core --dry-run
```

## Manifest Examples

### Multiple Remotes

```xml
<manifest>
  <remote name="github" fetch="https://github.com/" />
  <remote name="gitlab" fetch="https://gitlab.com/" />

  <default remote="github" revision="main" />

  <project name="org/repo1" path="lib/repo1" />
  <project name="other/repo2" path="lib/repo2" remote="gitlab" />
</manifest>
```

### Specific Revisions

```xml
<manifest>
  <remote name="origin" fetch="https://github.com/" />

  <!-- Use specific tag -->
  <project name="org/stable-lib" path="lib/stable" revision="v2.0.0" />

  <!-- Use branch -->
  <project name="org/dev-lib" path="lib/dev" revision="develop" />

  <!-- Use commit hash -->
  <project name="org/pinned-lib" path="lib/pinned"
           revision="abc123def456789..." />
</manifest>
```

### From URL

```bash
subrepo init https://example.com/manifests/default.xml
```

## Troubleshooting

### "Directory is not empty"

**Problem**: Trying to initialize in non-empty directory

**Solution**:
```bash
# Use a clean directory
mkdir new-workspace && cd new-workspace
subrepo init manifest.xml

# Or specify directory
subrepo init manifest.xml --directory /path/to/empty/dir
```

### "Not in a subrepo workspace"

**Problem**: Running commands outside initialized workspace

**Solution**:
```bash
# Ensure you're in the workspace root (where .subrepo/ exists)
cd /path/to/workspace
subrepo status
```

### "Push rejected by remote"

**Problem**: Upstream has diverged from local

**Solution**:
```bash
# Pull latest changes first
subrepo pull lib/component

# Resolve any conflicts
git status
git add .
git commit

# Try pushing again
subrepo push lib/component
```

### Checking Git Version

Subrepo requires Git 2.30+:

```bash
git --version
# Should show: git version 2.30.0 or later
```

## Best Practices

### 1. Commit Component Changes Separately

```bash
# Good: component-focused commits
git add lib/core/
git commit -m "feat(core): add feature X"

git add lib/utils/
git commit -m "fix(utils): resolve bug Y"

# Avoid: mixing components in one commit
git add lib/core/ lib/utils/
git commit -m "misc changes"  # Harder to push selectively
```

### 2. Sync Regularly

```bash
# Start of day
subrepo sync

# After long development session
subrepo sync
```

### 3. Check Status Before Pushing

```bash
subrepo status
subrepo push lib/component
```

### 4. Use Descriptive Commit Messages

Since commits will be pushed to upstream components, use clear messages:

```bash
git commit -m "feat(core): add user authentication

Implements OAuth2 authentication flow with refresh tokens.
Includes unit tests and documentation.

Closes #123"
```

### 5. Version Control Your Manifest

```bash
# Keep manifest in the workspace repository
git add manifest.xml
git commit -m "chore: update manifest to use v2.0 of lib/utils"
```

## Next Steps

- Read the [CLI Reference](contracts/cli-interface.md) for all commands
- Explore [Data Model](data-model.md) to understand internal structures
- Review [Implementation Plan](plan.md) for technical details
- Check [Feature Specification](spec.md) for user stories and requirements

## Getting Help

```bash
# Command help
subrepo --help
subrepo init --help
subrepo sync --help

# Version information
subrepo --version

# Verbose output for debugging
subrepo sync --verbose
```

## Comparison with Repo

| Feature | Repo | Subrepo |
|---------|------|---------|
| Storage | Multiple .git directories | Single .git directory |
| Disk Space | More (each repo separate) | Less (shared objects) |
| Atomic Commits | No (separate repos) | Yes (one git repo) |
| Manifest Format | XML | XML (compatible) |
| Sync Command | `repo sync` | `subrepo sync` |
| Upstream Push | Manual per repo | `subrepo push <component>` |
| Dependencies | Python, git | Python 3.14+, git 2.30+ |
| Backend | Multiple git clones | Git subtrees |

## What You've Learned

- ✅ How to create a manifest XML file
- ✅ Initialize a workspace with `subrepo init`
- ✅ Check component status with `subrepo status`
- ✅ Make changes and push with `subrepo push`
- ✅ Sync upstream changes with `subrepo sync`
- ✅ Handle common workflows and errors

You're ready to use subrepo for managing multi-repository projects!
