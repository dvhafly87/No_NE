import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../../../no_ne.db")
FINETUNE_DIR = os.path.join(os.path.dirname(__file__), "../../../docs/finetune/auto")


#.db 파일 자동 생성
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            history    TEXT DEFAULT '[]',
            settings   TEXT DEFAULT '[]',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

#파일에서 사용자와의 대화 내역 가져오기
def get_history(session_id: str) -> list:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT history FROM sessions WHERE session_id = ?",
        (session_id,)
    ).fetchone()
    conn.close()
    return json.loads(row[0]) if row else []

def export_finetune_chunk(history: list):
    
    #폴더 없으면 생성
    os.makedirs(FINETUNE_DIR, exist_ok=True)

    # history 전체를 messages 형식으로 변환
    messages = []
    for turn in history:
        role = "user" if turn["role"] == "user" else "assistant"
        messages.append({
            "role": role,
            "content": turn["content"]
        })

    # 50턴(=25쌍) 단위로 슬라이딩 윈도우로 자르기
    session_size = 50  # 메시지 기준 (user+assistant 합산)
    chunks = []
    for i in range(0, len(messages), session_size):
        chunk_messages = messages[i:i + session_size]
        if len(chunk_messages) >= 2:  # 최소 1쌍 이상
            chunks.append({"messages": chunk_messages})

    turn_count = len(history) // 2
    start = ((turn_count // 50) - 1) * 50 + 1
    end = start + 49
    filename = os.path.join(FINETUNE_DIR, f"turn_{start}_{end}.json")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

#새 대화 내역 저장
def save_history(session_id: str, history: list):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO sessions (session_id, history, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(session_id) DO UPDATE SET
            history = excluded.history,
            updated_at = CURRENT_TIMESTAMP
    """, (session_id, json.dumps(history, ensure_ascii=False)))
    conn.commit()
    conn.close()

    turn_count = len(history) // 2
    if turn_count % 50 == 0 and turn_count > 0:
        export_finetune_chunk(history)