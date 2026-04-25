import json
import os
import sys
from fastapi import FastAPI, HTTPException, status, UploadFile, File
from pydantic import BaseModel, ValidationError, model_validator
from typing import Optional
import pandas as pd
import io
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from fastapi import APIRouter

# Assuming 'zai' is your custom SDK or wrapper. 
# (Note: If you are using the official Zhipu AI SDK, it would be 'from zhipuai import ZhipuAI')
from zai import ZaiClient

# Ensure sibling modules (database/models) are importable even when
# running uvicorn from inside the clean/ directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from database.base import Base
from database.connection import SessionLocal, engine
from models.user import User  # Ensure users table is registered in metadata.
from models.transaction import Transaction

# 1. Initialize App and Client
router = APIRouter() # title="Data Intelligence Layer"

# Ensure required tables exist when this app runs standalone.
Base.metadata.create_all(bind=engine)
# Load the variables from the .env file into the system environment
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Fetch the variables using os.getenv
api_key = os.getenv("ZAI_API_KEY")
base_url = os.getenv("ZAI_BASE_URL")
# Initialize your client
client = ZaiClient(api_key=api_key, base_url=base_url)


# 2. Define Data Models (for Request & AI Validation)
class RawDataRequest(BaseModel):
    raw_content: str
    file_type: str = "Text/Log"
    source_system: Optional[str] = "Manual Entry"
    user_id: Optional[int] = None

# --- NEW: STRICT AI GATEKEEPER SCHEMAS ---
class TransactionItem(BaseModel):
    transaction_id: Optional[str] = None
    timestamp: str  # Validated as string to match YYYY-MM-DD format rule
    item_name: str
    quantity: int
    unit_price: float
    total_value: float
    currency: str = "MYR"

    @model_validator(mode='after')
    def validate_math(self) -> 'TransactionItem':
        """Prevents Math Hallucinations by ensuring total_value matches quantity * unit_price"""
        expected_total = self.quantity * self.unit_price
        # Check if total_value is within 1 cent of the calculation (handles float imprecision)
        if abs(self.total_value - expected_total) > 0.01:
            raise ValueError(f"Math mismatch: {self.quantity} * {self.unit_price} != {self.total_value}")
        return self

class AIResponseSchema(BaseModel):
    transactions: list[TransactionItem]
# -----------------------------------------


def parse_timestamp(value: Optional[str]) -> datetime:
    if not value:
        return datetime.utcnow()
    try:
        # Supports "YYYY-MM-DD HH:MM:SS" and ISO formats.
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return datetime.utcnow()


def extract_json_payload(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # Fallback for model responses that include extra commentary.
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return cleaned[first_brace:last_brace + 1]
    return cleaned


def persist_transactions(cleaned_data: dict, user_id: Optional[int] = None) -> int:
    db: Session = SessionLocal()
    try:
        for item in cleaned_data["transactions"]:
            row = Transaction(
                # Placeholder: frontend can send user_id in request payload later.
                user_id=user_id,
                transaction_id=item.get("transaction_id"),
                timestamp=parse_timestamp(item.get("timestamp")),
                item_name=item.get("item_name", ""),
                quantity=int(item.get("quantity", 0) or 0),
                unit_price=float(item.get("unit_price", 0.0) or 0.0),
                total_value=float(item.get("total_value", 0.0) or 0.0),
                currency=item.get("currency", "MYR"),
            )
            db.add(row)

        db.commit()
        return len(cleaned_data["transactions"])
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store transactions: {str(e)}"
        )
    finally:
        db.close()

# 3. The Reasoning Engine Logic
def transform_transaction_data(raw_content: str, file_type: str, max_retries: int = 3) -> Optional[dict]:
    """
    Uses GLM 5.1 to reason through messy retailer data and output a standardized JSON.
    Includes an automated self-correction loop and strict Pydantic validation.
    """
    system_prompt = """
    You are a Data Intelligence Engine. Your task is to parse raw retail transaction 
    records and transform them into a strict JSON object. 
    
    Target Schema:
    {
        "transactions": [
            {
                "transaction_id": "string or null",
                "timestamp": "YYYY-MM-DD HH:MM:SS",
                "item_name": "string",
                "quantity": integer,
                "unit_price": float,
                "total_value": float,
                "currency": "MYR"
            }
        ]
    }

    Strict Rules:
    1. ANTI-HALLUCINATION: Do NOT invent, guess, or generate fake data. 
    2. MISSING DATA: If a specific field (like transaction_id) is entirely missing from the raw input, you MUST set its value to null.
    3. MATH INFERENCE: You are allowed to calculate `total_value` if `quantity` and `unit_price` are provided.
    4. Normalize date formats to ISO standard (YYYY-MM-DD HH:MM:SS).
    5. Output ONLY valid JSON matching the exact schema above.
    """

    attempt = 0
    error_context = ""

    while attempt < max_retries:
        # Append feedback if this is a retry
        retry_suffix = f"\n\nPREVIOUS ERROR: {error_context}\nPlease fix the JSON structure, data types, or math." if error_context else ""
        user_input = f"Format: {file_type}\nRaw Data Content:\n{raw_content}{retry_suffix}"

        try:
            response = client.chat.completions.create(
                model="ilmu-glm-5.1", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.0, # Deterministic setting for data extraction
                response_format={"type": "json_object"}
            )

            # 1. Extract the raw text response
            raw_response = response.choices[0].message.content
            
            # ---> DEBUG: Print exactly what the AI said to the terminal <---
            print(f"\n--- RAW AI RESPONSE (Attempt {attempt+1}) ---\n{raw_response}\n-----------------------\n")

            if not raw_response:
                 raise ValueError("The AI returned an empty response.")

            # 2. Extract JSON safely even if model adds extra text.
            cleaned_response = extract_json_payload(raw_response)
                
            # 3. Now parse it safely into a Python dictionary
            data_dict = json.loads(cleaned_response)

            # 4. STRICT PYDANTIC VALIDATION (The Gatekeeper)
            validated_data = AIResponseSchema(**data_dict)
            
            # If we reach here, the data is 100% clean and verified
            return validated_data.model_dump()

        except (ValidationError, json.JSONDecodeError, ValueError) as e:
            attempt += 1
            error_context = str(e)
            print(f"Error in Reasoning Engine - Attempt {attempt} failed: {error_context}")
            
    # If we exhaust all retries, return None to trigger the graceful error state
    return None

# 4. The API Endpoints
@router.post("/api/v1/ingest-transaction")
async def ingest_transaction(request: RawDataRequest):
    """
    Endpoint to receive messy data, clean it via GLM, and store it.
    """
    # Step A: Clean the data via GLM 5.1 with strict gatekeeping
    cleaned_data = transform_transaction_data(request.raw_content, request.file_type)
    
    # Step B: Graceful Error State (Hard Rejection)
    if not cleaned_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail={
                "code": "AI_CONFIDENCE_LOW",
                "message": "AI Engine failed to parse the data into the correct schema after multiple attempts. Transaction rejected to protect database integrity."
            }
        )
        
    print("parse completed")
    # Step C: Store in SQLite via SQLAlchemy
    persist_transactions(cleaned_data, request.user_id)
    
    return {
        "status": "success",
        "message": "Data cleaned and stored successfully.",
        "processed_records": len(cleaned_data["transactions"]),
        "data": cleaned_data
    }

@router.post("/api/v1/ingest-file")
async def ingest_file(file: UploadFile = File(...)):
    """
    Endpoint to upload an Excel or CSV file, read it, and send it to the AI engine.
    """
    # 1. Validate file type
    filename = (file.filename or "").lower()
    if not filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file format. Please upload a CSV or Excel file."
        )

    try:
        # 2. Read the file into memory
        contents = await file.read()
        
        # 3. Use Pandas to convert the file into a structured DataFrame
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
            
        # 4. Convert the data to a raw string format for the AI
        raw_string_data = df.to_csv(index=False)
        
        # 5. Send it to your existing AI Reasoning function!
        cleaned_data = transform_transaction_data(raw_string_data, f"Uploaded File: {file.filename}")
        
        # 6. Graceful Error State (Hard Rejection)
        if not cleaned_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail={
                    "code": "AI_CONFIDENCE_LOW",
                    "message": "AI Engine failed to securely parse the uploaded file. Processing aborted."
                }
            )

        # Placeholder until frontend sends user_id for file ingest flow.
        persist_transactions(cleaned_data, user_id=None)
            
        return {
            "status": "success",
            "message": f"Processed {file.filename} successfully.",
            "processed_records": len(cleaned_data["transactions"]),
            "data": cleaned_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    #uvicorn data:app --reload