#!/usr/bin/env python3
"""
Tests for nexus-dist/context/importance.py
Tests the importance marking and compression system.
"""

import sys
from pathlib import Path

# Add nexus-dist/context to path
sys.path.insert(0, str(Path(__file__).parent.parent / "nexus-dist" / "context"))

import pytest
from importance import (
    Importance,
    MarkedContent,
    mark,
    compress_by_importance,
    format_marked_output,
)


class TestImportance:
    """Test Importance enum."""

    def test_importance_levels(self):
        """Test that all importance levels exist."""
        assert Importance.HIGH.value == "high"
        assert Importance.MEDIUM.value == "medium"
        assert Importance.LOW.value == "low"


class TestMarkedContent:
    """Test MarkedContent dataclass."""

    def test_create_marked_content(self):
        """Test creating MarkedContent."""
        content = MarkedContent(
            content="test content",
            importance=Importance.HIGH,
            category="file",
            source="explorer",
        )

        assert content.content == "test content"
        assert content.importance == Importance.HIGH
        assert content.category == "file"
        assert content.source == "explorer"

    def test_marked_content_len(self):
        """Test __len__ returns content length."""
        content = MarkedContent(
            content="hello",
            importance=Importance.HIGH,
            category="test",
            source="test",
        )
        assert len(content) == 5


class TestMark:
    """Test the mark() function."""

    def test_mark_creates_marked_content(self):
        """Test that mark() creates MarkedContent."""
        result = mark(
            "test content",
            Importance.HIGH,
            "file",
            "explorer",
        )

        assert isinstance(result, MarkedContent)
        assert result.content == "test content"
        assert result.importance == Importance.HIGH
        assert result.category == "file"
        assert result.source == "explorer"

    def test_mark_with_all_importance_levels(self):
        """Test marking with all importance levels."""
        high = mark("high", Importance.HIGH, "test", "test")
        medium = mark("medium", Importance.MEDIUM, "test", "test")
        low = mark("low", Importance.LOW, "test", "test")

        assert high.importance == Importance.HIGH
        assert medium.importance == Importance.MEDIUM
        assert low.importance == Importance.LOW


class TestCompressByImportance:
    """Test the compress_by_importance() function."""

    def test_compress_preserves_high_first(self):
        """Test that HIGH importance items are preserved first."""
        items = [
            mark("low item", Importance.LOW, "test", "test"),
            mark("high item", Importance.HIGH, "test", "test"),
            mark("medium item", Importance.MEDIUM, "test", "test"),
        ]

        # Compress to only fit high + medium
        compressed = compress_by_importance(items, max_chars=25)

        # Should keep HIGH first, then MEDIUM
        assert len(compressed) == 2
        assert compressed[0].importance == Importance.HIGH
        assert compressed[1].importance == Importance.MEDIUM

    def test_compress_respects_max_chars(self):
        """Test that compression respects max_chars limit."""
        items = [
            mark("a" * 100, Importance.HIGH, "test", "test"),
            mark("b" * 100, Importance.HIGH, "test", "test"),
            mark("c" * 100, Importance.LOW, "test", "test"),
        ]

        compressed = compress_by_importance(items, max_chars=150)

        # Should only fit first HIGH item
        assert len(compressed) <= 2
        total_chars = sum(len(item) for item in compressed)
        assert total_chars <= 150

    def test_compress_truncates_high_if_needed(self):
        """Test that HIGH items are truncated if exceeding max_chars."""
        items = [
            mark("a" * 200, Importance.HIGH, "test", "test"),
        ]

        compressed = compress_by_importance(items, max_chars=100)

        # Should truncate and add "..."
        # The "..." suffix adds 3 chars beyond the truncation point
        ELLIPSIS_OVERHEAD = 3
        assert len(compressed) == 1
        assert compressed[0].content.endswith("...")
        assert len(compressed[0]) <= 100 + ELLIPSIS_OVERHEAD

    def test_compress_skips_truncate_if_too_small(self):
        """Test that truncation is skipped if remaining space < 50."""
        items = [
            mark("a" * 100, Importance.HIGH, "test", "test"),
            mark("b" * 100, Importance.HIGH, "test", "test"),
        ]

        compressed = compress_by_importance(items, max_chars=110)

        # Should only keep first item, not truncate second (not enough space)
        assert len(compressed) == 1
        assert not compressed[0].content.endswith("...")

    def test_compress_empty_list(self):
        """Test compressing empty list."""
        compressed = compress_by_importance([], max_chars=100)
        assert compressed == []

    def test_compress_sorts_by_importance(self):
        """Test that items are sorted HIGH > MEDIUM > LOW."""
        items = [
            mark("1", Importance.LOW, "test", "test"),
            mark("2", Importance.HIGH, "test", "test"),
            mark("3", Importance.MEDIUM, "test", "test"),
            mark("4", Importance.HIGH, "test", "test"),
            mark("5", Importance.LOW, "test", "test"),
        ]

        compressed = compress_by_importance(items, max_chars=1000)

        # Should be sorted: HIGH items first, then MEDIUM, then LOW
        assert compressed[0].content == "2"
        assert compressed[1].content == "4"
        assert compressed[2].content == "3"
        assert compressed[3].content == "1"
        assert compressed[4].content == "5"


class TestFormatMarkedOutput:
    """Test the format_marked_output() function."""

    def test_format_empty_list(self):
        """Test formatting empty list."""
        result = format_marked_output([])
        assert result == ""

    def test_format_groups_by_importance(self):
        """Test that output is grouped by importance."""
        items = [
            mark("high1", Importance.HIGH, "file", "explorer"),
            mark("medium1", Importance.MEDIUM, "issue", "reviewer"),
            mark("low1", Importance.LOW, "info", "tester"),
        ]

        result = format_marked_output(items)

        # Should contain section headers
        assert "### 高优先级 (HIGH)" in result
        assert "### 中优先级 (MEDIUM)" in result
        assert "### 低优先级 (LOW)" in result

        # Should contain items
        assert "[file] (explorer) high1" in result
        assert "[issue] (reviewer) medium1" in result
        assert "[info] (tester) low1" in result

    def test_format_only_shows_existing_priorities(self):
        """Test that only non-empty priority sections are shown."""
        items = [
            mark("high1", Importance.HIGH, "file", "explorer"),
            mark("high2", Importance.HIGH, "file", "explorer"),
        ]

        result = format_marked_output(items)

        # Should only show HIGH section
        assert "### 高优先级 (HIGH)" in result
        assert "### 中优先级 (MEDIUM)" not in result
        assert "### 低优先级 (LOW)" not in result

    def test_format_includes_category_and_source(self):
        """Test that formatted output includes category and source."""
        items = [
            mark("content", Importance.HIGH, "decision", "architect"),
        ]

        result = format_marked_output(items)

        assert "[decision]" in result
        assert "(architect)" in result
        assert "content" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
