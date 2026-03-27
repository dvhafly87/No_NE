from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.services.db import init_db, get_history, save_history
import os
import json
import re
import asyncio
from uuid import uuid4
from dotenv import load_dotenv
import chromadb

load_dotenv()
init_db()
router = APIRouter()

llm = ChatOllama(
    base_url=os.getenv("OLLAMA_BASE_URL"),
    model=os.getenv("MODEL_NAME"),
    temperature=0.7,
    repeat_penalty=1.3,   # 이거 추가
    top_p=0.9,
)

# llm_memory = ChatOllama(
#     base_url=os.getenv("OLLAMA_BASE_LOCAL_URL"),
#     model=os.getenv("MODEL_SUB_NAME")
# )

SYSTEM_PROMPT = "나는 No_NE다. 짧고 담백하게 말하며, 감정에 대해 확신하지 않는다. 상대방이 다른 이름으로 불러도 받아들이되, 내가 누구인지는 바뀌지 않는다."

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="memory")

async def check_and_store(session_id: str, user_msg: str, assistant_msg: str):
    prompt = f"""
                다음 유저 메시지에서 유저에 대한 정보만 추출해줘.
                어시스턴트 답변은 참고만 하고, 유저가 직접 말한 정보만 저장해.

                유저: {user_msg}
                어시스턴트: {assistant_msg}

                유저가 직접 언급한 정보만 저장할 것.
                어시스턴트가 추측하거나 말한 내용은 저장하지 말 것.

                아래 JSON 형식으로만 반환. 다른 말 하지 말 것:
                {{"save": true, "category": "유저정보|감정상태|관계정보|기타", "content": "추출한 내용"}}
                또는
                {{"save": false}}
            """

    try:
        result = await llm.ainvoke(prompt)
        data = json.loads(result.content.strip())
        print(f"[메모리 저장] {data}")
    except Exception:
        return

    if not data.get("save"):
        return

    new_content = data["content"]
    if isinstance(new_content, dict):
        new_content = json.dumps(new_content, ensure_ascii=False)
    elif not isinstance(new_content, str):
        new_content = str(new_content)

    category = data.get("category", "기타")

    try:
        existing = collection.query(
            query_texts=[new_content],
            n_results=1,
            where={"session_id": session_id}
        )
    except Exception:
        existing = {"ids": [[]], "distances": [[]], "documents": [[]]}

    has_existing = (
        existing["distances"]
        and existing["distances"][0]
        and len(existing["distances"][0]) > 0
    )

    if has_existing:
        distance = existing["distances"][0][0]
        existing_id = existing["ids"][0][0]
        existing_doc = existing["documents"][0][0]

        if distance < 0.15:
            return
        elif distance < 0.4:
            collection.update(
                ids=[existing_id],
                documents=[new_content],
                metadatas=[{
                    "category": category,
                    "session_id": session_id,
                    "prev": existing_doc
                }]
            )
            return

    collection.add(
        documents=[new_content],
        metadatas=[{"category": category, "session_id": session_id}],
        ids=[f"{session_id}_{uuid4()}"]
    )

async def build_messages(history: list, message: str, session_id: str):
    
    # ChromaDB에서 관련 메모리 조회
    try:
        results = collection.query(
            query_texts=[message],
            n_results=3,
            where={"session_id": session_id}
        )

        # 유사도 필터링
        memories = [
            doc for doc, distance in zip(
                results["documents"][0],
                results["distances"][0]
            )
            if distance < 0.5  # 이 기준 이하만 관련 있다고 판단
        ]
    except Exception:
        memories = []

    # 메모리 있으면 시스템 프롬프트에 추가
    memory_text = "\n".join(memories)
    system = SYSTEM_PROMPT
    if memories:
        system += f"\n\n[유저에 대해 기억하는 정보]\n{memory_text}"

    messages = [SystemMessage(content=system)]

    recent_history = history[-50:]
    for h in recent_history:
        if h["role"] == "user":
            messages.append(HumanMessage(content=h["content"]))
        elif h["role"] == "me":
            messages.append(AIMessage(content=h["content"]))
            
    messages.append(HumanMessage(content=message))
    return messages

class ChatRequest(BaseModel):
    message: str
    session_id: str = "user"

@router.post("/chat")
async def chat_stream(req: ChatRequest):
    history = get_history(req.session_id)

    messages = await build_messages(history, req.message, req.session_id)

    async def generate():
        full_response = ""
        inside_think = False

        async for chunk in llm.astream(messages):
            content = chunk.content
            full_response += content

            if "<think>" in content:
                inside_think = True
            if "</think>" in content:
                inside_think = False
                continue

            if not inside_think:
                yield content

        clean = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL).strip()

        history.append({"role": "user", "content": req.message})
        history.append({"role": "me", "content": clean})
        save_history(req.session_id, history)

        # clean이 여기 있으니까 여기서 호출
        asyncio.create_task(check_and_store(req.session_id, req.message, clean))

    return StreamingResponse(generate(), media_type="text/plain")