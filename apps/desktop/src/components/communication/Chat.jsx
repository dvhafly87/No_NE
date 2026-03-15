import { useState, useRef, useEffect } from "react"
import API from '../../config/ApiConfig.js'

import '../../css/Chat.css';

const API_URL = API.API_BASE_URL
const SESSION_ID = API.SESSION_ID

export default function ChattingInterface({ theme, setTheme }) {
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState("")
    const [isStreaming, setIsStreaming] = useState(false)
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

    const toggleTheme = () => {
        const newTheme = theme === "dark" ? "light" : "dark"
        setTheme(newTheme)
        localStorage.setItem("theme", newTheme)
    }

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
                <button onClick={toggleTheme}>
                    {theme === "dark" ? "☀️" : "🌙"}
                </button>
            </div>
        </div>
    )
}
