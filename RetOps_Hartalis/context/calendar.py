# context/calendar.py
"""
Malaysian retail/F&B calendar context.

Returns plain-English strings describing upcoming public holidays,
school holidays, and Ramadan status — all factors that shift demand.

Note: MALAYSIAN_EVENTS is hardcoded through 2026. Extend annually or
migrate to the `holidays` Python package for auto-updates.
"""

from datetime import date, timedelta
from typing import Optional


MALAYSIAN_EVENTS = [
    # 2026
    ("2026-01-01", "New Year's Day", "low", ["party supplies", "beverages"], ""),
    ("2026-02-01", "Thaipusam", "medium", ["snacks", "beverages", "cooking essentials", "cookies"], "Hindu festival, affects areas with large Indian community"),
    ("2026-02-02", "Thaipusam Holiday", "low", ["snacks", "beverages"], "Public holiday followup"),
    ("2026-02-17", "Chinese New Year Eve", "very_high", ["snacks", "beverages", "cooking essentials", "cookies", "mandarin oranges"], "Biggest CNY shopping day, stock up 1-2 weeks before"),
    ("2026-02-18", "Chinese New Year Day 1", "high", ["snacks", "beverages"], "Most shops closed, pre-holiday sales already peaked"),
    ("2026-03-07", "Nuzul Al-Quran", "medium", ["dates", "beverages", "snacks", "cooking essentials"], "During Ramadan — iftar shopping increases"),
    ("2026-03-20", "Hari Raya Aidilfitri Eve", "very_high", ["cooking essentials", "sugar", "flour", "cooking oil", "biscuits", "beverages"], "Peak demand 1-2 weeks before, stock up early"),
    ("2026-03-21", "Hari Raya Aidilfitri Day 1", "very_high", ["cooking essentials"], "Most shops closed"),
    ("2026-03-22", "Hari Raya Aidilfitri Day 2", "very_high", ["cooking essentials"], "Visiting season continues"),
    ("2026-03-23", "Hari Raya Aidilfitri Day 3", "high", ["cooking essentials", "beverages"], ""),
    ("2026-03-24", "Hari Raya Aidilfitri Day 4", "medium", ["cooking essentials", "beverages"], ""),
    ("2026-05-01", "Labour Day", "low", ["beverages", "snacks"], ""),
    ("2026-05-27", "Hari Raya Haji", "medium", ["cooking essentials", "meat"], "Qurban season — meat and cooking supplies spike"),
    ("2026-05-31", "Wesak Day", "low", ["snacks", "beverages", "fruits"], ""),
    ("2026-06-01", "Agong's Birthday", "low", ["beverages", "snacks"], ""),
    ("2026-06-02", "Wesak Day Holiday", "low", ["snacks", "beverages"], ""),
    ("2026-06-17", "Awal Muharram", "low", ["beverages", "snacks"], "Islamic new year"),
    ("2026-08-25", "Prophet Muhammad's Birthday", "low", ["beverages", "snacks"], ""),
    ("2026-08-31", "Merdeka Day", "medium", ["beverages", "snacks", "party supplies"], "National Day — gatherings increase household spending"),
    ("2026-09-16", "Malaysia Day", "low", ["beverages", "snacks"], ""),
    ("2026-11-08", "Deepavali", "high", ["sweets", "snacks", "beverages", "cooking essentials"], "Major Hindu festival — significant retail spike"),
    ("2026-11-09", "Deepavali Holiday", "medium", ["snacks", "beverages"], ""),
    ("2026-12-25", "Christmas Day", "low", ["beverages", "snacks", "party supplies"], ""),
]

SCHOOL_HOLIDAYS = [
    ("2026-01-01", "2026-01-04", "New Year break"),
    ("2026-03-14", "2026-03-22", "Mid-term break 1"),
    ("2026-05-16", "2026-05-31", "Mid-year holidays"),
    ("2026-08-22", "2026-08-30", "Mid-term break 2"),
    ("2026-11-14", "2027-01-03", "Year-end holidays"),
]

# Ramadan periods (Gregorian dates). Update annually from JAKIM.
RAMADAN_PERIODS = [
    ("2026-02-18", "2026-03-19"),  # Ramadan 1447H
    ("2027-02-08", "2027-03-09"),  # Ramadan 1448H
    ("2028-01-28", "2028-02-26"),  # Ramadan 1449H
]

IMPACT_DESCRIPTIONS = {
    "very_high": "40-60% increase expected",
    "high":      "20-40% increase expected",
    "medium":    "10-20% increase expected",
    "low":       "5-10% increase expected",
}


# ---------------------------------------------------------------------------
# Public holiday events
# ---------------------------------------------------------------------------

def get_calendar_events(days_ahead: int = 21, reference_date: Optional[date] = None) -> list:
    today = reference_date or date.today()
    upcoming = []

    for event_date_str, name, impact, categories, notes in MALAYSIAN_EVENTS:
        event_date = date.fromisoformat(event_date_str)
        days_away = (event_date - today).days

        if 0 <= days_away <= days_ahead:
            upcoming.append({
                "name": name,
                "date": event_date_str,
                "days_away": days_away,
                "impact": impact,
                "impact_description": IMPACT_DESCRIPTIONS[impact],
                "affected_categories": categories,
                "notes": notes,
            })

    return sorted(upcoming, key=lambda x: x["days_away"])


# ---------------------------------------------------------------------------
# School holidays
# ---------------------------------------------------------------------------

def get_school_holiday_status(reference_date: Optional[date] = None) -> dict:
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


# ---------------------------------------------------------------------------
# Ramadan
# ---------------------------------------------------------------------------

def get_ramadan_status(reference_date: Optional[date] = None) -> dict:
    """
    Returns ramadan status. Phases:
      - early (days 1-10):  iftar shopping peak
      - mid (days 11-20):   bazaar Ramadan in full swing
      - late (days 21-30):  Raya prep overtakes iftar
    """
    today = reference_date or date.today()

    for start_str, end_str in RAMADAN_PERIODS:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
        days_to_start = (start - today).days

        if start <= today <= end:
            day_of = (today - start).days + 1
            if day_of <= 10:
                phase = "early"
            elif day_of <= 20:
                phase = "mid"
            else:
                phase = "late"
            return {
                "status": "active",
                "day_of_ramadan": day_of,
                "days_remaining": (end - today).days,
                "phase": phase,
            }

        if 0 < days_to_start <= 14:
            return {"status": "approaching", "starts_in_days": days_to_start}

    return {"status": "none"}


# ---------------------------------------------------------------------------
# Main context builder
# ---------------------------------------------------------------------------

def build_calendar_context_string(days_ahead: int = 21, reference_date: Optional[date] = None) -> str:
    """Returns plain English string for GLM injection. Never crashes."""
    try:
        events = get_calendar_events(days_ahead, reference_date)
        school = get_school_holiday_status(reference_date)
        ramadan = get_ramadan_status(reference_date)
        lines = []

        if not events and school["status"] == "none" and ramadan["status"] == "none":
            return "No major Malaysian public holidays, school holidays, or Ramadan activity in the next 3 weeks."

        # Public holidays
        if events:
            lines.append("UPCOMING EVENTS AFFECTING DEMAND:")
            for e in events:
                impact_desc = IMPACT_DESCRIPTIONS.get(e["impact"], "some impact expected")
                categories = ", ".join(c for c in e["affected_categories"] if c)
                line = f"- {e['name']} in {e['days_away']} days ({e['date']}): {impact_desc}"
                if categories:
                    line += f" — affected products: {categories}"
                if e["notes"]:
                    line += f". {e['notes']}"
                lines.append(line)

        # Ramadan status (major month-long signal)
        if ramadan["status"] == "active":
            phase_notes = {
                "early": "Iftar demand peaks. Dates, beverages, cooking oil, ready-to-eat iftar items elevated. Daytime F&B traffic drops in Muslim-majority areas; evening (post-7pm) surges heavily.",
                "mid":   "Bazaar Ramadan in full swing. Cooking ingredients, dates, beverages stay elevated. Evening-dominant demand pattern.",
                "late":  "Hari Raya prep overtaking iftar shopping. Biscuits, cookies, cooking essentials, flour, sugar, festive beverages spiking. Final 10 days are peak stock-up period.",
            }
            lines.append(
                f"\nRAMADAN STATUS: Day {ramadan['day_of_ramadan']}/30 ({ramadan['phase']} phase, "
                f"{ramadan['days_remaining']} days to Hari Raya). "
                f"{phase_notes[ramadan['phase']]}"
            )
        elif ramadan["status"] == "approaching":
            lines.append(
                f"\nRAMADAN STATUS: Ramadan begins in {ramadan['starts_in_days']} days. "
                f"Pre-Ramadan stock-up peaks 3-5 days before. Dates, cooking oil, flour, "
                f"sugar, beverages, and instant meal items should be stocked up NOW."
            )

        # School holidays
        if school["status"] == "active":
            lines.append(
                f"\nSCHOOL HOLIDAY STATUS: Currently school holidays ({school['name']}), "
                f"ends in {school['ends_in_days']} days. "
                f"Expect higher daytime foot traffic; increased snack/beverage demand."
            )
        elif school["status"] == "approaching":
            lines.append(
                f"\nSCHOOL HOLIDAY STATUS: School holidays ({school['name']}) begin in "
                f"{school['starts_in_days']} days. Anticipate pre-holiday shopping spike."
            )

        return "\n".join(lines)

    except Exception:
        return ""