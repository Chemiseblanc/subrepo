"""Unit tests for XML parsing logic in manifest_parser module.

Tests XML parsing and manifest validation functions.
Per TDD: These tests MUST fail until implementation is complete.
"""

import tempfile
from pathlib import Path

import pytest


class TestXMLParsingLogic:
    """Tests for XML parsing functionality."""

    def test_parse_simple_manifest_xml(self):
        """Test parsing a simple manifest XML with one remote and one project.

        This test will FAIL until parse_manifest is implemented.
        """
        from subrepo.manifest_parser import parse_manifest

        # Create test manifest
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <default remote="origin" revision="main" />
  <project name="org/repo" path="lib/repo" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            manifest = parse_manifest(manifest_path)

            # Assert remote parsed correctly
            assert len(manifest.remotes) == 1
            assert "origin" in manifest.remotes
            assert manifest.remotes["origin"].name == "origin"
            assert manifest.remotes["origin"].fetch == "https://github.com/"

            # Assert default parsed correctly
            assert manifest.default_remote == "origin"
            assert manifest.default_revision == "main"

            # Assert project parsed correctly
            assert len(manifest.projects) == 1
            project = manifest.projects[0]
            assert project.name == "org/repo"
            assert project.path == "lib/repo"
            assert project.remote == "origin"
            assert project.revision == "main"  # Should use default
        finally:
            manifest_path.unlink()

    def test_parse_manifest_with_multiple_remotes(self):
        """Test parsing manifest with multiple remotes.

        This test will FAIL until parse_manifest is implemented.
        """
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="github" fetch="https://github.com/" />
  <remote name="gitlab" fetch="https://gitlab.com/" />
  <default remote="github" revision="main" />
  <project name="org/repo1" path="lib/repo1" />
  <project name="org/repo2" path="lib/repo2" remote="gitlab" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            manifest = parse_manifest(manifest_path)

            assert len(manifest.remotes) == 2
            assert "github" in manifest.remotes
            assert "gitlab" in manifest.remotes

            # First project uses default remote
            assert manifest.projects[0].remote == "github"

            # Second project explicitly uses gitlab
            assert manifest.projects[1].remote == "gitlab"
        finally:
            manifest_path.unlink()

    def test_parse_manifest_with_explicit_revisions(self):
        """Test parsing manifest where projects specify explicit revisions.

        This test will FAIL until parse_manifest is implemented.
        """
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <default remote="origin" revision="main" />
  <project name="org/repo1" path="lib/repo1" revision="v1.0.0" />
  <project name="org/repo2" path="lib/repo2" revision="develop" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            manifest = parse_manifest(manifest_path)

            # Projects should use their explicit revisions
            assert manifest.projects[0].revision == "v1.0.0"
            assert manifest.projects[1].revision == "develop"
        finally:
            manifest_path.unlink()

    def test_parse_malformed_xml_raises_error(self):
        """Test that malformed XML raises a parsing error.

        This test will FAIL until parse_manifest is implemented.
        """
        from subrepo.exceptions import ManifestError
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("<manifest><unclosed>")
            manifest_path = Path(f.name)

        try:
            with pytest.raises(ManifestError):
                parse_manifest(manifest_path)
        finally:
            manifest_path.unlink()

    def test_parse_nonexistent_file_raises_error(self):
        """Test that parsing a non-existent file raises an error.

        This test will FAIL until parse_manifest is implemented.
        """
        from subrepo.exceptions import ManifestError
        from subrepo.manifest_parser import parse_manifest

        with pytest.raises(ManifestError):
            parse_manifest(Path("/nonexistent/manifest.xml"))


class TestManifestValidationRules:
    """Tests for manifest validation logic."""

    def test_validate_manifest_with_no_remotes_fails(self):
        """Test that validation fails when manifest has no remotes.

        Parse fails early when project has no remote and no default.
        """
        from subrepo.exceptions import ManifestError
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <project name="org/repo" path="lib/repo" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            with pytest.raises(ManifestError, match="has no remote specified"):
                parse_manifest(manifest_path)
        finally:
            manifest_path.unlink()

    def test_validate_manifest_with_no_projects_fails(self):
        """Test that validation fails when manifest has no projects.

        Model validation catches this in __post_init__.
        """
        from subrepo.exceptions import ManifestValidationError
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            # Model __post_init__ catches empty projects and raises ManifestValidationError
            with pytest.raises(ManifestValidationError):
                parse_manifest(manifest_path)
        finally:
            manifest_path.unlink()

    def test_validate_manifest_with_invalid_remote_reference(self):
        """Test that validation fails when project references non-existent remote.

        Model __post_init__ validates remote references.
        """
        from subrepo.exceptions import ManifestValidationError
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <project name="org/repo" path="lib/repo" remote="nonexistent" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            with pytest.raises(ManifestValidationError, match="references unknown remote"):
                parse_manifest(manifest_path)
        finally:
            manifest_path.unlink()

    def test_validate_manifest_with_duplicate_paths_fails(self):
        """Test that validation fails when multiple projects use the same path.

        Model __post_init__ validates path uniqueness.
        """
        from subrepo.exceptions import ManifestValidationError
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <default remote="origin" revision="main" />
  <project name="org/repo1" path="lib/repo" />
  <project name="org/repo2" path="lib/repo" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            with pytest.raises(ManifestValidationError, match="Duplicate"):
                parse_manifest(manifest_path)
        finally:
            manifest_path.unlink()

    def test_validate_manifest_with_absolute_path_fails(self):
        """Test that validation fails when project path is absolute.

        This test will FAIL until validate_manifest is implemented.
        """
        from subrepo.exceptions import ManifestValidationError
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <default remote="origin" revision="main" />
  <project name="org/repo" path="/absolute/path" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            with pytest.raises(ManifestValidationError):
                parse_manifest(manifest_path)
        finally:
            manifest_path.unlink()

    def test_validate_manifest_with_path_parent_reference_fails(self):
        """Test that validation fails when project path contains '..' components.

        This ensures projects can't escape the workspace directory.
        """
        from subrepo.exceptions import ManifestValidationError
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <default remote="origin" revision="main" />
  <project name="org/repo" path="../outside" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            with pytest.raises(ManifestValidationError):
                parse_manifest(manifest_path)
        finally:
            manifest_path.unlink()

    def test_parse_manifest_missing_project_name(self):
        """Test that parsing fails when project is missing name attribute."""
        from subrepo.exceptions import ManifestError
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <project path="lib/repo" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            with pytest.raises(ManifestError, match="missing required 'name' attribute"):
                parse_manifest(manifest_path)
        finally:
            manifest_path.unlink()

    def test_parse_manifest_missing_project_path(self):
        """Test that parsing fails when project is missing path attribute."""
        from subrepo.exceptions import ManifestError
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <project name="org/repo" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            with pytest.raises(ManifestError, match="missing required 'path' attribute"):
                parse_manifest(manifest_path)
        finally:
            manifest_path.unlink()

    def test_parse_manifest_missing_remote_name(self):
        """Test that parsing fails when remote is missing name attribute."""
        from subrepo.exceptions import ManifestError
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote fetch="https://github.com/" />
  <project name="org/repo" path="lib/repo" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            with pytest.raises(ManifestError, match="missing required 'name' attribute"):
                parse_manifest(manifest_path)
        finally:
            manifest_path.unlink()

    def test_parse_manifest_missing_remote_fetch(self):
        """Test that parsing fails when remote is missing fetch attribute."""
        from subrepo.exceptions import ManifestError
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" />
  <project name="org/repo" path="lib/repo" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            with pytest.raises(ManifestError, match="missing required 'fetch' attribute"):
                parse_manifest(manifest_path)
        finally:
            manifest_path.unlink()

    def test_parse_manifest_with_optional_attributes(self):
        """Test parsing manifest with optional remote and project attributes."""
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" push="https://github.com/push" review="https://review.com" />
  <default remote="origin" revision="main" />
  <project name="org/repo" path="lib/repo" upstream="upstream-branch" clone-depth="1" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            manifest = parse_manifest(manifest_path)

            # Check remote optional attributes
            assert manifest.remotes["origin"].push_url == "https://github.com/push"
            assert manifest.remotes["origin"].review == "https://review.com"

            # Check project optional attributes
            assert manifest.projects[0].upstream == "upstream-branch"
            assert manifest.projects[0].clone_depth == 1
        finally:
            manifest_path.unlink()

    def test_parse_manifest_with_notice(self):
        """Test parsing manifest with notice element."""
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <default remote="origin" revision="main" />
  <project name="org/repo" path="lib/repo" />
  <notice>
    This is a notice message.
    It can span multiple lines.
  </notice>
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            manifest = parse_manifest(manifest_path)
            assert manifest.notice is not None
            assert "This is a notice message" in manifest.notice
        finally:
            manifest_path.unlink()

    def test_parse_manifest_project_with_no_default_remote(self):
        """Test that parsing fails when project has no remote and no default remote."""
        from subrepo.exceptions import ManifestError
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <project name="org/repo" path="lib/repo" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            with pytest.raises(ManifestError, match="has no remote specified"):
                parse_manifest(manifest_path)
        finally:
            manifest_path.unlink()

    def test_validate_manifest_invalid_default_remote(self):
        """Test that validation fails when default remote doesn't exist."""
        from subrepo.exceptions import ManifestValidationError
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <default remote="nonexistent" revision="main" />
  <project name="org/repo" path="lib/repo" remote="origin" />
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            with pytest.raises(ManifestValidationError, match="Default remote"):
                parse_manifest(manifest_path)
        finally:
            manifest_path.unlink()

    def test_parse_manifest_wrong_root_element(self):
        """Test that parsing fails when root element is not <manifest>."""
        from subrepo.exceptions import ManifestError
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<wrongroot>
  <remote name="origin" fetch="https://github.com/" />
</wrongroot>
"""
            )
            manifest_path = Path(f.name)

        try:
            with pytest.raises(ManifestError, match="Expected <manifest> root element"):
                parse_manifest(manifest_path)
        finally:
            manifest_path.unlink()

    def test_is_commit_sha(self):
        """Test the is_commit_sha utility function."""
        from subrepo.manifest_parser import is_commit_sha

        # Valid SHA
        assert is_commit_sha("a" * 40)
        assert is_commit_sha("1234567890abcdef1234567890abcdef12345678")

        # Invalid SHAs
        assert not is_commit_sha("main")
        assert not is_commit_sha("v1.0.0")
        assert not is_commit_sha("a" * 39)  # Too short
        assert not is_commit_sha("a" * 41)  # Too long
        assert not is_commit_sha("g" * 40)  # Invalid character

    def test_extract_default_branch_from_project(self):
        """Test extracting default branch from project."""
        from subrepo.manifest_parser import extract_default_branch_from_project
        from subrepo.models import Project

        # Branch name
        project = Project(name="test", path="test", remote="origin", revision="main")
        assert extract_default_branch_from_project(project) == "main"

        # Tag
        project = Project(name="test", path="test", remote="origin", revision="v1.0.0")
        assert extract_default_branch_from_project(project) == "v1.0.0"

        # SHA - should return None
        project = Project(name="test", path="test", remote="origin", revision="a" * 40)
        assert extract_default_branch_from_project(project) is None


class TestCopyfileAndLinkfileParsing:
    """Tests for parsing copyfile and linkfile elements from XML."""

    def test_parse_project_extracts_copyfile_elements(self):
        """Test that parse_project extracts copyfile elements from XML."""
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <default remote="origin" revision="main" />
  <project name="org/repo" path="lib/repo">
    <copyfile src="docs/README.md" dest="README.md" />
  </project>
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            manifest = parse_manifest(manifest_path)

            assert len(manifest.projects) == 1
            project = manifest.projects[0]
            assert len(project.copyfiles) == 1
            assert project.copyfiles[0].src == "docs/README.md"
            assert project.copyfiles[0].dest == "README.md"
        finally:
            manifest_path.unlink()

    def test_parse_project_creates_copyfile_objects_with_correct_src_dest(self):
        """Test that parse_project creates Copyfile objects with correct attributes."""
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <default remote="origin" revision="main" />
  <project name="org/repo" path="lib/repo">
    <copyfile src="config/Makefile" dest="build/Makefile" />
  </project>
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            manifest = parse_manifest(manifest_path)

            copyfile = manifest.projects[0].copyfiles[0]
            assert copyfile.src == "config/Makefile"
            assert copyfile.dest == "build/Makefile"
        finally:
            manifest_path.unlink()

    def test_parse_project_handles_multiple_copyfile_elements(self):
        """Test that parse_project handles multiple copyfile elements per project."""
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <default remote="origin" revision="main" />
  <project name="org/repo" path="lib/repo">
    <copyfile src="docs/README.md" dest="README.md" />
    <copyfile src="docs/LICENSE" dest="LICENSE" />
    <copyfile src="config/Makefile" dest="Makefile" />
  </project>
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            manifest = parse_manifest(manifest_path)

            project = manifest.projects[0]
            assert len(project.copyfiles) == 3
            assert project.copyfiles[0].src == "docs/README.md"
            assert project.copyfiles[1].src == "docs/LICENSE"
            assert project.copyfiles[2].src == "config/Makefile"
        finally:
            manifest_path.unlink()

    def test_parse_project_extracts_linkfile_elements(self):
        """Test that parse_project extracts linkfile elements from XML. (T036)"""
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <default remote="origin" revision="main" />
  <project name="org/repo" path="lib/repo">
    <linkfile src="scripts/build.sh" dest="build.sh" />
  </project>
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            manifest = parse_manifest(manifest_path)

            assert len(manifest.projects) == 1
            project = manifest.projects[0]
            assert len(project.linkfiles) == 1
            assert project.linkfiles[0].src == "scripts/build.sh"
            assert project.linkfiles[0].dest == "build.sh"
        finally:
            manifest_path.unlink()

    def test_parse_project_creates_linkfile_objects_with_correct_src_dest(self):
        """Test that parse_project creates Linkfile objects with correct attributes. (T037)"""
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <default remote="origin" revision="main" />
  <project name="org/repo" path="lib/repo">
    <linkfile src="docs" dest="documentation" />
  </project>
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            manifest = parse_manifest(manifest_path)

            linkfile = manifest.projects[0].linkfiles[0]
            assert linkfile.src == "docs"
            assert linkfile.dest == "documentation"
        finally:
            manifest_path.unlink()

    def test_parse_project_handles_multiple_linkfile_elements(self):
        """Test that parse_project handles multiple linkfile elements per project. (T038)"""
        from subrepo.manifest_parser import parse_manifest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="origin" fetch="https://github.com/" />
  <default remote="origin" revision="main" />
  <project name="org/repo" path="lib/repo">
    <linkfile src="scripts/build.sh" dest="build.sh" />
    <linkfile src="scripts/test.sh" dest="test.sh" />
    <linkfile src="docs" dest="documentation" />
  </project>
</manifest>
"""
            )
            manifest_path = Path(f.name)

        try:
            manifest = parse_manifest(manifest_path)

            project = manifest.projects[0]
            assert len(project.linkfiles) == 3
            assert project.linkfiles[0].src == "scripts/build.sh"
            assert project.linkfiles[1].src == "scripts/test.sh"
            assert project.linkfiles[2].src == "docs"
        finally:
            manifest_path.unlink()
