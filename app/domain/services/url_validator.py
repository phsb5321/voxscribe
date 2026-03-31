"""Instagram URL validation service."""

import re

_INSTAGRAM_REEL_PATTERN = re.compile(
    r"^https?://(?:www\.)?instagram\.com(?:/[^/?#]+)?/reels?/([A-Za-z0-9_-]+)/?(?:\?.*)?$"
)

_INSTAGRAM_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?instagram\.com(?:/|$)"
)


def validate_instagram_reel_url(url: str) -> bool:
    """Check if the URL matches a recognized Instagram reel pattern."""
    return bool(_INSTAGRAM_REEL_PATTERN.match(url))


def extract_reel_id(url: str) -> str | None:
    """Extract the reel code from an Instagram reel URL, or None if not a reel URL."""
    match = _INSTAGRAM_REEL_PATTERN.match(url)
    if match:
        return match.group(1)
    return None


def is_instagram_url(url: str) -> bool:
    """Check if the URL is any Instagram URL (profiles, posts, stories, etc.)."""
    return bool(_INSTAGRAM_URL_PATTERN.match(url))
