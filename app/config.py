import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    transcription_engine: str = field(
        default_factory=lambda: os.environ.get("TRANSCRIPTION_ENGINE", "faster-whisper")
    )
    openai_api_key: str = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY", "")
    )
    redis_url: str = field(
        default_factory=lambda: os.environ.get("REDIS_URL", "redis://localhost:6379")
    )
    data_dir: str = field(
        default_factory=lambda: os.environ.get("DATA_DIR", "./DATA")
    )
    database_url: str = field(
        default_factory=lambda: os.environ.get(
            "DATABASE_URL", "sqlite:///./DATA/db.sqlite"
        )
    )
    default_language: str = field(
        default_factory=lambda: os.environ.get("DEFAULT_LANGUAGE", "pt-BR")
    )
    max_upload_size_bytes: int = 524_288_000  # 500 MB
    faster_whisper_model: str = field(
        default_factory=lambda: os.environ.get(
            "FASTER_WHISPER_MODEL", "large-v3-turbo"
        )
    )

    @property
    def sqlite_path(self) -> str:
        """Extract the SQLite file path from database_url."""
        url = self.database_url
        if url.startswith("sqlite:///"):
            return url[len("sqlite:///"):]
        return os.path.join(self.data_dir, "db.sqlite")

    @property
    def uploads_dir(self) -> str:
        return os.path.join(self.data_dir, "uploads")


def get_settings() -> Settings:
    return Settings()
