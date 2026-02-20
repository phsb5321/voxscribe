import logging
import os
import time
from uuid import UUID

from app.domain.entities.transcription_result import TranscriptionResult
from app.domain.services.chunking_strategy import (
    add_overlap,
    compute_chunk_boundaries,
    needs_chunking,
    stitch_transcriptions,
)
from app.domain.value_objects.job_status import JobStatus
from app.ports.audio_converter import AudioConverterPort
from app.ports.audio_storage import AudioStoragePort
from app.ports.job_repository import JobRepositoryPort
from app.ports.transcription_engine import TranscriptionEnginePort

logger = logging.getLogger(__name__)


class ProcessTranscriptionUseCase:
    def __init__(
        self,
        repository: JobRepositoryPort,
        storage: AudioStoragePort,
        converter: AudioConverterPort,
        engine: TranscriptionEnginePort,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._converter = converter
        self._engine = engine

    def execute(self, job_id: UUID) -> None:
        start_time = time.time()

        job = self._repository.get_job(job_id)
        if job is None:
            logger.error(f"Job {job_id} not found")
            return

        try:
            # PENDING → CONVERTING
            job.transition_to(JobStatus.CONVERTING)
            self._repository.save_job(job)
            logger.info(f"Job {job_id}: PENDING → CONVERTING")

            # Get the audio file and resolve absolute path
            audio_file = self._repository.get_audio_file(job.audio_file_id)
            if audio_file is None:
                raise ValueError(f"Audio file {job.audio_file_id} not found")

            absolute_input_path = self._storage.get_absolute_path(audio_file.storage_path)

            # Build converted WAV path
            converted_path = audio_file.storage_path.rsplit(".", 1)[0] + "_converted.wav"
            absolute_converted_path = self._storage.get_absolute_path(converted_path)

            # Convert to 16kHz mono WAV
            self._converter.convert_to_wav(absolute_input_path, absolute_converted_path)
            logger.info(f"Job {job_id}: Converted audio to WAV")

            # Update AudioFile with converted path and duration
            duration = self._converter.get_duration_seconds(absolute_converted_path)
            audio_file.converted_path = converted_path
            audio_file.duration_seconds = duration
            self._repository.create_audio_file(audio_file)

            # CONVERTING → TRANSCRIBING (progress 50%)
            job.transition_to(JobStatus.TRANSCRIBING)
            job.update_progress(50)
            self._repository.save_job(job)
            logger.info(f"Job {job_id}: CONVERTING → TRANSCRIBING (50%)")

            # Transcribe — with chunking for long files
            duration_ms = int(duration * 1000)
            full_text = self._transcribe_audio(
                job_id, absolute_converted_path, job.language, duration_ms
            )
            logger.info(f"Job {job_id}: Transcription complete")

            # Create TranscriptionResult entity
            processing_duration = time.time() - start_time
            result = TranscriptionResult(
                job_id=job.id,
                full_text=full_text,
                language=job.language,
                engine_name=job.engine_name,
                processing_duration_seconds=processing_duration,
            )
            self._repository.save_result(result)

            # Transition → COMPLETED (progress 100%)
            job.transition_to(JobStatus.COMPLETED)
            job.update_progress(100)
            self._repository.save_job(job)
            logger.info(f"Job {job_id}: TRANSCRIBING → COMPLETED (100%)")

        except Exception as e:
            logger.exception(f"Job {job_id} failed: {e}")
            job.fail(str(e))
            self._repository.save_job(job)

            # Attempt retry if under the limit
            if job.retry_count < 3:
                try:
                    job.retry()
                    self._repository.save_job(job)
                    logger.info(
                        f"Job {job_id}: Scheduled retry {job.retry_count}/3"
                    )
                except Exception as retry_error:
                    logger.error(
                        f"Job {job_id}: Retry failed: {retry_error}"
                    )

    def _transcribe_audio(
        self,
        job_id: UUID,
        audio_path: str,
        language: str,
        duration_ms: int,
    ) -> str:
        """Transcribe audio, splitting into chunks for long files."""
        if not needs_chunking(duration_ms):
            return self._engine.transcribe(audio_path, language)

        logger.info(f"Job {job_id}: Audio is {duration_ms}ms — chunking enabled")

        # Detect silence boundaries and compute chunk regions
        silence_segments = self._converter.detect_silence_boundaries(audio_path)
        boundaries = compute_chunk_boundaries(silence_segments, duration_ms)
        boundaries = add_overlap(boundaries)

        logger.info(f"Job {job_id}: Split into {len(boundaries)} chunks")

        # Split audio into chunk files
        chunk_paths = self._converter.split_at_boundaries(audio_path, boundaries)

        # Transcribe each chunk
        chunk_texts: list[str] = []
        for i, chunk_path in enumerate(chunk_paths):
            logger.info(f"Job {job_id}: Transcribing chunk {i+1}/{len(chunk_paths)}")
            text = self._engine.transcribe(chunk_path, language)
            chunk_texts.append(text)

            # Clean up temp chunk file
            try:
                os.unlink(chunk_path)
            except OSError:
                pass

        # Stitch chunk transcriptions together
        return stitch_transcriptions(chunk_texts)
