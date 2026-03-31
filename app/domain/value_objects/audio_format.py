from enum import StrEnum


class AudioFormat(StrEnum):
    MP3 = "MP3"
    WAV = "WAV"
    FLAC = "FLAC"
    OGG = "OGG"
    M4A = "M4A"

    @classmethod
    def from_extension(cls, ext: str) -> "AudioFormat":
        """Convert file extension (with or without dot) to AudioFormat."""
        ext = ext.lstrip(".").upper()
        try:
            return cls(ext)
        except ValueError as e:
            raise ValueError(f"Unsupported audio format: {ext}. Supported: {', '.join(f.value for f in cls)}") from e

    @property
    def extension(self) -> str:
        return f".{self.value.lower()}"
