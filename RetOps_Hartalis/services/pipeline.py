import asyncio
from data_processor import process_data, format_for_ai
from inventory_prompts import INVENTORY_SYSTEM_PROMPT, build_user_prompt
from glm_client import call_glm

async def run_pipeline(file_path: str, reorder_threshold: int = 5):

    print("\n" + "=" * 60)
    print("  SMARTSTOCK — AI INVENTORY PIPELINE")
    print("=" * 60)

    # ── Step 1: Process data ──────────────────────────────────────
    print("\n[STEP 1] Processing data...")
    df, summary, daily_totals = process_data(file_path, reorder_threshold=reorder_threshold)

    # ── Step 2: Format for AI ─────────────────────────────────────
    print("\n[STEP 2] Preparing AI prompt...")
    ai_summary   = format_for_ai(summary)
    date_range   = f"{df['date'].min().date()} → {df['date'].max().date()}"
    total_revenue = f"RM {df['revenue'].sum():,.2f}"

    user_prompt = build_user_prompt(ai_summary, date_range, total_revenue)

    print("\n── Prompt Preview ──────────────────────────────────────")
    print(user_prompt)
    print("────────────────────────────────────────────────────────")

    # ── Step 3: Call Z.AI ─────────────────────────────────────────
    print("\n[STEP 3] Sending to Z.AI...")
    try:
        response = await call_glm(
            system_prompt=INVENTORY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.2,   # low = more factual, less creative
            max_tokens=1000
        )

        print("\n" + "=" * 60)
        print("  Z.AI INVENTORY REPORT")
        print("=" * 60)
        print(response)
        print("=" * 60)
        return response

    except Exception as e:
        print(f"\n❌ Z.AI call failed: {e}")
        print("   Check your API key balance or network connection.")
        return None


# ── Run directly ──────────────────────────────────────────────────
if __name__ == "__main__":
    FILE_PATH = "dummy_inventory_data.xlsx"   # ← change to your file
    asyncio.run(run_pipeline(FILE_PATH, reorder_threshold=5))