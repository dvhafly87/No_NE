import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../../../no_ne.db")

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

def get_settings(session_id: str) -> list:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT settings FROM sessions WHERE session_id = ?",
        (session_id,)
    ).fetchone()
    conn.close()
    return json.loads(row[0]) if row else []

#새 대화 내역 저장
def save_history(session_id: str, history: list, settings: list):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO sessions (session_id, history, settings, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(session_id) DO UPDATE SET
            history = excluded.history,
            settings = excluded.settings,
            updated_at = CURRENT_TIMESTAMP
    """, (session_id, json.dumps(history, ensure_ascii=False),
          json.dumps(settings, ensure_ascii=False)))
    conn.commit()
    conn.close()