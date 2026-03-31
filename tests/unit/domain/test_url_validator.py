import pytest

from app.domain.services.url_validator import (
    extract_reel_id,
    is_instagram_url,
    validate_instagram_reel_url,
)


class TestValidateInstagramReelUrl:
    """Tests for validate_instagram_reel_url()."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://www.instagram.com/reel/ABC123/",
            "https://instagram.com/reel/ABC123/",
            "https://www.instagram.com/reel/ABC123",
            "http://www.instagram.com/reel/ABC123/",
            "https://www.instagram.com/reels/ABC123/",
            "https://www.instagram.com/reels/ABC123",
            "https://www.instagram.com/username/reel/ABC123/",
            "https://instagram.com/username/reel/XYZ_789-abc/",
            "https://www.instagram.com/reel/ABC123/?igsh=some_param",
        ],
    )
    def test_valid_reel_urls(self, url):
        assert validate_instagram_reel_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "https://www.instagram.com/p/ABC123/",
            "https://www.instagram.com/stories/user/123/",
            "https://www.instagram.com/username/",
            "https://www.instagram.com/",
            "https://www.facebook.com/reel/ABC123/",
            "https://www.youtube.com/watch?v=ABC123",
            "not-a-url",
            "",
            "https://www.instagram.com/reel/",
            "https://www.instagram.com/reels/audio/ABC123/",
        ],
    )
    def test_invalid_reel_urls(self, url):
        assert validate_instagram_reel_url(url) is False


class TestExtractReelId:
    """Tests for extract_reel_id()."""

    def test_extracts_id_from_standard_url(self):
        assert extract_reel_id("https://www.instagram.com/reel/ABC123/") == "ABC123"

    def test_extracts_id_from_url_without_trailing_slash(self):
        assert extract_reel_id("https://www.instagram.com/reel/XYZ789") == "XYZ789"

    def test_extracts_id_from_reels_plural(self):
        assert extract_reel_id("https://www.instagram.com/reels/DEF456/") == "DEF456"

    def test_extracts_id_from_user_scoped_url(self):
        assert extract_reel_id("https://www.instagram.com/user/reel/GHI012/") == "GHI012"

    def test_returns_none_for_non_reel_url(self):
        assert extract_reel_id("https://www.instagram.com/p/ABC123/") is None

    def test_returns_none_for_empty_string(self):
        assert extract_reel_id("") is None


class TestIsInstagramUrl:
    """Tests for is_instagram_url()."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://www.instagram.com/reel/ABC123/",
            "https://www.instagram.com/p/ABC123/",
            "https://www.instagram.com/username/",
            "https://instagram.com/",
            "https://www.instagram.com/stories/user/123/",
        ],
    )
    def test_recognizes_instagram_urls(self, url):
        assert is_instagram_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "https://www.facebook.com/",
            "https://www.youtube.com/",
            "not-a-url",
            "",
        ],
    )
    def test_rejects_non_instagram_urls(self, url):
        assert is_instagram_url(url) is False
