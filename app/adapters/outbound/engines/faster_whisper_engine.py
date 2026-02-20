import logging

from app.domain.exceptions import TranscriptionError
from app.ports.transcription_engine import TranscriptionEnginePort

logger = logging.getLogger(__name__)


class FasterWhisperEngine(TranscriptionEnginePort):
    def __init__(self, model_size: str = "large-v3-turbo") -> None:
        self._model_size = model_size
        self._model = None

    def _load_model(self) -> None:
        from faster_whisper import WhisperModel

        logger.info(f"Loading faster-whisper model: {self._model_size}")
        self._model = WhisperModel(
            self._model_size,
            device="auto",
            compute_type="int8",
        )
        logger.info("Model loaded successfully")

    @staticmethod
    def _normalize_language(language: str) -> str:
        """Strip region subtag (e.g. pt-BR → pt) for faster-whisper."""
        return language.split("-")[0].lower()

    def transcribe(self, audio_path: str, language: str) -> str:
        try:
            if self._model is None:
                self._load_model()

            lang = self._normalize_language(language)
            initial_prompt = None
            if lang == "pt":
                initial_prompt = "Transcrição em português brasileiro."

            segments, _ = self._model.transcribe(
                audio_path,
                language=lang,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=400,
                ),
                word_timestamps=True,
                condition_on_previous_text=True,
                hallucination_silence_threshold=2.0,
                initial_prompt=initial_prompt,
            )
            text = " ".join(segment.text.strip() for segment in segments)
            return text
        except TranscriptionError:
            raise
        except Exception as exc:
            raise TranscriptionError(
                f"Transcription failed for {audio_path}: {exc}"
            ) from exc

    @property
    def engine_name(self) -> str:
        return "faster-whisper"
