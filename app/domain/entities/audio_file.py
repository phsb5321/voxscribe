from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.domain.exceptions import FileTooLargeError, InvalidAudioFormatError
from app.domain.value_objects.audio_format import AudioFormat

MAX_FILE_SIZE_BYTES = 524_288_000  # 500 MB


@dataclass
class AudioFile:
    original_filename: str
    format: AudioFormat
    size_bytes: int
    storage_path: str
    id: UUID = field(default_factory=uuid4)
    duration_seconds: float | None = None
    upload_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    converted_path: str | None = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not self.original_filename or not self.original_filename.strip():
            raise ValueError("original_filename must not be empty")
        if "/" in self.original_filename or "\\" in self.original_filename:
            raise ValueError("original_filename must not contain path separators")
        if "\x00" in self.original_filename:
            raise ValueError("original_filename must not contain null bytes")
        if not isinstance(self.format, AudioFormat):
            raise InvalidAudioFormatError(
                f"Invalid format: {self.format}. Must be an AudioFormat enum value."
            )
        if self.size_bytes <= 0:
            raise ValueError("size_bytes must be positive")
        if self.size_bytes > MAX_FILE_SIZE_BYTES:
            raise FileTooLargeError(
                f"File size {self.size_bytes} exceeds maximum {MAX_FILE_SIZE_BYTES} bytes (500 MB)"
            )
