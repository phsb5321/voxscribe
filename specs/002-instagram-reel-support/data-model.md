# Data Model: Instagram Reel URL Transcription

**Branch**: `002-instagram-reel-support` | **Date**: 2026-03-30

## Entity Changes

### Modified: AudioFile

Add an optional `source_url` field to track the origin of the audio.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | UUID | Yes | Existing — no change |
| original_filename | string | Yes | Existing — for URL sources, derived from reel title/ID (e.g., `reel_ABC123.mp3`) |
| format | AudioFormat | Yes | Existing — MP3 for downloaded reels |
| size_bytes | integer | Yes | Existing — populated after download completes |
| storage_path | string | Yes | Existing — no change |
| duration_seconds | float | No | Existing — populated during conversion |
| upload_timestamp | datetime | Yes | Existing — set at job creation time |
| converted_path | string | No | Existing — no change |
| **source_url** | **string** | **No** | **New — the Instagram reel URL that was submitted. Null for file uploads.** |

### Modified: JobStatus (Value Object / Enum)

Add `DOWNLOADING` state to the state machine.

| Status | Description | Transitions To |
|--------|-------------|---------------|
| PENDING | Job queued, awaiting worker | DOWNLOADING, CONVERTING, FAILED |
| **DOWNLOADING** | **Worker is downloading media from URL** | **CONVERTING, FAILED** |
| CONVERTING | Audio being converted to WAV | TRANSCRIBING, FAILED |
| TRANSCRIBING | Audio being transcribed by engine | COMPLETED, FAILED |
| COMPLETED | Transcription finished successfully | *(terminal)* |
| FAILED | Job failed, may be retried | PENDING |

Note: `PENDING → CONVERTING` remains valid for file uploads (no download needed). `PENDING → DOWNLOADING` is used for URL-sourced jobs.

### Modified: Database Schema

**audio_files table** — add column:

| Column | Type | Default | Notes |
|--------|------|---------|-------|
| source_url | TEXT | NULL | Instagram reel URL, null for file uploads |

**transcription_jobs table** — no schema changes. The `status` column already stores status as TEXT; `DOWNLOADING` is a new valid value.

### Unchanged Entities

- **TranscriptionJob**: No field changes. The `status` field already supports arbitrary text values; `DOWNLOADING` is added to the enum, not the schema.
- **TranscriptionResult**: No changes. Results from URL-sourced jobs are identical in structure to file upload results.

## New Port Interface

### MediaDownloaderPort

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| download_audio | url: str, output_dir: str | DownloadResult | Downloads media from URL and extracts audio. Returns file path, filename, and file size. |
| validate_url | url: str | bool | Checks if URL matches a supported pattern (Instagram reel). |

### DownloadResult (Value Object)

| Field | Type | Description |
|-------|------|-------------|
| file_path | string | Absolute path to the downloaded audio file |
| filename | string | Generated filename (e.g., `reel_ABC123.mp3`) |
| size_bytes | integer | File size in bytes |
| title | string | Media title extracted from metadata (if available) |

## Validation Rules

- **URL format**: Must match Instagram reel URL pattern (see research.md R-005)
- **File size**: Downloaded audio must not exceed 500 MB (same as upload limit)
- **Audio format**: Downloaded audio is always MP3 (enforced by yt-dlp post-processor)
- **Source URL**: Stored as-is (the original URL the user submitted)
