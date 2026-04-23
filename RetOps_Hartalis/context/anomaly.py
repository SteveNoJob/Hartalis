# context/anomaly.py
"""
Detects recent anomalies in sales history to feed into the forecaster's context.

The forecaster uses historical patterns. If something weird happened in the last
7 days that the calendar doesn't explain (a competitor closed, a flash flood,
a viral TikTok about a product), the forecaster won't know unless we tell it.

This module flags those deviations in plain English.
"""

from typing import List, Dict, Optional
from datetime import date, timedelta
import statistics


# How many standard deviations from the mean before we flag something as an anomaly.
# 2.0 = roughly top/bottom 2.5% of days — conservative, avoids false alarms.
ANOMALY_Z_THRESHOLD = 2.0

# Minimum days of history needed before we'll attempt anomaly detection.
MIN_HISTORY_DAYS = 14

# How many recent days count as "recent" for the anomaly window.
RECENT_WINDOW_DAYS = 7


def _compute_baseline_stats(daily_sales: List[float]) -> Optional[Dict]:
    """
    Compute mean + stdev of the baseline period (everything except the recent window).
    Returns None if we don't have enough data.
    """
    if len(daily_sales) < MIN_HISTORY_DAYS:
        return None

    baseline = daily_sales[:-RECENT_WINDOW_DAYS]
    if len(baseline) < 7:
        return None

    mean = statistics.mean(baseline)
    stdev = statistics.stdev(baseline) if len(baseline) > 1 else 0

    return {"mean": mean, "stdev": stdev}


def detect_anomalies(sales_history: List[Dict]) -> List[Dict]:
    """
    sales_history format:
        [{"date": "2026-04-15", "product_name": "Milo", "units_sold": 12}, ...]

    Returns a list of anomaly dicts:
        [{"product_name": "Milo", "type": "spike", "magnitude": "+45%",
          "date": "2026-04-18", "baseline_avg": 8.2, "observed": 11.9}, ...]
    """
    if not sales_history:
        return []

    # Group sales by product
    by_product: Dict[str, List[Dict]] = {}
    for row in sales_history:
        name = row.get("product_name", "Unknown")
        by_product.setdefault(name, []).append(row)

    anomalies = []

    for product_name, rows in by_product.items():
        # Sort by date
        rows = sorted(rows, key=lambda r: r["date"])
        daily_units = [float(r.get("units_sold", 0)) for r in rows]

        stats = _compute_baseline_stats(daily_units)
        if stats is None:
            continue  # Not enough history

        mean = stats["mean"]
        stdev = stats["stdev"]
        if stdev == 0 or mean == 0:
            continue  # Flat sales — can't detect anomalies meaningfully

        # Check each day in the recent window
        recent_rows = rows[-RECENT_WINDOW_DAYS:]
        for r in recent_rows:
            observed = float(r.get("units_sold", 0))
            z_score = (observed - mean) / stdev

            if abs(z_score) >= ANOMALY_Z_THRESHOLD:
                pct_change = ((observed - mean) / mean) * 100
                anomalies.append({
                    "product_name": product_name,
                    "date": r["date"],
                    "type": "spike" if z_score > 0 else "drop",
                    "magnitude_pct": round(pct_change, 1),
                    "baseline_avg": round(mean, 1),
                    "observed": round(observed, 1),
                    "z_score": round(z_score, 2),
                })

    return anomalies


def build_anomaly_context_string(sales_history: List[Dict], max_shown: int = 5) -> str:
    """
    Main function context_builder.py calls.

    Returns a plain English string describing recent anomalies,
    or empty string if nothing unusual detected.

    Caps output to the top `max_shown` anomalies ranked by |magnitude_pct|
    to keep the section size bounded (PRD §4.3.3).
    """
    try:
        anomalies = detect_anomalies(sales_history)

        if not anomalies:
            return ""

        # Sort by absolute magnitude — biggest deviations matter most
        anomalies.sort(key=lambda a: abs(a["magnitude_pct"]), reverse=True)
        total_count = len(anomalies)
        shown = anomalies[:max_shown]
        omitted = total_count - len(shown)

        lines = [f"RECENT SALES ANOMALIES (last 7 days, {total_count} detected):"]
        lines.append(
            "These deviations are not explained by the calendar or trend modules. "
            "Consider them when forecasting."
        )

        for a in shown:
            direction = "spike" if a["type"] == "spike" else "drop"
            sign = "+" if a["magnitude_pct"] > 0 else ""
            lines.append(
                f"- {a['product_name']} on {a['date']}: {direction} of "
                f"{sign}{a['magnitude_pct']}% "
                f"(observed {a['observed']} units vs baseline avg {a['baseline_avg']})"
            )

        if omitted > 0:
            lines.append(
                f"(…plus {omitted} additional smaller anomalies not shown — "
                f"see full log for details.)"
            )

        return "\n".join(lines)

    except Exception:
        return ""  # Never crash the pipeline