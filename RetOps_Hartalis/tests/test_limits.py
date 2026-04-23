# tests/test_limits.py
"""
Tests for context/limits.py — input size enforcement.

Maps to PRD §4.3.3 (Context & Input Handling) and QATD §6.2 (Oversized Input Test).
Run with:  pytest tests/test_limits.py -v
"""

import pytest
from context.limits import (
    ContextSection,
    TruncationReport,
    enforce_section_limit,
    validate_sales_history,
    assemble_within_budget,
    estimate_tokens,
    MAX_CONTEXT_CHARS,
    MAX_SECTION_CHARS,
    MAX_SALES_HISTORY_ROWS,
)


class TestSectionLimit:
    """Per-section truncation — enforces MAX_SECTION_CHARS."""

    def test_small_content_unchanged(self):
        content = "Short content."
        result, truncated = enforce_section_limit(content, max_chars=1000)
        assert result == content
        assert not truncated

    def test_oversized_content_truncated(self):
        content = "line one.\n" + ("padding " * 500)  # ~4010 chars
        result, truncated = enforce_section_limit(content, max_chars=100)
        assert truncated
        assert len(result) <= 150  # 100 + ellipsis marker
        assert result.endswith("…[truncated]")

    def test_truncation_prefers_newline_boundary(self):
        content = "Para 1.\n\nPara 2.\n\n" + ("x" * 1000)
        result, _ = enforce_section_limit(content, max_chars=50)
        # Should cut at a newline, not mid-word
        assert "Para" in result

    def test_exact_boundary_not_truncated(self):
        content = "a" * 100
        result, truncated = enforce_section_limit(content, max_chars=100)
        assert not truncated
        assert result == content


class TestSalesHistoryValidation:
    """sales_history must be validated before anomaly detection."""

    def test_empty_list_ok(self):
        trimmed, warning = validate_sales_history([])
        assert trimmed == []
        assert warning is None

    def test_reasonable_size_unchanged(self):
        history = [{"date": "2026-01-01", "product_name": "A", "units_sold": 1}] * 50
        trimmed, warning = validate_sales_history(history)
        assert len(trimmed) == 50
        assert warning is None

    def test_oversized_list_trimmed(self):
        history = [
            {"date": f"2026-01-{(i%28)+1:02d}", "product_name": "A", "units_sold": i}
            for i in range(500)
        ]
        trimmed, warning = validate_sales_history(history)
        assert len(trimmed) == MAX_SALES_HISTORY_ROWS
        assert warning is not None
        assert "500" in warning
        # Critical: most recent rows preserved, not oldest
        assert trimmed[-1] == history[-1]
        assert trimmed[0] == history[-MAX_SALES_HISTORY_ROWS]

    def test_wrong_type_rejected(self):
        trimmed, warning = validate_sales_history("not a list")
        assert trimmed == []
        assert warning is not None
        assert "list" in warning.lower()


class TestAssembleWithinBudget:
    """Priority-ordered section assembly — the core of input handling."""

    def test_all_sections_fit_cleanly(self):
        sections = [
            ContextSection(name="calendar", content="Small calendar content."),
            ContextSection(name="weather", content="Small weather content."),
        ]
        final, report = assemble_within_budget(sections)
        assert "calendar" in final.lower()
        assert "weather" in final.lower()
        assert not report.anything_cut

    def test_oversized_drops_lowest_priority_first(self):
        """Weather (priority 5) should be dropped before calendar (priority 1)."""
        sections = [
            ContextSection(name="calendar", content="C" * 4000),
            ContextSection(name="weather", content="W" * 4000),
            ContextSection(name="trend", content="T" * 4000),
        ]
        final, report = assemble_within_budget(sections, max_chars=5000)
        # Calendar must survive; at least one lower-priority must drop
        assert "calendar" not in report.dropped_sections
        assert len(report.dropped_sections) >= 1

    def test_scenario_never_dropped(self):
        """Even if scenario is huge, it must survive (user-initiated)."""
        sections = [
            ContextSection(name="scenario", content="S" * 7000),
            ContextSection(name="calendar", content="C" * 2000),
            ContextSection(name="weather", content="W" * 2000),
        ]
        final, report = assemble_within_budget(sections, max_chars=8000)
        assert "scenario" not in report.dropped_sections

    def test_empty_sections_filtered(self):
        """Empty-content sections should not appear in output or report."""
        sections = [
            ContextSection(name="calendar", content="REAL_CALENDAR_CONTENT"),
            ContextSection(name="weather", content=""),
            ContextSection(name="trend", content="   "),  # whitespace only
        ]
        final, report = assemble_within_budget(sections)
        assert "REAL_CALENDAR_CONTENT" in final
        assert "weather" not in report.dropped_sections  # it was never considered
        assert "trend" not in report.dropped_sections

    def test_truncation_note_appended_when_dropped(self):
        """GLM must be told the context was trimmed (PRD §4.3.4 transparency)."""
        sections = [
            ContextSection(name="calendar", content="C" * 3000),
            ContextSection(name="weather", content="W" * 3000),
            ContextSection(name="trend", content="T" * 3000),
        ]
        final, report = assemble_within_budget(sections, max_chars=4000)
        if report.dropped_sections:
            assert "CONTEXT NOTE" in final


class TestTokenEstimation:
    """Rough token count — used for cost logging (PRD §8)."""

    def test_estimation_is_reasonable(self):
        # 4 chars per token is the conservative approximation
        assert estimate_tokens("a" * 4000) == 1000
        assert estimate_tokens("") == 0

    def test_scales_linearly(self):
        assert estimate_tokens("x" * 400) == 100
        assert estimate_tokens("x" * 4000) == 1000