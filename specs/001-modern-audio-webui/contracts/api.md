# API Contracts: Modern Audio Transcription Web UI

**Feature Branch**: `001-modern-audio-webui`
**Date**: 2026-02-20
**Transport**: HTTP REST (FastAPI) + SSE for progress
**Content Types**: `multipart/form-data` (upload), `application/json` (API), `text/html` (pages), `text/event-stream` (SSE)

## Pages (HTML — HTMX-driven)

### GET /

Upload page. Renders the file upload form with drag-and-drop zone.

### GET /jobs/{job_id}

Processing/results page. Shows job status with SSE-driven live updates.
When job is COMPLETED, displays the transcription result with copy/download buttons.

## API Endpoints

### POST /api/upload

Upload an audio file and create a transcription job.

**Request**: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | binary | Yes | Audio file (MP3, WAV, FLAC, OGG) |
| language | string | No | BCP-47 language tag, default "pt-BR" |

**Response** (201 Created):
```json
{
  "job_id": "uuid-string",
  "status": "PENDING",
  "redirect_url": "/jobs/{job_id}"
}
```

**Errors**:

| Status | Condition |
|--------|-----------|
| 400 | Unsupported file format |
| 413 | File exceeds 500 MB |
| 503 | Storage full or service unavailable |

### GET /api/jobs/{job_id}

Get current job status and metadata.

**Response** (200 OK):
```json
{
  "job_id": "uuid-string",
  "status": "TRANSCRIBING",
  "progress_percent": 45,
  "language": "pt-BR",
  "engine_name": "faster-whisper",
  "audio_file": {
    "original_filename": "meeting.mp3",
    "format": "MP3",
    "size_bytes": 5242880,
    "duration_seconds": 120.5
  },
  "created_at": "2026-02-20T15:30:00Z",
  "updated_at": "2026-02-20T15:31:00Z",
  "error_message": null
}
```

**Errors**:

| Status | Condition |
|--------|-----------|
| 404 | Job not found |

### GET /api/jobs/{job_id}/result

Get transcription result for a completed job.

**Response** (200 OK):
```json
{
  "job_id": "uuid-string",
  "full_text": "Transcribed text content...",
  "language": "pt-BR",
  "engine_name": "faster-whisper",
  "processing_duration_seconds": 45.2
}
```

**Errors**:

| Status | Condition |
|--------|-----------|
| 404 | Job not found or not yet completed |

### GET /api/jobs/{job_id}/result/download

Download transcription as a plain text file.

**Response** (200 OK):
- Content-Type: `text/plain; charset=utf-8`
- Content-Disposition: `attachment; filename="{original_filename}.txt"`
- Body: raw transcription text

### GET /api/jobs/{job_id}/progress

SSE stream for real-time job progress updates.

**Response**: `text/event-stream`

```
event: status
data: {"status": "CONVERTING", "progress_percent": 10}

event: status
data: {"status": "TRANSCRIBING", "progress_percent": 45}

event: status
data: {"status": "COMPLETED", "progress_percent": 100}

event: done
data: {"redirect_url": "/jobs/{job_id}"}
```

Events are sent whenever job status or progress changes.
Connection closes after `done` event or on error.

### GET /api/health

Health check endpoint.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "engine": "faster-whisper",
  "redis": "connected"
}
```

## CLI Interface (Backward Compatibility)

### python -m app.adapters.inbound.cli

```
Usage: python -m app.adapters.inbound.cli [OPTIONS] [DIRECTORY]

Arguments:
  DIRECTORY  Path to directory containing audio files [default: ./DATA]

Options:
  --language TEXT   BCP-47 language code [default: pt-BR]
  --engine TEXT     Transcription engine name [default: from config]
  --help           Show this message and exit.
```

Processes all supported audio files in the directory, prints transcriptions
to stdout, matching the current `main.py` behavior.
