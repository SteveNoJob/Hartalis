from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from routers import auth

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(auth.router, prefix="/auth")