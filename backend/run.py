"""Inicia FastAPI usando el puerto configurado en .env."""

import uvicorn

from backend.config import BACKEND_PORT


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=BACKEND_PORT,
        reload=True,
    )
