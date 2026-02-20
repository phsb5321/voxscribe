import os
import re
import uuid

from app.domain.exceptions import StorageError
from app.ports.audio_storage import AudioStoragePort


class LocalFileStorage(AudioStoragePort):
    """Stores audio files on the local filesystem."""

    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir

    def store(self, filename: str, data: bytes) -> str:
        """Store audio file, return relative storage path."""
        os.makedirs(self.base_dir, exist_ok=True)

        sanitized = re.sub(r"[^\w.\-]", "_", filename)
        unique_name = f"{uuid.uuid4()}_{sanitized}"

        full_path = os.path.join(self.base_dir, unique_name)
        with open(full_path, "wb") as f:
            f.write(data)

        return unique_name

    def retrieve(self, storage_path: str) -> bytes:
        """Retrieve audio file by storage path."""
        full_path = os.path.join(self.base_dir, storage_path)
        if not os.path.isfile(full_path):
            raise StorageError(f"File not found: {storage_path}")

        with open(full_path, "rb") as f:
            return f.read()

    def delete(self, storage_path: str) -> None:
        """Delete audio file from storage. Ignores missing files."""
        full_path = os.path.join(self.base_dir, storage_path)
        try:
            os.remove(full_path)
        except FileNotFoundError:
            pass

    def get_absolute_path(self, storage_path: str) -> str:
        """Return absolute filesystem path for a storage path."""
        return os.path.join(self.base_dir, storage_path)
