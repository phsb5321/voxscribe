<!--
Sync Impact Report
- Version change: 1.0.0 → 2.0.0 (major rewrite)
- Modified principles:
  - I. Simplicity → I. Hexagonal Simplicity (redefined for ports & adapters)
  - II. Reliability → II. Reliability (updated: removed Google Speech API ref)
  - III. Containerized Deployment → III. Containerized Deployment (updated: uv, docker-compose, Dokku)
  - IV. Concurrent Processing → IV. Background Job Processing (redefined: RQ workers, not ThreadPoolExecutor)
  - V. Dependency Hygiene → V. Dependency Hygiene (updated: uv add, dnspython violation resolved)
- Added principles:
  - VI. Code Quality Enforcement
  - VII. Conventional Commits & Gitflow
- Added sections:
  - CI/CD Pipeline
- Removed sections: none (all updated in place)
- Modified sections:
  - Runtime Constraints (multi-engine, multi-format, web app)
  - Development Workflow (uv, FastAPI, pytest, ruff)
  - Governance (unchanged structure, updated version)
- Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ no changes needed (Constitution Check is generic)
  - .specify/templates/spec-template.md — ✅ no changes needed
  - .specify/templates/tasks-template.md — ✅ no changes needed
- Follow-up TODOs: none
-->

# Voxscribe Constitution

## Core Principles

### I. Hexagonal Simplicity

All features MUST be implementable within the existing hexagonal (ports &
adapters) architecture. The application uses a FastAPI web UI with
`app/main.py` as the app factory, `app/bootstrap.py` as the composition
root, and clean layer separation: domain → ports → application → adapters.
New functionality MUST fit into existing layers (new adapter, new port, new
use case, or domain extension) rather than introduce new architectural
patterns, frameworks, or plugin systems. Rationale: the project solves a
focused problem (audio-to-text); the hexagonal structure provides
sufficient extensibility without additional abstraction layers.

### II. Reliability

Every external call (transcription API, media download, file I/O, Redis)
MUST include retry logic or explicit error handling that produces a
human-readable diagnostic. Silent failures are prohibited — all error
paths MUST log at WARNING or ERROR level before returning a fallback or
re-raising. The TranscriptionJob state machine enforces FAILED status with
up to 3 automatic retries. Rationale: audio transcription depends on
external services (faster-whisper, OpenAI, Groq, yt-dlp) and
heterogeneous input files; graceful degradation is non-negotiable.

### III. Containerized Deployment

The Docker image MUST remain the canonical deployment target. Changes to
system-level dependencies (e.g., ffmpeg, libsndfile1) MUST be reflected
in the Dockerfile. `docker compose up` MUST work as the single-command
local development entry point (web + worker + Redis). Production deploys
to Dokku via `git push dokku main` with health checks validated by the
`CHECKS` file. Local uv-based development MUST NOT diverge from what the
container executes. Rationale: reproducibility across environments is
essential when handling binary audio dependencies.

### IV. Background Job Processing

Audio transcription jobs MUST be processed asynchronously via RQ workers
backed by Redis. Each job MUST be processable independently (no shared
mutable state between jobs). The job state machine (PENDING → DOWNLOADING
→ CONVERTING → TRANSCRIBING → COMPLETED/FAILED) MUST be enforced by the
domain layer with explicit transition validation. SSE progress streaming
MUST provide real-time status updates to the web UI. Rationale: audio
processing is I/O-bound and long-running; background workers prevent
blocking the web server while maintaining user visibility.

### V. Dependency Hygiene

All runtime imports MUST have corresponding entries in `pyproject.toml`.
Adding a new dependency requires running `uv add <package>` (which updates
both pyproject.toml and uv.lock). System-level dependencies (apt packages)
MUST be documented in the Dockerfile. Dev-only dependencies (pytest, ruff,
commitizen) MUST be in the `[dependency-groups] dev` section, not in
production dependencies. Rationale: reproducible builds require explicit
dependency declarations; dev/prod separation keeps the Docker image lean.

### VI. Code Quality Enforcement

All code MUST pass `ruff check` and `ruff format --check` before merging.
Linting rules (E, F, I, W, UP, B, SIM) are configured in `pyproject.toml`
and enforced by pre-commit hooks and CI. Test coverage MUST meet the
minimum threshold (currently 50%, tracked via pytest-cov). New features
MUST include tests — unit tests for domain logic, integration tests for
adapters, and e2e tests for API endpoints. Rationale: automated quality
gates prevent regressions and maintain a consistent codebase as the
project grows.

### VII. Conventional Commits & Gitflow

All commits MUST follow the Conventional Commits specification, enforced
by commitizen pre-commit hooks. The branching model is simplified gitflow:
`main` (production) and `develop` (integration). Feature branches use
`NNN-feature-name` naming from `develop`, merged via PR back to `develop`.
Releases merge `develop` into `main`, triggering CI/CD deploy. Version
bumps use `uv run cz bump`. Rationale: standardized commits enable
automated changelogs and semantic versioning; gitflow provides a clear
separation between development and production.

## Runtime Constraints

- **Target language**: Brazilian Portuguese (pt-BR) by default, with
  en-US and es-ES also supported. Language selection is per-job.
- **Transcription engines**: faster-whisper (local, default), OpenAI
  gpt-4o-mini-transcribe (cloud), Groq whisper-large-v3 (cloud).
  Configured via `TRANSCRIPTION_ENGINE` env var.
- **Supported formats**: MP3, WAV, FLAC, OGG, M4A. Format conversion
  to 16kHz mono WAV is handled by pydub/ffmpeg before transcription.
- **URL sources**: Instagram reel URLs via yt-dlp with optional
  cookie-based authentication (`INSTAGRAM_COOKIES_FILE` env var).
- **File size limit**: 500 MB per upload.
- **Chunking**: Files >10 minutes are split at silence boundaries into
  5-10 minute chunks with 0.5s overlap, then stitched.
- **Storage**: SQLite database + local filesystem for audio files.
- **Python version**: 3.12+ as specified in `pyproject.toml`.

## CI/CD Pipeline

- **CI**: GitHub Actions runs lint (ruff) + tests (pytest with coverage)
  on every push/PR to `develop` and `main` (ubuntu-latest runner).
- **Deploy**: GitHub Actions pushes to Dokku on merge to `main`
  (self-hosted runner on local network, VM 103).
- **Health check**: Dokku validates `/health` endpoint via `CHECKS` file
  before completing zero-downtime deploys.

## Development Workflow

- **Package manager**: uv (local dev and Docker builds).
- **Run locally**: `uv sync && uv run uvicorn app.main:create_app --factory --host 0.0.0.0 --port 5000`
- **Run worker**: `uv run rq worker --url redis://localhost:6379`
- **Run via Docker**: `docker compose up`
- **Run tests**: `uv run pytest tests/ -v`
- **Run tests with coverage**: `uv run pytest tests/ -v --cov=app --cov-report=term-missing`
- **Lint**: `uv run ruff check . && uv run ruff format --check .`
- **Version bump**: `uv run cz bump`

## Governance

This constitution governs all changes to the Voxscribe project.
Amendments require:

1. A description of the change and its rationale.
2. An update to `CONSTITUTION_VERSION` following semantic versioning:
   - MAJOR: principle removal or redefinition.
   - MINOR: new principle or materially expanded guidance.
   - PATCH: clarifications, wording, typo fixes.
3. `LAST_AMENDED_DATE` MUST be updated to the date of the change.
4. A review of dependent templates (plan, spec, tasks) for consistency.

All feature work SHOULD be checked against these principles during the
plan phase (see "Constitution Check" in `.specify/templates/plan-template.md`).

**Version**: 2.0.0 | **Ratified**: 2026-02-20 | **Last Amended**: 2026-03-31
