# context/calendar.py
"""
Malaysian retail calendar context for the forecaster.

Combines:
  1. Public holiday DATES from the `holidays` library (auto-updates for any year)
  2. Retail IMPACT metadata (impact level, affected products, notes) — local lookup

This hybrid approach means we don't maintain a hardcoded list of dates
(which goes stale every year), but we keep the retail-specific intelligence
that no external API would give us.
"""

from datetime import date, timedelta
from typing import Optional

try:
    import holidays
    HOLIDAYS_AVAILABLE = True
except ImportError:
    HOLIDAYS_AVAILABLE = False


# --------------------------------------------------------------------------
# Retail impact metadata — local lookup table keyed by holiday NAME.
# The `holidays` library gives us dates; we attach retail intelligence here.
# --------------------------------------------------------------------------

EVENT_IMPACT = {
    # Major festivals
    "Chinese New Year":           ("very_high", ["snacks", "beverages", "cooking essentials", "cookies", "mandarin oranges"],
                                    "Biggest CNY shopping day, stock up 1-2 weeks before"),
    "Chinese New Year (Second Day)": ("high", ["snacks", "beverages"], "Most shops closed, pre-holiday sales already peaked"),
    "Hari Raya Puasa":            ("very_high", ["cooking essentials", "sugar", "flour", "cooking oil", "biscuits", "beverages"],
                                    "Peak demand 1-2 weeks before, stock up early"),
    "Hari Raya Puasa (Second Day)": ("very_high", ["cooking essentials"], "Visiting season continues"),
    "Hari Raya Haji":             ("medium", ["cooking essentials", "meat"], "Qurban season — meat and cooking supplies spike"),
    "Deepavali":                  ("high", ["sweets", "snacks", "beverages", "cooking essentials"], "Major Hindu festival — significant retail spike"),
    "Thaipusam":                  ("medium", ["snacks", "beverages", "cooking essentials", "cookies"],
                                    "Hindu festival, affects areas with large Indian community"),
    "Wesak Day":                  ("low", ["snacks", "beverages", "fruits"], ""),
    "Christmas Day":              ("low", ["beverages", "snacks", "party supplies"], ""),

    # Civic / national
    "New Year's Day":             ("low", ["party supplies", "beverages"], ""),
    "Labour Day":                 ("low", ["beverages", "snacks"], ""),
    "Agong's Birthday":           ("low", ["beverages", "snacks"], ""),
    "Birthday of SPB Yang di-Pertuan Agong": ("low", ["beverages", "snacks"], ""),
    "Merdeka Day":                ("medium", ["beverages", "snacks", "party supplies"], "National Day — gatherings increase household spending"),
    "Malaysia Day":               ("low", ["beverages", "snacks"], ""),
    "Nuzul Al-Quran":             ("medium", ["dates", "beverages", "snacks", "cooking essentials"], "During Ramadan — iftar shopping increases"),
    "Awal Muharram":              ("low", ["beverages", "snacks"], "Islamic new year"),
    "Maulidur Rasul":             ("low", ["beverages", "snacks"], ""),
    "Prophet Muhammad's Birthday": ("low", ["beverages", "snacks"], ""),
}

IMPACT_DESCRIPTIONS = {
    "very_high": "40-60% increase expected",
    "high":      "20-40% increase expected",
    "medium":    "10-20% increase expected",
    "low":       "5-10% increase expected",
}

DEFAULT_IMPACT = ("low", ["beverages", "snacks"], "")


# --------------------------------------------------------------------------
# School holidays — these don't change yearly in a predictable pattern,
# so we still hardcode but extend every year.
# --------------------------------------------------------------------------

SCHOOL_HOLIDAYS = [
    # 2026
    ("2026-01-01", "2026-01-04", "New Year break"),
    ("2026-03-14", "2026-03-22", "Mid-term break 1"),
    ("2026-05-16", "2026-05-31", "Mid-year holidays"),
    ("2026-08-22", "2026-08-30", "Mid-term break 2"),
    ("2026-11-14", "2027-01-03", "Year-end holidays"),
    # 2027 — extend annually when MOE publishes the calendar
]


# --------------------------------------------------------------------------
# Public API — same signatures as before, so context_builder.py doesn't change
# --------------------------------------------------------------------------

def _get_malaysia_holidays(year: int) -> dict:
    """Return {date: name} for Malaysia public holidays in given year."""
    if not HOLIDAYS_AVAILABLE:
        return {}
    try:
        # subdiv can be a state code ('KUL', 'SGR', etc.) for state-specific holidays.
        # Leaving it off gives national holidays only — usually what we want.
        my_holidays = holidays.Malaysia(years=[year])
        return dict(my_holidays)
    except Exception:
        return {}


def get_calendar_events(days_ahead: int = 21, reference_date: Optional[date] = None) -> list:
    """Return upcoming Malaysian public holidays with retail impact metadata."""
    today = reference_date or date.today()
    end = today + timedelta(days=days_ahead)

    # Fetch holidays for this year and next (in case window crosses year-end)
    all_holidays = {}
    for year in {today.year, end.year}:
        all_holidays.update(_get_malaysia_holidays(year))

    upcoming = []
    for event_date, name in all_holidays.items():
        days_away = (event_date - today).days
        if 0 <= days_away <= days_ahead:
            # Try exact name match first, then partial match, then default
            impact_data = EVENT_IMPACT.get(name)
            if impact_data is None:
                # Try partial match for name variants
                for key in EVENT_IMPACT:
                    if key.lower() in name.lower() or name.lower() in key.lower():
                        impact_data = EVENT_IMPACT[key]
                        break
            if impact_data is None:
                impact_data = DEFAULT_IMPACT

            impact, categories, notes = impact_data
            upcoming.append({
                "name": name,
                "date": event_date.isoformat(),
                "days_away": days_away,
                "impact": impact,
                "impact_description": IMPACT_DESCRIPTIONS[impact],
                "affected_categories": categories,
                "notes": notes,
            })

    return sorted(upcoming, key=lambda x: x["days_away"])


def get_school_holiday_status(reference_date: Optional[date] = None) -> dict:
    """Check if we're in or approaching a school holiday."""
    today = reference_date or date.today()

    for start_str, end_str, name in SCHOOL_HOLIDAYS:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
        days_to_start = (start - today).days

        if start <= today <= end:
            return {"status": "active", "name": name, "ends_in_days": (end - today).days}
        if 0 < days_to_start <= 14:
            return {"status": "approaching", "name": name, "starts_in_days": days_to_start}

    return {"status": "none"}


def build_calendar_context_string(days_ahead: int = 21, reference_date: Optional[date] = None) -> str:
    """Main entry point — returns plain English string for GLM injection."""
    try:
        events = get_calendar_events(days_ahead, reference_date)
        school = get_school_holiday_status(reference_date)
        lines = []

        if not events and school["status"] == "none":
            return "No major Malaysian public holidays or school holidays in the next 3 weeks."

        if events:
            lines.append("UPCOMING EVENTS AFFECTING RETAIL DEMAND:")
            for e in events:
                impact_desc = IMPACT_DESCRIPTIONS.get(e["impact"], "some impact expected")
                categories = ", ".join(c for c in e["affected_categories"] if c)
                line = f"- {e['name']} in {e['days_away']} days ({e['date']}): {impact_desc}"
                if categories:
                    line += f" — affected products: {categories}"
                if e["notes"]:
                    line += f". {e['notes']}"
                lines.append(line)

        if school["status"] == "active":
            lines.append(
                f"\nSCHOOL HOLIDAY STATUS: Currently school holidays ({school['name']}), "
                f"ends in {school['ends_in_days']} days. "
                f"Expect higher daytime foot traffic and increased snack/beverage demand."
            )
        elif school["status"] == "approaching":
            lines.append(
                f"\nSCHOOL HOLIDAY STATUS: School holidays ({school['name']}) begin in "
                f"{school['starts_in_days']} days. "
                f"Anticipate pre-holiday shopping spike for stationery, snacks, and beverages."
            )

        return "\n".join(lines)

    except Exception:
        return ""