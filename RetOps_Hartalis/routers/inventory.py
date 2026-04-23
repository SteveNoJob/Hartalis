from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from services.pipeline import InventoryPipeline
from services.data_processor import DataProcessor
import os

router = APIRouter()
processor = DataProcessor()

@router.post("/upload")
async def upload_and_run(
    sales:     UploadFile = File(...),
    stock:     UploadFile = File(...),
    forecasts: UploadFile = File(...),
    suppliers: UploadFile = File(...),
):
    os.makedirs("./data", exist_ok=True)

    for name, file in zip(
        ["sales", "stock", "forecasts", "suppliers"],
        [sales, stock, forecasts, suppliers]
    ):
        if not file.filename:
            raise HTTPException(400, f"{name}: no filename provided")
        if not file.filename.endswith((".csv", ".xlsx", ".xls")):
            raise HTTPException(400, f"{name}: only .csv or .xlsx accepted")
        ext = os.path.splitext(file.filename)[1]
        with open(f"./data/{name}{ext}", "wb") as f:
            f.write(await file.read())

    try:
        data       = await processor.load_all()
        summary_df = processor.build_sku_summary(data)
    except Exception as e:
        raise HTTPException(422, f"Data processing failed: {str(e)}")

    pipeline = InventoryPipeline()
    results  = await pipeline.run(summary_df)

    return JSONResponse(content={"status": "ok", "results": results})