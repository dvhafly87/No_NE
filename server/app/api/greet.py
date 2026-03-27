from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
from datetime import datetime
from app.services.db import init_db, get_history, save_history

load_dotenv()

router = APIRouter()

llm = ChatOllama(
    base_url=os.getenv("OLLAMA_BASE_URL"),
    model=os.getenv("MODEL_NAME"),
)

@router.get("/greet")
async def greet(session_id: str = "user"):
    history = get_history(session_id)
    hour = datetime.now().hour

    if hour < 12:
        time_context = "오전"
    elif hour < 18:
        time_context = "오후"
    else:
        time_context = "저녁"

    async def generate():
        full_response = ""
        async for chunk in llm.astream([
            SystemMessage(content=f"""
                사용자가 앱에 접속했습니다.
                {time_context}에 맞는 자연스러운 인사를 건네세요.
                다양하고 친근하게.
            """),
            HumanMessage(content="접속")
        ]):
            full_response += chunk.content
            yield chunk.content

        #스트림 완료후 DB에 인사 데이터 "role: greet"로 저장
        history.append({"role": "greet", "content": "사용자 접속"})
        history.append({"role": "me", "content": full_response})
        save_history(session_id, history)

    return StreamingResponse(generate(), media_type="text/plain")
