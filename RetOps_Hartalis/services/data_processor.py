import os
import json
import asyncio
import pandas as pd
from dataclasses import dataclass


FILE_PATHS = {
    "sales": "./data/iowrt_3d.csv",  # temp: using test dataset directly
}


def safe_read(name: str) -> pd.DataFrame:
    path = FILE_PATHS.get(name)
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"No file found for '{name}' at {path}")
    return pd.read_csv(path) if path.endswith(".csv") else pd.read_excel(path)


async def detect_columns(df: pd.DataFrame) -> dict:
    from services.glm_client import glm_client

    sample  = df.head(5).to_dict(orient="records")
    columns = df.columns.tolist()

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


async def smart_load(name: str, required: list[str]) -> pd.DataFrame:
    df      = safe_read(name)
    mapping = await detect_columns(df)

    print(f"[{name}] GLM column mapping: {mapping}")

    df = df.rename(columns=mapping)
    df.columns = df.columns.str.lower().str.strip()

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"[{name}] missing required columns: {missing}. Got: {list(df.columns)}"
        )

    return df.dropna(subset=required)


@dataclass
class InventoryData:
    sales:     pd.DataFrame
    stock:     pd.DataFrame | None
    forecasts: pd.DataFrame | None
    suppliers: pd.DataFrame | None


class DataProcessor:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir

    async def load_all(self) -> InventoryData:
        # only sales is compulsory — everything else is optional
        sales = await smart_load("sales", required=["sku", "quantity"])

        return InventoryData(
            sales     = sales,
            stock     = None,   # teammate's data, not available yet
            forecasts = None,   # teammate's forecast, not available yet
            suppliers = None,
        )

    def build_sku_summary(self, data: InventoryData) -> pd.DataFrame:
        # aggregate: avg monthly sales per SKU
        avg_sales = (
            data.sales
            .groupby("sku")["quantity"]
            .mean()
            .reset_index()
            .rename(columns={"quantity": "avg_daily_sales"})
        )

        # these are assumed values — clearly labelled
        return avg_sales.assign(
            stock_level    = avg_sales["avg_daily_sales"] * 14,  # assume 2-week stock
            forecast       = avg_sales["avg_daily_sales"] * 30,  # assume 30-day forecast
            lead_time_days = 7,                                   # assumed
            supplier_name  = "unknown",                           # no supplier data yet
        )

    def to_json_records(self, df: pd.DataFrame) -> list[dict]:
        return df.where(pd.notnull(df), None).to_dict(orient="records")