import pytest
from unittest.mock import MagicMock, PropertyMock, call
from uuid import uuid4

from app.application.process_transcription import ProcessTranscriptionUseCase
from app.domain.entities.audio_file import AudioFile
from app.domain.entities.transcription_job import TranscriptionJob
from app.domain.value_objects.audio_format import AudioFormat
from app.domain.value_objects.job_status import JobStatus
from app.domain.exceptions import TranscriptionError


@pytest.fixture
def audio_file_id():
    return uuid4()


@pytest.fixture
def job_id():
    return uuid4()


@pytest.fixture
def audio_file(audio_file_id):
    return AudioFile(
        original_filename="test.mp3",
        format=AudioFormat.MP3,
        size_bytes=1024,
        storage_path="uploads/test.mp3",
        id=audio_file_id,
    )


@pytest.fixture
def transcription_job(job_id, audio_file_id):
    return TranscriptionJob(
        id=job_id,
        audio_file_id=audio_file_id,
        language="pt-BR",
        engine_name="whisper",
        status=JobStatus.PENDING,
    )


@pytest.fixture
def mock_repository(transcription_job, audio_file):
    repo = MagicMock()
    repo.get_job.return_value = transcription_job
    repo.get_audio_file.return_value = audio_file
    return repo


@pytest.fixture
def mock_storage():
    storage = MagicMock()
    storage.get_absolute_path.side_effect = lambda p: f"/data/{p}"
    return storage


@pytest.fixture
def mock_converter():
    converter = MagicMock()
    converter.convert_to_wav.return_value = True
    converter.get_duration_seconds.return_value = 120.5
    return converter


@pytest.fixture
def mock_engine():
    engine = MagicMock()
    engine.transcribe.return_value = "Transcribed text content"
    return engine


@pytest.fixture
def use_case(mock_repository, mock_storage, mock_converter, mock_engine):
    return ProcessTranscriptionUseCase(
        repository=mock_repository,
        storage=mock_storage,
        converter=mock_converter,
        engine=mock_engine,
    )


class TestProcessHappyPath:
    def test_process_happy_path(
        self,
        use_case,
        mock_repository,
        mock_storage,
        mock_converter,
        mock_engine,
        transcription_job,
        job_id,
    ):
        use_case.execute(job_id)

        # repository.save_job was called multiple times (status transitions)
        assert mock_repository.save_job.call_count >= 3

        # converter.convert_to_wav was called
        mock_converter.convert_to_wav.assert_called_once()

        # engine.transcribe was called
        mock_engine.transcribe.assert_called_once()

        # repository.save_result was called
        mock_repository.save_result.assert_called_once()

        # Final job status should be COMPLETED
        # The last save_job call's first positional argument is the job entity
        last_save_call = mock_repository.save_job.call_args_list[-1]
        saved_job = last_save_call[0][0]
        assert saved_job.status == JobStatus.COMPLETED
        assert saved_job.progress_percent == 100


class TestProcessEngineFailureRetries:
    def test_process_engine_failure_retries(
        self,
        mock_repository,
        mock_storage,
        mock_converter,
        job_id,
        audio_file_id,
    ):
        # Create a fresh job for this test so state is clean
        job = TranscriptionJob(
            id=job_id,
            audio_file_id=audio_file_id,
            language="pt-BR",
            engine_name="whisper",
            status=JobStatus.PENDING,
        )
        mock_repository.get_job.return_value = job

        audio = AudioFile(
            original_filename="test.mp3",
            format=AudioFormat.MP3,
            size_bytes=1024,
            storage_path="uploads/test.mp3",
            id=audio_file_id,
        )
        mock_repository.get_audio_file.return_value = audio

        engine = MagicMock()
        engine.transcribe.side_effect = TranscriptionError("Engine crashed")

        # Capture job status snapshots at each save_job call, because the same
        # mutable job object is passed every time and its state keeps changing.
        saved_statuses = []

        def capture_save_job(j):
            saved_statuses.append((j.status, j.error_message, j.retry_count))

        mock_repository.save_job.side_effect = capture_save_job

        use_case = ProcessTranscriptionUseCase(
            repository=mock_repository,
            storage=mock_storage,
            converter=mock_converter,
            engine=engine,
        )

        use_case.execute(job_id)

        # The engine was called and raised TranscriptionError
        engine.transcribe.assert_called_once()

        # save_result should NOT have been called since transcription failed
        mock_repository.save_result.assert_not_called()

        # Verify save_job was called multiple times for the status transitions
        assert mock_repository.save_job.call_count >= 3

        # Extract just the statuses from the snapshots
        statuses_only = [s[0] for s in saved_statuses]

        # Verify the job transitioned through FAILED at some point
        assert JobStatus.FAILED in statuses_only

        # Find the FAILED snapshot and verify error_message was set
        failed_snapshot = next(s for s in saved_statuses if s[0] == JobStatus.FAILED)
        assert failed_snapshot[1] is not None  # error_message was set

        # The last save should be the retry back to PENDING (since retry_count < 3)
        last_status, last_error, last_retry = saved_statuses[-1]
        assert last_status == JobStatus.PENDING
        assert last_retry == 1
        assert last_error is None
