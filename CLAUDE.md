# subrepo Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-18

## Active Technologies
- Python 3.14+ (as specified in pyproject.toml) + Python standard library only (xml.etree, subprocess, pathlib, argparse, logging) (001-git-subtree-repo)
- Python 3.14+ + Python standard library only (subprocess, xml.etree, pathlib, argparse, logging) (002-push-feature-branches)
- Manifest XML file (existing format), git repositories (002-push-feature-branches)

## Project Structure
```
subrepo/           # Main package
tests/            # Test suite
  unit/           # Unit tests
  integration/    # Integration tests
  contract/       # CLI contract tests
```

## Commands
- `pytest` - Run test suite with coverage
- `mypy subrepo --strict` - Type checking
- `ruff check subrepo` - Linting
- `black subrepo tests` - Code formatting

## Code Style
Python 3.14+ (as specified in pyproject.toml): Follow standard conventions

## Recent Changes
- 002-push-feature-branches: Added Python 3.14+ + Python standard library only (subprocess, xml.etree, pathlib, argparse, logging)
- 001-git-subtree-repo: Added Python 3.14+ (as specified in pyproject.toml) + Python standard library only (xml.etree, subprocess, pathlib, argparse, logging)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
