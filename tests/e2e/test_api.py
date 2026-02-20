"""End-to-end API tests for the web application."""

import os
import struct
import tempfile
from unittest.mock import patch
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from app.bootstrap import reset_container
from app.main import create_app
from app.ports.job_queue import JobQueuePort


class NoOpQueue(JobQueuePort):
    """A queue that does nothing — for testing without Redis."""

    def __init__(self):
        self.enqueued: list[UUID] = []

    def enqueue(self, job_id: UUID) -> None:
        self.enqueued.append(job_id)


def _make_wav_bytes(duration_seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generate minimal valid WAV file bytes."""
    num_samples = int(sample_rate * duration_seconds)
    data = b"\x00\x00" * num_samples
    data_size = len(data)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,   # PCM
        1,   # mono
        sample_rate,
        sample_rate * 2,
        2,
        16,
        b"data",
        data_size,
    )
    return header + data


@pytest.fixture
def wav_bytes():
    return _make_wav_bytes(duration_seconds=1.0)


@pytest.fixture(autouse=True)
def _clean_container():
    """Reset the container and set test env vars."""
    reset_container()
    tmpdir = tempfile.mkdtemp()
    os.environ["DATA_DIR"] = tmpdir
    os.environ["DATABASE_URL"] = f"sqlite:///{tmpdir}/test.db"
    os.environ["REDIS_URL"] = "redis://localhost:6379"
    os.environ["TRANSCRIPTION_ENGINE"] = "faster-whisper"
    yield
    reset_container()


@pytest.fixture
def app():
    """Create FastAPI app with a no-op queue replacing the real RQ queue."""
    from app import bootstrap as bootstrap_mod

    original_bootstrap = bootstrap_mod.bootstrap

    def patched_bootstrap(settings=None):
        container = original_bootstrap(settings)
        # Replace the RQ queue with a no-op queue
        noop_queue = NoOpQueue()
        object.__setattr__(container, "queue", noop_queue)
        # Rebuild submit_transcription with the no-op queue
        from app.application.submit_transcription import SubmitTranscriptionUseCase

        submit = SubmitTranscriptionUseCase(
            storage=container.storage,
            repository=container.repository,
            queue=noop_queue,
            engine_name=container.engine.engine_name,
        )
        object.__setattr__(container, "submit_transcription", submit)
        return container

    with patch.object(bootstrap_mod, "bootstrap", patched_bootstrap):
        yield create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "engine" in data


class TestUploadEndpoint:
    @pytest.mark.asyncio
    async def test_upload_valid_wav(self, client, wav_bytes):
        response = await client.post(
            "/api/upload",
            files={"file": ("test.wav", wav_bytes, "audio/wav")},
            data={"language": "pt-BR"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "PENDING"
        assert "/jobs/" in data["redirect_url"]

    @pytest.mark.asyncio
    async def test_upload_invalid_format_returns_400(self, client):
        response = await client.post(
            "/api/upload",
            files={"file": ("test.txt", b"not audio", "text/plain")},
            data={"language": "pt-BR"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_missing_file_returns_422(self, client):
        response = await client.post("/api/upload")
        assert response.status_code == 422


class TestJobStatusEndpoint:
    @pytest.mark.asyncio
    async def test_get_nonexistent_job_returns_404(self, client):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/jobs/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_job_after_upload(self, client, wav_bytes):
        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("test.wav", wav_bytes, "audio/wav")},
            data={"language": "pt-BR"},
        )
        job_id = upload_resp.json()["job_id"]

        status_resp = await client.get(f"/api/jobs/{job_id}")
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["job_id"] == job_id
        assert data["status"] == "PENDING"
        assert data["language"] == "pt-BR"


class TestResultEndpoint:
    @pytest.mark.asyncio
    async def test_result_not_found_returns_404(self, client):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/jobs/{fake_id}/result")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_not_found_returns_404(self, client):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/jobs/{fake_id}/result/download")
        assert response.status_code == 404


class TestUploadPage:
    @pytest.mark.asyncio
    async def test_upload_page_returns_html(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Audio Transcriber" in response.text


class TestJobPage:
    @pytest.mark.asyncio
    async def test_job_page_for_nonexistent_returns_404(self, client):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/jobs/{fake_id}")
        assert response.status_code == 404
