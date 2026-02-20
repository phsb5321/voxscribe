from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class SubmitTranscriptionRequest:
    filename: str
    file_data: bytes
    language: str = "pt-BR"


@dataclass(frozen=True)
class SubmitTranscriptionResponse:
    job_id: UUID
    status: str
    redirect_url: str


@dataclass(frozen=True)
class AudioFileInfo:
    original_filename: str
    format: str
    size_bytes: int
    duration_seconds: float | None


@dataclass(frozen=True)
class JobStatusResponse:
    job_id: UUID
    status: str
    progress_percent: int
    language: str
    engine_name: str
    audio_file: AudioFileInfo | None
    created_at: datetime
    updated_at: datetime
    error_message: str | None


@dataclass(frozen=True)
class TranscriptionResultResponse:
    job_id: UUID
    full_text: str
    language: str
    engine_name: str
    processing_duration_seconds: float
