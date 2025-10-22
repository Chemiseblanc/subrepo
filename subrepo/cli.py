"""Command-line interface for subrepo.

Provides argparse-based CLI with subcommands for init, sync, push, pull, and status.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from . import __version__
from .exceptions import (
    BranchProtectionError,
    DetachedHeadError,
    GitOperationError,
    ManifestError,
    NonFastForwardError,
    RepositoryNotFoundError,
    SubrepoError,
    WorkspaceError,
)
from .git_commands import create_branch_info, git_subtree_add
from .manifest_parser import parse_manifest
from .models import FileOperationSummary, PushAction, PushStatus
from .subtree_manager import SubtreeManager
from .workspace import init_workspace, load_workspace_config

if TYPE_CHECKING:
    from .models import SubtreeState, WorkspaceConfig

# Global flags for output control
_verbose = False
_quiet = False
_no_color = False
logger = logging.getLogger("subrepo")


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging based on verbosity flags.

    Args:
        verbose: Enable verbose/debug output
        quiet: Suppress non-error output
    """
    global _verbose, _quiet
    _verbose = verbose
    _quiet = quiet

    # Configure logging level
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    else:
        level = logging.INFO

    # Configure handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Format: include timestamp and level in verbose mode
    if verbose:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        formatter = logging.Formatter("%(levelname)s: %(message)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)


def should_print(level: str = "info") -> bool:
    """Check if output should be printed based on quiet flag.

    Args:
        level: Output level ("info", "error", "debug")

    Returns:
        True if output should be printed
    """
    return not (_quiet and level in ("info", "debug"))


def colorize(text: str, color: str) -> str:
    """Add ANSI color codes to text if color is enabled.

    Args:
        text: Text to colorize
        color: Color name (red, green, yellow, blue, etc.)

    Returns:
        Colorized text or plain text if --no-color
    """
    if _no_color or os.getenv("NO_COLOR"):
        return text

    colors = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "reset": "\033[0m",
    }

    color_code = colors.get(color, "")
    reset_code = colors["reset"]

    return f"{color_code}{text}{reset_code}" if color_code else text


def init_command(args: argparse.Namespace) -> int:
    """Handle the 'init' command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for user error, 2 for system error)
    """
    manifest_source = args.manifest
    directory = Path(args.directory) if args.directory else Path.cwd()

    try:
        # Print initialization message
        if should_print("info"):
            print(f"Initializing workspace in {directory}")

        # Check manifest exists first
        manifest_path = Path(manifest_source)
        if not manifest_path.exists():
            logger.error(f"Manifest file not found: {manifest_path}")
            return 1

        # Now resolve the path after confirming it exists
        manifest_path = manifest_path.resolve()

        # Check if directory is empty (must check before workspace creation)
        if directory.exists():
            existing_files = list(directory.iterdir())
            # Allow .git directory (re-init case) and the manifest file itself
            non_init_files = [
                f for f in existing_files if f.name != ".git" and f.resolve() != manifest_path
            ]
            if non_init_files:
                logger.error(f"Directory is not empty: {directory}")
                logger.error(f"Contains {len(non_init_files)} file(s). Use an empty directory.")
                return 1

        if should_print("info"):
            print(f"Parsing manifest: {manifest_path}")

        # Parse manifest
        manifest = parse_manifest(manifest_path)

        # Print summary
        if should_print("info"):
            print(
                f"Found {len(manifest.remotes)} remote(s) and {len(manifest.projects)} project(s)"
            )

        # Validate manifest (already done in parse_manifest, but explicit check)
        if args.no_clone:
            if should_print("info"):
                print("Manifest validated successfully (--no-clone mode)")
            return 0

        # Initialize workspace
        init_workspace(directory, manifest, manifest_source)
        if should_print("info"):
            print("Workspace initialized successfully")

        # Create subtree manager for file operations
        manager = SubtreeManager(directory, manifest)

        # Add subtrees
        for i, project in enumerate(manifest.projects, 1):
            if should_print("info"):
                print(f"Adding component {i}/{len(manifest.projects)}: {project.path}")

            # Get remote URL
            remote = manifest.remotes[project.remote]
            repository_url = f"{remote.fetch}{project.name}"

            try:
                # Add subtree
                result = git_subtree_add(
                    path=directory,
                    prefix=project.path,
                    repository=repository_url,
                    ref=project.revision,
                    squash=True,
                )

                if result.success:
                    if should_print("info"):
                        print(f"  {colorize('✓', 'green')} Component added: {project.path}")

                    # Execute file operations after adding component
                    from .file_operations import (
                        execute_copyfile_operations,
                        execute_linkfile_operations,
                    )

                    project_dir = directory / project.path
                    if project.copyfiles:
                        if should_print("info"):
                            print(f"  Copying {len(project.copyfiles)} file(s)...")
                        copyfile_results = execute_copyfile_operations(
                            project=project,
                            workspace_root=directory,
                            project_dir=project_dir,
                        )
                        manager.file_operation_results.extend(copyfile_results)

                    if project.linkfiles:
                        if should_print("info"):
                            print(f"  Creating {len(project.linkfiles)} symlink(s)...")
                        linkfile_results = execute_linkfile_operations(
                            project=project,
                            workspace_root=directory,
                            project_dir=project_dir,
                        )
                        manager.file_operation_results.extend(linkfile_results)

                else:
                    logger.error(f"Failed to add component {project.path}: {result.stderr}")
                    return 2

            except GitOperationError as e:
                logger.error(f"Git operation failed for {project.path}: {e}")
                return 2

        # Display file operation summary if any
        file_op_results = manager.get_file_operation_summary()
        if file_op_results and should_print("info"):
            summary = FileOperationSummary(results=file_op_results)
            print()
            print(summary.format_summary())

        if should_print("info"):
            print(f"\n{colorize('Success!', 'green')} Workspace initialized successfully")
            print(f"  Location: {directory}")
            print(f"  Components: {len(manifest.projects)}")

        return 0

    except ManifestError as e:
        logger.error(f"Manifest parse error: {e}")
        return 1
    except WorkspaceError as e:
        logger.error(f"Workspace error: {e}")
        return 1
    except GitOperationError as e:
        logger.error(f"Git operation error: {e}")
        return 2
    except SubrepoError as e:
        logger.error(f"Subrepo error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if _verbose:
            import traceback

            traceback.print_exc()
        return 2


def sync_command(args: argparse.Namespace) -> int:
    """Handle the 'sync' command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for user error, 2 for system error)
    """
    workspace_path = Path.cwd()

    try:
        # Check if in a workspace
        if not (workspace_path / ".subrepo").exists():
            return 1

        # Load workspace config
        config = load_workspace_config(workspace_path)

        # Load manifest
        manifest_path = workspace_path / ".subrepo" / "manifest.xml"
        if not manifest_path.exists():
            manifest_path = Path(config.manifest_path)

        if not manifest_path.exists():
            return 1

        manifest = parse_manifest(manifest_path)

        # Create subtree manager
        manager = SubtreeManager(workspace_path, manifest)

        # Filter components if --component specified
        components_to_sync = manifest.projects
        if args.component:
            # Find component by name or path
            component = manifest.get_project_by_path(args.component)
            if not component:
                component = manifest.get_project_by_name(args.component)

            if not component:
                return 1

            components_to_sync = [component]

        # Sync components
        total_components = len(components_to_sync)

        results = {}
        for i, project in enumerate(components_to_sync, 1):
            if should_print("info"):
                print(f"Syncing component {i}/{total_components}: {project.path}")

            try:
                result = manager._sync_component(project)

                if result.success:
                    # Check if anything was updated
                    if "Already up to date" in result.stdout or "up-to-date" in result.stdout:
                        if should_print("info"):
                            print(f"  {colorize('✓', 'green')} Up to date")
                    else:
                        if should_print("info"):
                            print(f"  {colorize('✓', 'green')} Synced")

                    # Display file operation progress if any
                    if project.copyfiles:
                        if should_print("info"):
                            print(f"  Copying {len(project.copyfiles)} file(s)...")
                    if project.linkfiles:
                        if should_print("info"):
                            print(f"  Creating {len(project.linkfiles)} symlink(s)...")

                    results[project.path] = "success"
                else:
                    if should_print("info"):
                        print(f"  {colorize('✗', 'red')} Failed")
                    if not args.continue_on_error:
                        return 2
                    results[project.path] = "failed"

            except WorkspaceError as e:
                if "uncommitted changes" in str(e).lower() and not args.force:
                    return 1
                raise
            except GitOperationError:
                if should_print("info"):
                    print(f"  {colorize('✗', 'red')} Failed")
                if not args.continue_on_error:
                    return 2
                results[project.path] = "failed"

        # Display file operation summary
        file_op_results = manager.get_file_operation_summary()
        if file_op_results and should_print("info"):
            summary = FileOperationSummary(results=file_op_results)
            print()
            print(summary.format_summary())

        # Print summary
        success_count = sum(1 for v in results.values() if v == "success")
        failed_count = sum(1 for v in results.values() if v == "failed")

        if should_print("info"):
            print()
            if failed_count == 0:
                print(f"{colorize('Success!', 'green')} All {success_count} component(s) synced")
            else:
                msg = f"{colorize('Partial success', 'yellow')}: "
                msg += f"{success_count} synced, {failed_count} failed"
                print(msg)

        return 0 if failed_count == 0 else 2

    except ManifestError:
        return 1
    except WorkspaceError:
        return 1
    except GitOperationError:
        return 2
    except SubrepoError:
        return 1
    except Exception:
        return 2


def push_command(args: argparse.Namespace) -> int:
    """Handle the 'push' command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for user error, 2 for system error)
    """
    workspace_path = Path.cwd()

    try:
        # Check if in a workspace
        if not (workspace_path / ".subrepo").exists():
            logger.error("Not in a subrepo workspace. Run 'subrepo init' first.")
            return 3  # Configuration error

        # Load workspace config
        config = load_workspace_config(workspace_path)

        # Load manifest
        manifest_path = workspace_path / ".subrepo" / "manifest.xml"
        if not manifest_path.exists():
            manifest_path = Path(config.manifest_path)

        if not manifest_path.exists():
            logger.error(f"Manifest not found: {manifest_path}")
            return 3

        manifest = parse_manifest(manifest_path)

        # Find component by name or path
        component = manifest.get_project_by_path(args.component)
        if not component:
            component = manifest.get_project_by_name(args.component)

        if not component:
            logger.error(f"Component not found: {args.component}")
            return 3

        # Create subtree manager
        manager = SubtreeManager(workspace_path, manifest)

        # Get branch information to show user context
        try:
            branch_info = create_branch_info(cwd=workspace_path)

            if should_print("info"):
                if branch_info.is_default_branch:
                    print(f"Current branch: {colorize(branch_info.current_branch, 'cyan')}")
                else:
                    print(f"Current branch: {colorize(branch_info.current_branch, 'cyan')}")
                    print(f"Default branch: {colorize(branch_info.default_branch, 'cyan')}")
                    print()  # Blank line

        except DetachedHeadError as e:
            logger.error(str(e))
            return 3

        # Push component using new branch-aware logic
        try:
            result = manager.push_single_component(
                project=component,
                force=getattr(args, "force", False),
                dry_run=getattr(args, "dry_run", False),
            )

            # Display result
            if result.status == PushStatus.SUCCESS:
                action_str = "created" if result.action == PushAction.CREATED else "updated"
                action_symbol = "✓" if not _no_color else "[OK]"

                if should_print("info"):
                    print(
                        f"Pushing {component.path} to {result.branch_name}... "
                        f"{colorize(action_str, 'green')} {action_symbol}"
                    )

                return 0
            # This shouldn't happen (errors raise exceptions)
            logger.error(f"Push failed: {result.error_message}")
            return 2

        except NonFastForwardError as e:
            logger.error(str(e))
            if should_print("info"):
                print(
                    f"\n{colorize('Suggestion:', 'yellow')} "
                    f"Run 'git pull' or use 'subrepo push --force' to force push."
                )
            return 2

        except BranchProtectionError as e:
            logger.error(str(e))
            return 4  # Permission error

        except RepositoryNotFoundError as e:
            logger.error(str(e))
            return 3  # Configuration error

    except WorkspaceError as e:
        logger.error(str(e))
        return 1
    except ManifestError as e:
        logger.error(str(e))
        return 1
    except GitOperationError as e:
        logger.error(str(e))
        return 2
    except SubrepoError as e:
        logger.error(str(e))
        return 1
    except Exception:
        logger.exception("Unexpected error during push")
        return 2


def pull_command(args: argparse.Namespace) -> int:
    """Handle the 'pull' command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for user error, 2 for system error)
    """
    workspace_path = Path.cwd()

    try:
        # Check if in a workspace
        if not (workspace_path / ".subrepo").exists():
            return 1

        # Load workspace config
        config = load_workspace_config(workspace_path)

        # Load manifest
        manifest_path = workspace_path / ".subrepo" / "manifest.xml"
        if not manifest_path.exists():
            manifest_path = Path(config.manifest_path)

        if not manifest_path.exists():
            return 1

        manifest = parse_manifest(manifest_path)

        # Find component by name or path
        component = manifest.get_project_by_path(args.component)
        if not component:
            component = manifest.get_project_by_name(args.component)

        if not component:
            return 1

        # Create subtree manager
        manager = SubtreeManager(workspace_path, manifest)

        # Get remote URL and target branch
        manifest.remotes[component.remote]

        # Determine squash mode
        squash = not args.no_squash  # Default is to squash

        # Pull component
        result = manager.pull_component(
            component,
            branch=args.branch,
            squash=squash,
        )

        if result.success:
            # Check if anything was updated
            if "Already up to date" in result.stdout or "up-to-date" in result.stdout:
                return 0

            # Parse output for summary

            # Show summary from git output
            for line in result.stdout.split("\n"):
                if "file" in line.lower() and "changed" in line.lower():
                    pass

            return 0

        # Check for conflicts
        if "conflict" in result.stderr.lower():
            return 1

        return 2

    except WorkspaceError:
        return 1
    except ManifestError:
        return 1
    except GitOperationError:
        return 2
    except SubrepoError:
        return 1
    except Exception:
        return 2


def status_command(args: argparse.Namespace) -> int:
    """Handle the 'status' command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for all clean, 1 for needs attention, 2 for system error)
    """
    import sys

    from .subtree_manager import get_all_component_status, get_component_status

    try:
        # Find workspace root
        workspace_path = Path.cwd()
        subrepo_dir = workspace_path / ".subrepo"

        if not subrepo_dir.exists():
            print("Error: Not in a subrepo workspace", file=sys.stderr)
            return 2

        # Load workspace config and manifest
        config = load_workspace_config(workspace_path)
        manifest_path = workspace_path / ".subrepo" / "manifest.xml"

        if not manifest_path.exists():
            print("Error: Manifest file not found", file=sys.stderr)
            return 2

        manifest = parse_manifest(manifest_path)

        # Get status for all or specific component
        if hasattr(args, "component") and args.component:
            # Find the component
            project = manifest.get_project_by_name(args.component)
            if not project:
                project = manifest.get_project_by_path(args.component)

            if not project:
                print(f"Error: Component not found: {args.component}", file=sys.stderr)
                return 1

            statuses = [get_component_status(workspace_path, project)]
        else:
            statuses = get_all_component_status(workspace_path, manifest)

        # Determine output format
        output_format = "text"
        if hasattr(args, "porcelain") and args.porcelain:
            output_format = "compact"
        elif hasattr(args, "format") and args.format:
            output_format = args.format

        # Validate format
        if output_format not in ["text", "json", "compact"]:
            print(f"Error: Invalid format: {output_format}", file=sys.stderr)
            return 1

        # Output status based on format
        if output_format == "json":
            _output_status_json(workspace_path, config, statuses)
        elif output_format == "compact":
            _output_status_compact(statuses)
        else:
            _output_status_text(workspace_path, config, statuses)

        # Determine exit code based on component states
        from .models import SubtreeStatus

        # Components that need attention
        # (exclude UNINITIALIZED as it's expected in clean workspaces)
        needs_attention = any(
            s.status not in (SubtreeStatus.UP_TO_DATE, SubtreeStatus.UNINITIALIZED)
            for s in statuses
        )

        return 1 if needs_attention else 0

    except WorkspaceError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except ManifestError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except GitOperationError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except SubrepoError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


def _output_status_text(
    workspace_path: Path, config: WorkspaceConfig, statuses: list[SubtreeState]
) -> None:
    """Output status in human-readable text format."""
    from .models import SubtreeStatus

    print("Workspace Status:")
    print(f"  Location: {workspace_path}")
    print(f"  Manifest: {config.manifest_path}")
    print()
    print("Components:")

    # Status symbols
    symbols = {
        SubtreeStatus.UP_TO_DATE: "✓",
        SubtreeStatus.AHEAD: "↑",
        SubtreeStatus.BEHIND: "↓",
        SubtreeStatus.DIVERGED: "⇅",
        SubtreeStatus.MODIFIED: "⚠",
        SubtreeStatus.UNINITIALIZED: "?",
        SubtreeStatus.ERROR: "✗",
    }

    for state in statuses:
        symbol = symbols.get(state.status, "?")
        # Colorize symbol based on status
        if state.status == SubtreeStatus.UP_TO_DATE:
            symbol = colorize(symbol, "green")
        elif (
            state.status in (SubtreeStatus.AHEAD, SubtreeStatus.BEHIND, SubtreeStatus.DIVERGED)
            or state.status == SubtreeStatus.MODIFIED
        ):
            symbol = colorize(symbol, "yellow")
        elif state.status == SubtreeStatus.ERROR:
            symbol = colorize(symbol, "red")

        # Status description
        status_text = state.status.value.replace("-", "_")
        print(f"  {symbol} {state.project.path}: {status_text}")

    # Summary
    summary = {
        "total": len(statuses),
        "up_to_date": sum(1 for s in statuses if s.status == SubtreeStatus.UP_TO_DATE),
        "ahead": sum(1 for s in statuses if s.status == SubtreeStatus.AHEAD),
        "behind": sum(1 for s in statuses if s.status == SubtreeStatus.BEHIND),
        "diverged": sum(1 for s in statuses if s.status == SubtreeStatus.DIVERGED),
        "modified": sum(1 for s in statuses if s.status == SubtreeStatus.MODIFIED),
        "uninitialized": sum(1 for s in statuses if s.status == SubtreeStatus.UNINITIALIZED),
    }

    print()
    print("Summary:")
    print(f"  Total components: {summary['total']}")
    print(f"  up_to_date: {summary['up_to_date']}")
    if summary["ahead"] > 0:
        print(f"  ahead: {summary['ahead']}")
    if summary["behind"] > 0:
        print(f"  behind: {summary['behind']}")
    if summary["diverged"] > 0:
        print(f"  diverged: {summary['diverged']}")
    if summary["modified"] > 0:
        print(f"  modified: {summary['modified']}")
    if summary["uninitialized"] > 0:
        print(f"  uninitialized: {summary['uninitialized']}")


def _output_status_json(
    workspace_path: Path, config: WorkspaceConfig, statuses: list[SubtreeState]
) -> None:
    """Output status in JSON format."""
    import json

    from .models import SubtreeStatus

    components = []
    for state in statuses:
        components.append(
            {
                "name": state.project.name,
                "path": state.project.path,
                "branch": state.project.revision,
                "status": state.status.value,
                "ahead": state.local_commits,
                "behind": state.upstream_commits,
                "modified": state.has_local_changes,
            }
        )

    summary = {
        "total": len(statuses),
        "up_to_date": sum(1 for s in statuses if s.status == SubtreeStatus.UP_TO_DATE),
        "ahead": sum(1 for s in statuses if s.status == SubtreeStatus.AHEAD),
        "behind": sum(1 for s in statuses if s.status == SubtreeStatus.BEHIND),
        "diverged": sum(1 for s in statuses if s.status == SubtreeStatus.DIVERGED),
        "modified": sum(1 for s in statuses if s.status == SubtreeStatus.MODIFIED),
        "uninitialized": sum(1 for s in statuses if s.status == SubtreeStatus.UNINITIALIZED),
    }

    output = {
        "workspace": str(workspace_path),
        "manifest": config.manifest_path,
        "components": components,
        "summary": summary,
    }
    print(json.dumps(output, indent=2))


def _output_status_compact(statuses: list[SubtreeState]) -> None:
    """Output status in compact machine-readable format."""

    for state in statuses:
        parts = [state.project.path, state.status.value]

        if state.local_commits > 0:
            parts.append(f"ahead:{state.local_commits}")
        if state.upstream_commits > 0:
            parts.append(f"behind:{state.upstream_commits}")

        print(" ".join(parts))


def completion_command(args: argparse.Namespace) -> int:
    """Generate shell completion scripts.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    if args.shell == "bash" or args.shell == "zsh":
        pass

    return 0


def handle_global_error(error: Exception) -> int:
    """Global error handler with actionable error messages.

    Args:
        error: Exception that was raised

    Returns:
        Appropriate exit code (1 for user errors, 2 for system errors)
    """
    if isinstance(error, ManifestError):
        return 1

    if isinstance(error, WorkspaceError):
        if "not initialized" in str(error).lower() or "not empty" in str(error).lower():
            pass
        return 1

    if isinstance(error, GitOperationError):
        return 2

    if isinstance(error, SubrepoError):
        return 1

    if isinstance(error, KeyboardInterrupt):
        return 130  # Standard exit code for Ctrl+C

    if _verbose:
        import traceback

        traceback.print_exc()
    else:
        pass
    return 2


def main() -> int:
    """Main entry point for subrepo CLI.

    Returns:
        Exit code
    """
    try:
        parser = argparse.ArgumentParser(
            prog="subrepo",
            description="Manage multi-repository projects using git subtrees",
        )

        # Global options
        parser.add_argument(
            "--version",
            "-V",
            action="version",
            version=f"subrepo {__version__}",
        )
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Enable verbose output",
        )
        parser.add_argument(
            "--quiet",
            "-q",
            action="store_true",
            help="Suppress non-error output",
        )
        parser.add_argument(
            "--no-color",
            action="store_true",
            help="Disable colored output",
        )

        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # init command
        init_parser = subparsers.add_parser(
            "init",
            help="Initialize a new workspace from a manifest file",
        )
        init_parser.add_argument(
            "manifest",
            help="Path or URL to manifest XML file",
        )
        init_parser.add_argument(
            "--name",
            "-n",
            help="Workspace name (default: current directory name)",
        )
        init_parser.add_argument(
            "--directory",
            "-d",
            help="Directory to initialize (default: current directory)",
        )
        init_parser.add_argument(
            "--no-clone",
            action="store_true",
            help="Validate manifest without cloning repositories",
        )

        # sync command
        sync_parser = subparsers.add_parser(
            "sync",
            help="Synchronize all or specific components with upstream",
        )
        sync_parser.add_argument(
            "--component",
            "-c",
            help="Sync specific component only (by name or path)",
        )
        sync_parser.add_argument(
            "--force",
            "-f",
            action="store_true",
            help="Force sync even with local changes (stash and reapply)",
        )
        sync_parser.add_argument(
            "--continue-on-error",
            action="store_true",
            help="Continue syncing other components if one fails",
        )

        # push command
        push_parser = subparsers.add_parser(
            "push",
            help="Push local changes in a component back to upstream",
        )
        push_parser.add_argument(
            "component",
            help="Component name or path to push",
        )
        push_parser.add_argument(
            "--branch",
            "-b",
            help="Target branch for push (default: component's revision)",
        )
        push_parser.add_argument(
            "--force",
            "-f",
            action="store_true",
            help="Force push (use with caution)",
        )
        push_parser.add_argument(
            "--dry-run",
            "-n",
            action="store_true",
            help="Show what would be pushed without pushing",
        )

        # pull command
        pull_parser = subparsers.add_parser(
            "pull",
            help="Pull upstream changes for a specific component",
        )
        pull_parser.add_argument(
            "component",
            help="Component name or path to pull",
        )
        pull_parser.add_argument(
            "--branch",
            "-b",
            help="Branch to pull from (default: component's revision)",
        )
        pull_parser.add_argument(
            "--squash",
            "-s",
            action="store_true",
            default=True,
            help="Squash upstream commits (default)",
        )
        pull_parser.add_argument(
            "--no-squash",
            action="store_true",
            help="Preserve individual upstream commits",
        )

        # Status command
        status_parser = subparsers.add_parser(
            "status",
            help="Show workspace component status",
        )
        status_parser.add_argument(
            "--component",
            "-c",
            type=str,
            help="Show status for specific component only (by name or path)",
        )
        status_parser.add_argument(
            "--format",
            "-f",
            type=str,
            choices=["text", "json", "compact"],
            default="text",
            help="Output format (default: text)",
        )
        status_parser.add_argument(
            "--porcelain",
            action="store_true",
            help="Machine-readable output (implies --format=compact)",
        )

        # Completion command (hidden - for generating shell completions)
        completion_parser = subparsers.add_parser(
            "completion",
            help="Generate shell completion scripts",
            add_help=False,  # Hide from main help
        )
        completion_parser.add_argument(
            "shell",
            choices=["bash", "zsh"],
            help="Shell type (bash or zsh)",
        )

        # Parse arguments
        args = parser.parse_args()

        # Setup logging and output flags
        global _no_color
        setup_logging(verbose=args.verbose, quiet=args.quiet)
        _no_color = args.no_color

        # Log configuration in verbose mode
        if args.verbose:
            logger.debug("Verbose mode enabled")
            logger.debug(f"Arguments: {args}")

        # Route to command handler
        if args.command == "init":
            return init_command(args)
        if args.command == "sync":
            return sync_command(args)
        if args.command == "push":
            return push_command(args)
        if args.command == "pull":
            return pull_command(args)
        if args.command == "status":
            return status_command(args)
        if args.command == "completion":
            return completion_command(args)
        parser.print_help()
        return 1

    except Exception as e:
        return handle_global_error(e)


if __name__ == "__main__":
    sys.exit(main())
