from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.db import get_settings
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

router = APIRouter()

llm = ChatOllama(
    base_url=os.getenv("OLLAMA_BASE_URL"),
    model=os.getenv("MODEL_NAME"),
)

@router.get("/greet")
async def greet(session_id: str = "user"):
    settings = get_settings(session_id)
    setting_text = "\n".join([f"- {s['content']}" for s in settings]) if settings else ""
    hour = datetime.now().hour

    if hour < 12:
        time_context = "오전"
    elif hour < 18:
        time_context = "오후"
    else:
        time_context = "저녁"

    async def generate():
        async for chunk in llm.astream([
            SystemMessage(content=f"""
                사용자가 앱에 접속했습니다.
                {time_context}에 맞는 자연스러운 인사를 건네세요.
                짧고 친근하게.
                {f'[사용자 정보]{chr(10)}{setting_text}' if setting_text else ''}
            """),
            HumanMessage(content="접속")
        ]):
            yield chunk.content

    return StreamingResponse(generate(), media_type="text/plain")