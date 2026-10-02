import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str = "gsk_your_actual_key_here"
    groq_model: str = "llama-3.3-70b-versatile"
    groq_temperature: float = 0.25
    groq_max_tokens: int = 2000

    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_persist_dir: str = "./app/data/chroma"
    sqlite_path: str = "./app/data/resumepilot.db"

    candidate_json_path: str = "./app/data/candidate.json"
    prompts_dir: str = "./prompts"
    dna_dir: str = "./dna"
    templates_dir: str = "./templates"

    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
