# context/context_builder.py
"""
Orchestrates all context modules into a single string for the forecaster.

When a what-if scenario is provided, it is PREPENDED to the context
so GLM sees it first and knows to adjust the recommendations that follow.
"""

from datetime import date
from typing import List, Dict, Optional

from context.calendar import build_calendar_context_string
from context.holiday_trend import build_trend_context_string
from context.weather import get_weather_context
from context.anomaly import build_anomaly_context_string
from context.scenario import parse_scenario, build_scenario_context_string


async def build_full_context(
    sales_history: Optional[List[Dict]] = None,
    user_sales_csv_path: Optional[str] = None,
    store_type: str = "grocery",
    city: str = "Kuala Lumpur",
    include_weather: bool = True,
    reference_date: Optional[date] = None,
    scenario_query: Optional[str] = None,
) -> str:
    """
    Single function Feq/CS call to get all context as one injectable string.
    Never crashes — each module fails gracefully.

    Args:
        sales_history:      Recent daily sales for anomaly detection.
                            Format: [{"date":..., "product_name":..., "units_sold":...}]
        user_sales_csv_path: Path to user's uploaded long-term CSV for trend calc.
                            Falls back to DOSM if missing.
        store_type:         'grocery' | 'convenience' | 'electronics' | 'clothing' |
                            'household' | 'pharmacy' | 'automotive' | 'fuel' | 'all'
                            Used only when user CSV is absent.
        city:               Malaysian city for weather forecast.
        include_weather:    Set False to skip the weather API call (for tests).
        reference_date:     Override 'today' for testing.
        scenario_query:     Optional what-if query like "tomorrow is a holiday".
                            When provided, scenario context is prepended and
                            real weather fetch is skipped (scenario overrides it).
    """
    today = reference_date or date.today()
    sections = []

    # 0. Scenario override (prepended — highest priority)
    scenario_overrides_weather = False
    if scenario_query:
        try:
            override = parse_scenario(scenario_query)
            scenario_ctx = build_scenario_context_string(override)
            if scenario_ctx:
                sections.append(scenario_ctx)
                # Only skip real weather fetch if the scenario specifies weather
                scenario_overrides_weather = override.force_weather is not None
        except Exception:
            pass

    # 1. Calendar — always include
    try:
        calendar_ctx = build_calendar_context_string(reference_date=today)
        if calendar_ctx:
            sections.append(calendar_ctx)
    except Exception:
        pass

    # 2. Monthly trend
    try:
        trend_ctx = build_trend_context_string(
            month=today.month,
            user_csv_path=user_sales_csv_path,
            store_type=store_type,
        )
        if trend_ctx:
            sections.append(trend_ctx)
    except Exception:
        pass

    # 3. Weather — skip if scenario specifies weather (avoids contradicting context)
    if include_weather and not scenario_overrides_weather:
        try:
            weather_ctx = await get_weather_context(city)
            if weather_ctx:
                sections.append(weather_ctx)
        except Exception:
            pass

    # 4. Anomaly
    if sales_history:
        try:
            anomaly_ctx = build_anomaly_context_string(sales_history)
            if anomaly_ctx:
                sections.append(anomaly_ctx)
        except Exception:
            pass

    return "\n\n".join(sections) if sections else ""