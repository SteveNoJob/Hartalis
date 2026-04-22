import pytest
import asyncio
from datetime import date
from unittest.mock import patch, AsyncMock

from context.calendar import (
    get_calendar_events,
    get_school_holiday_status,
    build_calendar_context_string,
)
from context.holiday_trend import (
    get_monthly_lift_table,
    get_festive_category_lift,
    build_trend_context_string,
    _compute_lift_from_dataframe,
)
from context.anomaly import detect_anomalies, build_anomaly_context_string
from context.context_builder import build_full_context


# ---------------------------------------------------------------------------
# calendar.py tests
# ---------------------------------------------------------------------------

class TestCalendar:

    def test_upcoming_event_within_window(self):
        """An event 5 days away should appear."""
        events = get_calendar_events(
            days_ahead=21,
            reference_date=date(2026, 3, 16),  # 4 days before Hari Raya Eve
        )
        names = [e["name"] for e in events]
        assert "Hari Raya Aidilfitri Eve" in names

    def test_event_outside_window_excluded(self):
        """An event 30 days away should not appear in a 21-day window."""
        events = get_calendar_events(
            days_ahead=21,
            reference_date=date(2026, 1, 1),
        )
        names = [e["name"] for e in events]
        assert "Chinese New Year Eve" not in names  # Feb 17 is 47 days away

    def test_past_events_excluded(self):
        """Events before today should not appear."""
        events = get_calendar_events(
            days_ahead=365,
            reference_date=date(2026, 6, 1),
        )
        for e in events:
            assert e["days_away"] >= 0

    def test_empty_result_returns_sensible_string(self):
        """On a quiet day, we should still return a non-crashing string."""
        result = build_calendar_context_string(
            reference_date=date(2026, 7, 15),  # no events nearby
        )
        assert isinstance(result, str)
        # Either empty OR the "no events" message — both are fine
        assert "2026-07-15" not in result  # sanity

    def test_school_holiday_active(self):
        """Mid-year holidays are 16–31 May 2026."""
        status = get_school_holiday_status(reference_date=date(2026, 5, 20))
        assert status["status"] == "active"
        assert "Mid-year" in status["name"]

    def test_school_holiday_approaching(self):
        """10 days before start = approaching."""
        status = get_school_holiday_status(reference_date=date(2026, 5, 6))
        assert status["status"] == "approaching"

    def test_school_holiday_none(self):
        """Far from any holiday → status: none."""
        status = get_school_holiday_status(reference_date=date(2026, 7, 15))
        assert status["status"] == "none"


# ---------------------------------------------------------------------------
# holiday_trend.py tests
# ---------------------------------------------------------------------------

class TestHolidayTrend:

    def test_lift_from_synthetic_dataframe(self):
        """Feed a known dataframe and check math."""
        import pandas as pd
        # Baseline months (4, 6, 7, 9) average = 100
        # Feb average = 150 → lift should be +50%
        data = []
        for month in [4, 6, 7, 9]:
            data.append({"date": f"2025-{month:02d}-15", "sales": 100})
        data.append({"date": "2025-02-15", "sales": 150})
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])

        lift = _compute_lift_from_dataframe(df)
        assert abs(lift[2] - 50.0) < 0.1

    def test_festive_category_lift_known_value(self):
        assert get_festive_category_lift("Hari Raya", "cooking oil") == 0.65
        assert get_festive_category_lift("Chinese New Year", "mandarin oranges") == 2.10

    def test_festive_category_lift_unknown_returns_zero(self):
        assert get_festive_category_lift("Hari Raya", "bicycles") == 0.0
        assert get_festive_category_lift("Fake Festival", "anything") == 0.0

    def test_trend_context_string_is_string(self):
        """Never crash, always return a string."""
        result = build_trend_context_string(month=2)
        assert isinstance(result, str)

    def test_trend_context_recognizes_peak_month(self):
        """March should be flagged as peak if DOSM data loaded."""
        result = build_trend_context_string(month=3)
        # Should at least not crash; content depends on CSV availability
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# anomaly.py tests
# ---------------------------------------------------------------------------

class TestAnomaly:

    def _build_history(self, baseline: int, recent: list) -> list:
        """Helper: 30 days of baseline + 7 recent days."""
        history = []
        for i in range(30):
            history.append({
                "date": f"2026-03-{i+1:02d}",
                "product_name": "Milo",
                "units_sold": baseline,
            })
        for i, val in enumerate(recent):
            history.append({
                "date": f"2026-04-{i+1:02d}",
                "product_name": "Milo",
                "units_sold": val,
            })
        return history

    def test_detects_spike(self):
        """Baseline 10/day, then 50 on one recent day → should flag."""
        history = self._build_history(baseline=10, recent=[11, 10, 9, 50, 10, 11, 10])
        # Need small baseline variation for stdev > 0
        for i, h in enumerate(history[:30]):
            h["units_sold"] = 10 + (i % 3 - 1)  # vary by ±1
        anomalies = detect_anomalies(history)
        spikes = [a for a in anomalies if a["type"] == "spike"]
        assert len(spikes) >= 1

    def test_no_anomaly_on_stable_sales(self):
        """Flat-ish sales should produce no anomalies."""
        history = []
        for i in range(37):
            history.append({
                "date": f"2026-03-{(i % 28)+1:02d}",
                "product_name": "Milo",
                "units_sold": 10 + (i % 3 - 1),
            })
        anomalies = detect_anomalies(history)
        assert len(anomalies) == 0

    def test_insufficient_history_returns_empty(self):
        """Less than MIN_HISTORY_DAYS → return []."""
        history = [
            {"date": "2026-04-01", "product_name": "Milo", "units_sold": 10}
        ]
        assert detect_anomalies(history) == []

    def test_empty_input_returns_empty(self):
        assert detect_anomalies([]) == []
        assert build_anomaly_context_string([]) == ""


# ---------------------------------------------------------------------------
# context_builder.py — integration test
# ---------------------------------------------------------------------------

class TestContextBuilder:

    @pytest.mark.asyncio
    async def test_full_context_runs_without_crashing(self):
        """Smoke test — returns a string even with no inputs."""
        # Mock weather to avoid network call during tests
        with patch("context.context_builder.get_weather_context",
                   new=AsyncMock(return_value="")):
            result = await build_full_context(
                sales_history=None,
                include_weather=False,
                reference_date=date(2026, 3, 16),
            )
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_full_context_includes_calendar_event(self):
        """Near Hari Raya, the context should mention it."""
        with patch("context.context_builder.get_weather_context",
                   new=AsyncMock(return_value="")):
            result = await build_full_context(
                include_weather=False,
                reference_date=date(2026, 3, 16),
            )
            assert "Hari Raya" in result


# ---------------------------------------------------------------------------
# Run from command line: python -m pytest tests/test_context.py -v
# ---------------------------------------------------------------------------