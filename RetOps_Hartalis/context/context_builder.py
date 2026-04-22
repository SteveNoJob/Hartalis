# context/context_builder.py
"""
Orchestrates all context modules into a single, size-bounded string.

Enforces input limits documented in context/limits.py (PRD §4.3.3).
Scenario override is prepended and NEVER dropped (PRD §4.3.4 transparency).
"""

from datetime import date
from typing import List, Dict, Optional
import logging

from context.calendar import build_calendar_context_string
from context.holiday_trend import build_trend_context_string
from context.weather import get_weather_context
from context.anomaly import build_anomaly_context_string
from context.scenario import parse_scenario, build_scenario_context_string
from context.limits import (
    ContextSection,
    enforce_section_limit,
    validate_sales_history,
    assemble_within_budget,
    estimate_tokens,
    MAX_CONTEXT_CHARS,
)

logger = logging.getLogger(__name__)


async def build_full_context(
    sales_history: Optional[List[Dict]] = None,
    user_sales_csv_path: Optional[str] = None,
    store_type: str = "grocery",
    city: str = "Kuala Lumpur",
    include_weather: bool = True,
    reference_date: Optional[date] = None,
    scenario_query: Optional[str] = None,
    return_report: bool = False,
):
    """
    Build the GLM-ready context string with enforced size limits.

    Args:
        sales_history:       Daily sales rows. Trimmed if too long.
        user_sales_csv_path: Path to user's long-term CSV for trend calc.
        store_type:          'grocery' | 'clothing' | 'electronics' | etc.
        city:                Malaysian city for weather.
        include_weather:     False disables the weather API call.
        reference_date:      Override 'today' (for testing).
        scenario_query:      Optional what-if query.
        return_report:       If True, returns (context_str, TruncationReport).
                             Otherwise returns just the context string.

    Never raises — each module fails gracefully.
    """
    today = reference_date or date.today()
    sections: List[ContextSection] = []
    scenario_overrides_weather = False

    # Validate sales_history size up front (PRD §4.3.3 rejection path)
    if sales_history is not None:
        sales_history, warning = validate_sales_history(sales_history)
        if warning:
            logger.warning("build_full_context: %s", warning)

    # 0. Scenario override (prepended; never dropped)
    if scenario_query:
        try:
            override = parse_scenario(scenario_query)
            raw = build_scenario_context_string(override)
            if raw:
                content, truncated = enforce_section_limit(raw)
                sections.append(ContextSection(
                    name="scenario", content=content, truncated=truncated,
                ))
                scenario_overrides_weather = override.force_weather is not None
        except Exception as e:
            logger.exception("scenario parsing failed: %s", e)

    # 1. Calendar (includes Ramadan status)
    try:
        raw = build_calendar_context_string(reference_date=today)
        if raw:
            content, truncated = enforce_section_limit(raw)
            sections.append(ContextSection(
                name="calendar", content=content, truncated=truncated,
            ))
    except Exception as e:
        logger.exception("calendar failed: %s", e)

    # 2. Monthly retail trend
    try:
        raw = build_trend_context_string(
            month=today.month,
            user_csv_path=user_sales_csv_path,
            store_type=store_type,
        )
        if raw:
            content, truncated = enforce_section_limit(raw)
            sections.append(ContextSection(
                name="trend", content=content, truncated=truncated,
            ))
    except Exception as e:
        logger.exception("trend failed: %s", e)

    # 3. Weather (skipped if scenario overrides it)
    if include_weather and not scenario_overrides_weather:
        try:
            raw = await get_weather_context(city)
            if raw:
                content, truncated = enforce_section_limit(raw)
                sections.append(ContextSection(
                    name="weather", content=content, truncated=truncated,
                ))
        except Exception as e:
            logger.exception("weather failed: %s", e)

    # 4. Anomalies
    if sales_history:
        try:
            raw = build_anomaly_context_string(sales_history)
            if raw:
                content, truncated = enforce_section_limit(raw)
                sections.append(ContextSection(
                    name="anomaly", content=content, truncated=truncated,
                ))
        except Exception as e:
            logger.exception("anomaly failed: %s", e)

    # Final assembly with size budget
    final_str, report = assemble_within_budget(sections, MAX_CONTEXT_CHARS)

    logger.info(
        "context assembled: %d chars (~%d tokens), kept=%d, dropped=%s, truncated=%s",
        report.final_size,
        estimate_tokens(final_str),
        len(sections) - len(report.dropped_sections),
        report.dropped_sections or "none",
        report.truncated_sections or "none",
    )

    if return_report:
        return final_str, report
    return final_str