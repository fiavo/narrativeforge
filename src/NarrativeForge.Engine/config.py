from pathlib import Path

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    model_config = {"env_prefix": "NF_"}

    host: str = "127.0.0.1"
    port: int = 8000
    projects_dir: Path = Path("projects")
    database_url: str = "sqlite+aiosqlite:///narrativeforge.db"
    default_model: str = "llama-3-8b"
    max_context_tokens: int = 4096
    temperature: float = 0.7


config = Config()
