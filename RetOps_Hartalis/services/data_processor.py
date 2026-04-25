import os
import json
import pandas as pd
from dataclasses import dataclass


def safe_read(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"No file found at '{path}' — upload a sales file first")
    return pd.read_csv(path) if path.endswith(".csv") else pd.read_excel(path)


async def detect_columns(df: pd.DataFrame) -> dict:
    import asyncio

    # fallback mapping for common column names — no GLM needed
    fallback = {}
    col_lower = {c.lower(): c for c in df.columns}
    
    for canon, variants in {
        "sku":        ["sku", "series", "product", "item", "name", "product_name", "item_name", "id"],
        "quantity":   ["quantity", "sales", "volume", "units", "qty", "amount", "sold"],
        "date":       ["date", "timestamp", "time", "period", "month"],
        "stock_level":["stock", "stock_level", "current_stock", "inventory"],
    }.items():
        for v in variants:
            if v in col_lower:
                fallback[col_lower[v]] = canon
                break

    if "sku" in fallback.values() and "quantity" in fallback.values():
        print(f"[detect_columns] Using fallback mapping: {fallback}")
        return fallback

    # only call GLM if fallback didn't find required columns
    from services.glm_client import glm_client
    sample  = df.head(5).to_dict(orient="records")
    columns = df.columns.tolist()

    for attempt in range(3):
        try:
            raw = await glm_client.call(
                system_prompt="""You are a data schema analyst.
Given column names and sample data, map each column to one of these canonical names:
sku, quantity, date, stock_level, forecast, lead_time_days, supplier_name.

Rules:
- Each raw column maps to at most one canonical name
- Each canonical name is used at most once
- If a column doesn't clearly map to any canonical name, omit it
- Return ONLY valid JSON like: {"series": "sku", "sales": "quantity"}
- No extra text, no markdown""",
                user_prompt=f"Columns: {columns}\nSample data: {json.dumps(sample, default=str)}",
                temperature=0.0,
            )
            clean = raw.strip().removeprefix("```json").removesuffix("```").strip()
            return json.loads(clean)
        except Exception as e:
            if attempt == 2:
                raise ValueError(f"Column detection failed after 3 attempts: {str(e)}")
            await asyncio.sleep(3)

async def smart_load(path: str, required: list[str]) -> pd.DataFrame:
    df      = safe_read(path)
    mapping = await detect_columns(df)

    print(f"[smart_load] GLM column mapping: {mapping}")

    df = df.rename(columns=mapping)
    df.columns = df.columns.str.lower().str.strip()

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}. Got: {list(df.columns)}"
        )

    return df.dropna(subset=required)


@dataclass
class InventoryData:
    sales: pd.DataFrame
    stock: pd.DataFrame | None


class DataProcessor:
    def __init__(self, sales_path: str | None = None, stock_path: str | None = None):
        self.sales_path = sales_path
        self.stock_path = stock_path

    async def load_all(self) -> InventoryData:
        if not self.sales_path:
            raise ValueError("sales_path is required — upload a sales file first")
        sales = await smart_load(self.sales_path, required=["sku", "quantity"])
        stock = None
        if self.stock_path:
            stock = await smart_load(self.stock_path, required=["sku", "stock_level"])
        return InventoryData(sales=sales, stock=stock)

    def build_sku_summary(self, data: InventoryData) -> pd.DataFrame:
        avg_sales = (
            data.sales
            .groupby("sku")["quantity"]
            .mean()
            .reset_index()
            .rename(columns={"quantity": "avg_daily_sales"})
        )
        return avg_sales.assign(
            stock_level    = avg_sales["avg_daily_sales"] * 14,
            forecast       = avg_sales["avg_daily_sales"] * 30,
            lead_time_days = 7,
            supplier_name  = "unknown",
        )

    def to_json_records(self, df: pd.DataFrame) -> list[dict]:
        return df.where(pd.notnull(df), None).to_dict(orient="records")