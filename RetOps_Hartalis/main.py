from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from routers import auth
from database.connection import engine
from database.base import Base
from models import user # import models so SQLAlchemy registers them

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(auth.router, prefix="/auth")