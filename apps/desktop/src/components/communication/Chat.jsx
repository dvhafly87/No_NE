import { useState, useRef, useEffect } from "react"
import API from '../../config/ApiConfig.js'

import '../../css/Chat.css';


const API_URL = API.API_BASE_URL
const SESSION_ID = API.SESSION_ID

export default function ChattingInterface({ theme, setTheme, onSettingsOpen }) {
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState("")
    const [isStreaming, setIsStreaming] = useState(false)
    const [showTuneAlert, setShowTuneAlert] = useState(false)

    const bottomRef = useRef(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [messages])

    useEffect(() => {
        const greet = async () => {
            setMessages([{ role: "ai", content: "" }])
            const res = await fetch(`${API_URL}/greet?session_id=${SESSION_ID}`)
            const reader = res.body.getReader()
            const decoder = new TextDecoder()

            while (true) {
                const { done, value } = await reader.read()
                if (done) break
                const chunk = decoder.decode(value)
                setMessages(prev => {
                    const updated = [...prev]
                    updated[0] = {
                        role: "ai",
                        content: updated[0].content + chunk
                    }
                    return updated
                })
            }
        }
        greet()
    }, [])

    const sendMessage = async () => {
        if (!input.trim() || isStreaming) return

        const userMessage = input.trim()
        setInput("")
        setIsStreaming(true)

        setMessages(prev => [...prev, { role: "human", content: userMessage }])
        setMessages(prev => [...prev, { role: "ai", content: "" }])

        try {
            const res = await fetch(`${API_URL}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMessage, session_id: SESSION_ID }),
            })

            const reader = res.body.getReader()
            const decoder = new TextDecoder()

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                const chunk = decoder.decode(value)
                setMessages(prev => {
                    const updated = [...prev]
                    updated[updated.length - 1] = {
                        role: "ai",
                        content: updated[updated.length - 1].content + chunk,
                    }
                    return updated
                })
            }
        } catch (e) {
            console.error(e)
        } finally {
            setIsStreaming(false)

            const turnCount = messages.filter(m => m.role === "human").length + 1
            if (turnCount % 50 === 0) {

                // 백엔드에 알림
                await fetch(`${API_URL}/finetune/ready`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ session_id: SESSION_ID, turn_count: turnCount })
                })

                // 프론트에 알림 표시
                setShowTuneAlert(true)
            }
        }
    }

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }

    return (
        <div className="chat-container" style={{ display: "flex", flexDirection: "column", height: "100vh", fontFamily: "sans-serif" }}>
            {/* 상단 헤더 추가 */}
            <div style={{
                padding: "15px 20px",
                borderBottom: "1px solid #ccc",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center"
            }}>
                <h3 style={{ margin: 0 }}>No_NE</h3>
                <span style={{ fontSize: "0.85rem", background: "#eee", padding: "4px 8px", borderRadius: "12px", color: "#333" }}>
                    대화 기록: {messages.filter(m => m.role === "human").length} Turns
                </span>
                <button onClick={onSettingsOpen} style={{ padding: "6px 12px", borderRadius: "8px", border: "none", cursor: "pointer" }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="3" />
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
                    </svg>
                </button>
            </div>
            {/* 메시지 목록 */}
            <div style={{ flex: 1, overflowY: "auto", padding: "20px" }}>
                {messages.map((msg, i) => (
                    <div
                        key={i}
                        style={{
                            display: "flex",
                            justifyContent: msg.role === "human" ? "flex-end" : "flex-start",
                            marginBottom: "12px"
                        }}
                    >
                        <div
                            style={{
                                maxWidth: "60%",
                                padding: "10px 14px",
                                borderRadius: "12px",
                                background: msg.role === "human" ? "#0084ff" : "#f0f0f0",
                                color: msg.role === "human" ? "#fff" : "#000",
                                whiteSpace: "pre-wrap"
                            }}
                        >
                            {msg.content || "▋"}
                        </div>
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>

            {/* 입력창 */}
            <div style={{ padding: "10px", borderTop: "1px solid #ccc", display: "flex", gap: "8px" }}>
                <textarea
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="메시지를 입력하세요..."
                    rows={2}
                    style={{ flex: 1, resize: "none", padding: "8px", borderRadius: "8px", border: "1px solid #ccc" }}
                />
                <button
                    onClick={sendMessage}
                    disabled={isStreaming}
                    style={{ padding: "0 16px", borderRadius: "8px" }}
                >
                    {isStreaming ? "..." : "전송"}
                </button>
            </div>
        </div>
    )
}
