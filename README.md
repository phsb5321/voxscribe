# Voxscribe

Web-based audio transcription tool that converts audio files and Instagram reels to text using faster-whisper (local), OpenAI, or Groq engines. Targets Brazilian Portuguese (pt-BR) by default.

## Quick Start

```bash
# Prerequisites: ffmpeg, libsndfile1, Python 3.12+, Redis

# Install dependencies
uv sync

# Run web server
uv run uvicorn app.main:create_app --factory --host 0.0.0.0 --port 5000

# Run background worker (separate terminal)
uv run rq worker --url redis://localhost:6379

# Or run everything with Docker
docker compose up
```

## Architecture

Hexagonal (ports & adapters) architecture with FastAPI, RQ background workers, and SQLite.

```
app/
  domain/       -- Entities, value objects, services (zero deps)
  ports/        -- Abstract interfaces (6 ports)
  application/  -- Use cases + DTOs
  adapters/     -- Inbound (web, worker, CLI) + Outbound (engines, persistence, storage, converter, queue, downloader)
  bootstrap.py  -- Composition root (DI wiring)
  config.py     -- Environment-based settings
  main.py       -- FastAPI app factory
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TRANSCRIPTION_ENGINE` | `faster-whisper` | Engine: `faster-whisper`, `openai`, or `groq` |
| `OPENAI_API_KEY` | | Required for OpenAI engine |
| `GROQ_API_KEY` | | Required for Groq engine |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection for job queue |
| `DATA_DIR` | `./DATA` | Storage directory |
| `DATABASE_URL` | `sqlite:///DATA/db.sqlite` | SQLite database path |
| `INSTAGRAM_COOKIES_FILE` | | Optional: Netscape cookies.txt for Instagram auth |

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Run tests with coverage
uv run pytest tests/ -v --cov=app --cov-report=term-missing

# Lint
uv run ruff check .
uv run ruff format --check .
```

## Git Workflow

- **Branches**: `main` (production) and `develop` (integration)
- **Features**: Branch from `develop`, PR back to `develop`
- **Releases**: PR from `develop` to `main` triggers deploy to Dokku
- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/) enforced by commitizen
