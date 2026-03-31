# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Web-based audio transcriber that converts audio files (MP3, WAV, FLAC, OGG) to text using faster-whisper (local) or OpenAI gpt-4o-mini-transcribe (cloud). Targets Brazilian Portuguese (pt-BR) by default. Uses hexagonal architecture with FastAPI web UI, RQ background workers, and SQLite persistence.

## Commands

### Development
```bash
# Install dependencies
uv sync

# Run web server
uv run uvicorn app.main:create_app --factory --host 0.0.0.0 --port 5000

# Run background worker (requires Redis)
uv run rq worker --url redis://localhost:6379

# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/unit/domain/test_chunking_strategy.py -v

# CLI backward compatibility
uv run python -m app.adapters.inbound.cli DATA/ --language pt-BR
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

## Git Workflow

- **Simplified Gitflow**: `main` (production) and `develop` (integration)
- Feature branches: `NNN-feature-name` from `develop`, PR back to `develop`
- Releases: PR from `develop` to `main` triggers deploy to Dokku
- **Conventional Commits**: All commits must follow conventional commit format (enforced by commitizen pre-commit hook)
  - `feat:` new features, `fix:` bug fixes, `chore:` maintenance, `docs:` documentation, `refactor:` refactoring, `test:` tests
- **Version bumps**: `uv run cz bump` (updates pyproject.toml version + creates git tag)

## CI/CD

- GitHub Actions CI runs lint (ruff) + tests (pytest with coverage) on every push/PR to `develop` and `main`
- Deploy workflow pushes to Dokku on merge to `main` (requires self-hosted runner on local network)
- Dokku health check: `CHECKS` file validates `/health` endpoint before completing deploy

## Code Quality

- **Linting**: `uv run ruff check .` — rules: E, F, I, W, UP, B, SIM
- **Formatting**: `uv run ruff format .` — line length 120
- **Pre-commit hooks**: commitizen (commit-msg) + ruff (pre-commit)
- **Coverage**: `uv run pytest tests/ --cov=app --cov-report=term-missing` — minimum 50%

## Active Technologies
- Python 3.12, FastAPI, Jinja2, vanilla JavaScript, HTMX 2.0.4 (CDN)
- yt-dlp for Instagram reel downloads
- SQLite, local filesystem, pydub, faster-whisper/openai/groq, RQ/Redis
- Python 3.12 + vanilla JavaScript (no build tools) + FastAPI, Jinja2, HTMX 2.0.4 (CDN), wavesurfer.js v7 (CDN, new) (004-ux-improvements)
- SQLite (existing), local filesystem (existing) (004-ux-improvements)

## Recent Changes
- 004-ux-improvements: Added Python 3.12 + vanilla JavaScript (no build tools) + FastAPI, Jinja2, HTMX 2.0.4 (CDN), wavesurfer.js v7 (CDN, new)
