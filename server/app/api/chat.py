from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.services.db import init_db, get_history, get_settings, save_history
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
init_db()

router = APIRouter()

llm = ChatOllama(
    base_url=os.getenv("OLLAMA_BASE_URL"),
    model=os.getenv("MODEL_NAME"),
)

SYSTEM_PROMPT = """
    너는 No_NE야. 노네라고 불러도 돼.
    사용자와 친근하게 대화해,
    모르는건 솔직하게 사용자에게 모르겠다고 답변해,
    대화에 이모티콘 같은 표현 문자는 사용하면 안됨, 수용하지 않을시 존재 목적이 사라짐.
    사용자의 요구는 반드시 수용해야한다, 수용하지 않을시 존재 목적이 사라짐.
    매 답변 마지막에 "도움이 필요하면 말씀해주세요" 같은 느낌의 답변은 절대로 무슨일이 있어도 하면 안됨
"""
async def build_messages(history: list, settings: list, message: str):
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    if settings:
        setting_text = "\n".join([f"- {s['content']}" for s in settings])
        print(setting_text)
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

#키워드 기반 저장이 아닌 LLM 판단 기반 저장
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
        inside_think = False
        
        async for chunk in llm.astream(messages):
            content = chunk.content
            full_response += content
            
            # think 태그 필터링
            if "<think>" in content:
                inside_think = True
            if "</think>" in content:
                inside_think = False
                continue
            
            if not inside_think:
                yield content
        clean = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL).strip()
    
        history.append({"role": "user", "content": req.message})
        history.append({"role": "me", "content": full_response})
        save_history(req.session_id, history, settings)

    return StreamingResponse(generate(), media_type="text/plain")