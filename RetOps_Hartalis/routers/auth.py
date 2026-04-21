from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

router = APIRouter()
security = HTTPBearer()

# Fake DB (temporary)
users = {
    "admin": {
        "username": "admin",
        "password": "1234"
    }
}

class UserAuth(BaseModel):
    username: str
    password: str

# Fake token generator
def create_token(username: str):
    return f"token-{username}"

def verify_token(token: str):
    if token.startswith("token-"):
        return token.split("-")[1]
    return None

@router.post("/login")
def login(user: UserAuth):
    db_user = users.get(user.username)

    if not db_user or db_user["password"] != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user.username)

    return {"access_token": token}

@router.post("/register")
def register(user: UserAuth):
    if user.username in users:
        raise HTTPException(status_code=400, detail="User already exists")
    
    users[user.username] = {
        "username": user.username,
        "password": user.password
    }
    
    return {"message": "User registered"}

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    username = verify_token(token)

    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    return username


@router.get("/profile")
def profile(user: str = Depends(get_current_user)):
    return {"message": f"Hello {user}"}