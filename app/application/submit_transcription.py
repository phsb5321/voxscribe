import logging
import os
from uuid import UUID

from app.application.dto import (
    SubmitTranscriptionRequest,
    SubmitTranscriptionResponse,
    SubmitUrlTranscriptionRequest,
)
from app.domain.entities.audio_file import AudioFile
from app.domain.entities.transcription_job import TranscriptionJob
from app.domain.exceptions import InvalidUrlError
from app.domain.services.audio_validator import validate_audio_file
from app.domain.services.url_validator import (
    extract_reel_id,
    is_instagram_url,
    validate_instagram_reel_url,
)
from app.domain.value_objects.audio_format import AudioFormat
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

    def execute_from_url(
        self, request: SubmitUrlTranscriptionRequest
    ) -> SubmitTranscriptionResponse:
        # Validate URL with specific messaging
        if not validate_instagram_reel_url(request.url):
            if is_instagram_url(request.url):
                raise InvalidUrlError(
                    "This is an Instagram link but not a reel. "
                    "Only reel URLs are supported (e.g., instagram.com/reel/...)."
                )
            raise InvalidUrlError(
                "Invalid URL. Please provide a valid Instagram reel URL "
                "(e.g., https://www.instagram.com/reel/ABC123/)."
            )

        reel_id = extract_reel_id(request.url) or "unknown"
        filename = f"reel_{reel_id}.mp3"

        # Create stub AudioFile (size/storage populated by worker after download)
        audio_file = AudioFile(
            original_filename=filename,
            format=AudioFormat.MP3,
            size_bytes=0,
            storage_path="",
            source_url=request.url,
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

        logger.info(f"Submitted URL transcription job {job.id} for {request.url}")

        return SubmitTranscriptionResponse(
            job_id=job.id,
            status=job.status.value,
            redirect_url=f"/jobs/{job.id}",
        )
