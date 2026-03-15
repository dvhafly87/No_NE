from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.settings import router as settings_router
from app.api.greet import router as greet_router

app = FastAPI(title="No_NE", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(settings_router)
app.include_router(greet_router)

@app.get("/health")
async def health():
    return {"status": "ok", "message": "No_NE server is running"}