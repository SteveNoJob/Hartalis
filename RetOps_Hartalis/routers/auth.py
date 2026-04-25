from fastapi import APIRouter, HTTPException, Depends, Request, Response
from services.auth_service import create_access_token, verify_token, hash_password, verify_password, get_user_from_token, generate_reset_token, get_reset_expiry
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from models.schemas import RegisterRequest, LoginRequest, UpdateProfileRequest, ResetRequest, ResetConfirmRequest
from sqlalchemy.orm import Session
from database.connection import get_db
from models.user import User
from services.email_service import send_reset_email
from datetime import datetime

# For file upload
from fastapi import File, UploadFile
import shutil
import os
from uuid import uuid4

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
    existing = db.query(User).filter(User.email == data.email).first()

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
    
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "username": current_user.username,
        "gender": current_user.gender,
        "region": current_user.region,
        "profile_image": current_user.profile_image
    }
    
@router.put("/profile")
def update_profile(
    data: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    print("Incoming data:", data.dict())
    if data.username is not None:
        current_user.username = data.username

    if data.gender is not None:
        current_user.gender = data.gender

    if data.region is not None:
        current_user.region = data.region

    if data.password:
        current_user.password = hash_password(data.password)

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile updated",
        "user": {
            "email": current_user.email,
            "username": current_user.username,
            "gender": current_user.gender,
            "region": current_user.region
        }
    }

@router.post("/reset")
def reset_password(data: ResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if user:
        token = generate_reset_token()
        expiry = get_reset_expiry()

        user.reset_token = token
        user.reset_token_expiry = expiry

        db.commit()

        send_reset_email(user.email, token)

    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/reset-confirm")
def reset_confirm(data: ResetConfirmRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == data.token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    if user.reset_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

    # update password
    user.password = hash_password(data.new_password)

    # clear token
    user.reset_token = None
    user.reset_token_expiry = None

    db.commit()

    return {"message": "Password reset successful"}

@router.post("/upload-avatar")
def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # generate unique filename
    ext = file.filename.split(".")[-1]
    filename = f"{uuid4()}.{ext}"

    filepath = os.path.join("uploads", filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # save path in DB
    current_user.profile_image = f"/uploads/{filename}"
    db.commit()

    return {"profile_image": current_user.profile_image}