# context/scenario.py
"""
What-If Scenario module — handles hypothetical queries from the user.

User types: "What if it rains heavily tomorrow?"
         OR "Tomorrow is a public holiday"
         OR "Ramadan starts next week"
         OR "What if we run a 20% discount on beverages this weekend?"

This module:
  1. Parses the scenario into a structured override dict
  2. context_builder.py applies the override on top of the normal context
  3. The forecaster / reorder module sees the hypothetical world

Judge-facing demo feature — makes the trade-off reasoning explicit.
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ScenarioOverride:
    """
    Structured representation of a hypothetical scenario.
    Any field set here overrides the normal context pipeline output.
    """
    raw_query: str = ""
    scenario_type: str = "unknown"   # weather | holiday | ramadan | promo | custom
    description: str = ""             # plain English summary for GLM prompt

    # Weather overrides
    force_weather: Optional[str] = None          # "heavy_rain", "storm", "heatwave", "haze", "clear"
    rainfall_mm: Optional[float] = None

    # Calendar overrides
    force_public_holiday: Optional[str] = None   # name of synthetic holiday
    force_school_holiday: bool = False
    force_ramadan_phase: Optional[str] = None    # "early", "mid", "late", "approaching"

    # Promotional overrides (restaurant/retail promos)
    promo_items: List[str] = field(default_factory=list)
    promo_discount_pct: Optional[float] = None

    # Free-form additional context — always appended to GLM prompt
    extra_context: str = ""


# --------------------------------------------------------------------------
# Parsing patterns — keyword-based, cheap, deterministic
# --------------------------------------------------------------------------

WEATHER_PATTERNS = {
    "heavy_rain": [
        r"heavy\s+rain", r"rains?\s+heavily", r"rain\s+heavily",
        r"lebat", r"hujan\s+lebat", r"downpour",
        r"flood", r"banjir",
    ],
    "storm": [
        r"thunderstorm", r"storm", r"ribut", r"petir",
    ],
    "heatwave": [
        r"heat\s*wave", r"heatwave", r"very\s+hot", r"panas\s+terik",
        r"scorching",
    ],
    "haze": [
        r"haze", r"jerebu", r"smog",
    ],
    "rain": [
        r"\brain\b", r"\bhujan\b", r"wet",
    ],
    "clear": [
        r"sunny", r"clear", r"cerah", r"fine\s+weather",
    ],
}

HOLIDAY_PATTERNS = [
    r"public\s+holiday", r"cuti\s+umum", r"hari\s+cuti",
    r"it'?s\s+a\s+holiday", r"tomorrow\s+is\s+a\s+holiday",
]

SCHOOL_HOLIDAY_PATTERNS = [
    r"school\s+holiday", r"cuti\s+sekolah", r"kids?\s+at\s+home",
]

RAMADAN_PATTERNS = {
    "approaching": [r"ramadan\s+starts", r"ramadan\s+begins", r"ramadan\s+next"],
    "active":      [r"during\s+ramadan", r"ramadan\s+is", r"it'?s\s+ramadan",
                    r"puasa", r"bulan\s+puasa"],
}

PROMO_PATTERNS = [
    r"(\d+)%?\s*(discount|off|sale|promo|promotion)",
    r"(discount|promo|sale|promotion)\s*(of\s*)?(\d+)%?",
]


def parse_scenario(query: str) -> ScenarioOverride:
    """
    Parse a natural-language what-if query into a ScenarioOverride.
    Never crashes — unknown queries produce a ScenarioOverride with
    scenario_type='custom' and the raw query as extra_context.
    """
    if not query or not query.strip():
        return ScenarioOverride(raw_query=query, scenario_type="unknown")

    q = query.lower().strip()
    override = ScenarioOverride(raw_query=query)
    matched_parts = []

    # Weather detection — check strongest first
    for weather_type in ["storm", "heavy_rain", "heatwave", "haze", "rain", "clear"]:
        patterns = WEATHER_PATTERNS[weather_type]
        if any(re.search(p, q) for p in patterns):
            override.force_weather = weather_type
            override.scenario_type = "weather"
            matched_parts.append(f"weather override: {weather_type.replace('_', ' ')}")
            break

    # Holiday detection
    if any(re.search(p, q) for p in HOLIDAY_PATTERNS):
        override.force_public_holiday = "User-specified public holiday"
        override.scenario_type = "holiday"
        matched_parts.append("synthetic public holiday tomorrow")

    if any(re.search(p, q) for p in SCHOOL_HOLIDAY_PATTERNS):
        override.force_school_holiday = True
        if override.scenario_type == "unknown":
            override.scenario_type = "holiday"
        matched_parts.append("school holiday active")

    # Ramadan detection
    for phase, patterns in RAMADAN_PATTERNS.items():
        if any(re.search(p, q) for p in patterns):
            override.force_ramadan_phase = phase
            if override.scenario_type == "unknown":
                override.scenario_type = "ramadan"
            matched_parts.append(f"Ramadan ({phase})")
            break

    # Promo detection
    for pattern in PROMO_PATTERNS:
        m = re.search(pattern, q)
        if m:
            # Pull the first number from the match
            digits = re.search(r"\d+", m.group(0))
            if digits:
                override.promo_discount_pct = float(digits.group(0))
                override.scenario_type = "promo"
                matched_parts.append(f"{override.promo_discount_pct}% promo")
                break

    # If nothing matched, treat as custom free-form scenario
    if not matched_parts:
        override.scenario_type = "custom"
        override.extra_context = query
        override.description = f"Custom scenario: {query}"
    else:
        override.description = "Hypothetical: " + ", ".join(matched_parts)

    return override


# --------------------------------------------------------------------------
# Context string builder — converts the override into a GLM-ready string
# --------------------------------------------------------------------------

def build_scenario_context_string(override: ScenarioOverride) -> str:
    """
    Renders a ScenarioOverride into a plain English string that gets
    prepended to the normal context. Signals clearly to GLM that this
    is a HYPOTHETICAL scenario, not current reality.
    """
    if not override or override.scenario_type == "unknown":
        return ""

    lines = [
        "⚠️ WHAT-IF SCENARIO (hypothetical — adjust recommendations accordingly):",
        f"User query: \"{override.raw_query}\"",
    ]

    if override.force_weather:
        weather_impacts = {
            "storm":       "Thunderstorms expected. Walk-in traffic will collapse. Delivery orders may spike. Panic-buy essentials (rice, noodles, canned food) likely.",
            "heavy_rain":  "Heavy rain forecast. Walk-in traffic drops 20-40%. Delivery volumes rise sharply.",
            "rain":        "Rainy conditions. Mild drop in foot traffic expected.",
            "heatwave":    "Heatwave conditions. Cold beverages, ice cream, bottled water demand spikes 30-50%.",
            "haze":        "Haze conditions. Outdoor foot traffic drops. Face mask and bottled water demand rises.",
            "clear":       "Clear weather. Normal-to-elevated foot traffic.",
        }
        lines.append(f"- Weather scenario: {weather_impacts.get(override.force_weather, '')}")

    if override.force_public_holiday:
        lines.append(
            f"- Public holiday scenario: Treat tomorrow as a public holiday. "
            f"For restaurants: pre-holiday dinner rush tonight, reduced lunch crowd tomorrow if competitors closed. "
            f"For retail: stock-up shopping today, most shops closed tomorrow."
        )

    if override.force_school_holiday:
        lines.append(
            "- School holiday scenario: Kids home all day. Expect higher daytime "
            "foot traffic at restaurants (family lunches), and increased demand "
            "for snacks, beverages, and convenience meals at retail."
        )

    if override.force_ramadan_phase:
        ramadan_impacts = {
            "approaching": "Ramadan starts imminently. Stock up on dates, cooking oil, flour, sugar NOW.",
            "active":      "Ramadan is in progress. Daytime F&B demand drops for Muslim-majority areas; evening iftar period sees strong surge. Dates, beverages, cooking oil, flour, and sugar are elevated throughout the month.",
            "early":       "Early Ramadan. Daytime F&B demand collapses for Muslim-majority areas; evening iftar surge is massive.",
            "mid":         "Mid Ramadan. Bazaar Ramadan in full swing. Evening demand dominant.",
            "late":        "Late Ramadan. Hari Raya prep overtakes iftar shopping — biscuits, cookies, cooking essentials spike.",
        }
        lines.append(f"- Ramadan scenario: {ramadan_impacts.get(override.force_ramadan_phase, ramadan_impacts['active'])}")

    if override.promo_discount_pct:
        items_str = ", ".join(override.promo_items) if override.promo_items else "selected items"
        lines.append(
            f"- Promo scenario: {override.promo_discount_pct:.0f}% discount on {items_str}. "
            f"Expect 1.5x–2.5x volume lift on promoted items; substitution away from "
            f"non-promoted alternatives. Factor elasticity into reorder quantities."
        )

    if override.extra_context and override.scenario_type == "custom":
        lines.append(
            f"- Custom scenario context: {override.extra_context}. "
            f"Interpret naturally and adjust forecast/reorder recommendations."
        )

    lines.append(
        "INSTRUCTION TO GLM: Treat the above as the prevailing condition. "
        "Override or adjust the normal context sections below where they conflict. "
        "Explicitly explain in your reasoning which adjustments you made because of this scenario."
    )

    return "\n".join(lines)