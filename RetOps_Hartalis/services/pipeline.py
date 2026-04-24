import asyncio
import json
from services.glm_client import glm_client
from services.data_processor import DataProcessor
import re


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
    def __init__(self, batch_size: int = 20):
        self.batch_size = batch_size
        self.processor  = DataProcessor()

    async def run(self, summary_df=None) -> list[dict]:
        if summary_df is None:
            data       = await self.processor.load_all()
            summary_df = self.processor.build_sku_summary(data)

        records = self.processor.to_json_records(summary_df)
        batches = [
            records[i:i+self.batch_size]
            for i in range(0, len(records), self.batch_size)
        ]

        results = await asyncio.gather(*[self._analyze_batch(b) for b in batches])
        return [item for batch in results for item in batch]

    async def _analyze_batch(self, batch: list[dict]) -> list[dict]:
        prompt = f"Analyze these SKUs and return a JSON array:\n{json.dumps(batch, indent=2)}"
        raw = await glm_client.call(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.0,
        )
        try:
            clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
            return json.loads(clean)
        except json.JSONDecodeError:
            return [{"sku": r.get("sku"), "error": "parse_failed", "raw": raw} for r in batch]