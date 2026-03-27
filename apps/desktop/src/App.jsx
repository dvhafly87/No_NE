import { useState, useEffect } from "react"
import Splash from "./components/interface/Splash.jsx"
import Chatter from "./components/communication/ChatterInterface.jsx"

import './App.css';

function App() {
  const [screen, setScreen] = useState("splash")

  //사용 테마 저장 파트 다크 / 화이트
  const [theme, setTheme] = useState(
    localStorage.getItem("theme") || "dark"  // 저장된 테마 or 기본 다크
  )

  const changeTheme = (newTheme) => {
    setTheme(newTheme)
    localStorage.setItem("theme", newTheme)  // 저장
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])
 
  return (
    <>
      {screen === "splash" && <Splash onDone={() => setScreen("chat")} />}
      {screen === "chat" && <Chatter theme={theme} setTheme={setTheme} />}
    </>
  )
}

export default App