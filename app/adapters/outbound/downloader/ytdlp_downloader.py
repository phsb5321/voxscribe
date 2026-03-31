"""yt-dlp implementation of MediaDownloaderPort for Instagram reel audio download."""

import logging
import os

from app.domain.exceptions import DownloadError
from app.domain.services.url_validator import validate_instagram_reel_url
from app.ports.media_downloader import DownloadResult, MediaDownloaderPort

logger = logging.getLogger(__name__)


class YtDlpMediaDownloader(MediaDownloaderPort):
    """Downloads media audio using yt-dlp."""

    def __init__(self, cookies_file: str | None = None) -> None:
        self._cookies_file = cookies_file

    def download_audio(self, url: str, output_dir: str) -> DownloadResult:
        """Download audio from URL using yt-dlp, extracting as MP3."""
        import yt_dlp

        outtmpl = os.path.join(output_dir, "%(id)s.%(ext)s")

        ydl_opts: dict = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "0",
                }
            ],
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
        }

        if self._cookies_file:
            ydl_opts["cookiefile"] = self._cookies_file

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    raise DownloadError("Failed to extract information from the URL.")

                video_id = info.get("id", "unknown")
                title = info.get("title")
                # yt-dlp post-processes to mp3, so the final file has .mp3 extension
                downloaded_path = os.path.join(output_dir, f"{video_id}.mp3")

                if not os.path.exists(downloaded_path):
                    # Try to find the file with the prepared filename
                    prepared = ydl.prepare_filename(info)
                    base = os.path.splitext(prepared)[0]
                    downloaded_path = base + ".mp3"

                if not os.path.exists(downloaded_path):
                    raise DownloadError("Download completed but audio file not found on disk.")

                size_bytes = os.path.getsize(downloaded_path)
                filename = f"reel_{video_id}.mp3"

                return DownloadResult(
                    file_path=downloaded_path,
                    filename=filename,
                    size_bytes=size_bytes,
                    title=title,
                )

        except DownloadError:
            raise
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            if "login" in error_msg or "rate" in error_msg:
                logger.warning(f"Instagram auth/rate issue for {url}: {e}")
                raise DownloadError(
                    "This reel requires authentication or is rate-limited. Ensure cookies are configured."
                ) from e
            elif "not available" in error_msg or "not found" in error_msg:
                raise DownloadError(
                    "This reel could not be found. It may be deleted or the URL may be incorrect."
                ) from e
            elif "private" in error_msg:
                raise DownloadError("This reel is from a private account and cannot be accessed.") from e
            else:
                logger.warning(f"yt-dlp download failed for {url}: {e}")
                raise DownloadError(f"Failed to download the reel: {e}") from e
        except Exception as e:
            logger.warning(f"Unexpected error downloading {url}: {e}")
            raise DownloadError("Failed to download the reel due to a network error. Please try again.") from e

    def validate_url(self, url: str) -> bool:
        """Check if URL is a valid Instagram reel URL."""
        return validate_instagram_reel_url(url)
