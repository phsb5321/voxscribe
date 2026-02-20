class DomainError(Exception):
    """Base exception for domain errors."""


class InvalidAudioFormatError(DomainError):
    """Raised when an audio file has an unsupported format."""


class FileTooLargeError(DomainError):
    """Raised when a file exceeds the maximum allowed size."""


class InvalidStateTransitionError(DomainError):
    """Raised when a job status transition is invalid."""

    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            f"Invalid state transition: {current_status} → {target_status}"
        )
        self.current_status = current_status
        self.target_status = target_status


class TranscriptionError(DomainError):
    """Raised when transcription fails."""


class StorageError(DomainError):
    """Raised when file storage operations fail."""


class MaxRetriesExceededError(DomainError):
    """Raised when a job exceeds its maximum retry count."""
