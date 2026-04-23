import pandas as pd
from services.pipeline import InventoryPipeline  # ← add services.

class ResultsViewer:
    def __init__(self, results: list[dict]):
        self.df = pd.DataFrame(results)

    def summary(self):
        print("\n=== INVENTORY SUMMARY ===")
        print(self.df[["sku", "status", "reorder", "reorder_qty"]].to_string(index=False))

    def alerts(self):
        flagged = self.df[self.df["status"] != "ok"]
        print(f"\n⚠️  {len(flagged)} SKUs need attention:")
        for _, row in flagged.iterrows():
            print(f"  [{row['status'].upper()}] {row['sku']} — {row['reason']}")

    def reorder_list(self):
        to_reorder = self.df[self.df["reorder"] == True]
        print(f"\n📦 Reorder list ({len(to_reorder)} SKUs):")
        print(to_reorder[["sku", "reorder_qty"]].to_string(index=False))

    def export(self, path: str = "./output/results.csv"):
        self.df.to_csv(path, index=False)
        print(f"\n✅ Exported to {path}")

async def main():
    pipeline = InventoryPipeline()
    results  = await pipeline.run()

    viewer = ResultsViewer(results)
    viewer.summary()
    viewer.alerts()
    viewer.reorder_list()
    viewer.export()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())