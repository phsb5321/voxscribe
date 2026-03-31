# Tasks: Instagram Reel URL Transcription

**Input**: Design documents from `/specs/002-instagram-reel-support/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.yaml, quickstart.md

**Tests**: Included — the project has an established test structure and testing is part of the plan.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Add the new dependency and configuration needed for Instagram reel support.

- [x] T001 Add yt-dlp dependency via `uv add yt-dlp` (updates pyproject.toml and uv.lock)
- [x] T002 Add `instagram_cookies_file` setting (Optional[str], default None, from `INSTAGRAM_COOKIES_FILE` env var) to app/config.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain-layer changes that ALL user stories depend on. These extend the core model without changing existing behavior.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 Add `DOWNLOADING` enum value to `JobStatus` in app/domain/value_objects/job_status.py. Update the `_valid_transitions` dict: add PENDING → DOWNLOADING, DOWNLOADING → CONVERTING, DOWNLOADING → FAILED. Keep existing PENDING → CONVERTING transition (used by file uploads).
- [x] T004 [P] Add `source_url: str | None = None` field to the `AudioFile` dataclass in app/domain/entities/audio_file.py. Field is optional, defaults to None. Additionally, update the `__post_init__` validation to skip the `size_bytes > 0` check when `source_url is not None` (URL-sourced files are created as stubs with `size_bytes=0` and `storage_path=""` at submit time, then populated by the worker after download). Add a comment explaining this exception.
- [x] T005 [P] Add `DownloadError(DomainError)` and `InvalidUrlError(DomainError)` exception classes to app/domain/exceptions.py
- [x] T006 [P] Create Instagram URL validation service at app/domain/services/url_validator.py. Implement `validate_instagram_reel_url(url: str) -> bool` using regex pattern `^https?://(?:www\.)?instagram\.com(?:/[^/?#]+)?/reels?/[A-Za-z0-9_-]+/?(?:\?.*)?$` (see research.md R-005). Also implement `extract_reel_id(url: str) -> str | None` to extract the reel code from the URL.
- [x] T007 [P] Create `MediaDownloaderPort` ABC at app/ports/media_downloader.py. Define abstract methods: `download_audio(url: str, output_dir: str) -> DownloadResult` and `validate_url(url: str) -> bool`. Define `DownloadResult` dataclass with fields: `file_path: str`, `filename: str`, `size_bytes: int`, `title: str | None`.
- [x] T008 Add `source_url TEXT` column to the `audio_files` table in app/adapters/outbound/persistence/sqlite_repository.py. Update `_init_db()` to add the column (use `ALTER TABLE ... ADD COLUMN` with try/except for idempotency). Update `create_audio_file()` to persist `source_url`. Update `_row_to_audio_file()` to read `source_url` from the row.

**Checkpoint**: Foundation ready — domain model supports DOWNLOADING state, source URLs, and the download port contract is defined.

---

## Phase 3: User Story 1 — Transcribe an Instagram Reel by Pasting a URL (Priority: P1) MVP

**Goal**: A user can submit an Instagram reel URL and receive a completed transcription through the existing pipeline.

**Independent Test**: Paste a valid Instagram reel URL → job is created → worker downloads audio → converts → transcribes → user views/downloads result.

### Implementation for User Story 1

- [x] T009 [P] [US1] Create yt-dlp adapter at app/adapters/outbound/downloader/__init__.py (empty) and app/adapters/outbound/downloader/ytdlp_downloader.py. Implement `YtDlpMediaDownloader(MediaDownloaderPort)` with: (1) `__init__(self, cookies_file: str | None = None)` storing the cookie path, (2) `download_audio(url, output_dir)` using `yt_dlp.YoutubeDL` with opts: `format='bestaudio/best'`, `postprocessors=[{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]`, `outtmpl=output_dir/%(id)s.%(ext)s`, and `cookiefile=cookies_file` if provided. Return `DownloadResult` with file path, generated filename, size, and title from info dict. (3) `validate_url(url)` delegating to `validate_instagram_reel_url()`. Include error handling: catch `yt_dlp.utils.DownloadError` and re-raise as domain `DownloadError` with descriptive message. Log at WARNING level on auth failures.
- [x] T010 [P] [US1] Add `SubmitUrlTranscriptionRequest` dataclass to app/application/dto.py with fields: `url: str`, `language: str = "pt-BR"`. Add `source_url: str | None = None` field to `AudioFileInfo` dataclass.
- [x] T011 [US1] Add `execute_from_url(request: SubmitUrlTranscriptionRequest) -> SubmitTranscriptionResponse` method to `SubmitTranscriptionUseCase` in app/application/submit_transcription.py. This method: (1) validates URL via `url_validator.validate_instagram_reel_url()`, raising `InvalidUrlError` if invalid, (2) extracts reel ID for filename (e.g., `reel_{id}.mp3`), (3) creates an AudioFile entity with `source_url=request.url`, `format=AudioFormat.MP3`, `size_bytes=0` (stub — validation is skipped for URL-sourced files per T004), `storage_path=""` (stub — populated by worker after download in T012), (4) saves AudioFile and creates TranscriptionJob (PENDING), (5) enqueues job, (6) returns response. The use case needs `url_validator` imported but NOT the downloader — download happens in the worker.
- [x] T012 [US1] Extend `ProcessTranscriptionUseCase` in app/application/process_transcription.py to handle URL-sourced jobs. Before the CONVERTING step, check if `audio_file.source_url is not None`. If so: (1) transition job to DOWNLOADING, (2) call `downloader.download_audio(audio_file.source_url, storage.uploads_dir)`, (3) validate downloaded size against 500MB limit (raise `FileTooLargeError` if exceeded), (4) store the downloaded file via `storage.store()`, (5) update `audio_file.storage_path` and `audio_file.size_bytes` in repository, (6) clean up the temp download file. After updating `audio_file.storage_path` and `audio_file.size_bytes` via the repository, re-read the AudioFile from the repository before proceeding to the CONVERTING step to ensure the converter reads the updated path (do not use the stale in-memory entity with empty `storage_path`). **Retry handling**: When a URL-sourced job is retried (status reset to PENDING), the worker must detect that `audio_file.source_url is not None` and `audio_file.storage_path` is empty or the file no longer exists on disk, and re-download the audio. Do not assume the previously downloaded file is still available. Then continue with existing CONVERTING flow. Add `downloader: MediaDownloaderPort` as a constructor dependency (optional, default None for backward compatibility with file-upload-only workers).
- [x] T013 [US1] Add `UrlUploadRequest` Pydantic model to app/adapters/inbound/web/schemas.py with fields: `url: str`, `language: str = "pt-BR"`. Add `source_url: str | None = None` to `AudioFileSchema`.
- [x] T014 [US1] Add `POST /api/upload-url` endpoint to app/adapters/inbound/web/routes.py. Accept JSON body (`UrlUploadRequest`), call `submit_use_case.execute_from_url()`, return `UploadResponse` (status 201). Handle `InvalidUrlError` → 422 response with detail message. Handle `DomainError` → 400 response.
- [x] T015 [US1] Wire `MediaDownloaderPort` in app/bootstrap.py. Create `YtDlpMediaDownloader(cookies_file=settings.instagram_cookies_file)` instance. Pass downloader to `ProcessTranscriptionUseCase` constructor. Add `downloader` field to the `Container` dataclass.
- [x] T016 [US1] Update `GetJobStatusUseCase` in app/application/get_job_status.py to include `source_url` in the `AudioFileInfo` DTO when returning job status. Update the `JobStatusResponse` mapping to populate `source_url` from the AudioFile entity.
- [x] T017 [US1] Write unit test for URL validator at tests/unit/domain/test_url_validator.py. Test cases: valid reel URL (with/without www, with/without trailing slash, with username prefix, /reels/ plural form), invalid URLs (profile pages, photo posts, non-Instagram URLs, empty string, malformed URLs). Test `extract_reel_id()` returns correct code.
- [x] T018 [P] [US1] Update tests/unit/domain/test_audio_file.py to test AudioFile creation with `source_url` field (both None and with a URL value).
- [x] T019 [P] [US1] Update tests for DOWNLOADING state transitions in tests/unit/domain/ (create test_job_status.py if needed or add to existing test file). Test: PENDING → DOWNLOADING (valid), DOWNLOADING → CONVERTING (valid), DOWNLOADING → FAILED (valid), CONVERTING → DOWNLOADING (invalid).
- [x] T020 [US1] Write unit test for URL submission at tests/unit/application/test_submit_transcription.py. Add test for `execute_from_url()`: mock repository and queue, verify AudioFile created with source_url, verify job enqueued. Add test for invalid URL → raises InvalidUrlError.
- [x] T021 [US1] Write integration test for yt-dlp adapter at tests/integration/adapters/test_ytdlp_downloader.py. Mock `yt_dlp.YoutubeDL` to avoid real downloads. Test: download_audio returns DownloadResult with correct fields, validate_url delegates correctly, DownloadError from yt-dlp is caught and re-raised as domain DownloadError.
- [x] T022 [US1] Write e2e test for URL upload flow at tests/e2e/test_url_upload.py. Use httpx AsyncClient with NoOpQueue (same pattern as existing e2e tests). Test: POST /api/upload-url with valid URL → 201 + job_id, POST with invalid URL → 422, GET /api/jobs/{id} shows source_url in response.

**Checkpoint**: User Story 1 is fully functional. Users can submit an Instagram reel URL via the API, jobs appear in history with source URL metadata, and the worker pipeline downloads → converts → transcribes the audio.

---

## Phase 4: User Story 2 — Seamless Upload Experience for Both Files and URLs (Priority: P2)

**Goal**: The upload page UI provides an intuitive URL input alongside the existing file upload, with clear mode toggling between the two methods.

**Independent Test**: Visit the upload page → see URL input option → paste a URL → submit → job created. Also verify file upload still works unchanged.

### Implementation for User Story 2

- [x] T023 [US2] Add URL input section to app/adapters/inbound/web/templates/upload.html. Add a tab/toggle UI element ("Upload File" / "Paste URL") above the existing drop zone. When "Paste URL" is selected: show a URL text input field + language selector + submit button; hide/disable the file drop zone. When "Upload File" is selected: show the existing drop zone; hide/disable the URL input. Both modes share the same language selector. Style the URL input to match the existing dark theme and design system.
- [x] T024 [US2] Add JavaScript logic in upload.html for URL submission. Implement: (1) mode toggle handler that switches between file and URL views, (2) `submitUrl()` function that sends `POST /api/upload-url` with JSON body `{url, language}` via fetch API, (3) on success: redirect to job page (same as file upload), (4) on error: show toast notification with the error detail message, (5) URL input validation (basic format check before submit). Ensure the existing file upload JS is not broken.
- [x] T025 [US2] Update the job history display in upload.html to show source URL indicator for URL-sourced jobs. When `audio_file.source_url` is present in job data, show a small icon/badge (e.g., a link icon) next to the filename to indicate it came from a URL. Optionally show the source URL in a tooltip on hover.

**Checkpoint**: Users can toggle between file upload and URL paste on the same page. Both methods work independently. Job history shows URL source indicator.

---

## Phase 5: User Story 3 — Graceful Handling of Download Failures (Priority: P3)

**Goal**: When URL downloads fail, users receive specific, actionable error messages rather than generic failures.

**Independent Test**: Submit URLs for private reels, deleted reels, non-reel Instagram links, and invalid URLs → each produces a distinct, helpful error message.

### Implementation for User Story 3

- [x] T026 [US3] Enhance error handling in app/adapters/outbound/downloader/ytdlp_downloader.py. Parse yt-dlp error messages to distinguish: (1) "login required" / "rate limit" → DownloadError("This reel requires authentication or is rate-limited. Ensure cookies are configured."), (2) "not available" / "not found" → DownloadError("This reel could not be found. It may be deleted or the URL may be incorrect."), (3) "private" → DownloadError("This reel is from a private account and cannot be accessed."), (4) network/timeout errors → DownloadError("Failed to download the reel due to a network error. Please try again."), (5) any other yt-dlp error → DownloadError with the original message wrapped in user-friendly text. Log the raw yt-dlp error at WARNING level for debugging.
- [x] T027 [US3] Add non-reel Instagram URL detection in app/domain/services/url_validator.py. Add `is_instagram_url(url: str) -> bool` to detect any Instagram URL (profiles, posts, stories). In the submit flow, if `is_instagram_url()` is True but `validate_instagram_reel_url()` is False, raise `InvalidUrlError("This is an Instagram link but not a reel. Only reel URLs are supported (e.g., instagram.com/reel/...).")` instead of a generic invalid URL error.
- [x] T028 [US3] Update app/application/submit_transcription.py `execute_from_url()` to use the enhanced URL validation from T027: check `is_instagram_url()` for specific messaging before falling back to generic "Invalid URL" error.
- [x] T029 [US3] Update the job status page (app/adapters/inbound/web/templates/) to display download-specific error messages prominently when a URL-sourced job fails with a DOWNLOADING status. Show the error_message from the job and include a "Try Again" button (using existing retry functionality).

**Checkpoint**: All failure scenarios produce specific, actionable error messages. Users understand why a URL failed and what they can do about it.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and documentation.

- [x] T030 [P] Add `INSTAGRAM_COOKIES_FILE` env var documentation to docker-compose.yml comments and/or README if one exists
- [x] T031 [P] Run full test suite (`uv run pytest tests/ -v`) and fix any regressions — verify all existing tests still pass
- [x] T032 Verify existing file upload flow is completely unchanged (regression check): upload a file via the UI, confirm job completes, confirm no DOWNLOADING state appears for file uploads

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (yt-dlp must be installed) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 — core flow must work before UI or error polish
- **User Story 2 (Phase 4)**: Depends on Phase 3 (needs `POST /api/upload-url` endpoint to exist for the JS to call)
- **User Story 3 (Phase 5)**: Depends on Phase 3 (needs the yt-dlp adapter and download flow to exist for error handling refinement)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P2)**: Depends on US1's API endpoint (T014) being complete — the frontend needs a backend to call
- **US3 (P3)**: Depends on US1's yt-dlp adapter (T009) and submit flow (T011) being complete — error handling refines existing code

### Within Each User Story

- Models/ports before services
- Services before endpoints
- Core implementation before tests (tests are written alongside, not TDD)
- Story complete before moving to next priority

### Parallel Opportunities

Within Phase 2 (Foundational): T004, T005, T006, T007 can all run in parallel (different files).

Within Phase 3 (US1): T009 and T010 can run in parallel. T018 and T019 can run in parallel.

Within Phase 4 (US2): T023 must come before T024 (JS depends on HTML structure). T025 is independent.

---

## Parallel Example: Phase 2 (Foundational)

```text
# These 4 tasks touch different files and can run simultaneously:
T004: Add source_url to AudioFile entity       → app/domain/entities/audio_file.py
T005: Add DownloadError, InvalidUrlError        → app/domain/exceptions.py
T006: Create URL validator service              → app/domain/services/url_validator.py
T007: Create MediaDownloaderPort ABC            → app/ports/media_downloader.py
```

## Parallel Example: User Story 1

```text
# These 2 tasks touch different files and can run simultaneously:
T009: Create yt-dlp adapter                    → app/adapters/outbound/downloader/ytdlp_downloader.py
T010: Add SubmitUrlTranscriptionRequest DTO     → app/application/dto.py

# After T017 completes, these test tasks can run in parallel:
T018: Test AudioFile with source_url            → tests/unit/domain/test_audio_file.py
T019: Test DOWNLOADING state transitions        → tests/unit/domain/test_job_status.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T008)
3. Complete Phase 3: User Story 1 (T009-T022)
4. **STOP and VALIDATE**: Test via API (`curl -X POST /api/upload-url -d '{"url": "..."}'`)
5. Deploy/demo if ready — API-only MVP works without UI changes

### Incremental Delivery

1. Setup + Foundational → Domain model ready
2. Add User Story 1 → API-based URL transcription works (MVP!)
3. Add User Story 2 → Users can paste URLs in the web UI
4. Add User Story 3 → Error messages are specific and actionable
5. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Cookie file setup is an operational concern (documented, not automated)
- yt-dlp's Instagram support is functional but fragile — keep yt-dlp updated
- The DOWNLOADING state only appears for URL-sourced jobs; file uploads skip it entirely
