from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from routers import auth
from database.connection import engine
from database.base import Base
from models import user, transaction  # import models so SQLAlchemy registers them

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # your React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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