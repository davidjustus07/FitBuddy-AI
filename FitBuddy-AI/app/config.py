from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


DEMO_MODE = _bool_env("DEMO_MODE", True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/fitbuddy.db").strip()
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",") if x.strip()]


def database_path() -> Path:
    """Return the SQLite path used by the app."""
    prefix = "sqlite:///"
    raw = DATABASE_URL[len(prefix):] if DATABASE_URL.startswith(prefix) else DATABASE_URL
    path = Path(raw)
    if not path.is_absolute():
        path = BASE_DIR / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
