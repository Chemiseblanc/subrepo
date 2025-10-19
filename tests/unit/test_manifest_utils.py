"""Tests for manifest utility functions.

This module tests utility functions for parsing and interpreting manifest data,
specifically the is_commit_sha() function for distinguishing commit SHAs from branch names.
"""

import pytest

from subrepo.manifest_parser import is_commit_sha


class TestIsCommitSha:
    """Tests for is_commit_sha() function."""

    def test_recognizes_full_sha(self) -> None:
        """Test that full 40-character SHA-1 hashes are recognized."""
        sha = "a" * 40  # 40 hex characters
        assert is_commit_sha(sha) is True

    def test_recognizes_full_sha_mixed_case(self) -> None:
        """Test that SHAs with mixed case are recognized."""
        sha = "AbCdEf0123456789" * 2 + "abcdef01"  # 40 chars mixed case
        assert is_commit_sha(sha) is True

    def test_rejects_short_sha(self) -> None:
        """Test that short SHAs (7-8 chars) are not recognized as full SHAs."""
        sha = "a1b2c3d"  # 7 chars
        assert is_commit_sha(sha) is False

    def test_rejects_branch_name(self) -> None:
        """Test that regular branch names are not recognized as SHAs."""
        assert is_commit_sha("main") is False
        assert is_commit_sha("feature/auth") is False
        assert is_commit_sha("release-1.0") is False

    def test_rejects_empty_string(self) -> None:
        """Test that empty string is not recognized as SHA."""
        assert is_commit_sha("") is False

    def test_rejects_too_long_string(self) -> None:
        """Test that strings longer than 40 chars are not recognized as SHAs."""
        sha = "a" * 41  # 41 chars
        assert is_commit_sha(sha) is False

    def test_rejects_non_hex_characters(self) -> None:
        """Test that strings with non-hex characters are not recognized as SHAs."""
        # 40 chars but contains 'g'
        not_sha = "g" + "a" * 39
        assert is_commit_sha(not_sha) is False

    def test_recognizes_realistic_sha(self) -> None:
        """Test with realistic commit SHAs from actual git usage."""
        assert is_commit_sha("a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0") is True
        assert is_commit_sha("0123456789abcdef0123456789abcdef01234567") is True
        assert is_commit_sha("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF") is True
