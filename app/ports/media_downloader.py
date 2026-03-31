"""Port interface for downloading media from URLs."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadResult:
    """Result of a media download operation."""

    file_path: str
    filename: str
    size_bytes: int
    title: str | None


class MediaDownloaderPort(ABC):
    """Abstract port for downloading media from URLs."""

    @abstractmethod
    def download_audio(self, url: str, output_dir: str) -> DownloadResult:
        """Download media from URL and extract audio.

        Returns a DownloadResult with the path to the downloaded audio file.
        Raises DownloadError on failure.
        """

    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """Check if the URL matches a supported pattern."""
