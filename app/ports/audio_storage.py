from abc import ABC, abstractmethod


class AudioStoragePort(ABC):
    @abstractmethod
    def store(self, filename: str, data: bytes) -> str:
        """Store audio file, return storage path."""

    @abstractmethod
    def retrieve(self, storage_path: str) -> bytes:
        """Retrieve audio file by storage path."""

    @abstractmethod
    def delete(self, storage_path: str) -> None:
        """Delete audio file from storage."""

    @abstractmethod
    def get_absolute_path(self, storage_path: str) -> str:
        """Return absolute filesystem path for a storage path."""
