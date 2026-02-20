import pytest
from unittest.mock import MagicMock

from app.application.submit_transcription import SubmitTranscriptionUseCase
from app.application.dto import SubmitTranscriptionRequest
from app.domain.exceptions import InvalidAudioFormatError, FileTooLargeError


@pytest.fixture
def mock_storage():
    storage = MagicMock()
    storage.store.return_value = "uploads/test.mp3"
    return storage


@pytest.fixture
def mock_repository():
    return MagicMock()


@pytest.fixture
def mock_queue():
    return MagicMock()


@pytest.fixture
def use_case(mock_storage, mock_repository, mock_queue):
    return SubmitTranscriptionUseCase(
        storage=mock_storage,
        repository=mock_repository,
        queue=mock_queue,
        engine_name="whisper",
    )


class TestSubmitValidFile:
    def test_submit_valid_file(self, use_case, mock_storage, mock_repository, mock_queue):
        request = SubmitTranscriptionRequest(
            filename="test.mp3",
            file_data=b"fake_audio",
            language="pt-BR",
        )

        response = use_case.execute(request)

        # Assert storage.store was called with the filename and data
        mock_storage.store.assert_called_once_with("test.mp3", b"fake_audio")

        # Assert repository.create_audio_file was called
        mock_repository.create_audio_file.assert_called_once()

        # Assert repository.save_job was called
        mock_repository.save_job.assert_called_once()

        # Assert queue.enqueue was called
        mock_queue.enqueue.assert_called_once()

        # Assert response has correct fields
        assert response.job_id is not None
        assert response.status == "PENDING"
        assert response.redirect_url.startswith("/jobs/")


class TestSubmitInvalidFormat:
    def test_submit_invalid_format(self, use_case):
        request = SubmitTranscriptionRequest(
            filename="test.exe",
            file_data=b"fake_audio",
            language="pt-BR",
        )

        with pytest.raises(InvalidAudioFormatError):
            use_case.execute(request)


class TestSubmitFileTooLarge:
    def test_submit_file_too_large(self, use_case):
        request = SubmitTranscriptionRequest(
            filename="test.mp3",
            file_data=b"x" * (524_288_001),
            language="pt-BR",
        )

        with pytest.raises(FileTooLargeError):
            use_case.execute(request)
