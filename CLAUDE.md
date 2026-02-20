# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Web-based audio transcriber that converts audio files (MP3, WAV, FLAC, OGG) to text using faster-whisper (local) or OpenAI gpt-4o-mini-transcribe (cloud). Targets Brazilian Portuguese (pt-BR) by default. Uses hexagonal architecture with FastAPI web UI, RQ background workers, and SQLite persistence.

## Commands

### Development
```bash
# Install dependencies (NixOS: use nix-shell -p poetry)
poetry install

# Run web server
poetry run uvicorn app.main:create_app --factory --host 0.0.0.0 --port 5000

# Run background worker (requires Redis)
poetry run rq worker --url redis://localhost:6379

# Run all tests
poetry run pytest tests/ -v

# Run specific test file
poetry run pytest tests/unit/domain/test_chunking_strategy.py -v

# CLI backward compatibility
poetry run python -m app.adapters.inbound.cli DATA/ --language pt-BR
```

### Docker
```bash
docker compose up          # web + worker + redis
bash START.SH              # standalone container
```

### System Dependencies
ffmpeg and libsndfile1 are required at runtime.

## Architecture

Hexagonal (ports & adapters) architecture with clean dependency inversion.

### Layers
- **Domain** (`app/domain/`) — Entities, value objects, services. Zero external dependencies.
  - `entities/` — AudioFile (validation), TranscriptionJob (state machine), TranscriptionResult
  - `value_objects/` — AudioFormat enum, JobStatus enum (with transition rules)
  - `services/` — audio_validator, chunking_strategy (long file splitting)
  - `exceptions.py` — Domain-specific errors
- **Ports** (`app/ports/`) — 5 ABC interfaces: TranscriptionEnginePort, AudioStoragePort, AudioConverterPort, JobRepositoryPort, JobQueuePort
- **Application** (`app/application/`) — Use cases: SubmitTranscription, ProcessTranscription, GetJobStatus. DTOs in dto.py.
- **Adapters** (`app/adapters/`)
  - Inbound: `web/` (FastAPI routes, Jinja2 templates, Pydantic schemas), `worker.py` (RQ task), `cli.py` (argparse)
  - Outbound: `engines/` (faster-whisper, openai), `persistence/` (SQLite), `storage/` (local filesystem), `converter/` (pydub), `queue/` (RQ/Redis)
- **Bootstrap** (`app/bootstrap.py`) — Composition root. Wires adapters to ports. Singleton container.
- **App Factory** (`app/main.py`) — `create_app()` returns configured FastAPI instance.

### Key Patterns
- **State machine**: TranscriptionJob transitions PENDING → CONVERTING → TRANSCRIBING → COMPLETED (or FAILED with retry up to 3x)
- **Engine swap**: Set `TRANSCRIPTION_ENGINE=faster-whisper` or `TRANSCRIPTION_ENGINE=openai` (env var)
- **Chunking**: Files >10min are split at silence boundaries into 5-10min chunks with 0.5s overlap, then stitched
- **SSE progress**: GET /api/jobs/{id}/progress streams status updates via Server-Sent Events

### Config (env vars)
- `TRANSCRIPTION_ENGINE` — "faster-whisper" (default) or "openai"
- `OPENAI_API_KEY` — Required when engine is "openai"
- `REDIS_URL` — Default: redis://localhost:6379
- `DATA_DIR` — Default: ./DATA
- `DATABASE_URL` — Default: sqlite:///DATA/db.sqlite

## Test Structure
- `tests/unit/domain/` — AudioFile validation, TranscriptionJob state machine, chunking strategy
- `tests/unit/application/` — Use cases with mocked ports
- `tests/integration/adapters/` — SQLite repo, file storage, pydub converter (real I/O)
- `tests/e2e/` — Full API tests via httpx AsyncClient (uses NoOpQueue, no Redis needed)
