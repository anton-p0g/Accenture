"""Configuración local del backend."""

import os
from pathlib import Path

from dotenv import load_dotenv


RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ_PROYECTO / ".env")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b").strip() or "qwen3:4b"

BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
if not 1 <= BACKEND_PORT <= 65535:
    raise ValueError("BACKEND_PORT debe estar entre 1 y 65535")
