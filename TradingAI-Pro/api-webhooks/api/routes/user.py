from fastapi import APIRouter
from api.core.user_manager import list_users

router = APIRouter()

@router.get("/list")
async def list_all():
    return {"users": list_users()}
