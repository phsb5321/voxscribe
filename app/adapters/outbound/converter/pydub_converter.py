import logging
import os
import tempfile

from pydub import AudioSegment
from pydub.silence import detect_nonsilent

from app.ports.audio_converter import AudioConverterPort

logger = logging.getLogger(__name__)


class PydubAudioConverter(AudioConverterPort):
    def convert_to_wav(
        self,
        input_path: str,
        output_path: str,
        sample_rate: int = 16000,
        channels: int = 1,
    ) -> bool:
        """Convert audio file to WAV format. Returns success status."""
        try:
            audio = AudioSegment.from_file(input_path)
            audio = audio.set_frame_rate(sample_rate)
            audio = audio.set_channels(channels)
            audio.export(output_path, format="wav")
            return True
        except Exception as e:
            logger.error("Failed to convert %s to WAV: %s", input_path, e)
            return False

    def get_duration_seconds(self, audio_path: str) -> float:
        """Get audio file duration in seconds."""
        return len(AudioSegment.from_file(audio_path)) / 1000.0

    def detect_silence_boundaries(
        self, audio_path: str, min_silence_ms: int = 500
    ) -> list[tuple[int, int]]:
        """Detect non-silent segments. Returns list of (start_ms, end_ms) tuples."""
        audio = AudioSegment.from_file(audio_path)
        return detect_nonsilent(
            audio,
            min_silence_len=min_silence_ms,
            silence_thresh=-40,
        )

    def split_at_boundaries(
        self, audio_path: str, boundaries: list[tuple[int, int]]
    ) -> list[str]:
        """Split audio at given boundaries. Returns list of chunk file paths."""
        audio = AudioSegment.from_file(audio_path)
        chunk_paths = []
        for start_ms, end_ms in boundaries:
            chunk = audio[start_ms:end_ms]
            tmp = tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            )
            tmp.close()
            chunk.export(tmp.name, format="wav")
            chunk_paths.append(tmp.name)
        return chunk_paths
