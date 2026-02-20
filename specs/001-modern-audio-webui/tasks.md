# Tasks: Modern Audio Transcription Web UI

**Input**: Design documents from `/specs/001-modern-audio-webui/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: Included — plan.md explicitly defines test structure with pytest.

**Organization**: Tasks grouped by user story (P1-P4) from spec.md. Each story is independently testable.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- All file paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project skeleton and install all dependencies

- [x] T001 Create hexagonal directory structure with all package `__init__.py` files per plan.md project structure (`app/`, `app/domain/entities/`, `app/domain/value_objects/`, `app/domain/services/`, `app/ports/`, `app/application/`, `app/adapters/inbound/web/`, `app/adapters/outbound/engines/`, `app/adapters/outbound/storage/`, `app/adapters/outbound/persistence/`, `app/adapters/outbound/converter/`, `app/adapters/outbound/queue/`, `tests/unit/domain/`, `tests/unit/application/`, `tests/integration/adapters/`, `tests/e2e/`)
- [x] T002 Update `pyproject.toml` with all new dependencies (fastapi, uvicorn[standard], jinja2, python-multipart, faster-whisper, openai, rq, redis, pydub, httpx) and fix missing dnspython; sync `requirements.txt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain model, port interfaces, and configuration that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 [P] Create AudioFormat enum (MP3, WAV, FLAC, OGG) in `app/domain/value_objects/audio_format.py` and JobStatus enum (PENDING, CONVERTING, TRANSCRIBING, COMPLETED, FAILED) in `app/domain/value_objects/job_status.py`
- [x] T004 [P] Create domain exceptions (TranscriptionError, InvalidAudioFormatError, FileTooLargeError, InvalidStateTransitionError, StorageError) in `app/domain/exceptions.py`
- [x] T005 Create AudioFile dataclass with validation (format, size <=500MB, filename sanitization) in `app/domain/entities/audio_file.py`
- [x] T006 Create TranscriptionJob dataclass with state machine (valid transitions per data-model.md, retry_count <=3, updated_at refresh on transition) in `app/domain/entities/transcription_job.py`
- [x] T007 [P] Create TranscriptionResult dataclass in `app/domain/entities/transcription_result.py`
- [x] T008 Create all five port ABC interfaces per data-model.md signatures: TranscriptionEnginePort in `app/ports/transcription_engine.py`, AudioStoragePort in `app/ports/audio_storage.py`, AudioConverterPort in `app/ports/audio_converter.py`, JobRepositoryPort in `app/ports/job_repository.py`, JobQueuePort in `app/ports/job_queue.py`
- [x] T009 [P] Create environment-based configuration module (TRANSCRIPTION_ENGINE, OPENAI_API_KEY, REDIS_URL, DATA_DIR, DATABASE_URL) with defaults in `app/config.py`
- [x] T010 [P] Create application DTOs (SubmitTranscriptionRequest, SubmitTranscriptionResponse, JobStatusResponse, TranscriptionResultResponse) in `app/application/dto.py`
- [x] T011 [P] Create audio validator service (validate format against AudioFormat enum, validate size <=500MB, validate filename) in `app/domain/services/audio_validator.py`

**Checkpoint**: Domain model and interfaces ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Upload and Transcribe Audio via Web Browser (Priority: P1) MVP

**Goal**: User uploads audio via browser, sees real-time progress, gets pt-BR transcription with copy/download

**Independent Test**: Upload a 2-minute MP3 file in pt-BR via browser, observe progress updates, verify transcription appears and can be downloaded as TXT

### Outbound Adapters

- [x] T012 [P] [US1] Implement SQLite job repository (create tables on init, CRUD for AudioFile/TranscriptionJob/TranscriptionResult per data-model.md schema) in `app/adapters/outbound/persistence/sqlite_repository.py`
- [x] T013 [P] [US1] Implement local filesystem storage adapter (store files under DATA_DIR/uploads/, retrieve by path, delete) in `app/adapters/outbound/storage/local_file_storage.py`
- [x] T014 [P] [US1] Implement pydub audio converter adapter (convert to 16kHz mono WAV via ffmpeg, get duration) in `app/adapters/outbound/converter/pydub_converter.py`
- [x] T015 [P] [US1] Implement RQ job queue adapter (enqueue job_id to Redis for worker pickup) in `app/adapters/outbound/queue/rq_queue.py`
- [x] T016 [P] [US1] Implement faster-whisper transcription engine adapter (load large-v3-turbo model, transcribe audio_path in given language, return full text) in `app/adapters/outbound/engines/faster_whisper_engine.py`

### Application Use Cases

- [x] T017 [P] [US1] Implement submit_transcription use case (validate file via audio_validator, store via AudioStoragePort, create AudioFile + TranscriptionJob, enqueue via JobQueuePort) in `app/application/submit_transcription.py`
- [x] T018 [P] [US1] Implement process_transcription use case (transition PENDING→CONVERTING, convert via AudioConverterPort, transition CONVERTING→TRANSCRIBING, transcribe via TranscriptionEnginePort, save TranscriptionResult, transition→COMPLETED; handle errors→FAILED with retry logic) in `app/application/process_transcription.py`
- [x] T019 [P] [US1] Implement get_job_status use case (query JobRepositoryPort for job, audio_file, and result; return DTOs) in `app/application/get_job_status.py`

### Application Wiring

- [x] T020 [US1] Create bootstrap composition root (wire all concrete adapters to port interfaces based on config, instantiate use cases with injected ports) in `app/bootstrap.py`
- [x] T021 [US1] Create FastAPI app factory `create_app()` (call bootstrap, mount routes, configure Jinja2, add CORS/middleware) in `app/main.py`

### Inbound Web Adapter

- [x] T022 [P] [US1] Create Pydantic request/response schemas matching contracts/api.md (UploadResponse, JobStatusResponse, TranscriptionResultResponse, ProgressEvent) in `app/adapters/inbound/web/schemas.py`
- [x] T023 [US1] Create Jinja2 templates: `base.html` (layout with HTMX CDN), `upload.html` (drag-and-drop zone, format/size validation, upload form posting to /api/upload), `job.html` (status display, SSE progress via hx-ext="sse", result text, copy-to-clipboard JS, download button) in `app/adapters/inbound/web/templates/`
- [x] T024 [US1] Implement FastAPI routes per contracts/api.md: GET / (render upload.html), POST /api/upload (multipart, 201+redirect), GET /jobs/{job_id} (render job.html), GET /api/jobs/{job_id} (JSON status), GET /api/jobs/{job_id}/result (JSON result), GET /api/jobs/{job_id}/result/download (text/plain attachment), GET /api/jobs/{job_id}/progress (SSE StreamingResponse) in `app/adapters/inbound/web/routes.py`

### Background Worker

- [x] T025 [US1] Implement RQ worker task handler (receive job_id, call process_transcription use case via bootstrap, update progress via repository) in `app/adapters/inbound/worker.py`

### Tests for User Story 1

- [x] T026 [P] [US1] Write unit tests for AudioFile validation and TranscriptionJob state machine transitions (valid and invalid) in `tests/unit/domain/test_audio_file.py` and `tests/unit/domain/test_transcription_job.py`
- [x] T027 [P] [US1] Write unit tests for submit_transcription and process_transcription use cases with mocked ports in `tests/unit/application/test_submit_transcription.py` and `tests/unit/application/test_process_transcription.py`
- [x] T028 [P] [US1] Write integration tests for SQLite repository, local file storage, and pydub converter (real I/O, temp dirs) in `tests/integration/adapters/test_sqlite_repository.py`, `tests/integration/adapters/test_local_file_storage.py`, `tests/integration/adapters/test_pydub_converter.py`

**Checkpoint**: Upload-to-transcription flow works end-to-end via web browser with faster-whisper engine. MVP complete.

---

## Phase 4: User Story 2 — Swap Transcription Engine Without Code Changes (Priority: P2)

**Goal**: Switch between faster-whisper (local) and OpenAI gpt-4o-mini-transcribe (cloud) via config only

**Independent Test**: Transcribe the same file with TRANSCRIPTION_ENGINE=faster-whisper then TRANSCRIPTION_ENGINE=openai — both produce valid output without code changes

- [x] T029 [US2] Implement OpenAI gpt-4o-mini-transcribe engine adapter (use openai SDK, handle 25MB file limit per chunk, respect OPENAI_API_KEY from config) in `app/adapters/outbound/engines/openai_engine.py`
- [x] T030 [US2] Update bootstrap composition root to select engine adapter based on TRANSCRIPTION_ENGINE config value ("faster-whisper" or "openai") in `app/bootstrap.py`
- [x] T031 [US2] Add engine metadata to TranscriptionResult and job status responses (engine_name field populated from config) in `app/adapters/inbound/web/routes.py`

**Checkpoint**: Engine swap works via environment variable. Both engines produce valid transcriptions.

---

## Phase 5: User Story 3 — Deploy to Dokku Server via Git Push (Priority: P3)

**Goal**: Full deployment to ProxMox.Dokku with HTTPS, persistent storage, and background worker

**Independent Test**: `git push dokku main`, verify HTTPS web UI, upload file, confirm transcription completes. Redeploy and verify data persists.

- [x] T032 [P] [US3] Update Dockerfile: Python 3.12 base, multi-stage build, install ffmpeg/libsndfile1, copy app/, EXPOSE 5000, CMD uvicorn in `Dockerfile`
- [x] T033 [P] [US3] Create Procfile with web (gunicorn with uvicorn workers on $PORT) and worker (rq worker --url $REDIS_URL) process types in `Procfile`
- [x] T034 [P] [US3] Create docker-compose.yml for local dev: web service (port 5000, mounts DATA/), worker service (same image, rq command), redis service (port 6379) in `docker-compose.yml`
- [x] T035 [US3] Implement health check endpoint (GET /api/health returning engine name, redis connectivity status) in `app/adapters/inbound/web/routes.py`
- [x] T036 [US3] Update START.SH to launch new application structure (uvicorn app.main:create_app) in `START.SH`

**Checkpoint**: Application deployable via `git push dokku main` with persistent storage and SSL.

---

## Phase 6: User Story 4 — Process Multiple Files Concurrently (Priority: P4)

**Goal**: Upload multiple files with independent progress; auto-chunk long files at silence boundaries

**Independent Test**: Upload 3 files simultaneously, observe independent progress for each, verify all produce complete transcriptions

- [x] T037 [US4] Implement chunking strategy service (detect silence boundaries via pydub detect_nonsilent, split files >10min into 5-10min chunks with 0.5s overlap, define chunk boundary deduplication logic) in `app/domain/services/chunking_strategy.py`
- [x] T038 [US4] Extend process_transcription use case to split long audio via chunking strategy, process chunks, and stitch results into seamless text in `app/application/process_transcription.py`
- [x] T039 [US4] Update upload page template to support multiple file selection and show per-file progress indicators in `app/adapters/inbound/web/templates/upload.html`
- [x] T040 [US4] Update POST /api/upload route to accept multiple files and create individual jobs per file in `app/adapters/inbound/web/routes.py`
- [x] T041 [P] [US4] Write unit test for chunking strategy (boundary detection, split logic, overlap handling) in `tests/unit/domain/test_chunking_strategy.py`

**Checkpoint**: Multi-file and long-file handling works. All 4 user stories independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Backward compatibility, end-to-end testing, final validation

- [x] T042 [P] Implement CLI adapter for backward compatibility (argparse: DIRECTORY, --language, --engine; scan directory for audio files, process each via submit+process use cases, print transcriptions to stdout) in `app/adapters/inbound/cli.py`
- [x] T043 [P] Write e2e API tests (upload file, poll status, get result, download TXT, test error cases: bad format, oversized file, missing job) in `tests/e2e/test_api.py`
- [x] T044 Run quickstart.md validation: verify all local dev setup steps work end-to-end
- [x] T045 Verify all acceptance scenarios from spec.md pass (US1: drag-drop upload, progress display, copy/download; US2: engine swap; US3: Dokku deploy + persistence; US4: concurrent files)

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ─────────────────────────────────────────────┐
                                                             │
Phase 2: Foundational (BLOCKS all stories) ─────────────────┤
                                                             │
         ┌───────────────────┬───────────────┬───────────────┤
         ▼                   ▼               ▼               │
Phase 3: US1 (P1)    Phase 4: US2 (P2)   Phase 5: US3 (P3)  │
  MVP core             Needs US1 engine    Can parallel w/   │
                       selection base      US1               │
         │                   │               │               │
         ▼                   │               │               │
Phase 6: US4 (P4) ──────────┘───────────────┘               │
  Extends US1                                                │
         │                                                   │
         ▼                                                   │
Phase 7: Polish ─────────────────────────────────────────────┘
```

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 only. No dependencies on other stories. **Start here.**
- **US2 (P2)**: Depends on Phase 2. Benefits from US1 bootstrap being in place (T020) but is independently testable.
- **US3 (P3)**: Depends on Phase 2. Can proceed in parallel with US1/US2 (Dockerfile/Procfile are independent files). Health endpoint (T035) should come after routes.py exists (T024).
- **US4 (P4)**: Depends on US1 (extends process_transcription and upload UI). Must follow Phase 3.

### Within Each User Story

1. Outbound adapters (all [P] — different files, no cross-dependencies)
2. Use cases (all [P] — depend on ports from Phase 2, not on concrete adapters)
3. Bootstrap and app factory (sequential — wires adapters to use cases)
4. Web adapter: schemas [P] with templates, then routes (depends on app factory + schemas + templates)
5. Worker (depends on bootstrap + process_transcription use case)
6. Tests (after the code they test exists)

### Parallel Opportunities

**Phase 2** — Run in parallel:
- T003 + T004 (value objects + exceptions — separate files)
- T009 + T010 + T011 (config + DTOs + validator — independent modules)

**Phase 3 (US1)** — Run in parallel:
- T012 + T013 + T014 + T015 + T016 (all 5 outbound adapters — separate files)
- T017 + T018 + T019 (all 3 use cases — depend on ports, not adapters)
- T022 + T023 (schemas + templates — separate files)
- T026 + T027 + T028 (all test groups — separate directories)

**Phase 5 (US3)** — Run in parallel:
- T032 + T033 + T034 (Dockerfile + Procfile + docker-compose — separate files)

**Cross-story** — With sufficient staffing:
- US1 + US3 can proceed in parallel (web code vs deployment config are separate concerns)
- US2 can start once US1 bootstrap exists (T020)

---

## Parallel Example: User Story 1

```
# Wave 1: Outbound adapters (all parallel, different files):
T012: SQLite repository      → app/adapters/outbound/persistence/sqlite_repository.py
T013: Local file storage     → app/adapters/outbound/storage/local_file_storage.py
T014: Pydub converter        → app/adapters/outbound/converter/pydub_converter.py
T015: RQ queue adapter       → app/adapters/outbound/queue/rq_queue.py
T016: faster-whisper engine  → app/adapters/outbound/engines/faster_whisper_engine.py

# Wave 1 (same time): Use cases (parallel, depend on ports not adapters):
T017: submit_transcription   → app/application/submit_transcription.py
T018: process_transcription  → app/application/process_transcription.py
T019: get_job_status         → app/application/get_job_status.py

# Wave 2: Wiring (sequential, depends on Wave 1):
T020: bootstrap.py
T021: main.py (app factory)

# Wave 2 (same time): Web assets (parallel):
T022: Pydantic schemas       → app/adapters/inbound/web/schemas.py
T023: Jinja2 templates       → app/adapters/inbound/web/templates/

# Wave 3: Routes + worker (depend on Wave 2):
T024: FastAPI routes          → app/adapters/inbound/web/routes.py
T025: RQ worker handler       → app/adapters/inbound/worker.py

# Wave 4: Tests (after implementation):
T026: Domain unit tests       → tests/unit/domain/
T027: Use case unit tests     → tests/unit/application/
T028: Integration tests       → tests/integration/adapters/
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T011) — **CRITICAL, blocks all stories**
3. Complete Phase 3: User Story 1 (T012-T028)
4. **STOP and VALIDATE**: Upload a pt-BR MP3, watch progress, verify transcription
5. Deploy locally via `docker compose up` if ready

### Incremental Delivery

1. Setup + Foundational → Domain model ready
2. **Add US1** → Test independently → Local demo (**MVP!**)
3. **Add US2** → Test engine swap → Both engines verified
4. **Add US3** → Deploy to Dokku → Production accessible
5. **Add US4** → Test multi-file → Full feature set
6. Polish → CLI compat, e2e tests, quickstart validation

### Suggested MVP Scope

**Phase 1 + Phase 2 + Phase 3 (US1)** = 28 tasks delivers a fully working web transcription UI with faster-whisper. This is the minimum viable deployment that replaces the current CLI-only tool with a web interface.

---

## Summary

| Phase | Story | Tasks | Parallel Opportunities |
|-------|-------|-------|----------------------|
| Phase 1: Setup | — | 2 | — |
| Phase 2: Foundational | — | 9 | 2 groups of [P] tasks |
| Phase 3: US1 MVP | US1 | 17 | 4 parallel waves |
| Phase 4: Engine Swap | US2 | 3 | — |
| Phase 5: Dokku Deploy | US3 | 5 | 3 tasks [P] |
| Phase 6: Concurrency | US4 | 5 | 1 test [P] |
| Phase 7: Polish | — | 4 | 2 tasks [P] |
| **Total** | | **45** | |

**Tasks per user story**: US1=17, US2=3, US3=5, US4=5
**Independent test criteria**: Each story has a specific verification test defined in its checkpoint
