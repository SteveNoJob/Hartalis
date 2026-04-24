from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database.base import Base


class InventoryResult(Base):
    __tablename__ = "inventory_results"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"))
    sku             = Column(String)
    status          = Column(String)
    reorder         = Column(Boolean)
    reorder_qty     = Column(Float)
    recommendations = Column(JSON)
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class InventorySummary(Base):
    __tablename__ = "inventory_summary"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"))
    sku             = Column(String)
    avg_daily_sales = Column(Float)
    stock_level     = Column(Float)
    forecast        = Column(Float)
    lead_time_days  = Column(Float)
    supplier_name   = Column(String)
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ChatMessage(Base):
    __tablename__ = "inventory_chat_messages"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"))
    role       = Column(String)
    content    = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))