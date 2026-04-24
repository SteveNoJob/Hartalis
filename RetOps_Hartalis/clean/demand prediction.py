import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from zai import ZaiClient
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from database.base import Base
from database.connection import SessionLocal, engine
from models.user import User
from models.transaction import Transaction

# 1. Initialize App and Configuration
app = FastAPI(title="Demand Prediction API with Zai SDK")
Base.metadata.create_all(bind=engine)

load_dotenv()
api_key = os.getenv("ZAI_API_KEY")
base_url = os.getenv("ZAI_BASE_URL")
# Initialize the SDK Client
client = ZaiClient(api_key=api_key, base_url=base_url)

# 2. Define Data Models
class DemandPredictionRequest(BaseModel):
    user_id: int = Field(..., description="User ID to forecast demand for.")
    horizon_value: int = Field(..., ge=1, description="How far ahead to forecast.")
    horizon_unit: str = Field(..., description="One of: day, month, year.")


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
    """Helper from your data.py to safely extract JSON from model responses."""
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
    
    # Check for list array instead of dict (since our forecast returns a list)
    first_bracket = cleaned.find("[")
    last_bracket = cleaned.rfind("]")
    
    # Use array boundaries if they exist and wrap the whole thing
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        if first_brace == -1 or first_bracket < first_brace:
            return cleaned[first_bracket:last_bracket + 1]

    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return cleaned[first_brace:last_brace + 1]
    return cleaned

# 3. The Reasoning Engine Logic
def ask_zai_for_prediction(historical_data: dict, horizon_days: int, current_date_myt: str) -> list:
    """Calls the Zai SDK to generate demand forecasts based on time-series data."""
    
    # 1. The System Prompt: Define Persona, Rules, and Formatting
    system_prompt = """You are an expert supply chain and demand forecasting AI. 
    Your task is to analyze historical transaction data and predict future demand.

    CRITICAL INSTRUCTIONS:
    1. Identify trends, seasonality, and recent anomalies (spikes/drops).
    2. Factor in the current date and timeframe to anticipate upcoming seasonal shifts.
    3. If historical data is sparse or zero, reflect this with a low confidence score.
    4. You must output ONLY a valid JSON array. Do not wrap the JSON in markdown code blocks or add conversational text.

    EXPECTED JSON SCHEMA:
    [
    {
        "item_name": "string",
        "ai_reasoning": "string (Explain your step-by-step logic, referencing the numbers BEFORE giving the prediction)",
        "predicted_quantity": integer (The final forecasted number),
        "confidence_score": float (0.0 to 1.0)
    }
    ]"""

        # 2. The User Prompt: Inject dynamic data and Timezone Context
    user_input = f"""
        Current Date (Malaysia Time / UTC+8): {current_date_myt}
        Forecast Horizon: Next {horizon_days} days.

        Historical Data (Grouped by Year-Month):
        {json.dumps(historical_data, indent=2)}

        Generate the demand forecast JSON array now:
        """

    try:
        response = client.chat.completions.create(
            model="ilmu-glm-5.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.1, # Keep low for deterministic, analytical outputs
            # top_p=0.9, # Optional: uncomment if the model gets stuck in repetitive loops
            response_format={"type": "json_object"}
        )

        raw_response = response.choices[0].message.content
        print(f"\n--- RAW AI RESPONSE ---\n{raw_response}\n-----------------------\n")
        
        if not raw_response:
             raise ValueError("The AI returned an empty response.")

        cleaned_response = extract_json_payload(raw_response)
        standardized_json = json.loads(cleaned_response)
        
        # Ensure it returns the list we asked for
        if isinstance(standardized_json, dict) and "predictions" in standardized_json:
            return standardized_json["predictions"]
        elif isinstance(standardized_json, list):
            return standardized_json
        else:
             # Fallback if wrapped in an unexpected dict key
            return list(standardized_json.values())[0] if standardized_json else []

    except Exception as e:
        print(f"Error in Forecasting Engine: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI Engine failed to generate a forecast: {str(e)}"
        )

# 4. The API Endpoint
@app.post("/api/v1/predict-demand")
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
    
        # 1. Set the timezone to Malaysia
        myt_tz = ZoneInfo("Asia/Kuala_Lumpur")
        current_time_myt = datetime.now(myt_tz)
        current_date_myt_str = current_time_myt.strftime("%Y-%m-%d %H:%M:%S") # Pass this to the AI
        
        future_time_myt = current_time_myt + timedelta(days=horizon_days)
        future_timestamp = future_time_myt.strftime("%Y-%m-%d %H:%M:%S")

        # Prepare Time-Series Data for the AI
        ai_payload = defaultdict(lambda: defaultdict(int))
        
        for row in user_transactions:
            key = (row.item_name or "").strip()
            if not key:
                continue
                
            # Grouping by Year-Month. Assuming your model uses `timestamp` based on data.py
            if hasattr(row, 'timestamp') and row.timestamp:
                period = row.timestamp.strftime("%Y-%m")
            else:
                period = "unknown_date"
                
            ai_payload[key][period] += int(row.quantity or 0)

        if not ai_payload:
            raise HTTPException(status_code=422, detail="No valid item data to process.")

        # Let the Zai SDK act as the reasoning engine
        ai_predictions = ask_zai_for_prediction(
            historical_data=ai_payload, 
            horizon_days=horizon_days,
            current_date_myt=  current_date_myt_str
        )

        # Enrich AI data with static system data
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
            "predictions": final_predictions,
        }
    finally:
        db.close()
#uvicorn "demand prediction:app" --reload

# #{
#   "user_id": 1,
#   "horizon_value": 2,
#   "horizon_unit": "month"
# }