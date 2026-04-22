from fastapi import APIRouter, HTTPException, Depends, Request, Response
from services.auth_service import create_access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from models.schemas import RegisterRequest, LoginRequest
from sqlalchemy.orm import Session
from database.connection import get_db
from models.user import User

from services.auth_service import verify_token

from models.schemas import UpdateProfileRequest
from services.auth_service import hash_password, verify_password, get_user_from_token

router = APIRouter()
security = HTTPBearer()

@router.post("/login")
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # remember_me controls expiry
    expire_minutes = 60 * 24 * 7 if data.remember_me else 60

    token = create_access_token(
        data={"sub": user.email},
        expires_minutes=expire_minutes
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=expire_minutes * 60,
        secure=False,   # set True in production (HTTPS)
        samesite="lax"
    )

    return {"message": "Login successful"}

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == data.username).first()

    if existing:
        raise HTTPException(status_code=400, detail="User exists")

    new_user = User(
        email=data.email.lower(),
        username=data.username,
        password=hash_password(data.password)
    )

    db.add(new_user)
    db.commit()

    return {"message": "User created"}

    
# def get_current_user(request: Request):
#     token = request.cookies.get("access_token")

#     if not token:
#         raise HTTPException(status_code=401, detail="Not authenticated")

#     email = verify_token(token)

#     if not email:
#         raise HTTPException(status_code=401, detail="Invalid token")

#     return email

def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = get_user_from_token(token, db)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")

    return user

@router.get("/profile")
def profile(user: User = Depends(get_current_user)):
    return {"message": f"Hello {user}"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}

# @router.get("/me")
# def get_me(current_user: User = Depends(get_current_user)):
#     return current_user
    
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "username": current_user.username,
        "gender": current_user.gender,
        "region": current_user.region
    }
    
@router.put("/profile")
def update_profile(
    data: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if data.username:
        current_user.username = data.username

    if data.gender:
        current_user.gender = data.gender

    if data.region:
        current_user.region = data.region

    if data.password:
        current_user.password = hash_password(data.password)

    db.commit()
    db.refresh(current_user)

    return {"message": "Profile updated"}