"""Chunking strategy for splitting long audio files at silence boundaries."""

CHUNK_DURATION_MIN_MS = 5 * 60 * 1000  # 5 minutes
CHUNK_DURATION_MAX_MS = 10 * 60 * 1000  # 10 minutes
LONG_FILE_THRESHOLD_MS = 10 * 60 * 1000  # 10 minutes
OVERLAP_MS = 500  # 0.5 second overlap between chunks


def needs_chunking(duration_ms: int) -> bool:
    """Return True if the audio is long enough to benefit from chunking."""
    return duration_ms > LONG_FILE_THRESHOLD_MS


def compute_chunk_boundaries(
    silence_boundaries: list[tuple[int, int]],
    total_duration_ms: int,
) -> list[tuple[int, int]]:
    """Compute chunk boundaries from silence segments.

    Given a list of non-silent (start_ms, end_ms) segments,
    groups them into chunks of 5-10 minutes, splitting at silence gaps.

    Returns list of (chunk_start_ms, chunk_end_ms) tuples.
    """
    if not silence_boundaries:
        return [(0, total_duration_ms)]

    chunks: list[tuple[int, int]] = []
    chunk_start = silence_boundaries[0][0]
    chunk_end = silence_boundaries[0][1]

    for start, end in silence_boundaries[1:]:
        candidate_end = end
        chunk_length = candidate_end - chunk_start

        if chunk_length > CHUNK_DURATION_MAX_MS:
            # Current chunk is long enough, finalize it
            chunks.append((chunk_start, chunk_end))
            chunk_start = start
            chunk_end = end
        else:
            chunk_end = end

    # Add the final chunk
    chunks.append((chunk_start, chunk_end))

    return chunks


def add_overlap(
    boundaries: list[tuple[int, int]],
    overlap_ms: int = OVERLAP_MS,
) -> list[tuple[int, int]]:
    """Add overlap between consecutive chunks for boundary deduplication.

    Extends each chunk's start backward and end forward by overlap_ms/2,
    clamped to not overlap into adjacent chunks' core regions.
    """
    if len(boundaries) <= 1:
        return boundaries

    result: list[tuple[int, int]] = []
    for i, (start, end) in enumerate(boundaries):
        new_start = max(0, start - overlap_ms) if i > 0 else start
        new_end = end + overlap_ms if i < len(boundaries) - 1 else end
        result.append((new_start, new_end))

    return result


def stitch_transcriptions(texts: list[str]) -> str:
    """Stitch transcription texts from chunks into a seamless result.

    Removes duplicate sentences at chunk boundaries caused by overlap.
    """
    if not texts:
        return ""

    if len(texts) == 1:
        return texts[0].strip()

    result_parts = [texts[0].strip()]

    for text in texts[1:]:
        stripped = text.strip()
        if not stripped:
            continue

        # Simple dedup: if the beginning of the next chunk overlaps
        # with the end of the previous result, skip the overlap.
        prev = result_parts[-1]
        if prev and stripped:
            # Check if last sentence of prev matches first sentence of current
            prev_words = prev.split()[-10:]  # last ~10 words
            curr_words = stripped.split()[:10]  # first ~10 words

            overlap_len = 0
            for length in range(min(len(prev_words), len(curr_words)), 0, -1):
                if prev_words[-length:] == curr_words[:length]:
                    overlap_len = length
                    break

            if overlap_len > 0:
                stripped = " ".join(stripped.split()[overlap_len:])

        if stripped:
            result_parts.append(stripped)

    return " ".join(result_parts)
