import pytest
from uuid import UUID

from app.domain.entities.audio_file import AudioFile, MAX_FILE_SIZE_BYTES
from app.domain.value_objects.audio_format import AudioFormat
from app.domain.exceptions import FileTooLargeError, InvalidAudioFormatError


class TestAudioFileCreation:
    """Tests for creating AudioFile entities."""

    def test_create_valid_audio_file(self):
        audio_file = AudioFile(
            original_filename="recording.mp3",
            format=AudioFormat.MP3,
            size_bytes=1024,
            storage_path="/uploads/recording.mp3",
        )
        assert audio_file.original_filename == "recording.mp3"
        assert audio_file.format == AudioFormat.MP3
        assert audio_file.size_bytes == 1024
        assert audio_file.storage_path == "/uploads/recording.mp3"

    def test_raises_value_error_for_empty_filename(self):
        with pytest.raises(ValueError, match="original_filename must not be empty"):
            AudioFile(
                original_filename="",
                format=AudioFormat.MP3,
                size_bytes=1024,
                storage_path="/uploads/recording.mp3",
            )

    def test_raises_value_error_for_whitespace_only_filename(self):
        with pytest.raises(ValueError, match="original_filename must not be empty"):
            AudioFile(
                original_filename="   ",
                format=AudioFormat.MP3,
                size_bytes=1024,
                storage_path="/uploads/recording.mp3",
            )

    def test_raises_value_error_for_filename_with_forward_slash(self):
        with pytest.raises(
            ValueError, match="original_filename must not contain path separators"
        ):
            AudioFile(
                original_filename="path/file.mp3",
                format=AudioFormat.MP3,
                size_bytes=1024,
                storage_path="/uploads/recording.mp3",
            )

    def test_raises_value_error_for_filename_with_backslash(self):
        with pytest.raises(
            ValueError, match="original_filename must not contain path separators"
        ):
            AudioFile(
                original_filename="path\\file.mp3",
                format=AudioFormat.MP3,
                size_bytes=1024,
                storage_path="/uploads/recording.mp3",
            )

    def test_raises_value_error_for_filename_with_null_bytes(self):
        with pytest.raises(
            ValueError, match="original_filename must not contain null bytes"
        ):
            AudioFile(
                original_filename="file\x00.mp3",
                format=AudioFormat.MP3,
                size_bytes=1024,
                storage_path="/uploads/recording.mp3",
            )

    def test_raises_invalid_audio_format_error_for_invalid_format(self):
        with pytest.raises(InvalidAudioFormatError, match="Invalid format"):
            audio_file = object.__new__(AudioFile)
            audio_file.original_filename = "recording.xyz"
            audio_file.format = "NOT_A_FORMAT"
            audio_file.size_bytes = 1024
            audio_file.storage_path = "/uploads/recording.xyz"
            audio_file._validate()

    def test_raises_file_too_large_error_when_size_exceeds_max(self):
        with pytest.raises(FileTooLargeError, match="exceeds maximum"):
            AudioFile(
                original_filename="large_file.mp3",
                format=AudioFormat.MP3,
                size_bytes=MAX_FILE_SIZE_BYTES + 1,
                storage_path="/uploads/large_file.mp3",
            )

    def test_raises_value_error_when_size_bytes_is_zero(self):
        with pytest.raises(ValueError, match="size_bytes must be positive"):
            AudioFile(
                original_filename="recording.mp3",
                format=AudioFormat.MP3,
                size_bytes=0,
                storage_path="/uploads/recording.mp3",
            )

    def test_raises_value_error_when_size_bytes_is_negative(self):
        with pytest.raises(ValueError, match="size_bytes must be positive"):
            AudioFile(
                original_filename="recording.mp3",
                format=AudioFormat.MP3,
                size_bytes=-100,
                storage_path="/uploads/recording.mp3",
            )

    def test_valid_audio_file_has_correct_fields(self):
        audio_file = AudioFile(
            original_filename="podcast.wav",
            format=AudioFormat.WAV,
            size_bytes=2048,
            storage_path="/uploads/podcast.wav",
            duration_seconds=120.5,
        )
        assert isinstance(audio_file.id, UUID)
        assert audio_file.original_filename == "podcast.wav"
        assert audio_file.format == AudioFormat.WAV
        assert audio_file.size_bytes == 2048
        assert audio_file.storage_path == "/uploads/podcast.wav"
        assert audio_file.duration_seconds == 120.5
        assert audio_file.upload_timestamp is not None
        assert audio_file.converted_path is None
