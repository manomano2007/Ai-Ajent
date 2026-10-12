import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

DEFAULT_FRONTEND_ORIGIN = "http://localhost:5173"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"


@dataclass(frozen=True)
class Settings:
    frontend_origin: str
    groq_model: str


def get_settings() -> Settings:
    return Settings(
        frontend_origin=os.getenv("FRONTEND_ORIGIN", DEFAULT_FRONTEND_ORIGIN),
        groq_model=os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL),
    )


def groq_api_key_configured() -> bool:
    return bool(os.getenv("GROQ_API_KEY", "").strip())