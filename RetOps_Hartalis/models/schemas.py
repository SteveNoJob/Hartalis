#input/output data shapes
from pydantic import BaseModel, EmailStr

from typing import Optional, List

class ForecastRequest(BaseModel):
    session_id: str
    structured_data: str        
    context: Optional[str] = None   # ET provides this (calendar/weather)

# What frontend gets back
class DailyPrediction(BaseModel):
    day: int
    date: str
    predicted_units: float

class ProductForecast(BaseModel):
    product_name: str
    daily_predictions: List[DailyPrediction]
    weekly_total: float
    confidence: str
    reasoning: str

class ForecastResponse(BaseModel):
    forecast: List[ProductForecast]
    overall_insight: str
    parse_error: bool = False

# Reorder request
class ReorderRequest(BaseModel):
    session_id: str
    forecast: List[ProductForecast]    
    inventory_data: Optional[str] = None  
    budget: Optional[float] = None

# What-if request
class WhatIfRequest(BaseModel):
    session_id: str
    scenario: str              
    structured_data: str
    current_forecast: Optional[str] = None

# Chat message
class ChatRequest(BaseModel):
    session_id: str
    message: str
    conversation_history: List[dict]    # full history for context
    data_context: str        

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False