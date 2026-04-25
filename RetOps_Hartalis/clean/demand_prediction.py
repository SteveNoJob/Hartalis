import json
import os
import sys
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import Optional
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from fastapi import APIRouter

# Assuming 'zai' is your custom SDK or wrapper.
from zai import ZaiClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from database.base import Base
from database.connection import SessionLocal, engine
from models.user import User
from models.transaction import Transaction

# --- ET's context enrichment ---
from context.context_builder import build_full_context

# 1. Initialize App and Configuration
# app = FastAPI(title="Demand Prediction API with Zai SDK")
router = APIRouter()
Base.metadata.create_all(bind=engine)

load_dotenv()
api_key = os.getenv("ZAI_API_KEY")
base_url = os.getenv("ZAI_BASE_URL")
client = ZaiClient(api_key=api_key, base_url=base_url)

# 2. Define Data Models
class DemandPredictionRequest(BaseModel):
    user_id: int = Field(..., description="User ID to forecast demand for.")
    horizon_value: int = Field(..., ge=1, description="How far ahead to forecast.")
    horizon_unit: str = Field(..., description="One of: day, month, year.")
    # --- NEW: optional what-if scenario from frontend ---
    scenario: Optional[str] = None  # e.g., "What if it rains heavily tomorrow?"

# --- STRICT AI GATEKEEPER SCHEMAS (CS's original — unchanged) ---
class PredictionItem(BaseModel):
    item_name: str
    ai_reasoning: str
    predicted_quantity: int
    confidence_score: float

    @model_validator(mode='after')
    def validate_logic(self) -> 'PredictionItem':
        if self.predicted_quantity < 0:
            raise ValueError(f"predicted_quantity cannot be negative for {self.item_name}.")
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError(f"confidence_score must be between 0.0 and 1.0.")
        return self

class AIPredictionResponse(BaseModel):
    predictions: list[PredictionItem]
# -----------------------------------------


def horizon_to_days(value: int, unit: str) -> int:
    normalized = unit.strip().lower()
    if normalized in {"day", "days"}: return value
    if normalized in {"month", "months"}: return value * 30
    if normalized in {"year", "years"}: return value * 365
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="horizon_unit must be one of: day, month, year",
    )

def extract_json_payload(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return cleaned[first_brace:last_brace + 1]
    return cleaned


# 3. The Reasoning Engine Logic
# ============================================================
# CHANGED: Added `context_str` parameter — ET's context injection
# ============================================================
def ask_zai_for_prediction(
    historical_data: dict,
    horizon_days: int,
    current_date_myt: str,
    context_str: str = "",      # <-- ET's context goes here
    max_retries: int = 3,
) -> Optional[list]:
    """Calls the Zai SDK to generate demand forecasts based on time-series data + context."""

    # ============================================================
    # CHANGED: Updated system prompt to reference context
    # ============================================================
    system_prompt = """You are an expert supply chain and demand forecasting AI.
Your task is to analyze historical transaction data and predict future demand.

CRITICAL INSTRUCTIONS:
1. Identify trends, seasonality, and recent anomalies (spikes/drops).
2. Factor in the current date and timeframe to anticipate upcoming seasonal shifts.
3. You will receive a CONTEXT section with Malaysian calendar events, weather forecasts,
   retail trends, and anomaly alerts. USE THIS CONTEXT to adjust your predictions.
   For example: if Hari Raya is in 5 days, increase cooking essentials forecast.
   If heavy rain is expected, reduce walk-in traffic estimates.
4. If historical data is sparse or zero, reflect this with a low confidence score.
5. In your ai_reasoning, explicitly reference which context signals affected your prediction.
6. You must output ONLY a valid JSON object matching the exact schema below.

EXPECTED JSON SCHEMA:
{
    "predictions": [
        {
            "item_name": "string",
            "ai_reasoning": "string (Reference the CONTEXT — mention holidays, weather, trends that affected this prediction)",
            "predicted_quantity": integer (MUST be 0 or greater),
            "confidence_score": float (0.0 to 1.0)
        }
    ]
}"""

    attempt = 0
    error_context = ""

    while attempt < max_retries:
        retry_suffix = (
            f"\n\nPREVIOUS ERROR: {error_context}\n"
            "Please fix the JSON structure, data types, or logic."
            if error_context else ""
        )

        # ============================================================
        # CHANGED: Inject context_str into the user prompt
        # ============================================================
        user_input = f"""Current Date (Malaysia Time / UTC+8): {current_date_myt}
Forecast Horizon: Next {horizon_days} days.

=== CONTEXT (holidays, weather, trends, anomalies) ===
{context_str if context_str else "No additional context available."}

=== HISTORICAL DATA (Grouped by Year-Month) ===
{json.dumps(historical_data, indent=2)}

Generate the demand forecast JSON now.{retry_suffix}
"""

        try:
            response = client.chat.completions.create(
                model="ilmu-glm-5.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )

            raw_response = response.choices[0].message.content
            print(f"\n--- RAW AI RESPONSE (Attempt {attempt+1}) ---\n{raw_response}\n-----------------------\n")

            if not raw_response:
                raise ValueError("The AI returned an empty response.")

            cleaned_response = extract_json_payload(raw_response)
            data_dict = json.loads(cleaned_response)

            # THE GATEKEEPER: Strict Pydantic Validation (CS's original)
            validated_data = AIPredictionResponse(**data_dict)
            return validated_data.model_dump()["predictions"]

        except (ValidationError, json.JSONDecodeError, ValueError) as e:
            attempt += 1
            error_context = str(e)
            print(f"Error in Forecasting Engine - Attempt {attempt} failed: {error_context}")

    return None


# 4. The API Endpoint
@router.post("/api/v1/predict-demand")
async def predict_demand(request: DemandPredictionRequest):
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_transactions = db.query(Transaction).filter(Transaction.user_id == request.user_id).all()

        if not user_transactions:
            raise HTTPException(status_code=404, detail="No transactions found")

        horizon_days = horizon_to_days(request.horizon_value, request.horizon_unit)

        myt_tz = ZoneInfo("Asia/Kuala_Lumpur")
        current_time_myt = datetime.now(myt_tz)
        current_date_myt_str = current_time_myt.strftime("%Y-%m-%d %H:%M:%S")

        future_time_myt = current_time_myt + timedelta(days=horizon_days)
        future_timestamp = future_time_myt.strftime("%Y-%m-%d %H:%M:%S")

        # Prepare Time-Series Data for the AI (CS's original logic)
        ai_payload = defaultdict(lambda: defaultdict(int))
        for row in user_transactions:
            key = (row.item_name or "").strip()
            if not key:
                continue
            if hasattr(row, 'timestamp') and row.timestamp:
                period = row.timestamp.strftime("%Y-%m")
            else:
                period = "unknown_date"
            ai_payload[key][period] += int(row.quantity or 0)

        if not ai_payload:
            raise HTTPException(status_code=422, detail="No valid item data to process.")

        # ============================================================
        # NEW: Build ET's context string (calendar + weather + trends + anomalies)
        # Also handles what-if scenario if frontend sends one
        # ============================================================
        sales_history = [
            {
                "product_name": row.item_name,   # map item_name → product_name
                "date": row.timestamp.strftime("%Y-%m-%d") if row.timestamp else "unknown",
                "units_sold": int(row.quantity or 0),
            }
            for row in user_transactions
            if row.item_name
        ]

        context_str = await build_full_context(
            sales_history=sales_history,    # now anomaly detection works correctly
            scenario_query=request.scenario,
            include_weather=True,
            city="Kuala Lumpur",
        )
        print(f"\n--- CONTEXT INJECTED ---\n{context_str}\n------------------------\n")

        # ============================================================
        # CHANGED: Pass context_str to the prediction function
        # ============================================================
        ai_predictions = ask_zai_for_prediction(
            historical_data=ai_payload,
            horizon_days=horizon_days,
            current_date_myt=current_date_myt_str,
            context_str=context_str,            # <-- THE KEY LINE
        )

        if not ai_predictions:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "AI_FORECAST_FAILED",
                    "message": "The AI Engine failed to generate a reliable forecast after multiple attempts."
                }
            )

        final_predictions = []
        for pred in ai_predictions:
            pred["future_timestamp"] = future_timestamp
            final_predictions.append(pred)

        final_predictions.sort(key=lambda x: x.get("predicted_quantity", 0), reverse=True)

        return {
            "status": "success",
            "engine": "ilmu-GLM-5.1",
            "user_id": request.user_id,
            "forecast_horizon": {
                "value": request.horizon_value,
                "unit": request.horizon_unit.lower(),
                "days_equivalent": horizon_days,
            },
            # --- NEW: Include what context was used (useful for debugging + demo) ---
            "context_used": context_str[:500] if context_str else None,
            "scenario_applied": request.scenario,
            "predictions": final_predictions,
        }
    finally:
        db.close()

#uvicorn "demand prediction:app" --reload   