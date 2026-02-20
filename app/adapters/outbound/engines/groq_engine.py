"""Groq whisper-large-v3 transcription engine adapter."""

import logging
import os

from app.domain.exceptions import TranscriptionError
from app.ports.transcription_engine import TranscriptionEnginePort

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqEngine(TranscriptionEnginePort):
    def __init__(
        self, api_key: str = "", model: str = "whisper-large-v3"
    ) -> None:
        self._api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    api_key=self._api_key,
                    base_url=GROQ_BASE_URL,
                )
            except Exception as exc:
                raise TranscriptionError(
                    f"Failed to initialize Groq client: {exc}"
                ) from exc
        return self._client

    def transcribe(self, audio_path: str, language: str) -> str:
        """Transcribe audio using Groq's Whisper API."""
        try:
            client = self._get_client()
            lang = language.split("-")[0].lower()

            with open(audio_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model=self._model,
                    file=audio_file,
                    language=lang,
                    response_format="verbose_json",
                    temperature=0.0,
                )

            text = response.text.strip()
            logger.info(
                f"Groq transcription completed: {len(text)} chars from {audio_path}"
            )
            return text

        except TranscriptionError:
            raise
        except Exception as exc:
            raise TranscriptionError(
                f"Groq transcription failed for {audio_path}: {exc}"
            ) from exc

    @property
    def engine_name(self) -> str:
        return "groq"
