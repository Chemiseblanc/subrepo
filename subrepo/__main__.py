"""Main entry point for subrepo when run as a module.

Usage:
    python -m subrepo <command> [options]
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
