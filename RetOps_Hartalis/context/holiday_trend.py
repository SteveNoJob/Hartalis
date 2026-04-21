# context/holiday_trend.py
"""
Computes monthly retail sales lift.

Priority order:
  1. User-uploaded sales history (most accurate — reflects this specific store)
  2. DOSM IOWRT national baseline (fallback for new users with <3 months data)

This file does NOT call Z.AI. It produces numbers and a plain English string
that context_builder.py injects into the GLM prompt.
"""

from pathlib import Path
from typing import Optional, Dict
import pandas as pd
from functools import lru_cache


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Baseline months = "normal" months with no major Malaysian festivals.
# April, June, July, September have no major public holidays driving spikes.
BASELINE_MONTHS = [4, 6, 7, 9]

# Minimum months of user data required before we trust their CSV over DOSM.
# Below this, we fall back to the national baseline.
MIN_USER_MONTHS_REQUIRED = 3

# Path to the fallback DOSM CSV (bundled with the repo).
DOSM_CSV_PATH = Path(__file__).parent / "data" / "iowrt_3d.csv"

# Category-specific lift during major festivals (expressed as multipliers, not %).
# Example: 0.65 means +65% vs baseline during Hari Raya for cooking oil.
# These are kept hardcoded because they are editorial judgments about product-level
# behavior, not something that can be reliably derived from aggregate DOSM data.
FESTIVE_CATEGORY_LIFT = {
    "Hari Raya": {
        "cooking oil":        0.65,
        "sugar":              0.70,
        "flour":              0.55,
        "condensed milk":     0.60,
        "biscuits":           0.80,
        "beverages":          0.45,
        "cooking essentials": 0.60,
    },
    "Chinese New Year": {
        "snacks":             0.75,
        "beverages":          0.55,
        "mandarin oranges":   2.10,
        "cookies":            1.20,
        "cooking essentials": 0.40,
    },
    "Deepavali": {
        "sweets":             0.90,
        "snacks":             0.50,
        "beverages":          0.35,
        "cooking essentials": 0.30,
    },
}

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}


# ---------------------------------------------------------------------------
# Core lift computation
# ---------------------------------------------------------------------------

def _compute_lift_from_dataframe(
    df: pd.DataFrame,
    date_col: str = "date",
    sales_col: str = "sales",
) -> Dict[int, float]:
    """
    Given a dataframe with date + sales columns, return {month: lift_percent}.

    Lift is measured against the average of BASELINE_MONTHS.
    """
    if date_col not in df.columns or sales_col not in df.columns:
        raise ValueError(
            f"CSV must have '{date_col}' and '{sales_col}' columns. "
            f"Got: {list(df.columns)}"
        )

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df["month"] = df[date_col].dt.month

    monthly_avg = df.groupby("month")[sales_col].mean()

    # If we don't have at least one baseline month, we can't compute lift.
    available_baseline = [m for m in BASELINE_MONTHS if m in monthly_avg.index]
    if not available_baseline:
        raise ValueError(
            "Cannot compute lift: no baseline months (Apr, Jun, Jul, Sep) "
            "present in the data."
        )

    baseline = monthly_avg[available_baseline].mean()
    if baseline == 0:
        raise ValueError("Baseline sales is zero — cannot compute lift.")

    lift = ((monthly_avg - baseline) / baseline * 100).round(2)
    return lift.to_dict()


# DOSM retail group codes (MSIC 2008 classification).
# User's store type maps to one or more of these groups.
# Reference: https://storage.dosm.gov.my/technotes/iowrt.pdf
DOSM_RETAIL_GROUPS = {
    "grocery":      [471, 472],  # Supermarkets, mini-marts, food/beverage stores
    "convenience":  [471, 472],  # Same as grocery — convenience stores fit here
    "electronics":  [474],        # Electronics, audio/video
    "clothing":     [477],        # Apparel, footwear, leather
    "household":    [475],        # Hardware, paint, furniture
    "pharmacy":     [477],        # Pharma/medical/cosmetic (MSIC 4772)
    "automotive":   [453],        # Motor vehicle parts
    "fuel":         [473],        # Fuel stations
    "all":          None,         # Use entire dataset (least useful)
}

DEFAULT_STORE_TYPE = "grocery"


@lru_cache(maxsize=8)
def _load_dosm_baseline(store_type: str = DEFAULT_STORE_TYPE) -> Dict[int, float]:
    """
    Load DOSM national retail lift filtered to the user's store type.
    Cached per store_type so repeated calls are free.

    IMPORTANT: Filtering by store type matters. Averaging across ALL retail
    categories (electronics + clothing + groceries + fuel) washes out any
    festive signal because the categories move in different directions.
    """
    if not DOSM_CSV_PATH.exists():
        return {m: 0.0 for m in range(1, 13)}

    try:
        df = pd.read_csv(DOSM_CSV_PATH)
        if "series" in df.columns:
            df = df[df["series"] == "abs"]

        groups = DOSM_RETAIL_GROUPS.get(store_type.lower(), DOSM_RETAIL_GROUPS[DEFAULT_STORE_TYPE])
        if groups and "group" in df.columns:
            df = df[df["group"].isin(groups)]

        if df.empty:
            return {m: 0.0 for m in range(1, 13)}

        return _compute_lift_from_dataframe(df)
    except Exception:
        return {m: 0.0 for m in range(1, 13)}


def get_monthly_lift_table(
    user_csv_path: Optional[str] = None,
    store_type: str = DEFAULT_STORE_TYPE,
) -> Dict[int, float]:
    """
    Main entry point for computing monthly lift.

    Returns a dict: {1: 5.2, 2: 18.7, ...} mapping month → lift percent.

    Priority:
      1. User's own sales CSV (most accurate for this specific store)
      2. DOSM national baseline filtered by store_type (fallback)

    Args:
        user_csv_path: Optional path to user's uploaded sales CSV.
        store_type: One of DOSM_RETAIL_GROUPS keys (e.g., 'grocery',
                    'electronics', 'clothing'). Ignored if user CSV is used.
    """
    # Try user CSV first
    if user_csv_path:
        try:
            df = pd.read_csv(user_csv_path)
            df["date"] = pd.to_datetime(df["date"])
            unique_months = df["date"].dt.to_period("M").nunique()
            if unique_months >= MIN_USER_MONTHS_REQUIRED:
                return _compute_lift_from_dataframe(df)
        except Exception:
            pass

    return _load_dosm_baseline(store_type)


# ---------------------------------------------------------------------------
# Category-level lift (editorial / hardcoded)
# ---------------------------------------------------------------------------

def get_festive_category_lift(festival: str, category: str) -> float:
    """
    Returns expected sales multiplier for a product category during a festival.
    Example: get_festive_category_lift("Hari Raya", "cooking oil") → 0.65
    """
    festival_data = FESTIVE_CATEGORY_LIFT.get(festival, {})
    return festival_data.get(category.lower(), 0.0)


# ---------------------------------------------------------------------------
# Prompt context builder
# ---------------------------------------------------------------------------

def build_trend_context_string(
    month: int,
    user_csv_path: Optional[str] = None,
    store_type: str = DEFAULT_STORE_TYPE,
) -> str:
    """
    Returns a plain English string about the current month's retail trend,
    ready to inject into the GLM prompt.

    This is the function context_builder.py calls.
    """
    try:
        lift_table = get_monthly_lift_table(user_csv_path, store_type)
        lift = lift_table.get(month, 0.0)
        month_name = MONTH_NAMES.get(month, f"Month {month}")

        if user_csv_path:
            source_note = "based on your store's sales history"
        else:
            source_note = f"based on Malaysian {store_type} retail trends (DOSM)"

        if lift > 15:
            return (
                f"RETAIL TREND: {month_name} is historically a high-demand month "
                f"(~{lift:.1f}% above baseline, {source_note}). "
                f"This is a peak season — prioritise stocking up early."
            )
        elif lift > 5:
            return (
                f"RETAIL TREND: {month_name} sees moderate above-average activity "
                f"(~{lift:.1f}% above baseline, {source_note})."
            )
        elif lift < -5:
            return (
                f"RETAIL TREND: {month_name} is typically a slower month "
                f"(~{abs(lift):.1f}% below baseline, {source_note}). "
                f"Consider reducing reorder quantities to avoid deadstock."
            )
        else:
            return (
                f"RETAIL TREND: {month_name} is a baseline month with normal demand."
            )
    except Exception:
        return ""  # Never crash the pipeline