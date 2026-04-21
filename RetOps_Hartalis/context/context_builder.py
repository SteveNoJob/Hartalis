# context/context_builder.py
"""
Orchestrates all context modules into a single string for the forecaster.
"""

from datetime import date
from typing import List, Dict, Optional

from context.calendar import build_calendar_context_string
from context.holiday_trend import build_trend_context_string
from context.weather import get_weather_context
from context.anomaly import build_anomaly_context_string


async def build_full_context(
    sales_history: Optional[List[Dict]] = None,
    user_sales_csv_path: Optional[str] = None,
    store_type: str = "grocery",
    city: str = "Kuala Lumpur",
    include_weather: bool = True,
    reference_date: Optional[date] = None,
) -> str:
    """
    Single function Feq calls to get all context as one injectable string.
    Never crashes — each module fails gracefully.

    Args:
        sales_history: Recent daily sales, for anomaly detection.
                       Format: [{"date":..., "product_name":..., "units_sold":...}]
        user_sales_csv_path: Path to user's uploaded long-term CSV, for
                             trend lift calculation. Falls back to DOSM if missing.
        store_type: User's retail category — 'grocery', 'convenience',
                    'electronics', 'clothing', 'household', 'pharmacy',
                    'automotive', 'fuel', or 'all'. Used only when falling
                    back to DOSM (ignored if user CSV is available).
        city: Malaysian city for weather forecast.
        include_weather: Set False to skip the weather API call (useful for tests).
        reference_date: Override 'today' — used for testing.
    """
    today = reference_date or date.today()
    sections = []

    # 1. Calendar — always include
    try:
        calendar_ctx = build_calendar_context_string(reference_date=today)
        if calendar_ctx:
            sections.append(calendar_ctx)
    except Exception:
        pass

    # 2. Monthly trend — from user CSV if available, else DOSM filtered by store_type
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

    # 3. Weather — optional
    if include_weather:
        try:
            weather_ctx = await get_weather_context(city)
            if weather_ctx:
                sections.append(weather_ctx)
        except Exception:
            pass

    # 4. Anomaly — only if sales history provided
    if sales_history:
        try:
            anomaly_ctx = build_anomaly_context_string(sales_history)
            if anomaly_ctx:
                sections.append(anomaly_ctx)
        except Exception:
            pass

    return "\n\n".join(sections) if sections else ""