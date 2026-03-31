"""Generate SRT and VTT subtitle files from transcription text."""

import re


def _split_into_segments(text: str, max_words: int = 10) -> list[str]:
    """Split text into segments of roughly max_words words each."""
    if not text or not text.strip():
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    segments: list[str] = []

    for sentence in sentences:
        words = sentence.split()
        if len(words) <= max_words:
            segments.append(sentence)
        else:
            for i in range(0, len(words), max_words):
                chunk = " ".join(words[i : i + max_words])
                segments.append(chunk)

    return [s for s in segments if s.strip()]


def _format_timestamp_srt(seconds: float) -> str:
    """Format seconds as HH:MM:SS,mmm (SRT format)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _format_timestamp_vtt(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm (VTT format)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def generate_srt(text: str, duration_seconds: float) -> str:
    """Generate SRT subtitle content from transcription text and total duration."""
    segments = _split_into_segments(text)
    if not segments:
        return ""

    total_chars = sum(len(s) for s in segments)
    lines: list[str] = []
    current_time = 0.0

    for i, segment in enumerate(segments):
        proportion = len(segment) / total_chars if total_chars > 0 else 1 / len(segments)
        segment_duration = duration_seconds * proportion
        end_time = min(current_time + segment_duration, duration_seconds)

        start_ts = _format_timestamp_srt(current_time)
        end_ts = _format_timestamp_srt(end_time)

        lines.append(f"{i + 1}")
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(segment)
        lines.append("")

        current_time = end_time

    return "\n".join(lines)


def generate_vtt(text: str, duration_seconds: float) -> str:
    """Generate WebVTT subtitle content from transcription text and total duration."""
    segments = _split_into_segments(text)
    if not segments:
        return "WEBVTT\n"

    total_chars = sum(len(s) for s in segments)
    lines: list[str] = ["WEBVTT", ""]
    current_time = 0.0

    for segment in segments:
        proportion = len(segment) / total_chars if total_chars > 0 else 1 / len(segments)
        segment_duration = duration_seconds * proportion
        end_time = min(current_time + segment_duration, duration_seconds)

        start_ts = _format_timestamp_vtt(current_time)
        end_ts = _format_timestamp_vtt(end_time)

        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(segment)
        lines.append("")

        current_time = end_time

    return "\n".join(lines)
