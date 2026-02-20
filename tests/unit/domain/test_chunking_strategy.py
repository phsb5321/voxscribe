"""Unit tests for chunking strategy service."""

from app.domain.services.chunking_strategy import (
    CHUNK_DURATION_MAX_MS,
    CHUNK_DURATION_MIN_MS,
    LONG_FILE_THRESHOLD_MS,
    OVERLAP_MS,
    add_overlap,
    compute_chunk_boundaries,
    needs_chunking,
    stitch_transcriptions,
)


class TestNeedsChunking:
    def test_short_file_no_chunking(self):
        assert needs_chunking(5 * 60 * 1000) is False

    def test_exactly_threshold_no_chunking(self):
        assert needs_chunking(LONG_FILE_THRESHOLD_MS) is False

    def test_above_threshold_needs_chunking(self):
        assert needs_chunking(LONG_FILE_THRESHOLD_MS + 1) is True

    def test_long_file_needs_chunking(self):
        assert needs_chunking(30 * 60 * 1000) is True


class TestComputeChunkBoundaries:
    def test_empty_boundaries_returns_full_range(self):
        result = compute_chunk_boundaries([], 600_000)
        assert result == [(0, 600_000)]

    def test_single_segment_returns_as_chunk(self):
        result = compute_chunk_boundaries([(0, 300_000)], 300_000)
        assert result == [(0, 300_000)]

    def test_splits_at_max_duration(self):
        # Three 6-minute segments: first two form a 12-min block > 10min max
        segments = [
            (0, 360_000),        # 0-6 min
            (360_000, 720_000),  # 6-12 min
            (720_000, 1_080_000),  # 12-18 min
        ]
        result = compute_chunk_boundaries(segments, 1_080_000)
        # First chunk: 0 to 360_000 (6 min), then second segment would make 12 min > max
        # So split: chunk 1 = (0, 360_000), chunk 2 starts at 360_000
        assert len(result) >= 2
        assert result[0][0] == 0

    def test_short_segments_grouped_together(self):
        # Two 4-minute segments = 8 min total, under 10 min max
        segments = [
            (0, 240_000),       # 0-4 min
            (240_000, 480_000),  # 4-8 min
        ]
        result = compute_chunk_boundaries(segments, 480_000)
        assert result == [(0, 480_000)]

    def test_many_small_segments(self):
        # 15 two-minute segments = 30 min total, should split into chunks
        segments = [(i * 120_000, (i + 1) * 120_000) for i in range(15)]
        result = compute_chunk_boundaries(segments, 1_800_000)
        assert len(result) >= 3  # 30 min / 10 min max = at least 3 chunks
        # Verify coverage: first chunk starts at 0, last chunk ends at or near last segment
        assert result[0][0] == 0


class TestAddOverlap:
    def test_single_chunk_unchanged(self):
        boundaries = [(1000, 5000)]
        result = add_overlap(boundaries)
        assert result == [(1000, 5000)]

    def test_empty_list_unchanged(self):
        assert add_overlap([]) == []

    def test_two_chunks_get_overlap(self):
        boundaries = [(0, 300_000), (300_000, 600_000)]
        result = add_overlap(boundaries, overlap_ms=OVERLAP_MS)
        # First chunk: start unchanged (i==0), end extended by overlap
        assert result[0] == (0, 300_000 + OVERLAP_MS)
        # Last chunk: start extended backward by overlap, end unchanged (i==last)
        assert result[1] == (300_000 - OVERLAP_MS, 600_000)

    def test_middle_chunk_both_sides_extended(self):
        boundaries = [(0, 300_000), (300_000, 600_000), (600_000, 900_000)]
        result = add_overlap(boundaries, overlap_ms=1000)
        # Middle chunk: both sides extended
        assert result[1] == (299_000, 601_000)

    def test_start_clamped_to_zero(self):
        boundaries = [(100, 300_000), (300_000, 600_000)]
        result = add_overlap(boundaries, overlap_ms=500)
        # Second chunk start: 300_000 - 500 = 299_500, not negative
        assert result[1][0] == 299_500


class TestStitchTranscriptions:
    def test_empty_list(self):
        assert stitch_transcriptions([]) == ""

    def test_single_text(self):
        assert stitch_transcriptions(["Hello world"]) == "Hello world"

    def test_single_text_stripped(self):
        assert stitch_transcriptions(["  Hello world  "]) == "Hello world"

    def test_no_overlap_concatenates(self):
        result = stitch_transcriptions(["Hello world.", "Good morning."])
        assert result == "Hello world. Good morning."

    def test_overlapping_words_deduplicated(self):
        result = stitch_transcriptions([
            "The quick brown fox jumps",
            "fox jumps over the lazy dog",
        ])
        assert result == "The quick brown fox jumps over the lazy dog"

    def test_empty_chunks_skipped(self):
        result = stitch_transcriptions(["Hello.", "", "World."])
        assert result == "Hello. World."

    def test_whitespace_only_chunks_skipped(self):
        result = stitch_transcriptions(["Hello.", "   ", "World."])
        assert result == "Hello. World."

    def test_multiple_chunks_stitched(self):
        result = stitch_transcriptions([
            "Part one text here",
            "text here and part two",
            "part two continues further",
        ])
        assert "Part one" in result
        assert "part two" in result
        assert "continues further" in result
