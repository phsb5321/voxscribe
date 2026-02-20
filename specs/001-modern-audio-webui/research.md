# Research: Modern Audio Transcription Web UI

**Feature Branch**: `001-modern-audio-webui`
**Date**: 2026-02-20

## R1: Transcription Engine Selection

**Decision**: Use **faster-whisper** (local, self-hosted) as the primary engine and
**OpenAI gpt-4o-mini-transcribe** as the cloud engine adapter.

**Rationale**:
- faster-whisper with large-v3-turbo model: free, 4-6x faster than vanilla Whisper,
  ~7-8% WER for pt-BR, runs on CPU (slower) or GPU, fully offline.
- gpt-4o-mini-transcribe: $0.003/min (cheapest cloud), near-best accuracy, simple API,
  25 MB file limit per request.
- The current `speechrecognition` + free Google API is undocumented, rate-limited, and
  has no SLA. It must be replaced.

**Alternatives Considered**:
- ElevenLabs Scribe v2: Best pt-BR accuracy (<5% WER) but newer entrant, subscription model.
- Deepgram Nova-3: Best for streaming (sub-300ms), but batch-only is sufficient here.
- AssemblyAI Universal-2: 99 languages, feature-rich, but add-on costs stack.
- Vosk: Free/offline but ~20-30% WER for pt-BR — unacceptable accuracy.

## R2: Web Framework

**Decision**: Use **FastAPI** with Jinja2 templates and HTMX for the web layer.

**Rationale**:
- FastAPI: largest ecosystem (4.5M+ daily downloads), built-in async, native `UploadFile`
  for file uploads, built-in `Depends()` for DI at the HTTP layer.
- Jinja2 + HTMX: zero JS build step, ~14KB HTMX library via CDN, native SSE extension
  for progress updates. No node_modules, no webpack/vite.
- Litestar was the research favorite for hexagonal fit (explicit DI), but FastAPI's
  ecosystem advantage (more docs, more community, more plugins) wins for practical
  development speed. Supplement with manual DI in `bootstrap.py`.

**Alternatives Considered**:
- Litestar: Better DI alignment with hexagonal, ~2x faster benchmarks, but smaller
  ecosystem and steeper learning curve.
- Flask: Synchronous by nature, no native DI, poorest fit for async audio workloads.
- React/Svelte SPA: Adds JS build toolchain complexity — overkill for upload+progress+results flow.

## R3: Background Job Queue

**Decision**: Use **RQ (Redis Queue)** for background transcription processing.

**Rationale**:
- Simplest Python task queue: ~200 lines to integrate, Redis-backed, minimal config.
- Dokku has an official Redis plugin; `REDIS_URL` is auto-set when linked.
- Procfile pattern (`web` + `worker`) is native to Dokku.
- RQ is synchronous (not async-native), but transcription is CPU-bound work that
  benefits from process isolation, not async I/O.

**Alternatives Considered**:
- Taskiq: Async-native, ~10x faster than RQ, pairs with Litestar. Overkill for
  this workload and adds async complexity.
- Celery: Full-featured but heavyweight config. Overkill unless routing/rate-limiting needed.
- Huey: Even lighter than RQ but less community adoption.

## R4: Architecture Pattern

**Decision**: Hexagonal architecture (ports and adapters) with selective application.

**Rationale**:
- Apply full port/adapter pattern to: transcription engine, audio storage, job queue.
- Apply lightweight pattern to: web routes (FastAPI adapter), CLI (typer/click adapter).
- Do NOT apply to: health checks, static file serving, simple config reads.
- Use `abc.ABC` for port interfaces (explicit over Protocol for team clarity).
- Use `bootstrap.py` as composition root — the only file that imports concrete adapters.
- Use plain Python dataclasses for domain entities (no ORM, no Pydantic in domain).

**Alternatives Considered**:
- Clean Architecture: More formal layers (entities, use cases, interface adapters,
  frameworks) — too much ceremony for this project size.
- No architecture (keep monolithic): rejected per user requirement for swappable engines.

## R5: Audio Processing Pipeline

**Decision**: Convert to 16 kHz mono WAV via ffmpeg, chunk at silence boundaries
for files >10 min, process chunks in parallel.

**Rationale**:
- All STT engines internally downsample to 16 kHz. Pre-converting avoids redundant work.
- Mono channel: STT processes mono; stereo doubles file size for no benefit.
- Chunking at silence boundaries (via pydub `detect_nonsilent()`) prevents mid-word cuts.
- Target chunks of 5-10 minutes with 0.5s overlap for boundary deduplication.
- faster-whisper handles chunking internally via 30-second segments, but explicit
  chunking enables parallel processing across workers.

## R6: Progress Updates

**Decision**: Use **SSE (Server-Sent Events)** via HTMX's SSE extension.

**Rationale**:
- Transcription progress is unidirectional (server→client). SSE is simpler than WebSocket.
- Browser `EventSource` API has automatic reconnection built-in.
- HTMX SSE extension (`hx-ext="sse"`) swaps HTML fragments automatically.
- FastAPI implements SSE via `StreamingResponse` with `text/event-stream` MIME type.
- Progression path: start with polling (simplest), upgrade to SSE for production.

**Alternatives Considered**:
- WebSocket: Bidirectional — unnecessary for progress updates.
- Long polling: More complex server-side than SSE with no benefit.

## R7: Deployment Strategy

**Decision**: Dockerfile-based Dokku deployment with Procfile (web + worker),
Redis via plugin, persistent storage mount.

**Rationale**:
- Dockerfile: required for system deps (ffmpeg, libportaudio2, libsndfile1).
- Procfile: `web` for uvicorn/gunicorn, `worker` for RQ worker. Dokku-native scaling.
- Redis: `dokku redis:create` + `dokku redis:link` auto-sets `REDIS_URL`.
- Persistent storage: `dokku storage:mount` at `/app/DATA` for uploads.
- SSL: `dokku-letsencrypt` plugin with auto-renewal cron.
- Must add `EXPOSE` directive to Dockerfile (currently missing).

## R8: Data Persistence

**Decision**: Use **SQLite** for job/result metadata, local filesystem for audio files.

**Rationale**:
- SQLite: zero infrastructure, single file, survives container redeploys via persistent mount.
- No need for PostgreSQL at this scale (single-server, no concurrent writes from multiple
  processes — RQ workers process sequentially per worker instance).
- Audio files stored on disk via Dokku persistent storage mount.
- SQLite file stored alongside audio in the persistent storage mount.

**Alternatives Considered**:
- PostgreSQL via Dokku plugin: adds infrastructure complexity for minimal benefit at MVP scale.
- JSON files: no querying capability, poor for job status tracking.
- Redis-only: volatile unless configured for persistence, not ideal for result storage.

## Sources

- [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [OpenAI gpt-4o-mini-transcribe](https://platform.openai.com/docs/models/gpt-4o-mini-transcribe)
- [HTMX SSE Extension](https://htmx.org/extensions/sse/)
- [Dokku Dockerfile Deployment](https://dokku.com/docs/deployment/builders/dockerfiles/)
- [Hexagonal Architecture in Python](https://blog.szymonmiks.pl/p/hexagonal-architecture-in-python/)
- [AWS Prescriptive Guidance - Hexagonal with Python](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/structure-a-python-project-in-hexagonal-architecture-using-aws-lambda.html)
- [RQ (Redis Queue)](https://python-rq.org/)
- [FastAPI File Upload](https://fastapi.tiangolo.com/tutorial/request-files/)
