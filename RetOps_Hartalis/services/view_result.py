import pandas as pd


from data_processor import process_data, format_for_ai


# ── separator helper ──────────────────────────────────────────────────────────
SEP = "=" * 60

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    FILE_PATH = "dummy.csv"   # ← change this to your file path

    print(f"\n{SEP}")
    print("  SMARTSTOCK — DATA PROCESSOR VIEWER")
    print(SEP)

    df, summary, daily_totals = process_data(FILE_PATH, reorder_threshold=5)

    # ── 1. Cleaned dataset overview ───────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("  [1] CLEANED DATASET OVERVIEW")
    print(f"{'─'*60}")
    print(f"  Total rows      : {len(df)}")
    print(f"  Date range      : {df['date'].min().date()}  →  {df['date'].max().date()}")
    print(f"  Products found  : {df['product'].nunique()}")
    print(f"  Total revenue   : RM {df['revenue'].sum():,.2f}")

    # ── 2. Sample of cleaned data ─────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("  [2] SAMPLE CLEANED ROWS (first 10)")
    print(f"{'─'*60}")
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 120)
    print(df[["date", "product", "units_sold", "price", "revenue",
              "month", "week", "day_of_week"]].head(10).to_string(index=False))

    # ── 3. Daily aggregation sample ───────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("  [3] DAILY TOTALS SAMPLE (first 10)")
    print(f"{'─'*60}")
    print(daily_totals.head(10).to_string(index=False))

    # ── 4. Product summary ────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("  [4] PRODUCT SUMMARY")
    print(f"{'─'*60}")
    print(summary.to_string(index=False))

    # ── 5. Reorder alerts ─────────────────────────────────────────────────────
    reorder_items = summary[summary["reorder_flag"]]
    print(f"\n{'─'*60}")
    print(f"  [5] REORDER ALERTS  ({len(reorder_items)} product(s) flagged)")
    print(f"{'─'*60}")
    if reorder_items.empty:
        print("  No products need reordering.")
    else:
        for _, row in reorder_items.iterrows():
            print(f"  ⚠️  {row['product']}  —  avg {row['avg_daily_sales']} units/day")

    # ── 6. AI-ready formatted string ─────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("  [6] AI-READY SUMMARY (what gets sent to Z.AI)")
    print(f"{'─'*60}")
    print(format_for_ai(summary))

    print(f"\n{SEP}\n")

    # Step 2 — ask user if they want to send to AI
    print(f"\n{'─'*60}")
    answer = input("  Send this data to Z.AI for recommendations? (y/n): ").strip().lower()
    if answer == "y":
        import asyncio
        from pipeline import run_pipeline
        asyncio.run(run_pipeline(FILE_PATH, reorder_threshold=5))