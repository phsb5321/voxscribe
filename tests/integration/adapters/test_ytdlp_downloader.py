"""Integration tests for YtDlpMediaDownloader (mocked yt-dlp to avoid real downloads)."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
import yt_dlp
import yt_dlp.utils

from app.adapters.outbound.downloader.ytdlp_downloader import YtDlpMediaDownloader
from app.domain.exceptions import DownloadError


class TestYtDlpMediaDownloader:
    def test_validate_url_valid_reel(self):
        downloader = YtDlpMediaDownloader()
        assert downloader.validate_url("https://www.instagram.com/reel/ABC123/") is True

    def test_validate_url_invalid(self):
        downloader = YtDlpMediaDownloader()
        assert downloader.validate_url("https://www.youtube.com/watch?v=abc") is False

    @patch("yt_dlp.YoutubeDL")
    def test_download_audio_success(self, mock_ydl_class):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake downloaded file
            fake_path = os.path.join(tmpdir, "ABC123.mp3")
            with open(fake_path, "wb") as f:
                f.write(b"fake_audio_data_here")

            mock_ydl_instance = MagicMock()
            mock_ydl_instance.extract_info.return_value = {
                "id": "ABC123",
                "title": "Test Reel",
            }
            mock_ydl_class.return_value.__enter__ = MagicMock(
                return_value=mock_ydl_instance
            )
            mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)

            downloader = YtDlpMediaDownloader()
            result = downloader.download_audio(
                "https://www.instagram.com/reel/ABC123/", tmpdir
            )

            assert result.filename == "reel_ABC123.mp3"
            assert result.title == "Test Reel"
            assert result.size_bytes == len(b"fake_audio_data_here")

    @patch("yt_dlp.YoutubeDL")
    def test_download_error_reraised_as_domain_error(self, mock_ydl_class):
        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.side_effect = yt_dlp.utils.DownloadError(
            "not available"
        )
        mock_ydl_class.return_value.__enter__ = MagicMock(
            return_value=mock_ydl_instance
        )
        mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)

        downloader = YtDlpMediaDownloader()
        with pytest.raises(DownloadError, match="could not be found"):
            downloader.download_audio(
                "https://www.instagram.com/reel/ABC123/", "/tmp"
            )

    def test_cookies_file_passed_to_constructor(self):
        downloader = YtDlpMediaDownloader(cookies_file="/path/to/cookies.txt")
        assert downloader._cookies_file == "/path/to/cookies.txt"
