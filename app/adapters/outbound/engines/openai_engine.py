"""OpenAI-compatible transcription engine adapter.

Works against api.openai.com (default) OR any OpenAI-compatible
`/v1/audio/transcriptions` endpoint via OPENAI_BASE_URL — e.g. a self-hosted
faster-whisper server. Model + base URL are configurable so the same engine
serves gpt-4o-mini-transcribe and a local whisper-large-v3-turbo endpoint.
"""

import logging
import os

from app.domain.exceptions import TranscriptionError
from app.ports.transcription_engine import TranscriptionEnginePort

logger = logging.getLogger(__name__)


class OpenAIEngine(TranscriptionEnginePort):
    def __init__(self, api_key: str = "", base_url: str = "", model: str = "") -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._base_url = base_url or os.environ.get("OPENAI_BASE_URL", "")
        self._model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini-transcribe")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI

                # A self-hosted endpoint may need no real key; the SDK still
                # requires a non-empty api_key, so fall back to a placeholder.
                kwargs = {"api_key": self._api_key or "sk-noauth"}
                if self._base_url:
                    kwargs["base_url"] = self._base_url
                self._client = OpenAI(**kwargs)
            except Exception as exc:
                raise TranscriptionError(f"Failed to initialize OpenAI client: {exc}") from exc
        return self._client

    def transcribe(self, audio_path: str, language: str) -> str:
        """Transcribe audio via the configured OpenAI-compatible endpoint."""
        try:
            client = self._get_client()

            with open(audio_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model=self._model,
                    file=audio_file,
                    language=language.split("-")[0],  # ISO 639-1 (e.g., "pt")
                )

            text = response.text.strip()
            logger.info(
                f"OpenAI-compatible transcription completed: {len(text)} chars "
                f"from {audio_path} (model={self._model}, base={self._base_url or 'openai'})"
            )
            return text

        except TranscriptionError:
            raise
        except Exception as exc:
            raise TranscriptionError(f"OpenAI transcription failed for {audio_path}: {exc}") from exc

    @property
    def engine_name(self) -> str:
        return "openai"
