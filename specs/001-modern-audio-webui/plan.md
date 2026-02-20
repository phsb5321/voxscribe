# Implementation Plan: Modern Audio Transcription Web UI

**Branch**: `001-modern-audio-webui` | **Date**: 2026-02-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-modern-audio-webui/spec.md`

## Summary

Modernize the audio transcription tool from a monolithic single-file CLI app to a
hexagonal (ports and adapters) architecture with a web UI, swappable transcription
engines (faster-whisper local + OpenAI cloud), background job processing via RQ/Redis,
and Dokku deployment via git push. The web UI uses FastAPI + Jinja2 + HTMX with SSE
for real-time progress. Audio files and metadata persist across redeployments via
Dokku persistent storage with SQLite.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: FastAPI, Jinja2, HTMX (CDN), faster-whisper, openai, RQ, pydub, SQLite (stdlib)
**Storage**: SQLite (job metadata), local filesystem (audio files), Redis (job queue)
**Testing**: pytest, no network access for unit tests
**Target Platform**: Linux server (Dokku on Proxmox VM), local dev on Linux/macOS
**Project Type**: Web application (server-rendered, no frontend build step)
**Performance Goals**: Transcription within 2x audio duration; 3 concurrent jobs
**Constraints**: 500 MB max upload; pt-BR default language; offline-capable with local engine
**Scale/Scope**: Single server, single Dokku app, no authentication for MVP

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Simplicity** | VIOLATION (justified) | Constitution says "no new architectural layers" and "extend AudioTranscriber class". This feature explicitly requires hexagonal architecture + web framework + background workers per user request. See Complexity Tracking. |
| **II. Reliability** | PASS | All external calls (transcription APIs, Redis, file I/O) include retry logic and error handling. Failed jobs log at ERROR level with human-readable messages. |
| **III. Containerized Deployment** | PASS with amendment | Docker remains canonical target. Dockerfile updated for web server. `START.SH` updated to work with new structure. Procfile added for Dokku. |
| **IV. Concurrent Processing** | PASS with amendment | Background workers replace ThreadPoolExecutor for web context. CLI adapter preserves ThreadPoolExecutor for backward compatibility. Each file remains independently processable. |
| **V. Dependency Hygiene** | PASS | All new dependencies (fastapi, uvicorn, jinja2, rq, faster-whisper, openai, etc.) will be added to both pyproject.toml and requirements.txt. ffmpeg already in Dockerfile. Existing dnspython gap will be fixed. |

**Post-Phase 1 Re-check**: All gates pass. Constitution amendment recommended (MAJOR version bump) to update Principle I to allow hexagonal architecture as the standard pattern.

## Project Structure

### Documentation (this feature)

```text
specs/001-modern-audio-webui/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity models and ports
├── quickstart.md        # Phase 1: developer guide
├── contracts/
│   └── api.md           # Phase 1: HTTP API + CLI contracts
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2: task breakdown (via /speckit.tasks)
```

### Source Code (repository root)

```text
app/
├── __init__.py
├── main.py                              # FastAPI app factory (create_app)
├── config.py                            # Environment-based configuration
├── bootstrap.py                         # Composition root: wires adapters to ports
│
├── domain/                              # Core — zero external dependencies
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── audio_file.py                # AudioFile dataclass
│   │   ├── transcription_job.py         # TranscriptionJob with state machine
│   │   └── transcription_result.py      # TranscriptionResult dataclass
│   ├── value_objects/
│   │   ├── __init__.py
│   │   ├── audio_format.py              # AudioFormat enum
│   │   └── job_status.py                # JobStatus enum
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audio_validator.py           # Format/size validation
│   │   └── chunking_strategy.py         # Silence-boundary splitting logic
│   └── exceptions.py                    # Domain exceptions
│
├── ports/                               # Abstract interfaces
│   ├── __init__.py
│   ├── transcription_engine.py          # TranscriptionEnginePort (ABC)
│   ├── audio_storage.py                 # AudioStoragePort (ABC)
│   ├── audio_converter.py               # AudioConverterPort (ABC)
│   ├── job_repository.py                # JobRepositoryPort (ABC)
│   └── job_queue.py                     # JobQueuePort (ABC)
│
├── application/                         # Use cases / orchestration
│   ├── __init__.py
│   ├── submit_transcription.py          # Upload + create job + enqueue
│   ├── process_transcription.py         # Convert + transcribe + save result
│   ├── get_job_status.py                # Query job state
│   └── dto.py                           # Request/response dataclasses
│
├── adapters/                            # Concrete implementations
│   ├── __init__.py
│   ├── inbound/
│   │   ├── __init__.py
│   │   ├── web/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py                # FastAPI routes
│   │   │   ├── schemas.py               # Pydantic request/response models
│   │   │   └── templates/               # Jinja2 HTML templates
│   │   │       ├── base.html
│   │   │       ├── upload.html
│   │   │       └── job.html
│   │   ├── cli.py                       # CLI adapter (backward compat)
│   │   └── worker.py                    # RQ worker task handler
│   │
│   └── outbound/
│       ├── __init__.py
│       ├── engines/
│       │   ├── __init__.py
│       │   ├── faster_whisper_engine.py  # faster-whisper adapter
│       │   └── openai_engine.py          # OpenAI gpt-4o-mini-transcribe adapter
│       ├── storage/
│       │   ├── __init__.py
│       │   └── local_file_storage.py     # Local filesystem adapter
│       ├── persistence/
│       │   ├── __init__.py
│       │   └── sqlite_repository.py      # SQLite job/result repository
│       ├── converter/
│       │   ├── __init__.py
│       │   └── pydub_converter.py        # pydub/ffmpeg audio converter
│       └── queue/
│           ├── __init__.py
│           └── rq_queue.py               # RQ job queue adapter
│
tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   ├── domain/                           # Pure domain tests (no mocks needed)
│   │   ├── test_audio_file.py
│   │   ├── test_transcription_job.py
│   │   └── test_chunking_strategy.py
│   └── application/                      # Use case tests (mock ports)
│       ├── test_submit_transcription.py
│       └── test_process_transcription.py
├── integration/
│   ├── __init__.py
│   └── adapters/                         # Test adapters with real services
│       ├── test_sqlite_repository.py
│       ├── test_local_file_storage.py
│       └── test_pydub_converter.py
└── e2e/
    └── test_api.py                       # Full HTTP tests

Dockerfile                                # Updated multi-stage build
Procfile                                  # web + worker process types
docker-compose.yml                        # Local dev: app + redis
```

**Structure Decision**: Single project with hexagonal directory layout. No separate
frontend directory since HTMX templates are server-rendered within the web adapter.
This keeps deployment as a single Dokku app with a Procfile for web + worker scaling.

## Complexity Tracking

> Constitution Principle I (Simplicity) violations, justified by explicit user requirements.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Hexagonal architecture (ports/adapters) | User explicitly requested "hexagonal informed ports and adapters setup". FR-007 requires swappable transcription engines. FR-015 mandates hexagonal architecture. | Monolithic single-file cannot support multiple engines without tight coupling. |
| Web framework (FastAPI) | FR-001 requires a web interface. The current CLI-only tool cannot serve browser requests. | No simpler alternative exists for serving HTTP. HTMX minimizes frontend complexity. |
| Background worker (RQ) | FR-006 requires async job processing. Web requests cannot block for minutes during transcription. | ThreadPoolExecutor in a web process would block request handling and is not compatible with Dokku's process model. |
| SQLite database | FR-009 requires persistence across redeployments. Job status tracking needs queryable storage. | JSON files lack querying capability. In-memory storage is volatile. |

**Recommended**: Amend Constitution Principle I to acknowledge hexagonal architecture
as the project's standard pattern. Bump constitution to version 2.0.0 (MAJOR — principle
redefinition).
