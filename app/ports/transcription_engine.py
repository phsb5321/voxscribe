from abc import ABC, abstractmethod


class TranscriptionEnginePort(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, language: str) -> str:
        """Transcribe audio file at given path in given language.

        Returns full transcription text.
        Raises TranscriptionError on failure.
        """

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Return the identifier of this engine."""
