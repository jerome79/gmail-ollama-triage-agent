from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    default_model: str = os.getenv("DEFAULT_MODEL", "llama3.1")
    log_path: str = os.getenv("LOG_PATH", "data/triage_runs.jsonl")
    label_prefix: str = os.getenv("LABEL_PREFIX", "AI/")
    max_body_chars: int = int(os.getenv("MAX_BODY_CHARS", "2000"))

SETTINGS = Settings()
