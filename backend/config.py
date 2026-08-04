"""Application configuration.

All settings come from environment variables or a local .env file.
The .env file is never committed to git.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str) -> str:
    """Read an env var, falling back to a default value."""
    return os.getenv(name, default)


# LLM provider settings.
# LLM_PROVIDER chooses which API format to use:
#   "openai" - any OpenAI-compatible API (OpenAI, DeepSeek, Groq, OpenRouter).
#   "gemini" - Google Gemini API.
LLM_PROVIDER: str = _get("LLM_PROVIDER", "openai")

# OpenAI-compatible settings.
# Examples for LLM_BASE_URL:
#   OpenAI:     https://api.openai.com/v1
#   DeepSeek:   https://api.deepseek.com/v1
#   Groq:       https://api.groq.com/openai/v1
LLM_BASE_URL: str = _get("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_API_KEY: str = _get("LLM_API_KEY", "")
LLM_MODEL: str = _get("LLM_MODEL", "gpt-4o-mini")
EMBED_MODEL: str = _get("EMBED_MODEL", "text-embedding-3-small")

# Gemini settings.
GEMINI_BASE_URL: str = _get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
GEMINI_API_KEY: str = _get("GEMINI_API_KEY", "")
GEMINI_MODEL: str = _get("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_EMBED_MODEL: str = _get("GEMINI_EMBED_MODEL", "gemini-embedding-001")

# Request limits.
LLM_TIMEOUT_SECONDS: float = float(_get("LLM_TIMEOUT_SECONDS", "120"))
EMBED_BATCH_SIZE: int = int(_get("EMBED_BATCH_SIZE", "32"))

# Storage.
DATA_DIR: str = _get("DATA_DIR", "data")
DB_PATH: str = os.path.join(DATA_DIR, "study.db")
UPLOAD_DIR: str = os.path.join(DATA_DIR, "uploads")

# Allowed uploads.
ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx", ".pptx", ".txt", ".md"}
MAX_UPLOAD_BYTES: int = int(_get("MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))

# Retrieval.
TOP_K: int = int(_get("TOP_K", "5"))
CHUNK_SIZE: int = int(_get("CHUNK_SIZE", "800"))
CHUNK_OVERLAP: int = int(_get("CHUNK_OVERLAP", "100"))


def ensure_dirs() -> None:
    """Create data folders if they do not exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
