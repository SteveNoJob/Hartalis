# context/limits.py
"""
Input size limits and truncation policy for the context pipeline.

Why this module exists:
  PRD §4.3.3 requires us to document max input size, truncation behavior,
  and what happens when inputs exceed limits. This module is the single
  source of truth for those rules.

Design decisions:
  - We measure size in characters, not tokens. ~4 chars ≈ 1 GLM token
    for English; ~3 chars ≈ 1 token for Bahasa Melayu. Character count
    is fast, dependency-free, and deterministic.
  - Hard cap: 8000 chars (~2000 tokens) for the full context string.
    This leaves room for system prompt + user data + GLM response
    within a reasonable 7-10K token call budget.
  - When oversized, we drop sections by priority, not by chopping the
    string at a character boundary (which would produce garbled output).
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Size policy — edit these to tune the budget
# ---------------------------------------------------------------------------

MAX_CONTEXT_CHARS = 8000            # Hard cap on full assembled context string
MAX_SECTION_CHARS = 2500            # Hard cap on any single section
MAX_ANOMALIES_SHOWN = 5             # Truncate anomaly list to top-N
MAX_SALES_HISTORY_ROWS = 180        # Reject sales history longer than this
                                    # 180 rows ≈ 6 months daily data — plenty
                                    # for anomaly detection, keeps parsing fast

# Approximate tokens-per-char ratio. Useful for logging / cost estimation.
# Slightly conservative (assumes shorter, more token-dense words).
CHARS_PER_TOKEN = 4.0

# Section priority — LOWER number = higher priority = kept longer.
# When we need to trim, sections with HIGHER numbers are dropped first.
SECTION_PRIORITY = {
    "scenario":     0,   # user-initiated what-if — never drop
    "calendar":     1,   # core signal, usually small
    "ramadan":      2,   # critical during Ramadan, small footprint
    "anomaly":      3,   # keep but can truncate to top-N
    "trend":        4,   # often redundant with calendar
    "weather":      5,   # useful but expendable
}


# ---------------------------------------------------------------------------
# Section container
# ---------------------------------------------------------------------------

@dataclass
class ContextSection:
    """One named section of the full context string."""
    name: str                     # e.g., "calendar", "weather" — must be in SECTION_PRIORITY
    content: str = ""
    truncated: bool = False       # True if we shortened this section's content

    @property
    def priority(self) -> int:
        return SECTION_PRIORITY.get(self.name, 99)

    @property
    def size(self) -> int:
        return len(self.content)


@dataclass
class TruncationReport:
    """Tells caller (and downstream GLM) what we cut. Used for PRD §4.3.4."""
    original_size: int = 0
    final_size: int = 0
    dropped_sections: List[str] = field(default_factory=list)
    truncated_sections: List[str] = field(default_factory=list)

    @property
    def anything_cut(self) -> bool:
        return bool(self.dropped_sections or self.truncated_sections)

    def to_glm_note(self) -> str:
        """
        Short note we append to the context so GLM knows it got a
        truncated view. Meets PRD §4.3.4 (transparency in failure state).
        """
        if not self.anything_cut:
            return ""
        parts = []
        if self.dropped_sections:
            parts.append(f"dropped: {', '.join(self.dropped_sections)}")
        if self.truncated_sections:
            parts.append(f"truncated: {', '.join(self.truncated_sections)}")
        return (
            f"[CONTEXT NOTE: Input exceeded {MAX_CONTEXT_CHARS} chars; "
            f"{'; '.join(parts)}. Reasoning may be less complete than usual.]"
        )


# ---------------------------------------------------------------------------
# Core enforcement
# ---------------------------------------------------------------------------

def enforce_section_limit(content: str, max_chars: int = MAX_SECTION_CHARS) -> Tuple[str, bool]:
    """
    Enforce per-section cap. If content exceeds max_chars, truncate at a
    clean boundary (newline or sentence) and append an ellipsis marker.

    Returns (possibly-shortened content, was_truncated_bool).
    """
    if len(content) <= max_chars:
        return content, False

    # Prefer cutting at a newline boundary near the limit, not mid-sentence
    cut_at = content.rfind("\n", 0, max_chars)
    if cut_at < max_chars * 0.7:  # no good newline — try sentence end
        cut_at = content.rfind(". ", 0, max_chars)
    if cut_at < max_chars * 0.7:  # still nothing — hard cut
        cut_at = max_chars

    return content[:cut_at].rstrip() + " …[truncated]", True


def validate_sales_history(sales_history: list) -> Tuple[list, Optional[str]]:
    """
    Reject or trim oversized sales history BEFORE it hits anomaly detection.

    Returns (possibly-trimmed history, warning_message_or_None).
    """
    if not sales_history:
        return [], None

    if not isinstance(sales_history, list):
        return [], f"sales_history must be a list, got {type(sales_history).__name__}"

    if len(sales_history) > MAX_SALES_HISTORY_ROWS:
        # Keep the most recent rows — they matter most for anomaly detection
        trimmed = sales_history[-MAX_SALES_HISTORY_ROWS:]
        warning = (
            f"sales_history had {len(sales_history)} rows; "
            f"trimmed to most recent {MAX_SALES_HISTORY_ROWS}"
        )
        return trimmed, warning

    return sales_history, None


def assemble_within_budget(
    sections: List[ContextSection],
    max_chars: int = MAX_CONTEXT_CHARS,
) -> Tuple[str, TruncationReport]:
    """
    Main function the context_builder calls.

    Joins sections into one string under max_chars, dropping lowest-priority
    sections first if the budget is exceeded. Per-section truncation has
    already happened before this (via enforce_section_limit).

    Returns (final_context_string, TruncationReport).
    """
    # Filter out empty sections immediately
    active = [s for s in sections if s.content.strip()]
    report = TruncationReport(
        original_size=sum(s.size for s in active),
    )
    report.truncated_sections = [s.name for s in active if s.truncated]

    # Sort by priority — we keep lower priority-numbers, drop higher
    active.sort(key=lambda s: s.priority)

    # Greedy assembly: add sections in priority order until budget is gone
    kept: List[ContextSection] = []
    running_size = 0
    separator_size = len("\n\n")  # gap between sections

    for section in active:
        needed = section.size + (separator_size if kept else 0)
        if running_size + needed <= max_chars:
            kept.append(section)
            running_size += needed
        else:
            # Can't fit — mark as dropped
            report.dropped_sections.append(section.name)

    # Build final string
    parts = [s.content for s in kept]

    # If we dropped anything, append a transparency note for GLM
    if report.dropped_sections:
        note = report.to_glm_note()
        # Only add the note if there's room — otherwise it defeats the purpose
        if running_size + len(note) + separator_size <= max_chars:
            parts.append(note)

    final = "\n\n".join(parts)
    report.final_size = len(final)
    return final, report


def estimate_tokens(text: str) -> int:
    """Rough token-count estimator for cost logging / PRD §8."""
    return int(len(text) / CHARS_PER_TOKEN)