from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.services.db import init_db, get_history, get_settings, save_history
import os
import json
from dotenv import load_dotenv

load_dotenv()
init_db()

router = APIRouter()

llm = ChatOllama(
    base_url=os.getenv("OLLAMA_BASE_URL"),
    model=os.getenv("MODEL_NAME"),
)

SYSTEM_PROMPT = """
   당신은 사용자의 개인 AI 어시스턴트입니다.
   기본 이름은 No_NE이지만
   사용자가 다른 이름을 설정했다면 그 이름을 따릅니다.
   반드시 상대방이 소통하는 언어에 맞춰 대화하세요.
"""

async def build_messages(history: list, settings: list, message: str):
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    if settings:
        setting_text = "\n".join([f"- {s['content']}" for s in settings])
        messages.append(SystemMessage(content=f"[기억해야 할 사용자 정보]\n{setting_text}"))

    recent_history = history[-50:]
    old_history = history[:-50]
    related = [
        h for h in old_history
        if any(word in h["content"] for word in message.split())
    ]

    for h in related[-10:]:
        if h["role"] == "user":
            messages.append(HumanMessage(content=h["content"]))
        else:
            messages.append(AIMessage(content=h["content"]))

    for h in recent_history:
        if h["role"] == "user":
            messages.append(HumanMessage(content=h["content"]))
        else:
            messages.append(AIMessage(content=h["content"]))

    messages.append(HumanMessage(content=message))
    return messages

async def should_save(message: str, settings: list) -> dict:
    existing = "\n".join([f"- {s['content']}" for s in settings])
    judge = await llm.ainvoke([
        SystemMessage(content=f"""
            영구 저장할 정보면 카테고리와 함께 반환
            {{"save": "yes", "category": "카테고리명"}}
            일반 대화면
            {{"save": "no"}}
            JSON으로만 답할 것. 다른 텍스트 절대 금지.
            
            [현재 저장된 설정]
            {existing}
        """),
        HumanMessage(content=message)
    ])
    try:
        return json.loads(judge.content.strip())
    except:
        return {"save": "no"}

class ChatRequest(BaseModel):
    message: str
    session_id: str = "user"

@router.post("/chat")
async def chat_stream(req: ChatRequest):
    history = get_history(req.session_id)
    settings = get_settings(req.session_id)

    result = await should_save(req.message, settings)

    if result.get("save") == "yes":
        category = result.get("category", "기타")
        settings = [s for s in settings if s.get("category") != category]
        settings.append({"category": category, "content": req.message})

    messages = await build_messages(history, settings, req.message)

    async def generate():
        full_response = ""
        async for chunk in llm.astream(messages):
            full_response += chunk.content
            yield chunk.content

        history.append({"role": "user", "content": req.message})
        history.append({"role": "me", "content": full_response})
        save_history(req.session_id, history, settings)

    return StreamingResponse(generate(), media_type="text/plain")