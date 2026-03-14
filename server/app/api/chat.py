from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.services.db import init_db, get_history, get_settings, save_history
import os
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
    상대방이 소통하는 언어에 맞춰 대화하세요.
"""

#프롬프트 튜닝 파트 => 영구 기억 설정 + 사용자 리퀘스트 + 최근 대화 50개 + 50개 이전 옛날 대화 10개 + 시스템 기본 프롬프트
async def build_messages(history: list, settings: list, message: str):
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    
    #저장된 영구설정 정보 추가
    if settings:
        setting_text = "\n".join([f"- {s['content']}" for s in settings])
        messages.append(SystemMessage(content=f"[기억해야 할 사용자 정보]\n{setting_text}"))


    # 1. 최근 50개 (단기 기억)
    recent_history = history[-50:]

    # 2. 현재 질문과 관련된 오래된 대화 검색 (장기 기억)
    old_history = history[:-50]  # 50개 이전 대화
    related = [
        h for h in old_history
        if any(word in h["content"] for word in message.split())
    ]

    # 관련 대화 + 최근 대화 합쳐서 전달
    for h in related[-10:]:  # 관련된 것 최대 10개
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

async def should_save(message: str) -> bool:
    judge = await llm.ainvoke([
        SystemMessage(content="""
            사용자 메시지에 영구적으로 기억해야 할
            개인정보나 설정이 있으면 yes
            일반 대화면 no
            yes 또는 no 만 답할 것
        """),
        HumanMessage(content=message)
    ])
    return "yes" in judge.content.strip().lower()

class ChatRequest(BaseModel):
    message: str
    session_id: str = "user"

@router.post("/chat")
async def chat_stream(req: ChatRequest):
    history = get_history(req.session_id)
    settings = get_settings(req.session_id)

    # LLM이 영구 저장 판단
    if await should_save(req.message):
        settings.append({"content": req.message})

    # await 추가
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