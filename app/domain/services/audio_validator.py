import os

from app.domain.exceptions import FileTooLargeError, InvalidAudioFormatError
from app.domain.value_objects.audio_format import AudioFormat

MAX_FILE_SIZE_BYTES = 524_288_000  # 500 MB
ALLOWED_EXTENSIONS = {f.extension for f in AudioFormat}


def validate_audio_file(filename: str, size_bytes: int) -> AudioFormat:
    """Validate an audio file's format and size.

    Returns the AudioFormat if valid.
    Raises InvalidAudioFormatError or FileTooLargeError otherwise.
    """
    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidAudioFormatError(
            f"Unsupported format '{ext}'. Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise FileTooLargeError(
            f"File size {size_bytes} bytes exceeds maximum {MAX_FILE_SIZE_BYTES} bytes (500 MB)"
        )

    if size_bytes <= 0:
        raise ValueError("File size must be positive")

    return AudioFormat.from_extension(ext)
