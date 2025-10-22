"""Unit tests for file operations module."""

import os
import tempfile
from pathlib import Path

import pytest

# These imports will fail until we create the file_operations module (TDD RED phase)
try:
    from subrepo.file_operations import (
        copy_file,
        create_symlink,
        execute_copyfile_operations,
        execute_linkfile_operations,
        validate_path_security,
    )
    from subrepo.exceptions import FileOperationError, PathSecurityError
    from subrepo.models import Copyfile, Linkfile, Project
except ImportError:
    # Tests will be skipped until implementation exists
    pytest.skip("file_operations module not yet implemented", allow_module_level=True)


class TestValidatePathSecurity:
    """Tests for validate_path_security function."""

    def test_rejects_dotdot_components(self):
        """Test that paths with '..' components are rejected."""
        workspace_root = Path("/workspace")
        project_dir = Path("/workspace/project")

        with pytest.raises(PathSecurityError, match="cannot contain"):
            validate_path_security(
                src_path="../etc/passwd",
                dest_path="output.txt",
                workspace_root=workspace_root,
                project_dir=project_dir,
            )

    def test_rejects_absolute_paths(self):
        """Test that absolute paths are rejected."""
        workspace_root = Path("/workspace")
        project_dir = Path("/workspace/project")

        with pytest.raises(PathSecurityError, match="must be relative"):
            validate_path_security(
                src_path="/etc/passwd",
                dest_path="output.txt",
                workspace_root=workspace_root,
                project_dir=project_dir,
            )

    def test_rejects_paths_escaping_workspace(self):
        """Test that dest paths escaping workspace root are rejected."""
        workspace_root = Path("/workspace")
        project_dir = Path("/workspace/project")

        # This would resolve outside workspace
        with pytest.raises(PathSecurityError, match="cannot contain"):
            validate_path_security(
                src_path="file.txt",
                dest_path="../../outside/file.txt",
                workspace_root=workspace_root,
                project_dir=project_dir,
            )

    def test_accepts_valid_relative_paths(self):
        """Test that valid relative paths are accepted."""
        workspace_root = Path("/workspace")
        project_dir = Path("/workspace/project")

        # Should not raise any exception
        validate_path_security(
            src_path="docs/README.md",
            dest_path="README.md",
            workspace_root=workspace_root,
            project_dir=project_dir,
        )

        validate_path_security(
            src_path="config/build/Makefile",
            dest_path="output/build/Makefile",
            workspace_root=workspace_root,
            project_dir=project_dir,
        )


class TestCopyFile:
    """Tests for copy_file function."""

    def test_preserves_permissions(self):
        """Test that copy_file preserves file permissions using shutil.copy2."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "source.txt"
            dest = Path(tmpdir) / "dest.txt"

            src.write_text("content")
            src.chmod(0o755)  # rwxr-xr-x

            copy_file(src, dest)

            assert dest.exists()
            assert dest.read_text() == "content"
            assert dest.stat().st_mode == src.stat().st_mode

    def test_creates_parent_directories(self):
        """Test that copy_file creates parent directories if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "source.txt"
            dest = Path(tmpdir) / "nested" / "dirs" / "dest.txt"

            src.write_text("content")

            copy_file(src, dest)

            assert dest.exists()
            assert dest.read_text() == "content"

    def test_dereferences_symlinks_at_source(self):
        """Test that copy_file dereferences symlinks at source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target.txt"
            symlink_src = Path(tmpdir) / "link.txt"
            dest = Path(tmpdir) / "dest.txt"

            target.write_text("target content")
            symlink_src.symlink_to(target)

            copy_file(symlink_src, dest)

            assert dest.exists()
            assert dest.read_text() == "target content"
            assert not dest.is_symlink()  # Should be regular file

    def test_overwrites_existing_dest_files(self):
        """Test that copy_file overwrites existing destination files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "source.txt"
            dest = Path(tmpdir) / "dest.txt"

            src.write_text("new content")
            dest.write_text("old content")

            copy_file(src, dest)

            assert dest.read_text() == "new content"

    def test_handles_missing_source_file_error(self):
        """Test that copy_file raises FileOperationError when source missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "nonexistent.txt"
            dest = Path(tmpdir) / "dest.txt"

            with pytest.raises(FileOperationError, match="source.*not found"):
                copy_file(src, dest)


class TestCreateSymlink:
    """Tests for create_symlink function."""

    def test_creates_symlink(self):
        """Test that create_symlink creates a symbolic link."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target.txt"
            link = Path(tmpdir) / "link.txt"

            target.write_text("content")

            result = create_symlink(target, link)

            assert link.exists()
            assert link.is_symlink()
            assert link.resolve() == target.resolve()
            assert not result.fallback_used

    def test_creates_parent_directories(self):
        """Test that create_symlink creates parent directories if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target.txt"
            link = Path(tmpdir) / "nested" / "dirs" / "link.txt"

            target.write_text("content")

            result = create_symlink(target, link)

            assert link.exists()
            assert link.is_symlink()

    def test_handles_symlink_to_directory(self):
        """Test that create_symlink handles symlinks to directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "target_dir"
            link = Path(tmpdir) / "link_dir"

            target_dir.mkdir()
            (target_dir / "file.txt").write_text("content")

            result = create_symlink(target_dir, link)

            assert link.exists()
            assert link.is_symlink()
            assert link.is_dir()

    def test_fallback_to_copy_on_symlink_failure(self):
        """Test that create_symlink falls back to copy when symlink fails. (T040)"""
        import unittest.mock

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target.txt"
            link = Path(tmpdir) / "link.txt"

            target.write_text("content")

            # Mock symlink_to to raise OSError (simulating unsupported filesystem)
            with unittest.mock.patch.object(
                Path, "symlink_to", side_effect=OSError("Not supported")
            ):
                result = create_symlink(target, link)

            # Should have fallen back to copy
            assert link.exists()
            assert not link.is_symlink()  # It's a regular file now
            assert link.read_text() == "content"
            assert result.fallback_used
            assert result.success

    def test_fallback_preserves_content_for_directories(self):
        """Test that create_symlink fallback works for directories. (T040 continued)"""
        import unittest.mock

        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "target_dir"
            link = Path(tmpdir) / "link_dir"

            target_dir.mkdir()
            (target_dir / "file1.txt").write_text("content1")
            (target_dir / "file2.txt").write_text("content2")

            # Mock symlink_to to raise OSError
            with unittest.mock.patch.object(
                Path, "symlink_to", side_effect=OSError("Not supported")
            ):
                result = create_symlink(target_dir, link)

            # Should have fallen back to copytree
            assert link.exists()
            assert link.is_dir()
            assert not link.is_symlink()
            assert (link / "file1.txt").read_text() == "content1"
            assert (link / "file2.txt").read_text() == "content2"
            assert result.fallback_used
            assert result.success

    def test_fallback_raises_on_copy_failure(self):
        """Test that create_symlink raises when both symlink and copy fail."""
        import unittest.mock

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target.txt"
            link = Path(tmpdir) / "link.txt"

            target.write_text("content")

            # Mock both symlink_to and copy2 to fail
            with unittest.mock.patch.object(
                Path, "symlink_to", side_effect=OSError("Symlink not supported")
            ):
                with unittest.mock.patch(
                    "shutil.copy2", side_effect=OSError("Copy failed")
                ):
                    with pytest.raises(FileOperationError, match="Failed to create symlink"):
                        create_symlink(target, link)

    def test_copy_file_raises_on_oserror(self):
        """Test that copy_file raises FileOperationError on OSError."""
        import unittest.mock

        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "source.txt"
            dest = Path(tmpdir) / "dest.txt"

            src.write_text("content")

            # Mock copy2 to raise OSError
            with unittest.mock.patch(
                "shutil.copy2", side_effect=OSError("Permission denied")
            ):
                with pytest.raises(FileOperationError, match="Failed to copy"):
                    copy_file(src, dest)


class TestExecuteCopyfileOperations:
    """Tests for execute_copyfile_operations function."""

    def test_execute_successful_copyfile(self):
        """Test executing a successful copyfile operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            project_dir = Path(tmpdir) / "workspace" / "myproject"
            project_dir.mkdir(parents=True)

            # Create source file
            (project_dir / "README.md").write_text("Project readme")

            project = Project(
                name="myproject",
                path="myproject",
                remote="origin",
                copyfiles=[Copyfile(src="README.md", dest="docs/README.md")],
            )

            results = execute_copyfile_operations(project, workspace, project_dir)

            assert len(results) == 1
            assert results[0].success
            assert results[0].project_name == "myproject"
            assert results[0].operation_type == "copyfile"
            assert results[0].src == "README.md"
            assert results[0].dest == "docs/README.md"
            assert (workspace / "docs" / "README.md").read_text() == "Project readme"

    def test_execute_multiple_copyfiles(self):
        """Test executing multiple copyfile operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            project_dir = Path(tmpdir) / "workspace" / "myproject"
            project_dir.mkdir(parents=True)

            # Create source files
            (project_dir / "README.md").write_text("Project readme")
            (project_dir / "LICENSE").write_text("MIT License")

            project = Project(
                name="myproject",
                path="myproject",
                remote="origin",
                copyfiles=[
                    Copyfile(src="README.md", dest="docs/README.md"),
                    Copyfile(src="LICENSE", dest="LICENSE"),
                ],
            )

            results = execute_copyfile_operations(project, workspace, project_dir)

            assert len(results) == 2
            assert all(r.success for r in results)
            assert (workspace / "docs" / "README.md").exists()
            assert (workspace / "LICENSE").exists()

    def test_execute_copyfile_handles_errors_gracefully(self):
        """Test that errors during copyfile operations are captured in results."""
        import unittest.mock

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            project_dir = Path(tmpdir) / "workspace" / "myproject"
            project_dir.mkdir(parents=True)

            # Create source file
            (project_dir / "file.txt").write_text("content")

            project = Project(
                name="myproject",
                path="myproject",
                remote="origin",
                copyfiles=[Copyfile(src="file.txt", dest="output.txt")],
            )

            # Mock validate_path_security to raise an error
            with unittest.mock.patch(
                "subrepo.file_operations.validate_path_security",
                side_effect=PathSecurityError("Mock security error"),
            ):
                results = execute_copyfile_operations(project, workspace, project_dir)

            assert len(results) == 1
            assert not results[0].success
            assert "Mock security error" in results[0].error_message

    def test_execute_copyfile_with_missing_source(self):
        """Test that missing source files are captured in results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            project_dir = Path(tmpdir) / "workspace" / "myproject"
            project_dir.mkdir(parents=True)

            # Don't create source file
            project = Project(
                name="myproject",
                path="myproject",
                remote="origin",
                copyfiles=[Copyfile(src="missing.txt", dest="output.txt")],
            )

            results = execute_copyfile_operations(project, workspace, project_dir)

            assert len(results) == 1
            assert not results[0].success
            assert "not found" in results[0].error_message


class TestExecuteLinkfileOperations:
    """Tests for execute_linkfile_operations function."""

    def test_execute_successful_linkfile(self):
        """Test executing a successful linkfile operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            project_dir = Path(tmpdir) / "workspace" / "myproject"
            project_dir.mkdir(parents=True)

            # Create source file
            (project_dir / "config.yml").write_text("config: value")

            project = Project(
                name="myproject",
                path="myproject",
                remote="origin",
                linkfiles=[Linkfile(src="config.yml", dest="config/config.yml")],
            )

            results = execute_linkfile_operations(project, workspace, project_dir)

            assert len(results) == 1
            assert results[0].success
            assert results[0].project_name == "myproject"
            assert results[0].operation_type == "linkfile"
            assert results[0].src == "config.yml"
            assert results[0].dest == "config/config.yml"

            link_path = workspace / "config" / "config.yml"
            assert link_path.exists()
            # Should be a symlink (or copy on systems that don't support symlinks)
            assert link_path.read_text() == "config: value"

    def test_execute_multiple_linkfiles(self):
        """Test executing multiple linkfile operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            project_dir = Path(tmpdir) / "workspace" / "myproject"
            project_dir.mkdir(parents=True)

            # Create source files
            (project_dir / "config1.yml").write_text("config1")
            (project_dir / "config2.yml").write_text("config2")

            project = Project(
                name="myproject",
                path="myproject",
                remote="origin",
                linkfiles=[
                    Linkfile(src="config1.yml", dest="cfg/config1.yml"),
                    Linkfile(src="config2.yml", dest="cfg/config2.yml"),
                ],
            )

            results = execute_linkfile_operations(project, workspace, project_dir)

            assert len(results) == 2
            assert all(r.success for r in results)
            assert (workspace / "cfg" / "config1.yml").exists()
            assert (workspace / "cfg" / "config2.yml").exists()

    def test_execute_linkfile_handles_errors_gracefully(self):
        """Test that errors during linkfile operations are captured in results."""
        import unittest.mock

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            project_dir = Path(tmpdir) / "workspace" / "myproject"
            project_dir.mkdir(parents=True)

            # Create source file
            (project_dir / "file.txt").write_text("content")

            project = Project(
                name="myproject",
                path="myproject",
                remote="origin",
                linkfiles=[Linkfile(src="file.txt", dest="output.txt")],
            )

            # Mock validate_path_security to raise an error
            with unittest.mock.patch(
                "subrepo.file_operations.validate_path_security",
                side_effect=PathSecurityError("Mock security error"),
            ):
                results = execute_linkfile_operations(project, workspace, project_dir)

            assert len(results) == 1
            assert not results[0].success
            assert "Mock security error" in results[0].error_message
