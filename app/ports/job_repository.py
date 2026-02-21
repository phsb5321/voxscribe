from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.audio_file import AudioFile
from app.domain.entities.transcription_job import TranscriptionJob
from app.domain.entities.transcription_result import TranscriptionResult
from app.domain.value_objects.job_status import JobStatus


class JobRepositoryPort(ABC):
    @abstractmethod
    def save_job(self, job: TranscriptionJob) -> None:
        """Save or update a transcription job."""

    @abstractmethod
    def create_audio_file(self, audio_file: AudioFile) -> None:
        """Persist a new audio file record."""

    @abstractmethod
    def save_result(self, result: TranscriptionResult) -> None:
        """Save a transcription result."""

    @abstractmethod
    def get_job(self, job_id: UUID) -> TranscriptionJob | None:
        """Get a job by ID, or None if not found."""

    @abstractmethod
    def get_jobs_by_status(self, status: JobStatus) -> list[TranscriptionJob]:
        """Get all jobs with the given status."""

    @abstractmethod
    def get_result_for_job(self, job_id: UUID) -> TranscriptionResult | None:
        """Get the result for a completed job, or None."""

    @abstractmethod
    def get_audio_file(self, audio_file_id: UUID) -> AudioFile | None:
        """Get an audio file by ID, or None if not found."""

    @abstractmethod
    def get_all_jobs(self, limit: int = 50, offset: int = 0) -> list[TranscriptionJob]:
        """Get all jobs, ordered by most recent first."""

    @abstractmethod
    def delete_all_jobs(self) -> int:
        """Delete all jobs, results, and audio file records. Return count of deleted jobs."""
