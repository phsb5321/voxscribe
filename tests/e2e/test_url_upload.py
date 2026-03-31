"""End-to-end API tests for Instagram reel URL upload."""

import os
import tempfile
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.bootstrap import reset_container
from app.main import create_app
from app.ports.job_queue import JobQueuePort


class NoOpQueue(JobQueuePort):
    """A queue that does nothing — for testing without Redis."""

    def __init__(self):
        self.enqueued = []

    def enqueue(self, job_id) -> None:
        self.enqueued.append(job_id)


@pytest.fixture(autouse=True)
def _clean_container():
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
    from app import bootstrap as bootstrap_mod

    original_bootstrap = bootstrap_mod.bootstrap

    def patched_bootstrap(settings=None):
        container = original_bootstrap(settings)
        noop_queue = NoOpQueue()
        object.__setattr__(container, "queue", noop_queue)

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


class TestUrlUploadEndpoint:
    @pytest.mark.asyncio
    async def test_upload_valid_reel_url(self, client):
        response = await client.post(
            "/api/upload-url",
            json={
                "url": "https://www.instagram.com/reel/ABC123/",
                "language": "pt-BR",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "PENDING"
        assert "/jobs/" in data["redirect_url"]

    @pytest.mark.asyncio
    async def test_upload_invalid_url_returns_422(self, client):
        response = await client.post(
            "/api/upload-url",
            json={
                "url": "https://www.youtube.com/watch?v=abc",
                "language": "pt-BR",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_instagram_non_reel_returns_422(self, client):
        response = await client.post(
            "/api/upload-url",
            json={
                "url": "https://www.instagram.com/p/ABC123/",
                "language": "pt-BR",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "not a reel" in data["detail"]

    @pytest.mark.asyncio
    async def test_job_status_includes_source_url(self, client):
        # Create a job via URL upload
        response = await client.post(
            "/api/upload-url",
            json={
                "url": "https://www.instagram.com/reel/XYZ789/",
                "language": "en-US",
            },
        )
        assert response.status_code == 201
        job_id = response.json()["job_id"]

        # Fetch job status
        status_response = await client.get(f"/api/jobs/{job_id}")
        assert status_response.status_code == 200
        data = status_response.json()
        assert data["audio_file"]["source_url"] == "https://www.instagram.com/reel/XYZ789/"
        assert data["audio_file"]["original_filename"] == "reel_XYZ789.mp3"

    @pytest.mark.asyncio
    async def test_url_upload_default_language(self, client):
        response = await client.post(
            "/api/upload-url",
            json={"url": "https://www.instagram.com/reel/DEF456/"},
        )
        assert response.status_code == 201
