from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from services.pipeline import InventoryPipeline
from services.data_processor import DataProcessor
from services.inventory_prompts import INVENTORY_SYSTEM_PROMPT, build_user_prompt
from services.chat_service import chat_with_inventory
from services.glm_client import glm_client
from models.inventory import InventoryResult, InventorySummary, ChatMessage
from models.schemas import ChatRequest
from database.connection import get_db
import os

router = APIRouter()


@router.post("/upload")
async def upload_and_run(
    sales:   UploadFile = File(...),
    stock:   UploadFile = File(None),
    db:      Session    = Depends(get_db),
):
    os.makedirs("./data", exist_ok=True)

    if not sales.filename.endswith((".csv", ".xlsx")):
        raise HTTPException(400, "sales: only .csv or .xlsx accepted")
    sales_ext  = os.path.splitext(sales.filename)[1]
    sales_path = f"./data/sales{sales_ext}"
    with open(sales_path, "wb") as f:
        f.write(await sales.read())

    stock_path = None
    if stock and stock.filename:
        if not stock.filename.endswith((".csv", ".xlsx")):
            raise HTTPException(400, "stock: only .csv or .xlsx accepted")
        stock_ext  = os.path.splitext(stock.filename)[1]
        stock_path = f"./data/stock{stock_ext}"
        with open(stock_path, "wb") as f:
            f.write(await stock.read())

    processor = DataProcessor(sales_path=sales_path, stock_path=stock_path)

    try:
        data       = await processor.load_all()
        summary_df = processor.build_sku_summary(data)
    except Exception as e:
        raise HTTPException(422, f"Data processing failed: {str(e)}")

    pipeline = InventoryPipeline()
    results  = await pipeline.run(summary_df)

    db.query(InventoryResult).filter_by(user_id=1).delete()
    db.query(InventorySummary).filter_by(user_id=1).delete()

    for r in results:
        if "error" not in r:
            db.add(InventoryResult(
                user_id         = 1,
                sku             = r["sku"],
                status          = r["status"],
                reorder         = r["reorder"],
                reorder_qty     = r["reorder_qty"],
                recommendations = r["recommendations"],
            ))

    for _, row in summary_df.iterrows():
        db.add(InventorySummary(
            user_id         = 1,
            sku             = row["sku"],
            avg_daily_sales = row["avg_daily_sales"],
            stock_level     = row["stock_level"],
            forecast        = row["forecast"],
            lead_time_days  = row["lead_time_days"],
            supplier_name   = row["supplier_name"],
        ))

    db.commit()

    ai_summary = "\n".join(
        f"SKU {r['sku']}: status={r['status']}, reorder={r['reorder']}, qty={r['reorder_qty']}"
        for r in results if "error" not in r
    )
    user_prompt = build_user_prompt(
        ai_summary    = ai_summary,
        date_range    = "latest upload",
        total_revenue = "N/A",
    )
    try:
        report = await glm_client.call(
            system_prompt = INVENTORY_SYSTEM_PROMPT,
            user_prompt   = user_prompt,
            temperature   = 0.3,
        )
    except Exception:
        report = "Report generation failed — try again later"

    return JSONResponse(content={
        "status":  "ok",
        "user_id": 1,
        "results": results,
        "report":  report,
    })


@router.post("/chat")
async def chat(
    body: ChatRequest,
    db:   Session = Depends(get_db),
):
    response = await chat_with_inventory(
        user_id      = 1,
        user_message = body.message,
        db           = db,
    )
    return JSONResponse(content={"reply": response})


@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
):
    results = db.query(InventoryResult).filter_by(user_id=1).all()
    summary = db.query(InventorySummary).filter_by(user_id=1).all()
    history = db.query(ChatMessage).filter_by(user_id=1).order_by(ChatMessage.id).all()

    return {
        "results": [
            {
                "sku": r.sku, "status": r.status,
                "reorder": r.reorder, "reorder_qty": r.reorder_qty,
                "recommendations": r.recommendations,
            } for r in results
        ],
        "summary": [
            {
                "sku": s.sku, "avg_daily_sales": s.avg_daily_sales,
                "stock_level": s.stock_level, "forecast": s.forecast,
            } for s in summary
        ],
        "chat_history": [
            {"role": m.role, "content": m.content}
            for m in history
        ],
    }