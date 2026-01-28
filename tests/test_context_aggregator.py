#!/usr/bin/env python3
"""
Tests for nexus-dist/context/aggregator.py
Tests the result aggregation system.
"""

import sys
from pathlib import Path

# Add nexus-dist/context to path
sys.path.insert(0, str(Path(__file__).parent.parent / "nexus-dist" / "context"))

import pytest
from aggregator import TaskResult, ResultAggregator
from importance import Importance, mark


class TestTaskResult:
    """Test TaskResult dataclass."""

    def test_create_task_result(self):
        """Test creating a TaskResult."""
        result = TaskResult(
            task_id="task-001",
            avatar="explorer",
            status="completed",
            output="Exploration completed",
            marked_items=[
                mark("file1.py", Importance.HIGH, "file", "explorer"),
            ],
            metadata={"duration": "5s"},
        )

        assert result.task_id == "task-001"
        assert result.avatar == "explorer"
        assert result.status == "completed"
        assert result.output == "Exploration completed"
        assert len(result.marked_items) == 1
        assert result.metadata == {"duration": "5s"}

    def test_task_result_defaults(self):
        """Test TaskResult with default values."""
        result = TaskResult(
            task_id="task-001",
            avatar="explorer",
            status="completed",
            output="test",
        )

        assert result.marked_items == []
        assert result.metadata == {}


class TestResultAggregator:
    """Test ResultAggregator class."""

    def test_init(self):
        """Test creating a ResultAggregator."""
        aggregator = ResultAggregator()
        assert aggregator.results == []

    def test_add_result(self):
        """Test adding a result."""
        aggregator = ResultAggregator()
        result = TaskResult(
            task_id="task-001",
            avatar="explorer",
            status="completed",
            output="test",
        )

        aggregator.add_result(result)
        assert len(aggregator.results) == 1
        assert aggregator.results[0] == result

    def test_add_multiple_results(self):
        """Test adding multiple results."""
        aggregator = ResultAggregator()

        for i in range(3):
            result = TaskResult(
                task_id=f"task-{i}",
                avatar="explorer",
                status="completed",
                output=f"output {i}",
            )
            aggregator.add_result(result)

        assert len(aggregator.results) == 3

    def test_aggregate_empty(self):
        """Test aggregating with no results."""
        aggregator = ResultAggregator()
        output = aggregator.aggregate()
        assert output == "无任务结果"

    def test_aggregate_basic(self):
        """Test basic aggregation."""
        aggregator = ResultAggregator()
        aggregator.add_result(
            TaskResult(
                task_id="task-001",
                avatar="explorer",
                status="completed",
                output="test",
                marked_items=[
                    mark("item1", Importance.HIGH, "file", "explorer"),
                ],
            )
        )

        output = aggregator.aggregate(max_chars=2000)

        # Should contain status summary
        assert "## 聚合结果 (1 个任务)" in output
        assert "1 完成" in output

        # Should contain marked items
        assert "item1" in output

    def test_aggregate_multiple_tasks(self):
        """Test aggregating multiple task results."""
        aggregator = ResultAggregator()

        # Add explorer result
        aggregator.add_result(
            TaskResult(
                task_id="explorer-1",
                avatar="explorer",
                status="completed",
                output="Explored files",
                marked_items=[
                    mark("file1.py", Importance.HIGH, "file", "explorer"),
                    mark("file2.py", Importance.MEDIUM, "file", "explorer"),
                ],
            )
        )

        # Add reviewer result
        aggregator.add_result(
            TaskResult(
                task_id="reviewer-1",
                avatar="reviewer",
                status="completed",
                output="Review done",
                marked_items=[
                    mark("Found bug", Importance.HIGH, "issue", "reviewer"),
                ],
            )
        )

        output = aggregator.aggregate(max_chars=2000)

        # Should show 2 tasks
        assert "2 个任务" in output
        assert "2 完成" in output

        # Should contain items from both
        assert "file1.py" in output or "Found bug" in output

    def test_aggregate_respects_max_chars(self):
        """Test that aggregation respects max_chars."""
        aggregator = ResultAggregator()

        # Add lots of items
        items = [
            mark(f"item {i}" + "x" * 100, Importance.HIGH, "file", "test")
            for i in range(10)
        ]

        aggregator.add_result(
            TaskResult(
                task_id="task-001",
                avatar="test",
                status="completed",
                output="test",
                marked_items=items,
            )
        )

        output = aggregator.aggregate(max_chars=500)

        # Output should be close to max_chars (allowing for header overhead and truncation suffix)
        # Header overhead: ~50 chars for "## 聚合结果 (X 个任务)\n\n状态: X 完成, X 失败\n\n"
        # Truncation suffix: ~10 chars for "\n...(已截断)"
        HEADER_OVERHEAD = 60
        assert len(output) <= 500 + HEADER_OVERHEAD

    def test_aggregate_shows_failed_tasks(self):
        """Test that failed tasks are counted."""
        aggregator = ResultAggregator()

        aggregator.add_result(
            TaskResult(
                task_id="task-001",
                avatar="test",
                status="completed",
                output="ok",
            )
        )

        aggregator.add_result(
            TaskResult(
                task_id="task-002",
                avatar="test",
                status="failed",
                output="error",
            )
        )

        output = aggregator.aggregate()

        assert "1 完成, 1 失败" in output

    def test_get_compact_summary_empty(self):
        """Test compact summary with no results."""
        aggregator = ResultAggregator()
        output = aggregator.get_compact_summary()
        assert output == "无任务结果"

    def test_get_compact_summary_basic(self):
        """Test basic compact summary."""
        aggregator = ResultAggregator()
        aggregator.add_result(
            TaskResult(
                task_id="task-001",
                avatar="explorer",
                status="completed",
                output="test",
                marked_items=[
                    mark("high item", Importance.HIGH, "file", "explorer"),
                    mark("low item", Importance.LOW, "file", "explorer"),
                ],
            )
        )

        output = aggregator.get_compact_summary(max_chars=500)

        # Should only show HIGH items
        assert "high item" in output
        assert "low item" not in output

    def test_get_compact_summary_respects_max_chars(self):
        """Test that compact summary respects max_chars."""
        aggregator = ResultAggregator()

        items = [
            mark(f"high {i}" + "x" * 100, Importance.HIGH, "file", "test")
            for i in range(10)
        ]

        aggregator.add_result(
            TaskResult(
                task_id="task-001",
                avatar="test",
                status="completed",
                output="test",
                marked_items=items,
            )
        )

        output = aggregator.get_compact_summary(max_chars=200)
        assert len(output) <= 200

    def test_get_high_importance_only(self):
        """Test getting only HIGH importance items."""
        aggregator = ResultAggregator()

        aggregator.add_result(
            TaskResult(
                task_id="task-001",
                avatar="test",
                status="completed",
                output="test",
                marked_items=[
                    mark("high1", Importance.HIGH, "file", "test"),
                    mark("medium1", Importance.MEDIUM, "file", "test"),
                    mark("high2", Importance.HIGH, "file", "test"),
                    mark("low1", Importance.LOW, "file", "test"),
                ],
            )
        )

        high_items = aggregator.get_high_importance_only()

        # Should only return HIGH items
        assert len(high_items) == 2
        assert all(item.importance == Importance.HIGH for item in high_items)
        assert high_items[0].content == "high1"
        assert high_items[1].content == "high2"

    def test_get_high_importance_from_multiple_tasks(self):
        """Test getting HIGH items from multiple tasks."""
        aggregator = ResultAggregator()

        aggregator.add_result(
            TaskResult(
                task_id="task-001",
                avatar="explorer",
                status="completed",
                output="test",
                marked_items=[
                    mark("explorer-high", Importance.HIGH, "file", "explorer"),
                    mark("explorer-low", Importance.LOW, "file", "explorer"),
                ],
            )
        )

        aggregator.add_result(
            TaskResult(
                task_id="task-002",
                avatar="reviewer",
                status="completed",
                output="test",
                marked_items=[
                    mark("reviewer-high", Importance.HIGH, "issue", "reviewer"),
                ],
            )
        )

        high_items = aggregator.get_high_importance_only()

        assert len(high_items) == 2
        assert "explorer-high" in [item.content for item in high_items]
        assert "reviewer-high" in [item.content for item in high_items]

    def test_clear(self):
        """Test clearing all results."""
        aggregator = ResultAggregator()

        aggregator.add_result(
            TaskResult(
                task_id="task-001",
                avatar="test",
                status="completed",
                output="test",
            )
        )

        assert len(aggregator.results) == 1

        aggregator.clear()
        assert len(aggregator.results) == 0

    def test_aggregate_truncates_if_over_limit(self):
        """Test that aggregate truncates output if over max_chars."""
        aggregator = ResultAggregator()

        # Create very long items
        items = [
            mark("x" * 1000, Importance.HIGH, "file", "test")
            for _ in range(10)
        ]

        aggregator.add_result(
            TaskResult(
                task_id="task-001",
                avatar="test",
                status="completed",
                output="test",
                marked_items=items,
            )
        )

        output = aggregator.aggregate(max_chars=100)

        # Should be truncated (allowing for truncation suffix overhead: "\n...(已截断)" = ~10 chars)
        TRUNCATION_SUFFIX_OVERHEAD = 15
        assert len(output) <= 100 + TRUNCATION_SUFFIX_OVERHEAD
        assert output.endswith("(已截断)")


    def test_init_with_custom_defaults(self):
        """Test creating ResultAggregator with custom default limits."""
        aggregator = ResultAggregator(
            default_max_chars=1000,
            default_compact_max_chars=200,
        )
        assert aggregator._default_max_chars == 1000
        assert aggregator._default_compact_max_chars == 200

    def test_aggregate_uses_default_max_chars(self):
        """Test that aggregate uses default max_chars when not specified."""
        aggregator = ResultAggregator(default_max_chars=100)

        # Create long items
        items = [
            mark("x" * 500, Importance.HIGH, "file", "test")
        ]

        aggregator.add_result(
            TaskResult(
                task_id="task-001",
                avatar="test",
                status="completed",
                output="test",
                marked_items=items,
            )
        )

        # Call aggregate without max_chars - should use default
        output = aggregator.aggregate()

        # Should be truncated based on default (100)
        TRUNCATION_SUFFIX_OVERHEAD = 15
        assert len(output) <= 100 + TRUNCATION_SUFFIX_OVERHEAD

    def test_aggregate_override_default(self):
        """Test that max_chars parameter overrides default."""
        aggregator = ResultAggregator(default_max_chars=50)

        items = [
            mark("short", Importance.HIGH, "file", "test")
        ]

        aggregator.add_result(
            TaskResult(
                task_id="task-001",
                avatar="test",
                status="completed",
                output="test",
                marked_items=items,
            )
        )

        # Override with larger limit
        output = aggregator.aggregate(max_chars=2000)

        # Should not be truncated
        assert "short" in output
        assert "(已截断)" not in output

    def test_compact_summary_uses_default_max_chars(self):
        """Test that get_compact_summary uses default max_chars when not specified."""
        aggregator = ResultAggregator(default_compact_max_chars=50)

        items = [
            mark("x" * 200, Importance.HIGH, "file", "test")
        ]

        aggregator.add_result(
            TaskResult(
                task_id="task-001",
                avatar="test",
                status="completed",
                output="test",
                marked_items=items,
            )
        )

        # Call without max_chars - should use default compact limit
        output = aggregator.get_compact_summary()

        # Should be truncated based on default (50)
        assert len(output) <= 50 + 5  # Allow small overhead for "..."

    def test_backward_compatibility(self):
        """Test that default behavior is preserved (backward compatible)."""
        # Create aggregator with no arguments (old behavior)
        aggregator = ResultAggregator()

        # Should have original defaults
        assert aggregator._default_max_chars == 2000
        assert aggregator._default_compact_max_chars == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
