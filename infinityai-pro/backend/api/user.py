from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

# Simple in-memory user store (replace with DB)
users = {
    "admin": {"password": "password123", "role": "admin"},
    "user": {"password": "user123", "role": "user"}
}

@router.post("/login")
async def login(request: LoginRequest):
    user = users.get(request.username)
    if user and user["password"] == request.password:
        return {"message": "Login successful", "token": "fake-jwt-token", "role": user["role"]}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/profile")
async def get_profile():
    # Mock profile
    return {"username": "admin", "balance": 12311.19}