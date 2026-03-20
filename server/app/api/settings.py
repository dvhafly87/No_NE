from fastapi import APIRouter
from app.services.db import get_settings

router = APIRouter()

@router.get("/setting/check")
async def check_settings(session_id: str):
    settings = get_settings(session_id)
    for s in settings:
        print(f"- {s['content']}")
    return { "has_settings": len(settings) > 0 }