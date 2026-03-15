import { useEffect, useState } from "react"
import API from '../../config/ApiConfig.js'
import logo from '../../img/No_NE_Nuke.png'
import '../../css/Splash.css'

export default function Splash({ onDone }) {
  const [error, setError] = useState(false)
  const [transitioning, setTransitioning] = useState(false)

  const init = async () => {
    setError(false)
    try {
      const [_, res] = await Promise.all([
        new Promise(resolve => setTimeout(resolve, 3000)),
        Promise.race([
          fetch(`${API.API_BASE_URL}/health`).then(() =>
            fetch(`${API.API_BASE_URL}/setting/check?session_id=${API.SESSION_ID}`)
          ),
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error("timeout")), 5000)
          )
        ])
      ])

      setTransitioning(true)
      setTimeout(() => onDone("chat"), 500)
    } catch (e) {
      console.error(e.message === "timeout" ? "타임아웃" : "서버 연결 실패")
      setError(true)
    }
  }

  useEffect(() => {
    init()
  }, [])

  return (
    <div className={`splash-container ${transitioning ? "fade-out" : ""}`}>
      <div className="splash-ring-wrapper">

        {/* 회전 그라디언트 링 */}
        <div className={`splash-ring ${error ? "error" : ""}`} />

        {/* 원형 내부 */}
        <div className="splash-inner">
          <img src={logo} alt="No_NE" className="splash-logo" />

          {error ? (
            <>
              <p className="splash-error-text">
                중요 프로그램이 다운되었습니다<br />
                재실행 후 다시 시도해주세요
              </p>
              <button className="splash-retry-btn" onClick={init}>
                RETRY
              </button>
            </>
          ) : (
            <div className="splash-loading-text">
              LOADING
              <span className="splash-dots">
                <span>.</span>
                <span>.</span>
                <span>.</span>
              </span>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}