import asyncio
import json
import re
from services.glm_client import glm_client

SYSTEM_PROMPT = """
You are an inventory optimization engine.
Analyze each SKU and return ONLY a valid JSON array, no extra text.
Each item must follow this schema exactly:{
  "sku": "abs",
  "status": "understock",
  "reorder": true,
  "reorder_qty": 100430,
  "recommendations": [
    "Consider negotiating bulk pricing given consistent high volume",
    "Review supplier lead time — 7 days may cause stockout risk",
    "Set reorder trigger at 80,000 units to avoid future understocking"
  ]
}
"""

class InventoryPipeline:
    def __init__(self, batch_size: int = 5):
        self.batch_size = batch_size

    async def run(self, summary_df) -> list[dict]:
        records = summary_df.where(
            summary_df.notna(), other=None
        ).to_dict(orient="records")

        batches = [
            records[i:i+self.batch_size]
            for i in range(0, len(records), self.batch_size)
        ]
        results = await asyncio.gather(*[self._analyze_batch(b) for b in batches])
        return [item for batch in results for item in batch]

    async def _analyze_batch(self, batch: list[dict]) -> list[dict]:
        prompt = f"Analyze these SKUs and return a JSON array:\n{json.dumps(batch, indent=2)}"

        for attempt in range(3):
            try:
                raw = await glm_client.call(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=prompt,
                    temperature=0.0,
                )
                clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
                return json.loads(clean)
            except Exception as e:
                if attempt == 2:
                    return self._fallback_analysis(batch)
                await asyncio.sleep(2)

    def _fallback_analysis(self, batch: list[dict]) -> list[dict]:
        results = []
        for r in batch:
            avg_sales   = r.get("avg_daily_sales", 0) or 0
            stock_level = r.get("stock_level", 0) or 0
            days_cover  = (stock_level / avg_sales) if avg_sales > 0 else 999

            if days_cover < 7:
                status      = "critical"
                reorder     = True
                reorder_qty = int(avg_sales * 30)
                recs = [
                    f"Stock will run out in {days_cover:.1f} days — reorder immediately",
                    f"Suggested reorder quantity: {reorder_qty} units (30-day buffer)",
                    "Consider emergency supplier contact to reduce lead time"
                ]
            elif days_cover < 14:
                status      = "understock"
                reorder     = True
                reorder_qty = int(avg_sales * 21)
                recs = [
                    f"Only {days_cover:.1f} days of stock remaining",
                    f"Reorder {reorder_qty} units to maintain 3-week buffer",
                    "Monitor daily sales closely for demand spikes"
                ]
            else:
                status      = "ok"
                reorder     = False
                reorder_qty = 0
                recs = [
                    f"Stock sufficient for {days_cover:.1f} days",
                    "No immediate action required",
                    "Review monthly to maintain optimal levels"
                ]

            results.append({
                "sku":             r.get("sku"),
                "status":          status,
                "reorder":         reorder,
                "reorder_qty":     reorder_qty,
                "recommendations": recs,
            })
        return results