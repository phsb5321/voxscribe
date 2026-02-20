from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AudioFileSchema(BaseModel):
    original_filename: str
    format: str
    size_bytes: int
    duration_seconds: float | None


class UploadResponse(BaseModel):
    job_id: UUID
    status: str
    redirect_url: str


class JobStatusResponse(BaseModel):
    job_id: UUID
    status: str
    progress_percent: int
    language: str
    engine_name: str
    audio_file: AudioFileSchema | None
    created_at: datetime
    updated_at: datetime
    error_message: str | None


class TranscriptionResultResponse(BaseModel):
    job_id: UUID
    full_text: str
    language: str
    engine_name: str
    processing_duration_seconds: float


class ProgressEvent(BaseModel):
    status: str
    progress_percent: int


class HealthResponse(BaseModel):
    status: str
    engine: str
    redis: str
