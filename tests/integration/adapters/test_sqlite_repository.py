import pytest
from uuid import uuid4
from datetime import datetime, timezone

from app.adapters.outbound.persistence.sqlite_repository import SQLiteJobRepository
from app.domain.entities.audio_file import AudioFile
from app.domain.entities.transcription_job import TranscriptionJob
from app.domain.entities.transcription_result import TranscriptionResult
from app.domain.value_objects.audio_format import AudioFormat
from app.domain.value_objects.job_status import JobStatus


@pytest.fixture
def repo(tmp_path):
    return SQLiteJobRepository(db_path=str(tmp_path / "test.db"))


def _make_audio_file(**overrides) -> AudioFile:
    defaults = dict(
        id=uuid4(),
        original_filename="recording.mp3",
        format=AudioFormat.MP3,
        size_bytes=1024,
        storage_path="abc123_recording.mp3",
        upload_timestamp=datetime.now(timezone.utc),
        duration_seconds=12.5,
        converted_path=None,
    )
    defaults.update(overrides)
    return AudioFile(**defaults)


def _make_job(audio_file_id=None, **overrides) -> TranscriptionJob:
    defaults = dict(
        id=uuid4(),
        audio_file_id=audio_file_id or uuid4(),
        status=JobStatus.PENDING,
        language="pt-BR",
        engine_name="whisper",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return TranscriptionJob(**defaults)


def _make_result(job_id=None, **overrides) -> TranscriptionResult:
    defaults = dict(
        id=uuid4(),
        job_id=job_id or uuid4(),
        full_text="Hello world",
        language="pt-BR",
        engine_name="whisper",
        processing_duration_seconds=3.14,
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return TranscriptionResult(**defaults)


class TestSQLiteJobRepository:

    def test_create_and_get_audio_file(self, repo):
        audio_file = _make_audio_file()

        repo.create_audio_file(audio_file)
        retrieved = repo.get_audio_file(audio_file.id)

        assert retrieved is not None
        assert retrieved.id == audio_file.id
        assert retrieved.original_filename == audio_file.original_filename
        assert retrieved.format == audio_file.format
        assert retrieved.size_bytes == audio_file.size_bytes
        assert retrieved.storage_path == audio_file.storage_path
        assert retrieved.duration_seconds == audio_file.duration_seconds
        assert retrieved.converted_path == audio_file.converted_path

    def test_save_and_get_job(self, repo):
        audio_file = _make_audio_file()
        repo.create_audio_file(audio_file)

        job = _make_job(audio_file_id=audio_file.id)
        repo.save_job(job)
        retrieved = repo.get_job(job.id)

        assert retrieved is not None
        assert retrieved.id == job.id
        assert retrieved.audio_file_id == job.audio_file_id
        assert retrieved.status == job.status
        assert retrieved.language == job.language
        assert retrieved.engine_name == job.engine_name
        assert retrieved.progress_percent == job.progress_percent
        assert retrieved.retry_count == job.retry_count

    def test_update_job_status(self, repo):
        audio_file = _make_audio_file()
        repo.create_audio_file(audio_file)

        job = _make_job(audio_file_id=audio_file.id, status=JobStatus.PENDING)
        repo.save_job(job)

        job.transition_to(JobStatus.CONVERTING)
        repo.save_job(job)

        retrieved = repo.get_job(job.id)
        assert retrieved is not None
        assert retrieved.status == JobStatus.CONVERTING

    def test_save_and_get_result(self, repo):
        audio_file = _make_audio_file()
        repo.create_audio_file(audio_file)

        job = _make_job(audio_file_id=audio_file.id)
        repo.save_job(job)

        result = _make_result(job_id=job.id)
        repo.save_result(result)

        retrieved = repo.get_result_for_job(job.id)
        assert retrieved is not None
        assert retrieved.id == result.id
        assert retrieved.job_id == result.job_id
        assert retrieved.full_text == result.full_text
        assert retrieved.language == result.language
        assert retrieved.engine_name == result.engine_name
        assert retrieved.processing_duration_seconds == pytest.approx(
            result.processing_duration_seconds
        )

    def test_get_jobs_by_status(self, repo):
        audio_file = _make_audio_file()
        repo.create_audio_file(audio_file)

        pending_jobs = [
            _make_job(audio_file_id=audio_file.id, status=JobStatus.PENDING)
            for _ in range(3)
        ]
        converting_jobs = [
            _make_job(audio_file_id=audio_file.id, status=JobStatus.CONVERTING)
            for _ in range(2)
        ]

        for job in pending_jobs + converting_jobs:
            repo.save_job(job)

        pending = repo.get_jobs_by_status(JobStatus.PENDING)
        converting = repo.get_jobs_by_status(JobStatus.CONVERTING)
        completed = repo.get_jobs_by_status(JobStatus.COMPLETED)

        assert len(pending) == 3
        assert len(converting) == 2
        assert len(completed) == 0

    def test_get_nonexistent_job_returns_none(self, repo):
        result = repo.get_job(uuid4())
        assert result is None
