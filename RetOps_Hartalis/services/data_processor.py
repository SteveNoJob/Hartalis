import pandas as pd
import numpy as np

# ── Known aliases for auto-detection ─────────────────────────────────────────
COLUMN_MAP = {
    "date":        ["date", "transaction_date", "order_date", "timestamp", "period"],
    "product":     ["product", "item", "product_name", "sku", "name", "category",
                    "label", "item_name", "group"],
    "units_sold":  ["units_sold", "quantity", "qty", "units", "volume", "sold",
                    "count", "sales_qty"],
    # Unit price only — cost per single item, NOT totals
    "price":       ["price", "unit_price", "selling_price", "cost", "rate", "unit_cost"],
    # Total revenue — pre-multiplied, used directly instead of price × units
    "revenue_col": ["sales", "revenue", "total_sales", "total_revenue",
                    "amount", "value", "turnover"]
}

# ── Series/type column names that indicate a filter is needed ─────────────────
SERIES_TYPE_COLUMNS = ["series", "type", "metric", "measure", "indicator"]

# ── Values meaning actual absolute sales data (keep) ─────────────────────────
ABS_VALUES = ["abs", "absolute", "actual", "total", "raw"]

# ── Values meaning rates/growth (drop) ───────────────────────────────────────
RATE_VALUES = ["growth", "growth_yoy", "growth_mom", "yoy", "mom", "rate",
               "pct", "percent", "percentage", "index", "ratio"]


def find_column(df, possible_names):
    for col in df.columns:
        normalized = col.lower().strip().replace(" ", "_")
        if normalized in possible_names:
            return col
    return None


def detect_and_filter_series(df):
    """
    Detect if dataset has a series/type column (e.g. abs, growth_yoy)
    and filter to only keep absolute value rows.
    """
    series_col = None
    for col in df.columns:
        if col.lower().strip() in SERIES_TYPE_COLUMNS:
            series_col = col
            break

    if series_col is None:
        return df, None

    unique_vals = df[series_col].str.lower().str.strip().unique().tolist()
    print(f"\n⚠️  Detected series/type column: '{series_col}'")
    print(f"   Unique values: {unique_vals}")

    abs_mask  = df[series_col].str.lower().str.strip().isin(ABS_VALUES)
    rate_mask = df[series_col].str.lower().str.strip().apply(
        lambda v: any(r in v for r in RATE_VALUES)
    )

    if abs_mask.sum() > 0:
        dropped = rate_mask.sum()
        df = df[abs_mask].copy()
        print(f"   ✅ Kept {abs_mask.sum()} absolute rows | 🗑  Dropped {dropped} rate/growth rows")
    else:
        print(f"\n   Could not auto-identify absolute rows.")
        print(f"   Which value in '{series_col}' represents actual sales? Options: {unique_vals}")
        chosen = input("   Enter value: ").strip().lower()
        df = df[df[series_col].str.lower().str.strip() == chosen].copy()
        print(f"   ✅ Filtered to '{chosen}': {len(df)} rows remaining")

    return df, series_col


def confirm_mapping(date_col, product_col, units_col, price_col, revenue_col):
    """
    Show detected mapping to user and ask for confirmation.
    Returns True if confirmed, False if user wants to remap manually.
    """
    print(f"\n{'─'*60}")
    print("  📋 COLUMN MAPPING — PLEASE CONFIRM")
    print(f"{'─'*60}")
    print(f"   date         → {date_col}")
    print(f"   product      → {product_col}")
    print(f"   units_sold   → {units_col}")
    print(f"   price        → {price_col  or 'NOT FOUND (will default to 0)'}")
    print(f"   revenue      → {revenue_col or 'NOT FOUND'}")
    print(f"{'─'*60}")
    answer = input("   Is this correct? (y/n): ").strip().lower()
    return answer == "y"


def interactive_column_mapping(df, required=("date", "product", "units_sold"), optional=("price",)):
    """
    When auto-detection fails or user rejects mapping, prompt to map manually.
    """
    print(f"\n   Available columns: {list(df.columns)}\n")
    mapping = {}

    for field in list(required) + list(optional):
        is_required = field in required
        print(f"  {'[REQUIRED]' if is_required else '[OPTIONAL]'} Which column is '{field}'?")
        print(f"   Options: {list(df.columns)}")
        while True:
            val = input("   Enter column name (or press Enter to skip if optional): ").strip()
            if val == "" and not is_required:
                mapping[field] = None
                break
            elif val in df.columns:
                mapping[field] = val
                break
            elif val == "" and is_required:
                print("   ❌ Required — please enter a valid column name.")
            else:
                print(f"   ❌ '{val}' not found. Choose from: {list(df.columns)}")

    return mapping


def remove_outliers(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    upper = Q3 + 1.5 * IQR
    removed = (df[column] > upper).sum()
    if removed > 0:
        print(f"   🗑  Outlier removal: dropped {removed} rows where {column} > {upper:.2f}")
    return df[df[column] <= upper]


def load_file(file_path):
    ext = file_path.lower().split(".")[-1]
    loaders = {
        "csv":  lambda: pd.read_csv(file_path),
        "tsv":  lambda: pd.read_csv(file_path, sep="\t"),
        "xlsx": lambda: pd.read_excel(file_path),
        "xls":  lambda: pd.read_excel(file_path),
        "json": lambda: pd.read_json(file_path),
    }
    if ext not in loaders:
        raise ValueError(f"Unsupported file type: .{ext}. Supported: {list(loaders.keys())}")
    return loaders[ext]()


def validate_data_quality(df):
    """
    Run quality checks and print a report. Warns but does not crash.
    """
    print(f"\n{'─'*60}")
    print("  DATA QUALITY REPORT")
    print(f"{'─'*60}")
    issues = 0

    for col in ["date", "product", "units_sold", "price"]:
        if col in df.columns:
            nulls = df[col].isna().sum()
            if nulls > 0:
                pct = round(nulls / len(df) * 100, 1)
                print(f"  ⚠️  '{col}' has {nulls} nulls ({pct}%) — will be handled")
                issues += 1

    neg_units = (df["units_sold"] < 0).sum()
    if neg_units > 0:
        print(f"  ⚠️  {neg_units} rows have negative units_sold — will be dropped")
        issues += 1

    if "price" in df.columns:
        neg_price = (df["price"] < 0).sum()
        if neg_price > 0:
            print(f"  ⚠️  {neg_price} rows have negative price — will be set to median")
            issues += 1

    dupes = df.duplicated().sum()
    if dupes > 0:
        print(f"  ⚠️  {dupes} fully duplicate rows — will be dropped")
        issues += 1

    if pd.api.types.is_datetime64_any_dtype(df["date"]):
        date_range_years = (df["date"].max() - df["date"].min()).days / 365
        if date_range_years > 20:
            print(f"  ⚠️  Date range spans {date_range_years:.1f} years — check for bad dates")
            issues += 1

    if issues == 0:
        print("  ✅ No data quality issues detected")
    else:
        print(f"\n  ⚠️  {issues} issue(s) found — auto-fixing where possible")
    print(f"{'─'*60}")


def process_data(file_path, reorder_threshold=5):
    # 1. Load
    df = load_file(file_path)
    df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_")
    print(f"\n📂 Loaded: {len(df)} rows | Columns: {list(df.columns)}")

    # 2. Drop fully duplicate rows early
    before = len(df)
    df = df.drop_duplicates()
    if len(df) < before:
        print(f"   🗑  Dropped {before - len(df)} duplicate rows")

    # 3. Detect & filter series/type column (abs vs growth_yoy vs growth_mom)
    df, series_col = detect_and_filter_series(df)

    # 4. Auto-detect columns
    date_col    = find_column(df, COLUMN_MAP["date"])
    product_col = find_column(df, COLUMN_MAP["product"])
    units_col   = find_column(df, COLUMN_MAP["units_sold"])
    price_col   = find_column(df, COLUMN_MAP["price"])
    revenue_col = find_column(df, COLUMN_MAP["revenue_col"])  # e.g. 'sales'

    # 5. Confirm mapping with user — remap manually if wrong
    confirmed = confirm_mapping(date_col, product_col, units_col, price_col, revenue_col)
    if not confirmed:
        manual = interactive_column_mapping(df)
        date_col    = manual.get("date")       or date_col
        product_col = manual.get("product")    or product_col
        units_col   = manual.get("units_sold") or units_col
        price_col   = manual.get("price")      or price_col

    # 6. Validate required columns are present
    if not all([date_col, product_col, units_col]):
        raise ValueError(
            f"Missing required columns after mapping.\n"
            f"  date={date_col}, product={product_col}, units_sold={units_col}\n"
            f"  Available: {list(df.columns)}"
        )

    # 7. Rename to standard schema
    rename_map = {date_col: "date", product_col: "product", units_col: "units_sold"}
    if price_col:
        rename_map[price_col] = "price"
    if revenue_col and revenue_col not in rename_map:
        rename_map[revenue_col] = "revenue_raw"
    df = df.rename(columns=rename_map)
    if "price" not in df.columns:
        df["price"] = np.nan

    # 8. Type conversion
    df["date"]       = pd.to_datetime(df["date"], errors="coerce")
    df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce")
    df["price"]      = pd.to_numeric(df["price"], errors="coerce")
    if "revenue_raw" in df.columns:
        df["revenue_raw"] = pd.to_numeric(df["revenue_raw"], errors="coerce")

    # 9. Fix negative price
    df.loc[df["price"] < 0, "price"] = np.nan

    # 10. Quality report
    validate_data_quality(df)

    # 11. Drop invalid rows
    before = len(df)
    df = df.dropna(subset=["date", "product", "units_sold"])
    df = df[df["units_sold"] > 0]
    dropped = before - len(df)
    if dropped > 0:
        print(f"\n   🗑  Dropped {dropped} invalid rows (null/zero units or missing date/product)")

    if df.empty:
        raise ValueError("No valid data after cleaning. Check your dataset.")

    # 12. Outlier removal
    df = remove_outliers(df, "units_sold")

    # 13. Fill missing price
    if df["price"].isna().all():
        print("   ℹ️  No unit price data — setting price to 0")
        df["price"] = 0.0
    else:
        median_price = df["price"].median()
        filled = df["price"].isna().sum()
        if filled > 0:
            print(f"   ℹ️  Filled {filled} missing prices with median (RM{median_price:.2f})")
        df["price"] = df["price"].fillna(median_price)

    # 14. Date features
    df["month"]       = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.day_name()
    df["week"]        = df["date"].dt.isocalendar().week.astype(int)

    # 15. Revenue — use pre-calculated if available, otherwise compute
    if "revenue_raw" in df.columns and df["revenue_raw"].notna().any():
        df["revenue"] = df["revenue_raw"].round(2)
        print("   ℹ️  Using pre-calculated revenue column directly (not units × price)")
    else:
        df["revenue"] = (df["units_sold"] * df["price"]).round(2)

    # 16. Sort
    df = df.sort_values(by="date")

    # 17. Daily aggregation
    daily_totals = (
        df.groupby(["date", "product"])
        .agg(units_sold=("units_sold", "sum"), revenue=("revenue", "sum"))
        .reset_index()
    )

    # 18. Summary with reorder flag
    summary = (
        daily_totals.groupby("product")
        .agg(
            total_units=("units_sold", "sum"),
            avg_daily_sales=("units_sold", "mean"),
            total_revenue=("revenue", "sum"),
        )
        .reset_index()
    )
    summary["avg_daily_sales"] = summary["avg_daily_sales"].round(2)
    summary["total_revenue"]   = summary["total_revenue"].round(2)
    summary["reorder_flag"]    = summary["avg_daily_sales"] >= reorder_threshold

    print(f"\n✅ Processing complete: {len(df)} rows | {summary['product'].nunique()} products")
    return df, summary, daily_totals


def format_for_ai(summary: pd.DataFrame) -> str:
    lines = ["Product inventory summary (avg daily sales | total units | revenue | reorder needed):"]
    for _, row in summary.iterrows():
        flag = "⚠️  REORDER" if row["reorder_flag"] else "✅ OK"
        lines.append(
            f"  - {row['product']}: {row['avg_daily_sales']} units/day | "
            f"{int(row['total_units'])} total | RM{row['total_revenue']} revenue | {flag}"
        )
    return "\n".join(lines)