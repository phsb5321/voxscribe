"""Composition root: wires concrete adapters to port interfaces."""

import os
from dataclasses import dataclass

from app.adapters.outbound.converter.pydub_converter import PydubAudioConverter
from app.adapters.outbound.engines.faster_whisper_engine import FasterWhisperEngine
from app.adapters.outbound.persistence.sqlite_repository import SQLiteJobRepository
from app.adapters.outbound.queue.rq_queue import RQJobQueue
from app.adapters.outbound.storage.local_file_storage import LocalFileStorage
from app.application.get_job_status import GetJobStatusUseCase
from app.application.process_transcription import ProcessTranscriptionUseCase
from app.application.submit_transcription import SubmitTranscriptionUseCase
from app.config import Settings, get_settings
from app.ports.audio_converter import AudioConverterPort
from app.ports.audio_storage import AudioStoragePort
from app.ports.job_queue import JobQueuePort
from app.ports.job_repository import JobRepositoryPort
from app.ports.transcription_engine import TranscriptionEnginePort


@dataclass
class Container:
    """Holds all wired dependencies."""

    settings: Settings
    repository: JobRepositoryPort
    storage: AudioStoragePort
    converter: AudioConverterPort
    engine: TranscriptionEnginePort
    queue: JobQueuePort
    submit_transcription: SubmitTranscriptionUseCase
    process_transcription: ProcessTranscriptionUseCase
    get_job_status: GetJobStatusUseCase


_container: Container | None = None


def _create_engine(settings: Settings) -> TranscriptionEnginePort:
    engine_name = settings.transcription_engine

    if engine_name == "faster-whisper":
        return FasterWhisperEngine(model_size=settings.faster_whisper_model)
    elif engine_name == "openai":
        from app.adapters.outbound.engines.openai_engine import OpenAIEngine

        return OpenAIEngine(api_key=settings.openai_api_key)
    elif engine_name == "groq":
        from app.adapters.outbound.engines.groq_engine import GroqEngine

        return GroqEngine(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
        )
    else:
        raise ValueError(f"Unknown transcription engine: {engine_name}")


def bootstrap(settings: Settings | None = None) -> Container:
    """Create and wire all dependencies. Returns a Container."""
    global _container

    if _container is not None:
        return _container

    if settings is None:
        settings = get_settings()

    # Ensure data directories exist
    os.makedirs(settings.data_dir, exist_ok=True)
    os.makedirs(settings.uploads_dir, exist_ok=True)

    # Outbound adapters
    repository = SQLiteJobRepository(db_path=settings.sqlite_path)
    storage = LocalFileStorage(base_dir=settings.uploads_dir)
    converter = PydubAudioConverter()
    engine = _create_engine(settings)
    queue = RQJobQueue(redis_url=settings.redis_url)

    # Use cases
    submit_transcription = SubmitTranscriptionUseCase(
        storage=storage,
        repository=repository,
        queue=queue,
        engine_name=engine.engine_name,
    )

    process_transcription = ProcessTranscriptionUseCase(
        repository=repository,
        storage=storage,
        converter=converter,
        engine=engine,
    )

    get_job_status = GetJobStatusUseCase(repository=repository)

    _container = Container(
        settings=settings,
        repository=repository,
        storage=storage,
        converter=converter,
        engine=engine,
        queue=queue,
        submit_transcription=submit_transcription,
        process_transcription=process_transcription,
        get_job_status=get_job_status,
    )

    return _container


def get_container() -> Container:
    """Get the current container, bootstrapping if needed."""
    if _container is None:
        return bootstrap()
    return _container


def reset_container() -> None:
    """Reset the container (for testing)."""
    global _container
    _container = None
