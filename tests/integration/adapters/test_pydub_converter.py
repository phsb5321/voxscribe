import pytest
import os
import wave

from pydub import AudioSegment

from app.adapters.outbound.converter.pydub_converter import PydubAudioConverter


@pytest.fixture
def converter():
    return PydubAudioConverter()


class TestPydubAudioConverter:

    def test_convert_to_wav(self, tmp_path, converter):
        # Create a 1-second silent audio segment and export as MP3
        silence = AudioSegment.silent(duration=1000)
        mp3_path = str(tmp_path / "input.mp3")
        silence.export(mp3_path, format="mp3")

        wav_path = str(tmp_path / "output.wav")
        result = converter.convert_to_wav(mp3_path, wav_path)

        assert result is True
        assert os.path.isfile(wav_path)

        # Verify the output is a valid WAV file
        with wave.open(wav_path, "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getframerate() == 16000
            assert wf.getnframes() > 0

    def test_get_duration_seconds(self, tmp_path, converter):
        # Create a 2-second silent audio segment and export as WAV
        silence = AudioSegment.silent(duration=2000)
        wav_path = str(tmp_path / "two_seconds.wav")
        silence.export(wav_path, format="wav")

        duration = converter.get_duration_seconds(wav_path)
        assert duration == pytest.approx(2.0, abs=0.1)
