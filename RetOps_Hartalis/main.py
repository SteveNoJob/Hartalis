from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from routers import auth
from database.connection import engine
from database.base import Base
from models import user
from services.data_processor import DataProcessor
from services.pipeline import InventoryPipeline

app = FastAPI()
processor = DataProcessor()

# database setup
Base.metadata.create_all(bind=engine)

# auth routes
app.include_router(auth.router, prefix="/auth")

# inventory routes
@app.post("/run")
async def run_pipeline():
    try:
        data       = await processor.load_all()       # ← add await
        summary_df = processor.build_sku_summary(data)
    except Exception as e:
        raise HTTPException(422, f"Data processing failed: {str(e)}")

    pipeline = InventoryPipeline()
    results  = await pipeline.run(summary_df)

    return JSONResponse(content={"status": "ok", "results": results})