import logging
import os
from uuid import UUID

from app.application.dto import SubmitTranscriptionRequest, SubmitTranscriptionResponse
from app.domain.entities.audio_file import AudioFile
from app.domain.entities.transcription_job import TranscriptionJob
from app.domain.services.audio_validator import validate_audio_file
from app.ports.audio_storage import AudioStoragePort
from app.ports.job_queue import JobQueuePort
from app.ports.job_repository import JobRepositoryPort

logger = logging.getLogger(__name__)


class SubmitTranscriptionUseCase:
    def __init__(
        self,
        storage: AudioStoragePort,
        repository: JobRepositoryPort,
        queue: JobQueuePort,
        engine_name: str,
    ) -> None:
        self._storage = storage
        self._repository = repository
        self._queue = queue
        self._engine_name = engine_name

    def execute(self, request: SubmitTranscriptionRequest) -> SubmitTranscriptionResponse:
        # Validate file format and size
        audio_format = validate_audio_file(request.filename, len(request.file_data))

        # Store file
        storage_path = self._storage.store(request.filename, request.file_data)

        # Create AudioFile entity
        audio_file = AudioFile(
            original_filename=request.filename,
            format=audio_format,
            size_bytes=len(request.file_data),
            storage_path=storage_path,
        )
        self._repository.create_audio_file(audio_file)

        # Create TranscriptionJob
        job = TranscriptionJob(
            audio_file_id=audio_file.id,
            language=request.language,
            engine_name=self._engine_name,
        )
        self._repository.save_job(job)

        # Enqueue for background processing
        self._queue.enqueue(job.id)

        logger.info(f"Submitted transcription job {job.id} for {request.filename}")

        return SubmitTranscriptionResponse(
            job_id=job.id,
            status=job.status.value,
            redirect_url=f"/jobs/{job.id}",
        )
