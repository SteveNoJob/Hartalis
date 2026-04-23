import os
import json
import asyncio
import pandas as pd
from dataclasses import dataclass


FILE_PATHS = {
    "sales":     "./data/iowrt_3d.csv",
    "stock":     "./data/iowrt_3d.csv",
    "forecasts": "./data/iowrt_3d.csv",
    "suppliers": "./data/iowrt_3d.csv",
}


def safe_read(name: str) -> pd.DataFrame:
    path = FILE_PATHS.get(name)
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"No file found for '{name}' at {path}")
    if path.endswith(".csv"):
        return pd.read_csv(path)
    else:
        return pd.read_excel(path)


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
- Return ONLY valid JSON like: {"series": "sku", "sales": "quantity", "volume": "stock_level"}
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
            f"{name} is missing required columns: {missing}. "
            f"Got: {list(df.columns)}"
        )

    df = df.dropna(subset=required)
    return df


@dataclass
class InventoryData:
    sales:     pd.DataFrame
    stock:     pd.DataFrame
    forecasts: pd.DataFrame
    suppliers: pd.DataFrame


class DataProcessor:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir

    async def load_all(self) -> InventoryData:
        sales = await smart_load("sales", required=["sku", "quantity"])
        return InventoryData(
            sales     = sales,
            stock     = sales,
            forecasts = sales,
            suppliers = sales,
        )

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