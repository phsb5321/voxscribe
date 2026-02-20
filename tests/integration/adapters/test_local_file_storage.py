import pytest
import os

from app.adapters.outbound.storage.local_file_storage import LocalFileStorage
from app.domain.exceptions import StorageError


@pytest.fixture
def storage(tmp_path):
    return LocalFileStorage(base_dir=str(tmp_path / "uploads"))


class TestLocalFileStorage:

    def test_store_and_retrieve(self, storage):
        data = b"fake audio content here"
        storage_path = storage.store("sample.mp3", data)

        retrieved = storage.retrieve(storage_path)
        assert retrieved == data

    def test_store_creates_directory(self, storage):
        """Store should create the base directory if it does not exist."""
        assert not os.path.isdir(storage.base_dir)

        storage.store("file.wav", b"wav bytes")

        assert os.path.isdir(storage.base_dir)

    def test_retrieve_nonexistent_raises(self, storage):
        os.makedirs(storage.base_dir, exist_ok=True)

        with pytest.raises(StorageError):
            storage.retrieve("does_not_exist.mp3")

    def test_delete_removes_file(self, storage):
        storage_path = storage.store("to_delete.mp3", b"delete me")

        storage.delete(storage_path)

        with pytest.raises(StorageError):
            storage.retrieve(storage_path)

    def test_delete_nonexistent_is_noop(self, storage):
        os.makedirs(storage.base_dir, exist_ok=True)

        # Should not raise any exception
        storage.delete("nonexistent_file.mp3")

    def test_get_absolute_path(self, storage):
        result = storage.get_absolute_path("some_file.wav")
        expected = os.path.join(storage.base_dir, "some_file.wav")
        assert result == expected
