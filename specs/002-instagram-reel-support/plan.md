# Implementation Plan: Instagram Reel URL Transcription

**Branch**: `002-instagram-reel-support` | **Date**: 2026-03-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-instagram-reel-support/spec.md`

## Summary

Add Instagram reel URL transcription to Voxscribe. Users paste a reel URL, the system downloads the audio via yt-dlp in a background worker, then processes it through the existing transcription pipeline. Requires a new `MediaDownloaderPort` (with yt-dlp adapter), a `DOWNLOADING` job state, a `source_url` field on AudioFile, a new API endpoint (`POST /api/upload-url`), and a URL input section in the upload UI.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI, yt-dlp (new), pydub, faster-whisper/openai/groq, RQ, Redis, Jinja2
**Storage**: SQLite (existing), local filesystem (existing)
**Testing**: pytest, httpx, pytest-asyncio
**Target Platform**: Linux server (Docker)
**Project Type**: Web application (FastAPI + Jinja2 templates + vanilla JS)
**Performance Goals**: URL submission response < 1s; download + transcription time proportional to reel length
**Constraints**: Instagram requires cookie-based auth for reliable access; yt-dlp support is functional but fragile
**Scale/Scope**: Single-user/small-team tool; sequential URL downloads (no parallel downloading)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check

| Principle | Status | Assessment |
|-----------|--------|------------|
| **I. Simplicity** | PASS | No new architectural layers. Adding a 6th port follows the existing hexagonal pattern. The download step extends `ProcessTranscriptionUseCase` rather than creating new frameworks or abstractions. |
| **II. Reliability** | PASS | All external calls (yt-dlp download, Instagram network) include error handling with human-readable diagnostics. Failed downloads produce descriptive error messages. Retry mechanism reuses existing 3-retry logic. |
| **III. Containerized Deployment** | PASS | yt-dlp is a Python dependency (no system packages). ffmpeg already in Dockerfile. Cookie file is a volume mount, not a Dockerfile change. |
| **IV. Concurrent Processing** | PASS | Each URL download job is independent — no shared mutable state. Downloads run in the existing RQ worker. |
| **V. Dependency Hygiene** | PASS | yt-dlp will be added via `uv add yt-dlp`. No undeclared imports. |

### Post-Design Re-Check

| Principle | Status | Assessment |
|-----------|--------|------------|
| **I. Simplicity** | PASS | Design adds one port, one adapter, one URL validator service, one enum value, one field. No new patterns introduced. |
| **II. Reliability** | PASS | URL validation at submit time (fast fail). Download errors produce specific messages (private, deleted, network). Cookie auth failure logged at WARNING. |
| **III. Containerized Deployment** | PASS | No Dockerfile build changes. Cookie mount documented in quickstart.md. |
| **IV. Concurrent Processing** | PASS | RQ worker processes one job at a time. URL download is I/O-bound and isolated per job. |
| **V. Dependency Hygiene** | PASS | `yt-dlp` added to pyproject.toml. `INSTAGRAM_COOKIES_FILE` env var added to config.py. |

**GATE RESULT: PASS** — No violations.

## Project Structure

### Documentation (this feature)

```text
specs/002-instagram-reel-support/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 — yt-dlp research, auth, architecture decisions
├── data-model.md        # Phase 1 — entity changes, new port, DB schema
├── quickstart.md        # Phase 1 — implementation overview, file map, config
├── contracts/
│   └── api.yaml         # Phase 1 — OpenAPI contract for new endpoint
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
app/
├── domain/
│   ├── entities/
│   │   └── audio_file.py          # MODIFY: add source_url field
│   ├── value_objects/
│   │   └── job_status.py          # MODIFY: add DOWNLOADING state + transitions
│   ├── services/
│   │   ├── audio_validator.py     # EXISTING: no changes
│   │   ├── chunking_strategy.py   # EXISTING: no changes
│   │   └── url_validator.py       # CREATE: Instagram URL validation
│   └── exceptions.py             # MODIFY: add DownloadError, InvalidUrlError
├── ports/
│   └── media_downloader.py       # CREATE: MediaDownloaderPort ABC
├── application/
│   ├── dto.py                    # MODIFY: add SubmitUrlTranscriptionRequest
│   ├── submit_transcription.py   # MODIFY: add execute_from_url() or new method
│   └── process_transcription.py  # MODIFY: add DOWNLOADING step for URL jobs
├── adapters/
│   ├── inbound/
│   │   └── web/
│   │       ├── routes.py         # MODIFY: add POST /api/upload-url
│   │       ├── schemas.py        # MODIFY: add UrlUploadRequest/Response
│   │       └── templates/
│   │           └── upload.html   # MODIFY: add URL input section
│   └── outbound/
│       ├── downloader/
│       │   ├── __init__.py       # CREATE
│       │   └── ytdlp_downloader.py  # CREATE: yt-dlp MediaDownloaderPort impl
│       └── persistence/
│           └── sqlite_repository.py  # MODIFY: add source_url column
├── bootstrap.py                  # MODIFY: wire MediaDownloaderPort
└── config.py                     # MODIFY: add instagram_cookies_file setting

tests/
├── unit/
│   ├── domain/
│   │   ├── test_url_validator.py     # CREATE: URL validation tests
│   │   └── test_job_status.py        # MODIFY: test DOWNLOADING transitions
│   └── application/
│       └── test_submit_transcription.py  # MODIFY: test URL submission
├── integration/
│   └── adapters/
│       └── test_ytdlp_downloader.py  # CREATE: yt-dlp adapter tests (with mocks)
└── e2e/
    └── test_url_upload.py            # CREATE: full URL upload flow test
```

**Structure Decision**: Follows the existing hexagonal architecture. New files are placed in their natural locations within the ports/adapters pattern. The `downloader/` directory under `outbound/` mirrors the existing `converter/`, `storage/`, `engines/`, and `queue/` directories.

## Complexity Tracking

> No constitution violations — this section is empty.
