import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import debug_secure_code, summarize_security_text


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


@api.get("/")
def health_check():
    return {"status": "ok", "service": "CyberGuard AI API"}


@api.post("/summarize")
def summarize(payload: AnalyzeRequest):
    return summarize_security_text(payload.text)


@api.post("/debug-code")
def debug_code(payload: AnalyzeRequest):
    return debug_secure_code(payload.text)
