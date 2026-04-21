from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from models.schemas import RegisterRequest, LoginRequest
from sqlalchemy.orm import Session
from database.connection import get_db
from models.user import User
from passlib.context import CryptContext

router = APIRouter()
security = HTTPBearer()

# Fake DB (temporary)
users = {
    "admin": {
        "username": "admin",
        "password": "1234"
    }
}

# Fake token generator
def create_token(username: str):
    return f"token-{username}"

def verify_token(token: str):
    if not token:
        return None
    if token.startswith("token-"):
        return token.split("-")[1]
    return None

pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(password: str):
    return pwd_context.hash(password[:72])

def verify_password(plain, hashed):
    return pwd_context.verify(plain[:72], hashed)

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "message": "Login success",
        "remember_me": data.remember_me
    }

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == data.username).first()

    if existing:
        raise HTTPException(status_code=400, detail="User exists")

    new_user = User(
        username=data.username,
        password=hash_password(data.password)
    )

    db.add(new_user)
    db.commit()

    return {"message": "User created"}

def get_current_user(request: Request):
    token = request.cookies.get("access_token")

    username = verify_token(token)

    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return username


@router.get("/profile")
def profile(user: str = Depends(get_current_user)):
    return {"message": f"Hello {user}"}