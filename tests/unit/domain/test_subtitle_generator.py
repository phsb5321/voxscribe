from app.domain.services.subtitle_generator import generate_srt, generate_vtt


class TestGenerateSrt:
    def test_empty_text_returns_empty(self):
        assert generate_srt("", 60.0) == ""

    def test_single_sentence(self):
        result = generate_srt("Hello world.", 10.0)
        assert "1\n" in result
        assert "00:00:00,000 --> 00:00:10,000" in result
        assert "Hello world." in result

    def test_multiple_sentences(self):
        result = generate_srt("First sentence. Second sentence. Third sentence.", 30.0)
        assert "1\n" in result
        assert "2\n" in result
        assert "3\n" in result
        assert "First sentence." in result
        assert "Third sentence." in result

    def test_sequential_numbering(self):
        text = "One. Two. Three. Four. Five."
        result = generate_srt(text, 50.0)
        lines = result.strip().split("\n")
        numbers = [line for line in lines if line.strip().isdigit()]
        assert numbers == ["1", "2", "3", "4", "5"]

    def test_valid_timestamp_format(self):
        result = generate_srt("Test sentence.", 65.5)
        import re

        timestamps = re.findall(r"\d{2}:\d{2}:\d{2},\d{3}", result)
        assert len(timestamps) == 2  # start and end
        assert timestamps[0] == "00:00:00,000"

    def test_timestamps_cover_full_duration(self):
        result = generate_srt("Hello. World.", 120.0)
        import re

        timestamps = re.findall(r"\d{2}:\d{2}:\d{2},\d{3}", result)
        # Last timestamp should be at or near 120 seconds
        assert "00:02:00,000" in timestamps


class TestGenerateVtt:
    def test_empty_text_returns_header_only(self):
        result = generate_vtt("", 60.0)
        assert result.startswith("WEBVTT")
        assert result.strip() == "WEBVTT"

    def test_starts_with_webvtt_header(self):
        result = generate_vtt("Hello world.", 10.0)
        assert result.startswith("WEBVTT\n")

    def test_single_cue(self):
        result = generate_vtt("Hello world.", 10.0)
        assert "00:00:00.000 --> 00:00:10.000" in result
        assert "Hello world." in result

    def test_uses_dot_separator(self):
        """VTT uses dots in timestamps, not commas like SRT."""
        result = generate_vtt("Test.", 5.0)
        assert "." in result.split("-->")[0]
        assert "," not in result.split("-->")[0]

    def test_multiple_cues(self):
        result = generate_vtt("First. Second. Third.", 30.0)
        assert result.count("-->") == 3

    def test_whitespace_only_returns_header(self):
        result = generate_vtt("   ", 60.0)
        assert result.strip() == "WEBVTT"
