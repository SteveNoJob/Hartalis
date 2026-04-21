from datetime import date, timedelta
from typing import Optional


MALAYSIAN_EVENTS = [
    
    #2026
    ("2026-01-01", "New Year's Day", "low", ["party supplies", "beverages"], ""),
    ("2026-02-01", "Thaipusam", "", ["snacks", "beverages", "cooking essentials", "cookies"], ""),
    ("2026-02-02", "Thaipusam holiday", "", ["snacks", "beverages", "cooking essentials", "cookies"], ""),
    ("2026-02-17", "Chinese New Year Eve", "very_high", ["snacks", "beverages", "cooking essentials", "cookies"], ""),
    ("2026-02-18", "Chinese New Year Day 1", "very_high", ["snacks", "beverages"], ""),
    ("2026-03-07", "Nuzul Al Quran", "", ["snacks", "beverages", "cooking essentials", "cookies"], ""),
    ("2026-03-20", "Hari Raya Aidilfitri Eve", "very_high", ["cooking essentials", "sugar", "flour", "cooking oil", "biscuits"], ""),
    ("2026-03-21", "Hari Raya Aidilfitri Day 1", "very_high", ["cooking essentials"], ""),
    ("2026-03-22", "Hari Raya Aidilfitri Day 2", "very_high", ["cooking essentials"], ""),
    ("2026-03-23", "Hari Raya Aidilfitri Day 3", "very_high", ["cooking essentials"], ""),
    ("2026-03-24", "Hari Raya Aidilfitri Day 4", "very_high", ["cooking essentials"], ""),
    ("2026-05-01", "Labour Day", "low", [""], ""),
    ("2026-05-27", "Hari Raya Haji", "low", [""], ""),
    ("2026-05-31", "Wesak Day", "low", ["snacks", "beverages"], ""),
    ("2026-06-01", "Agong's birthday", "low", [""], ""),
    ("2026-06-02", "Wesak Day Holiday", "low", [""], ""),
    ("2026-06-17", "Awal Muharram", "low", [""], ""),
    ("2026-08-25", "Prophet Muhammad's Birthday", "low", [""], ""),
    ("2026-08-31", "Merdeka Day", "medium", [""], ""),
    ("2026-09-16", "Malaysia Day", "low", [""], ""),
    ("2026-11-08", "Deepavali", "high", [""], ""),
    ("2026-11-09", "Deepavali holiday", "high", [""], ""),
    ("2026-12-25", "Christmas Day", "low", [""], ""),
]

SCHOOL_HOLIDAYS = [
    ("2025-03-15", "2025-03-23", "Mid-term break 1"),
    ("2025-05-17", "2025-05-31", "Mid-year holidays"),
    ("2025-08-23", "2025-08-31", "Mid-term break 2"),
    ("2025-11-15", "2026-01-01", "Year-end holidays"),
]

IMPACT_DESCRIPTIONS = {
    "very_high": "40-60% increase expected",
    "high": "20-40% increase expected",
    "medium": "10-20% increase expected",
    "low": "5-10% increase expected"
}

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
                "notes": notes
            })
    
    return sorted(upcoming, key=lambda x: x["days_away"])

def get_school_holiday_status(reference_date: Optional[date] = None) -> dict:
    today = reference_date or date.today()
    
    for start_str, end_str, name in SCHOOL_HOLIDAYS:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
        days_to_start = (start - today).days
        
        # Currently in school holiday
        if start <= today <= end:
            return {
                "status": "active",
                "name": name,
                "ends_in_days": (end - today).days
            }
        
        # Approaching school holiday (within 14 days)
        if 0 < days_to_start <= 14:
            return {
                "status": "approaching",
                "name": name,
                "starts_in_days": days_to_start
            }
    
    return {"status": "none"}