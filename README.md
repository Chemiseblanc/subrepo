# Subrepo

A git subtree-based alternative to Google's repo tool for managing multi-repository projects.

## Overview

Subrepo is a command-line tool that helps you manage multi-repository projects using **git subtrees** instead of multiple independent checkouts. Unlike the traditional repo tool which creates multiple `.git` directories, subrepo maintains a single unified git repository with all components integrated as subtrees.

### Key Benefits

- **Single Repository**: One `.git` directory instead of many, reducing disk usage by 40-60%
- **Unified History**: All components share a common git history, simplifying cross-component changes
- **Standard Git Workflow**: Use normal git commands for most operations - no special tooling required
- **Manifest Compatible**: Supports standard repo manifest XML format for easy migration
- **Transparent Operations**: Push and pull individual components without manual git subtree commands

### How It Works

Subrepo uses git's subtree functionality to embed external repositories as subdirectories within a parent repository. When you initialize a workspace from a manifest file, subrepo:

1. Creates a new git repository
2. Adds each component as a git subtree at the specified path
3. Maintains the manifest configuration for future sync/push/pull operations

Unlike traditional repo which maintains separate git repositories, all components share the same git repository, enabling atomic commits across multiple components while preserving the ability to push/pull individual component changes.

## Installation

```bash
# Using pip (recommended)
pip install subrepo

# From source
git clone https://github.com/yourorg/subrepo.git
cd subrepo
pip install -e .
```

## Quick Start

### 1. Create a Manifest File

Create a `manifest.xml` file defining your project structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="github" fetch="https://github.com/" />

  <default remote="github" revision="main" />

  <project name="myorg/backend" path="services/backend" />
  <project name="myorg/frontend" path="services/frontend" />
  <project name="myorg/shared-lib" path="libs/shared" revision="v2.0" />
</manifest>
```

### 2. Initialize Workspace

```bash
# Initialize in current directory
subrepo init manifest.xml

# Or specify a directory
subrepo init manifest.xml --directory ./my-workspace
```

This creates a new git repository with all components as subtrees:

```
my-workspace/
├── .git/              # Single git repository
├── .subrepo/          # Subrepo configuration
│   ├── config.json
│   └── manifest.xml
├── services/
│   ├── backend/       # Subtree from myorg/backend
│   └── frontend/      # Subtree from myorg/frontend
└── libs/
    └── shared/        # Subtree from myorg/shared-lib
```

### 3. Work with Components

```bash
# Sync all components with upstream
subrepo sync

# Check status of all components
subrepo status

# Make changes to a component
cd services/backend
# Edit files, make commits normally with git
git add .
git commit -m "Add new API endpoint"

# Push changes back to component's upstream
subrepo push backend

# Pull updates from a specific component
subrepo pull frontend
```

## Usage Examples

### Initialize with Validation Only

Validate a manifest without cloning repositories:

```bash
subrepo init manifest.xml --no-clone
```

### Sync Specific Component

```bash
# Sync by component name
subrepo sync --component myorg/backend

# Sync by component path
subrepo sync --component services/backend

# Force sync even with local changes (stashes and reapplies)
subrepo sync --force
```

### Push Component Changes

```bash
# Push to component's default branch (from manifest)
subrepo push backend

# Push to specific branch
subrepo push backend --branch feature/new-api

# Dry run to see what would be pushed
subrepo push backend --dry-run

# Force push (use with caution)
subrepo push backend --force
```

### Pull Component Updates

```bash
# Pull from default branch
subrepo pull frontend

# Pull from specific branch
subrepo pull frontend --branch develop

# Pull without squashing commits
subrepo pull frontend --no-squash
```

### Check Workspace Status

```bash
# Show status of all components
subrepo status

# Show status in JSON format
subrepo status --format json

# Machine-readable format for scripting
subrepo status --porcelain

# Status for specific component
subrepo status --component backend
```

## Command Reference

### `subrepo init <manifest> [options]`

Initialize a new workspace from a manifest file.

**Options:**
- `--directory, -d <path>`: Directory to initialize (default: current directory)
- `--name, -n <name>`: Workspace name (default: directory name)
- `--no-clone`: Validate manifest only, don't clone repositories

**Exit Codes:**
- `0`: Success
- `1`: User error (invalid manifest, non-empty directory)
- `2`: System error (git operation failed)

### `subrepo sync [options]`

Synchronize components with upstream repositories.

**Options:**
- `--component, -c <name|path>`: Sync specific component only
- `--force, -f`: Force sync even with local changes
- `--continue-on-error`: Continue syncing if one component fails

### `subrepo push <component> [options]`

Push local changes in a component back to upstream.

**Options:**
- `--branch, -b <branch>`: Target branch (default: component's revision)
- `--force, -f`: Force push
- `--dry-run, -n`: Show what would be pushed

**Exit Codes:**
- `0`: Success
- `1`: User error (component not found, validation failed)
- `2`: Git error (non-fast-forward, conflicts)
- `3`: Configuration error (not in workspace, detached HEAD)
- `4`: Permission error (branch protection)

### `subrepo pull <component> [options]`

Pull upstream changes for a specific component.

**Options:**
- `--branch, -b <branch>`: Branch to pull from (default: component's revision)
- `--no-squash`: Preserve individual commits (default: squash)

### `subrepo status [options]`

Show status of workspace components.

**Options:**
- `--component, -c <name|path>`: Show specific component only
- `--format, -f <format>`: Output format: `text`, `json`, or `compact`
- `--porcelain`: Machine-readable output (implies `--format=compact`)

**Status Values:**
- `up-to-date`: Component matches upstream
- `ahead`: Local commits not pushed
- `behind`: Upstream commits not pulled
- `diverged`: Both local and upstream have commits
- `modified`: Uncommitted local changes

### Global Options

All commands support:
- `--verbose, -v`: Enable verbose output
- `--quiet, -q`: Suppress non-error output
- `--no-color`: Disable colored output

## Manifest Format

Subrepo supports standard repo manifest XML format:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <!-- Define remotes -->
  <remote name="github"
          fetch="https://github.com/"
          review="https://github.com/" />

  <remote name="gitlab"
          fetch="https://gitlab.com/" />

  <!-- Set defaults -->
  <default remote="github"
           revision="main" />

  <!-- Define projects -->
  <project name="org/repo-name"
           path="local/path"
           remote="github"
           revision="main" />

  <project name="other/component"
           path="components/other" />
           <!-- Uses default remote and revision -->
</manifest>
```

### Manifest Elements

- **`<remote>`**: Defines a git remote
  - `name`: Unique identifier
  - `fetch`: Base URL for repositories
  - `review`: Optional code review URL

- **`<default>`**: Sets default values
  - `remote`: Default remote name
  - `revision`: Default branch/tag/commit

- **`<project>`**: Defines a component
  - `name`: Repository identifier (e.g., "org/repo")
  - `path`: Local path for subtree
  - `remote`: Remote name (optional, uses default)
  - `revision`: Branch/tag/commit (optional, uses default)

## Comparison with Repo

| Feature | Repo | Subrepo |
|---------|------|---------|
| Storage | Multiple `.git` dirs | Single `.git` dir |
| Cross-component commits | Manual coordination | Atomic commits |
| Disk usage | Higher | 40-60% less |
| Git commands | Works normally | Works normally |
| History | Separate per component | Unified with component tracking |
| Component updates | `repo sync` | `subrepo sync` |
| Push changes | Standard git push | `subrepo push <component>` |
| Manifest format | XML | Same XML format |

## Development

### Requirements

- Python 3.14+
- Git 2.30+

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test types
pytest tests/unit
pytest tests/integration
pytest tests/contract

# Type checking
mypy subrepo --strict

# Linting
ruff check subrepo

# Code formatting
black subrepo tests
```

### Project Structure

```
subrepo/
├── subrepo/              # Main package
│   ├── cli.py           # Command-line interface
│   ├── manifest_parser.py  # Manifest XML parsing
│   ├── subtree_manager.py  # Git subtree operations
│   ├── workspace.py     # Workspace initialization
│   ├── git_commands.py  # Git command wrappers
│   ├── models.py        # Data models
│   └── exceptions.py    # Custom exceptions
├── tests/               # Test suite
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── contract/       # CLI contract tests
└── specs/              # Feature specifications
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass and coverage stays above 90%
5. Submit a pull request

## License

[Your License Here]

## Support

- Report issues: https://github.com/yourorg/subrepo/issues
- Documentation: https://github.com/yourorg/subrepo/wiki
- Discussions: https://github.com/yourorg/subrepo/discussions
