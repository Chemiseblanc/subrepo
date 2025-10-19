# Quick Start: Feature Branch Push Synchronization Development

**Feature**: 002-push-feature-branches
**Date**: 2025-10-18
**Branch**: `002-push-feature-branches`

## Prerequisites

- Python 3.14+ installed
- Git installed and in PATH
- Basic familiarity with git subtrees and the subrepo codebase

## Development Setup (5 minutes)

### 1. Clone and Switch to Feature Branch

```bash
cd /path/to/subrepo
git checkout 002-push-feature-branches
```

### 2. Install Development Dependencies

```bash
# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dev dependencies
pip install -e ".[dev]"  # Or manually:
pip install pytest pytest-cov mypy ruff black
```

### 3. Verify Setup

```bash
# Run existing tests to ensure environment works
pytest

# Check type checking works
mypy src

# Check linting works
ruff check src

# Check formatting works
black --check src
```

Expected output: All checks should pass (existing codebase is compliant).

## Test-Driven Development Workflow

**IMPORTANT**: Follow strict TDD - write tests BEFORE implementation.

### Step 1: Write a Failing Test

```bash
# Create a new test file
touch tests/unit/test_branch_detection.py
```

Example test structure:

```python
"""Tests for git branch detection operations."""

import subprocess
from unittest.mock import patch
import pytest

from subrepo.git_commands import detect_current_branch, detect_default_branch
from subrepo.exceptions import DetachedHeadError


def test_detect_current_branch_returns_branch_name():
    """Test that detect_current_branch returns the current branch name."""
    # This test will fail until implementation exists
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "feature-branch\n"

        result = detect_current_branch()

        assert result == "feature-branch"
        mock_run.assert_called_once()


def test_detect_current_branch_raises_on_detached_head():
    """Test that detect_current_branch raises DetachedHeadError when HEAD is detached."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "fatal: ref HEAD is not a symbolic ref"

        with pytest.raises(DetachedHeadError):
            detect_current_branch()
```

### Step 2: Run Test - Verify It Fails (RED)

```bash
pytest tests/unit/test_branch_detection.py -v
```

Expected: Test fails because `detect_current_branch()` doesn't exist yet.

### Step 3: Implement Minimal Code to Pass (GREEN)

Add to `src/git_commands.py`:

```python
def detect_current_branch() -> str:
    """Detect the current git branch name.

    Returns:
        Current branch name

    Raises:
        DetachedHeadError: If HEAD is detached
    """
    result = subprocess.run(
        ["git", "symbolic-ref", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise DetachedHeadError("Cannot push from detached HEAD state")

    return result.stdout.strip()
```

### Step 4: Run Test - Verify It Passes (GREEN)

```bash
pytest tests/unit/test_branch_detection.py -v
```

Expected: All tests pass ✓

### Step 5: Refactor While Keeping Tests Green (REFACTOR)

- Improve code clarity
- Add type hints
- Extract constants
- Run tests after each change

### Step 6: Repeat for Each Requirement

Continue this cycle for each function/class:
1. Write test → RED
2. Implement → GREEN
3. Refactor → GREEN

## Development Checklist

Use this checklist to track implementation progress:

### Phase 1: Git Operations (Branch Detection)
- [ ] Write tests for `detect_current_branch()`
- [ ] Implement `detect_current_branch()`
- [ ] Write tests for `detect_default_branch()`
- [ ] Implement `detect_default_branch()`
- [ ] Write tests for `is_commit_sha()`
- [ ] Implement `is_commit_sha()`

### Phase 2: Manifest Integration
- [ ] Write tests for `extract_default_branch_from_project()`
- [ ] Implement `extract_default_branch_from_project()`
- [ ] Write tests for manifest fallback logic
- [ ] Implement manifest fallback

### Phase 3: Data Models
- [ ] Write tests for `PushResult` dataclass
- [ ] Implement `PushResult` with validation
- [ ] Write tests for `BranchInfo` dataclass
- [ ] Implement `BranchInfo` with validation
- [ ] Write tests for new exception types
- [ ] Implement exception hierarchy

### Phase 4: Push Logic
- [ ] Write tests for dry-run push detection
- [ ] Implement dry-run logic
- [ ] Write tests for single component push (feature branch)
- [ ] Implement single component push
- [ ] Write tests for single component push (default branch)
- [ ] Verify backward compatibility
- [ ] Write tests for multi-component push
- [ ] Implement multi-component push with continue-on-error

### Phase 5: Error Handling
- [ ] Write tests for non-fast-forward detection
- [ ] Implement non-fast-forward error handling
- [ ] Write tests for protected branch detection
- [ ] Implement protected branch error handling
- [ ] Write tests for missing repository detection
- [ ] Implement missing repository error handling

### Phase 6: CLI Integration
- [ ] Write tests for --force flag
- [ ] Implement --force flag
- [ ] Write tests for --dry-run flag
- [ ] Implement --dry-run flag
- [ ] Write contract tests for CLI interface
- [ ] Update CLI help text

### Phase 7: Integration Tests
- [ ] Write end-to-end test for feature branch push
- [ ] Write end-to-end test for default branch push
- [ ] Write end-to-end test for multi-component push
- [ ] Write end-to-end test for error scenarios

## Running Tests

### All Tests

```bash
pytest
```

### Specific Test File

```bash
pytest tests/unit/test_branch_detection.py -v
```

### Specific Test Function

```bash
pytest tests/unit/test_branch_detection.py::test_detect_current_branch_returns_branch_name -v
```

### With Coverage Report

```bash
pytest --cov=src --cov-report=term-missing
```

Coverage must be ≥90% (enforced by constitution).

### Only Failed Tests

```bash
pytest --lf  # Last failed
pytest --ff  # Failed first, then rest
```

## Code Quality Checks

Run before committing:

```bash
# Type checking
mypy src

# Linting
ruff check src

# Formatting
black src tests

# All checks together
mypy src && ruff check src && black --check src && pytest
```

## Common Development Tasks

### Add a New Exception Type

1. Write test in `tests/unit/test_error_handling.py`
2. Add exception class to `src/exceptions.py`
3. Run `mypy` to verify type safety
4. Update `__init__.py` if exception should be publicly exported

### Add a New Data Model

1. Write validation tests in `tests/unit/test_<model_name>.py`
2. Add dataclass to `src/models.py`
3. Implement `__post_init__` validation
4. Run `mypy --strict` to verify type annotations
5. Add to `__all__` in `models.py`

### Extend Git Operations

1. Write unit tests with subprocess mocking
2. Implement function in `git_commands.py`
3. Use `subprocess.run` with `check=False`
4. Always handle return codes explicitly
5. Return meaningful error messages

## Debugging Tips

### Debug Test Failure

```bash
# Run with verbose output
pytest -vv tests/unit/test_branch_detection.py

# Run with print statements visible
pytest -s tests/unit/test_branch_detection.py

# Drop into debugger on failure
pytest --pdb tests/unit/test_branch_detection.py
```

### Debug Git Commands

```bash
# Enable verbose mode in development
export SUBREPO_DEBUG=1

# Then run your subrepo command
python -m subrepo push platform/core
```

### Inspect Type Errors

```bash
# Show detailed type error messages
mypy --show-error-codes --pretty src/git_commands.py
```

## Integration Test Setup

Integration tests require a real git repository setup:

```bash
# Integration tests use temporary directories
pytest tests/integration/ -v

# Integration tests will:
# 1. Create temp git repos
# 2. Set up fake remotes
# 3. Test actual git operations
# 4. Clean up automatically
```

## Performance Testing

```bash
# Run tests with timing
pytest --durations=10

# Unit tests should be <0.1s each
# Integration tests should be <1s each
```

## Next Steps After Setup

1. Read [data-model.md](./data-model.md) to understand data structures
2. Read [contracts/cli-push.md](./contracts/cli-push.md) for CLI contract
3. Read [research.md](./research.md) for technical decisions
4. Run `/speckit.tasks` to generate implementation tasks
5. Start with Phase 1 (Git Operations) from checklist above

## Questions?

- Check [spec.md](./spec.md) for requirements
- Check [plan.md](./plan.md) for architecture
- Check existing code in `src/` for patterns
- Follow constitution principles in `.specify/memory/constitution.md`

---

**Remember**: Write tests first! Red → Green → Refactor. No implementation without tests.
