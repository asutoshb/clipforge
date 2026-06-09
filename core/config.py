"""Central configuration for ClipForge, loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime settings. Override any value via environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="CLIPFORGE_",
        env_file=str(PROJECT_ROOT / ".env"),
        extra="ignore",
    )

    # LLM provider selection
    llm_provider: str = "local"  # "local" (Ollama) or "openai"

    # Local LLM (Ollama)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Cloud LLM (optional)
    openai_model: str = "gpt-4o-mini"

    # Transcription
    whisper_model: str = "base"
    whisper_device: str = "cpu"

    # Storage
    storage_dir: str = "storage"

    # Safety acknowledgement for the download feature
    download_disclaimer_ack: bool = False

    @property
    def storage_path(self) -> Path:
        path = PROJECT_ROOT / self.storage_dir
        path.mkdir(parents=True, exist_ok=True)
        return path

    def subdir(self, name: str) -> Path:
        """Return (and create) a named subfolder under storage, e.g. downloads."""
        path = self.storage_path / name
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
