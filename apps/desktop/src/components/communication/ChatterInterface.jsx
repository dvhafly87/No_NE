import { useState } from "react"
import Chat from '../communication/Chat.jsx';
import Settings from '../interface/Settings.jsx';
import '../../css/MainInterface.css';

export default function ChatterInterface({ theme, setTheme }) {
    const [settingsOpen, setSettingsOpen] = useState(false);

    return (
        <>
            <Chat
                theme={theme}
                setTheme={setTheme}
                onSettingsOpen={() => setSettingsOpen(prev => !prev)}
            />

            <div 
                className={`settings-overlay ${settingsOpen ? "open" : ""}`}
                onClick={() => setSettingsOpen(false)}
            />

            <div className={`settings-panel ${settingsOpen ? "open" : ""}`}>
                <Settings
                    theme={theme}
                    setTheme={setTheme}
                    onClose={() => setSettingsOpen(false)}
                />
            </div>
        </>
    )
}