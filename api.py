import asyncio
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import chat_with_gemini, debug_secure_code, persist_result, summarize_security_text


def load_env_file():
    env_path = Path(".env")
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()

api = FastAPI(title="CyberGuard AI API")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    text: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@api.get("/")
def health_check():
    return {"status": "ok", "service": "CyberGuard AI API"}


@api.post("/summarize")
async def summarize(payload: AnalyzeRequest):
    result = await asyncio.to_thread(summarize_security_text, payload.text)
    await asyncio.to_thread(persist_result, "summary", payload.text, result)
    return result


@api.post("/debug-code")
async def debug_code(payload: AnalyzeRequest):
    result = await asyncio.to_thread(debug_secure_code, payload.text)
    await asyncio.to_thread(persist_result, "code-debug", payload.text, result)
    return result


@api.post("/chat")
async def chat(payload: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in payload.messages]
    return await asyncio.to_thread(chat_with_gemini, messages)
