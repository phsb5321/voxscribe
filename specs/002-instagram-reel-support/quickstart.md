# Quickstart: Instagram Reel URL Transcription

**Branch**: `002-instagram-reel-support` | **Date**: 2026-03-30

## What This Feature Does

Adds a URL input to Voxscribe so users can paste an Instagram reel link and get a transcription — no manual download needed. The system uses yt-dlp to extract the reel's audio, then runs it through the existing transcription pipeline.

## Key Design Decisions

1. **yt-dlp for downloads** — industry-standard media downloader with Instagram support and Python API
2. **Cookie-based auth** — Instagram requires authentication even for public reels; optional cookie file via `INSTAGRAM_COOKIES_FILE` env var
3. **New DOWNLOADING state** — added to the job state machine for progress visibility during URL downloads
4. **New MediaDownloaderPort** — follows existing hexagonal architecture; yt-dlp adapter implements the port
5. **Separate API endpoint** — `POST /api/upload-url` accepts JSON `{url, language}` rather than overloading the multipart file upload endpoint
6. **Download in background worker** — avoids blocking the HTTP response; download time is visible via DOWNLOADING state

## Architecture Overview

```
User pastes URL → POST /api/upload-url → Validate URL → Create Job (PENDING) → Enqueue
                                                                                    ↓
Worker picks up → DOWNLOADING (yt-dlp extracts audio) → Store AudioFile → CONVERTING → TRANSCRIBING → COMPLETED
```

## Files to Create

| File | Purpose |
|------|---------|
| `app/ports/media_downloader.py` | MediaDownloaderPort ABC + DownloadResult value object |
| `app/adapters/outbound/downloader/ytdlp_downloader.py` | yt-dlp implementation of MediaDownloaderPort |
| `app/domain/services/url_validator.py` | Instagram URL validation logic |

## Files to Modify

| File | Change |
|------|--------|
| `app/domain/value_objects/job_status.py` | Add DOWNLOADING enum value and state transitions |
| `app/domain/entities/audio_file.py` | Add optional `source_url` field |
| `app/application/dto.py` | Add `SubmitUrlTranscriptionRequest` DTO |
| `app/application/submit_transcription.py` | Add `execute_from_url()` method or new use case |
| `app/application/process_transcription.py` | Add DOWNLOADING step for URL-sourced jobs |
| `app/adapters/inbound/web/routes.py` | Add `POST /api/upload-url` endpoint |
| `app/adapters/inbound/web/schemas.py` | Add `UrlUploadRequest` Pydantic schema |
| `app/adapters/inbound/web/templates/upload.html` | Add URL input section to UI |
| `app/adapters/outbound/persistence/sqlite_repository.py` | Add `source_url` column to audio_files table |
| `app/bootstrap.py` | Wire MediaDownloaderPort adapter |
| `app/config.py` | Add `instagram_cookies_file` setting |
| `pyproject.toml` | Add `yt-dlp` dependency |
| `Dockerfile` | Document cookie file mount (no build changes needed) |

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `INSTAGRAM_COOKIES_FILE` | *(none)* | Path to Netscape-format cookies.txt for Instagram auth. Optional but recommended. |

## Dependencies

| Package | Purpose | System-level? |
|---------|---------|---------------|
| `yt-dlp` | Download Instagram reel audio | No (Python package) |
| `ffmpeg` | Audio extraction post-processing | Yes (already in Dockerfile) |
