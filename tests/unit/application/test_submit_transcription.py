from unittest.mock import MagicMock

import pytest

from app.application.dto import SubmitTranscriptionRequest, SubmitUrlTranscriptionRequest
from app.application.submit_transcription import SubmitTranscriptionUseCase
from app.domain.exceptions import FileTooLargeError, InvalidAudioFormatError, InvalidUrlError


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

    def test_submit_valid_m4a_file(self, use_case, mock_storage, mock_repository, mock_queue):
        mock_storage.store.return_value = "uploads/test.m4a"
        request = SubmitTranscriptionRequest(
            filename="test.m4a",
            file_data=b"fake_audio",
            language="pt-BR",
        )

        response = use_case.execute(request)

        mock_storage.store.assert_called_once_with("test.m4a", b"fake_audio")
        mock_repository.create_audio_file.assert_called_once()
        mock_repository.save_job.assert_called_once()
        mock_queue.enqueue.assert_called_once()
        assert response.job_id is not None
        assert response.status == "PENDING"


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


class TestSubmitFromUrl:
    def test_submit_valid_reel_url(self, use_case, mock_repository, mock_queue):
        request = SubmitUrlTranscriptionRequest(
            url="https://www.instagram.com/reel/ABC123/",
            language="pt-BR",
        )

        response = use_case.execute_from_url(request)

        mock_repository.create_audio_file.assert_called_once()
        audio_file = mock_repository.create_audio_file.call_args[0][0]
        assert audio_file.source_url == "https://www.instagram.com/reel/ABC123/"
        assert audio_file.original_filename == "reel_ABC123.mp3"
        assert audio_file.size_bytes == 0

        mock_repository.save_job.assert_called_once()
        mock_queue.enqueue.assert_called_once()

        assert response.job_id is not None
        assert response.status == "PENDING"
        assert response.redirect_url.startswith("/jobs/")

    def test_submit_invalid_url_raises_error(self, use_case):
        request = SubmitUrlTranscriptionRequest(
            url="https://www.youtube.com/watch?v=abc",
            language="pt-BR",
        )
        with pytest.raises(InvalidUrlError, match="Invalid URL"):
            use_case.execute_from_url(request)

    def test_submit_instagram_non_reel_url_raises_specific_error(self, use_case):
        request = SubmitUrlTranscriptionRequest(
            url="https://www.instagram.com/p/ABC123/",
            language="pt-BR",
        )
        with pytest.raises(InvalidUrlError, match="not a reel"):
            use_case.execute_from_url(request)
