from fastapi import APIRouter
from app.services.db import get_history

router = APIRouter()

@router.get("/setting/check")
async def check_settings(session_id: str):
    history = get_history(session_id)
    for s in history:
        print(f"- {s['content']}")
    return { "has_settings": len(history) > 0 }