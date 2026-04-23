from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Ensure sibling modules are importable when running from clean/ directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from database.base import Base
from database.connection import SessionLocal, engine
from models.user import User
from models.transaction import Transaction

app = FastAPI(title="Demand Prediction API")
Base.metadata.create_all(bind=engine)


class DemandPredictionRequest(BaseModel):
    user_id: int = Field(..., description="User ID to forecast demand for.")
    horizon_value: int = Field(..., ge=1, description="How far ahead to forecast.")
    horizon_unit: str = Field(..., description="One of: day, month, year.")


def horizon_to_days(value: int, unit: str) -> int:
    normalized = unit.strip().lower()
    if normalized in {"day", "days"}:
        return value
    if normalized in {"month", "months"}:
        return value * 30
    if normalized in {"year", "years"}:
        return value * 365
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="horizon_unit must be one of: day, month, year",
    )


def estimate_confidence(sample_size: int) -> float:
    # Simple confidence heuristic based on how many transactions exist per item.
    if sample_size >= 30:
        return 0.9
    if sample_size >= 10:
        return 0.75
    if sample_size >= 3:
        return 0.6
    return 0.45


@app.post("/api/v1/predict-demand")
async def predict_demand(request: DemandPredictionRequest):
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"user_id {request.user_id} does not exist",
            )

        user_transactions = (
            db.query(Transaction)
            .filter(Transaction.user_id == request.user_id)
            .all()
        )
        if not user_transactions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No transactions found for user_id {request.user_id}",
            )

        horizon_days = horizon_to_days(request.horizon_value, request.horizon_unit)
        future_timestamp = (datetime.utcnow() + timedelta(days=horizon_days)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        grouped = defaultdict(lambda: {"total_qty": 0, "count": 0})
        for row in user_transactions:
            key = (row.item_name or "").strip()
            if not key:
                continue
            grouped[key]["total_qty"] += int(row.quantity or 0)
            grouped[key]["count"] += 1

        if not grouped:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="User transactions exist but contain no valid item_name values.",
            )

        predictions = []
        for item_name, stats in grouped.items():
            avg_per_transaction = stats["total_qty"] / max(stats["count"], 1)
            # Lightweight forecast: average quantity per transaction scaled by horizon.
            predicted_quantity = max(1, int(round(avg_per_transaction * horizon_days)))
            predictions.append(
                {
                    "item_name": item_name,
                    "predicted_quantity": predicted_quantity,
                    "confidence_score": estimate_confidence(stats["count"]),
                    "based_on_transactions": stats["count"],
                    "future_timestamp": future_timestamp,
                }
            )

        predictions.sort(key=lambda x: x["predicted_quantity"], reverse=True)

        return {
            "status": "success",
            "user_id": request.user_id,
            "forecast_horizon": {
                "value": request.horizon_value,
                "unit": request.horizon_unit.lower(),
                "days_equivalent": horizon_days,
            },
            "predictions": predictions,
        }
    finally:
        db.close()