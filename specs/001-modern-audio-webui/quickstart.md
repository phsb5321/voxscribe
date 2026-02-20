# Quickstart: Modern Audio Transcription Web UI

**Feature Branch**: `001-modern-audio-webui`

## Prerequisites

- Python 3.12+
- ffmpeg installed (`sudo apt install ffmpeg` or `brew install ffmpeg`)
- Redis running locally (`redis-server` or via Docker: `docker run -d -p 6379:6379 redis`)
- Poetry installed

## Local Development

### 1. Install dependencies

```bash
poetry install
```

### 2. Configure environment

```bash
# Copy example env (or set these in your shell)
export TRANSCRIPTION_ENGINE=faster-whisper    # or "openai"
export OPENAI_API_KEY=sk-...                  # only if using openai engine
export REDIS_URL=redis://localhost:6379
export DATA_DIR=./DATA                        # persistent storage path
export DATABASE_URL=sqlite:///./DATA/db.sqlite
```

### 3. Start the web server

```bash
poetry run uvicorn app.main:create_app --factory --reload --port 5000
```

### 4. Start the background worker (separate terminal)

```bash
poetry run rq worker --url redis://localhost:6379
```

### 5. Open the web UI

Navigate to http://localhost:5000 in your browser.

## CLI Mode (Backward Compatible)

```bash
# Process all audio files in ./DATA directory
poetry run python -m app.adapters.inbound.cli

# Process a specific directory with a different language
poetry run python -m app.adapters.inbound.cli --language en-US ./my-audio-files
```

## Docker (Local)

```bash
docker compose up
```

This starts:
- Web server on port 5000
- RQ worker for background processing
- Redis for job queue

## Deploy to Dokku

### One-time server setup (on Dokku host via SSH)

```bash
dokku apps:create audio-transcriber
dokku redis:create audio-redis
dokku redis:link audio-redis audio-transcriber
dokku storage:ensure-directory audio-transcriber
dokku storage:mount audio-transcriber /var/lib/dokku/data/storage/audio-transcriber:/app/DATA
dokku config:set audio-transcriber TRANSCRIPTION_ENGINE=faster-whisper
```

### Deploy

```bash
# From your local machine
git remote add dokku dokku@ProxMox.Dokku:audio-transcriber
git push dokku main

# Scale the worker
ssh dokku@ProxMox.Dokku ps:scale audio-transcriber worker=1

# Enable SSL
ssh dokku@ProxMox.Dokku letsencrypt:enable audio-transcriber
```

## Verify

1. Web UI: Open https://your-domain.com
2. Upload a short MP3/WAV file in pt-BR
3. Watch progress updates
4. Verify transcription text appears
5. Test "Copy to clipboard" and "Download as TXT"

## Running Tests

```bash
poetry run pytest tests/unit/          # Domain logic, no external deps
poetry run pytest tests/integration/   # Adapter tests, needs Redis
poetry run pytest                       # All tests
```
