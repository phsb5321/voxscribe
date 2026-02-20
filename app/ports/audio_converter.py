from abc import ABC, abstractmethod


class AudioConverterPort(ABC):
    @abstractmethod
    def convert_to_wav(
        self,
        input_path: str,
        output_path: str,
        sample_rate: int = 16000,
        channels: int = 1,
    ) -> bool:
        """Convert audio file to WAV format. Returns success status."""

    @abstractmethod
    def get_duration_seconds(self, audio_path: str) -> float:
        """Get audio file duration in seconds."""

    @abstractmethod
    def detect_silence_boundaries(
        self, audio_path: str, min_silence_ms: int = 500
    ) -> list[tuple[int, int]]:
        """Detect non-silent segments. Returns list of (start_ms, end_ms) tuples."""

    @abstractmethod
    def split_at_boundaries(
        self, audio_path: str, boundaries: list[tuple[int, int]]
    ) -> list[str]:
        """Split audio at given boundaries. Returns list of chunk file paths."""
