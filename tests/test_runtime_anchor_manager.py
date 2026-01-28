#!/usr/bin/env python3
"""
Tests for runtime/anchor_manager.py
Tests anchor management for cross-session knowledge persistence.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add runtime to path
sys.path.insert(0, str(Path(__file__).parent.parent / "runtime"))

import pytest
from anchor_manager import AnchorManager


class TestAnchorManager:
    """Test AnchorManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp = Path(tempfile.mkdtemp())
        yield temp
        shutil.rmtree(temp)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create an AnchorManager instance."""
        return AnchorManager(temp_dir)

    def test_init_creates_directories(self, temp_dir):
        """Test that initialization creates necessary directories."""
        manager = AnchorManager(temp_dir)

        assert temp_dir.exists()
        assert (temp_dir / "anchors.json").exists()
        assert (temp_dir / "candidates.json").exists()

    def test_add_candidate_basic(self, manager):
        """Test adding a basic candidate anchor."""
        candidate_id = manager.add_candidate({
            "type": "decision",
            "title": "Use JWT for auth",
            "content": "JWT provides stateless authentication",
            "keywords": ["auth", "jwt"],
        })

        assert candidate_id.startswith("cand_")
        assert len(candidate_id) == 17  # "cand_" + 12 hex chars

    def test_add_candidate_requires_type(self, manager):
        """Test that type is required."""
        with pytest.raises(ValueError, match="must have a 'type' field"):
            manager.add_candidate({
                "title": "Test",
                "content": "Test content",
            })

    def test_add_candidate_validates_type(self, manager):
        """Test that type is validated."""
        with pytest.raises(ValueError, match="Invalid anchor type"):
            manager.add_candidate({
                "type": "invalid_type",
                "title": "Test",
                "content": "Test content",
            })

    def test_add_candidate_requires_title(self, manager):
        """Test that title is required."""
        with pytest.raises(ValueError, match="must have a non-empty 'title' field"):
            manager.add_candidate({
                "type": "decision",
                "content": "Test content",
            })

    def test_add_candidate_requires_content(self, manager):
        """Test that content is required."""
        with pytest.raises(ValueError, match="must have a non-empty 'content' field"):
            manager.add_candidate({
                "type": "decision",
                "title": "Test",
            })

    def test_add_candidate_with_source(self, manager):
        """Test adding candidate with source information."""
        candidate_id = manager.add_candidate(
            {
                "type": "decision",
                "title": "Test",
                "content": "Test content",
            },
            source={"graph_id": "graph-123", "node_id": "node-456"},
        )

        candidate = manager.get_candidate(candidate_id)
        assert candidate["source"]["graph_id"] == "graph-123"
        assert candidate["source"]["node_id"] == "node-456"

    def test_promote_anchor(self, manager):
        """Test promoting a candidate to anchor."""
        candidate_id = manager.add_candidate({
            "type": "decision",
            "title": "Use JWT",
            "content": "JWT for auth",
        })

        anchor_id = manager.promote_anchor(candidate_id)

        assert anchor_id.startswith("anc_")
        assert len(anchor_id) == 16  # "anc_" + 12 hex chars

        # Candidate should be removed
        assert manager.get_candidate(candidate_id) is None

        # Anchor should exist
        anchor = manager.get_anchor(anchor_id)
        assert anchor is not None
        assert anchor["title"] == "Use JWT"

    def test_promote_anchor_invalid_candidate(self, manager):
        """Test promoting non-existent candidate."""
        with pytest.raises(ValueError, match="Candidate not found"):
            manager.promote_anchor("cand_nonexistent")

    def test_promote_anchor_to_project(self, manager, temp_dir):
        """Test promoting anchor to project-specific location."""
        candidate_id = manager.add_candidate({
            "type": "decision",
            "title": "Test",
            "content": "Test content",
        })

        anchor_id = manager.promote_anchor(candidate_id, project="nexus")

        # Should create project directory
        project_dir = temp_dir / "nexus"
        assert project_dir.exists()
        assert (project_dir / "anchors.json").exists()

    def test_search_anchors_by_keyword(self, manager):
        """Test searching anchors by keyword."""
        # Add and promote some anchors
        cand1 = manager.add_candidate({
            "type": "decision",
            "title": "Use JWT",
            "content": "JWT for authentication",
            "keywords": ["auth", "jwt", "security"],
        })
        manager.promote_anchor(cand1)

        cand2 = manager.add_candidate({
            "type": "constraint",
            "title": "HTTPS only",
            "content": "All connections must use HTTPS",
            "keywords": ["security", "https"],
        })
        manager.promote_anchor(cand2)

        # Search for "security"
        results = manager.search_anchors(["security"])

        assert len(results) == 2
        titles = [r["title"] for r in results]
        assert "Use JWT" in titles
        assert "HTTPS only" in titles

    def test_search_anchors_relevance_scoring(self, manager):
        """Test that search results are ordered by relevance."""
        # Anchor with keyword match (highest score)
        cand1 = manager.add_candidate({
            "type": "decision",
            "title": "Something else",
            "content": "Other content",
            "keywords": ["auth"],
        })
        manager.promote_anchor(cand1)

        # Anchor with title match (medium score)
        cand2 = manager.add_candidate({
            "type": "decision",
            "title": "Auth system",
            "content": "Other content",
            "keywords": [],
        })
        manager.promote_anchor(cand2)

        # Anchor with content match (low score)
        cand3 = manager.add_candidate({
            "type": "decision",
            "title": "Something",
            "content": "This mentions auth in content",
            "keywords": [],
        })
        manager.promote_anchor(cand3)

        results = manager.search_anchors(["auth"])

        # Should be ordered: keyword > title > content
        assert len(results) == 3
        assert results[0]["title"] == "Something else"  # keyword match
        assert results[1]["title"] == "Auth system"     # title match

    def test_search_anchors_by_type(self, manager):
        """Test filtering search by anchor type."""
        cand1 = manager.add_candidate({
            "type": "decision",
            "title": "Decision about auth",
            "content": "test",
            "keywords": ["auth"],
        })
        manager.promote_anchor(cand1)

        cand2 = manager.add_candidate({
            "type": "constraint",
            "title": "Constraint about auth",
            "content": "test",
            "keywords": ["auth"],
        })
        manager.promote_anchor(cand2)

        # Search only for decisions
        results = manager.search_anchors(["auth"], anchor_type="decision")

        assert len(results) == 1
        assert results[0]["type"] == "decision"

    def test_get_relevant_anchors(self, manager):
        """Test getting anchors relevant to a task description."""
        cand = manager.add_candidate({
            "type": "decision",
            "title": "Use JWT for authentication",
            "content": "JWT provides stateless auth",
            "keywords": ["auth", "jwt"],
        })
        manager.promote_anchor(cand)

        results = manager.get_relevant_anchors(
            "Implement user authentication with JWT tokens",
            max_results=5,
        )

        assert len(results) > 0
        assert any("JWT" in r["title"] for r in results)

    def test_list_candidates(self, manager):
        """Test listing all candidates."""
        manager.add_candidate({
            "type": "decision",
            "title": "Test 1",
            "content": "content 1",
        })
        manager.add_candidate({
            "type": "decision",
            "title": "Test 2",
            "content": "content 2",
        })

        candidates = manager.list_candidates()
        assert len(candidates) == 2

    def test_delete_candidate(self, manager):
        """Test deleting a candidate."""
        cand_id = manager.add_candidate({
            "type": "decision",
            "title": "Test",
            "content": "Test content",
        })

        assert manager.get_candidate(cand_id) is not None

        result = manager.delete_candidate(cand_id)
        assert result is True

        assert manager.get_candidate(cand_id) is None

    def test_delete_candidate_not_found(self, manager):
        """Test deleting non-existent candidate."""
        result = manager.delete_candidate("cand_nonexistent")
        assert result is False

    def test_delete_anchor(self, manager):
        """Test deleting an anchor."""
        cand_id = manager.add_candidate({
            "type": "decision",
            "title": "Test",
            "content": "Test content",
        })
        anchor_id = manager.promote_anchor(cand_id)

        assert manager.get_anchor(anchor_id) is not None

        result = manager.delete_anchor(anchor_id)
        assert result is True

        assert manager.get_anchor(anchor_id) is None

    def test_get_statistics(self, manager):
        """Test getting anchor statistics."""
        # Add some candidates
        manager.add_candidate({
            "type": "decision",
            "title": "Test 1",
            "content": "content",
        })

        # Add and promote some anchors
        cand1 = manager.add_candidate({
            "type": "decision",
            "title": "Test 2",
            "content": "content",
            "evidence_level": "L2",
        })
        manager.promote_anchor(cand1)

        cand2 = manager.add_candidate({
            "type": "constraint",
            "title": "Test 3",
            "content": "content",
            "evidence_level": "L3",
        })
        manager.promote_anchor(cand2)

        stats = manager.get_statistics()

        assert stats["total_anchors"] == 2
        assert stats["total_candidates"] == 1
        assert stats["by_type"]["decision"] == 1
        assert stats["by_type"]["constraint"] == 1
        assert stats["by_level"]["L2"] == 1
        assert stats["by_level"]["L3"] == 1

    def test_export_anchors_md(self, manager):
        """Test exporting anchors to Markdown."""
        cand = manager.add_candidate({
            "type": "decision",
            "title": "Use JWT",
            "content": "JWT provides stateless authentication",
            "keywords": ["auth", "jwt"],
            "evidence_level": "L2",
        })
        manager.promote_anchor(cand)

        md = manager.export_anchors_md()

        # Should contain headers
        assert "# Anchors" in md
        assert "## Architecture Decisions" in md

        # Should contain anchor details
        assert "### Use JWT" in md
        assert "JWT provides stateless authentication" in md
        assert "auth, jwt" in md
        assert "L2" in md


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
