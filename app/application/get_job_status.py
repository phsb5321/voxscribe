from uuid import UUID

from app.application.dto import AudioFileInfo, JobStatusResponse, TranscriptionResultResponse
from app.ports.job_repository import JobRepositoryPort


class GetJobStatusUseCase:
    def __init__(self, repository: JobRepositoryPort) -> None:
        self._repository = repository

    def execute(self, job_id: UUID) -> JobStatusResponse | None:
        job = self._repository.get_job(job_id)
        if job is None:
            return None

        audio_file = self._repository.get_audio_file(job.audio_file_id)
        audio_info = None
        if audio_file:
            audio_info = AudioFileInfo(
                original_filename=audio_file.original_filename,
                format=audio_file.format.value,
                size_bytes=audio_file.size_bytes,
                duration_seconds=audio_file.duration_seconds,
            )

        return JobStatusResponse(
            job_id=job.id,
            status=job.status.value,
            progress_percent=job.progress_percent,
            language=job.language,
            engine_name=job.engine_name,
            audio_file=audio_info,
            created_at=job.created_at,
            updated_at=job.updated_at,
            error_message=job.error_message,
        )

    def get_result(self, job_id: UUID) -> TranscriptionResultResponse | None:
        result = self._repository.get_result_for_job(job_id)
        if result is None:
            return None

        return TranscriptionResultResponse(
            job_id=result.job_id,
            full_text=result.full_text,
            language=result.language,
            engine_name=result.engine_name,
            processing_duration_seconds=result.processing_duration_seconds,
        )
