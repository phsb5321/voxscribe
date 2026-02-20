from enum import Enum


class AudioFormat(str, Enum):
    MP3 = "MP3"
    WAV = "WAV"
    FLAC = "FLAC"
    OGG = "OGG"

    @classmethod
    def from_extension(cls, ext: str) -> "AudioFormat":
        """Convert file extension (with or without dot) to AudioFormat."""
        ext = ext.lstrip(".").upper()
        try:
            return cls(ext)
        except ValueError:
            raise ValueError(
                f"Unsupported audio format: {ext}. "
                f"Supported: {', '.join(f.value for f in cls)}"
            )

    @property
    def extension(self) -> str:
        return f".{self.value.lower()}"
