# context/weather.py
"""
Fetches weather forecast and converts it into retail demand context.

Weather affects Malaysian retail in ways the calendar can't capture:
  - Heavy rain → fewer walk-ins, but spikes in rice/instant noodles/cooking oil
  - Heatwaves → cold beverage, ice cream, bottled water spikes
  - Haze → bottled water + masks spike, general foot traffic drops

Uses OpenWeatherMap forecast API (requires WEATHER_API_KEY in .env).
"""

import httpx
import os
from dotenv import load_dotenv
from collections import Counter
from typing import Optional

load_dotenv()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Thresholds tuned for Malaysian climate
HEAVY_RAIN_MM = 20.0      # single 3-hour interval — counts as heavy
WET_DAY_MM = 15.0         # total over forecast window — counts as a wet period
HOT_TEMP_C = 34.0         # sustained max temp above this = heatwave
# OpenWeather thunderstorm weather codes (2xx)
STORM_WEATHER_IDS = {200, 201, 202, 210, 211, 212, 221, 230, 231, 232}


async def _fetch_forecast(city: str) -> Optional[dict]:
    """Call OpenWeatherMap for ~48 hours of 3-hour forecast intervals."""
    if not WEATHER_API_KEY:
        return None

    params = {
        "q": f"{city},MY",
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "cnt": 16,  # 16 intervals * 3 hours = 48 hours
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(OPENWEATHER_URL, params=params)
            response.raise_for_status()
            return response.json()
    except Exception:
        return None


def _interpret_forecast(data: dict) -> str:
    """Turn raw forecast data into retail-relevant insight."""
    forecasts = data.get("list", [])
    if not forecasts:
        return ""

    # Gather signals across the whole window — don't just pick 'dominant'
    total_precip = 0.0
    max_precip_single = 0.0
    max_temp = float("-inf")
    weather_ids = []
    weather_mains = []

    for f in forecasts:
        rain_mm = f.get("rain", {}).get("3h", 0) or 0
        snow_mm = f.get("snow", {}).get("3h", 0) or 0
        precip = rain_mm + snow_mm
        total_precip += precip
        max_precip_single = max(max_precip_single, precip)

        main = f.get("main", {})
        temp_max = main.get("temp_max", main.get("temp", 0))
        max_temp = max(max_temp, temp_max)

        weather = f.get("weather", [{}])[0]
        weather_ids.append(weather.get("id", 0))
        weather_mains.append(weather.get("main", "Unknown"))

    insights = []

    # 1. Thunderstorms — highest retail impact
    storm_count = sum(1 for wid in weather_ids if wid in STORM_WEATHER_IDS)
    if storm_count >= 2:
        insights.append(
            f"Thunderstorms expected ({storm_count} intervals in next 48h). "
            "Foot traffic will drop sharply. Expect panic-buy spikes on rice, "
            "instant noodles, canned goods, bottled water."
        )
    # 2. Heavy rainfall
    elif max_precip_single >= HEAVY_RAIN_MM:
        insights.append(
            f"Heavy rainfall forecast (peak ~{max_precip_single:.0f}mm in 3h). "
            "Walk-in traffic will drop. Flood-prep items may spike: "
            "rice, cooking oil, instant noodles."
        )
    elif total_precip >= WET_DAY_MM:
        insights.append(
            f"Wet period ahead (~{total_precip:.0f}mm total over 48h). "
            "Modest traffic reduction expected; comfort items (instant noodles, "
            "hot drinks, biscuits) may see mild lift."
        )

    # 3. Heat
    if max_temp >= HOT_TEMP_C:
        insights.append(
            f"Hot period forecast (peak {max_temp:.1f}°C). "
            "Cold beverages, ice cream, bottled water, and ice demand will rise."
        )

    # 4. Haze / smoke / persistent mist
    haze_count = sum(1 for m in weather_mains if m in ("Haze", "Smoke", "Dust", "Mist"))
    if haze_count >= 3:
        insights.append(
            "Persistent haze conditions. Expect higher demand for bottled water, "
            "face masks, and indoor comfort items; reduced outdoor foot traffic."
        )

    # 5. Normal weather fallback
    if not insights:
        dominant = Counter(weather_mains).most_common(1)[0][0]
        insights.append(
            f"Normal weather ({dominant.lower()}, peak {max_temp:.1f}°C, "
            f"{total_precip:.0f}mm rainfall). No weather-driven demand shift expected."
        )

    return " ".join(insights)


async def get_weather_context(city: str = "Kuala Lumpur") -> str:
    """
    Main function context_builder.py calls.
    Returns plain English weather context, or empty string on failure.
    """
    try:
        data = await _fetch_forecast(city)
        if not data:
            return ""
        insight = _interpret_forecast(data)
        if not insight:
            return ""
        return f"WEATHER FORECAST ({city}, next 48h): {insight}"
    except Exception:
        return ""