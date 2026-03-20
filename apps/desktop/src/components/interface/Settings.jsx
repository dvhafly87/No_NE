import '../../css/Settings.css';

export default function Settings({ theme, setTheme, onClose }) {
    return (
        <div className="settings">
            <span className="setting-header">
                <h2>설정</h2>
                <button onClick={onClose}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="3" />
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
                    </svg>
                </button>
            </span>
            <div style={{ marginTop: "20px" }}>
                <h3>테마 설정</h3>
                <button onClick={() => setTheme("light")} style={{ padding: "6px 12px", borderRadius: "8px", marginRight: "10px" }}>
                    라이트 테마
                </button>
                <button onClick={() => setTheme("dark")} style={{ padding: "6px 12px", borderRadius: "8px" }}>
                    다크 테마
                </button>
            </div>
            <div style={{ marginTop: "20px" }}>
                <h3>기타 설정</h3>
                <p>추후 추가될 설정 옵션들...</p>
            </div>
        </div>
    )
}   