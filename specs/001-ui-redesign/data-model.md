# Data Model: UI/UX Redesign & Transcription History

**Date**: 2026-02-20
**Feature**: 001-ui-redesign

## Existing Entities (No Changes)

This feature is purely a frontend/API-response enhancement. No database schema changes are needed.

### TranscriptionJob (existing)

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| audio_file_id | UUID | FK → AudioFile |
| status | Enum | PENDING, CONVERTING, TRANSCRIBING, COMPLETED, FAILED |
| progress_percent | Integer | 0-100 |
| language | String | e.g., "pt-BR" |
| engine_name | String | e.g., "groq", "faster-whisper" |
| created_at | DateTime | UTC |
| updated_at | DateTime | UTC |
| error_message | String? | Null unless FAILED |
| retry_count | Integer | 0-3 |

### AudioFile (existing)

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| original_filename | String | User-facing name |
| format | Enum | MP3, WAV, FLAC, OGG |
| size_bytes | Integer | File size |
| duration_seconds | Float? | Null until conversion |
| storage_path | String | Internal path |
| upload_timestamp | DateTime | UTC |
| converted_path | String? | Post-conversion path |

### TranscriptionResult (existing)

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| job_id | UUID | FK → TranscriptionJob (unique) |
| full_text | String | Transcription output |
| language | String | Language used |
| engine_name | String | Engine used |
| processing_duration_seconds | Float | Time taken |
| created_at | DateTime | UTC |

## API Response Changes

### `/api/jobs` — Enhanced Response

New fields added to each job object (sourced from existing AudioFile entity):

| New Field | Type | Source |
|-----------|------|--------|
| size_bytes | Integer | AudioFile.size_bytes |
| duration_seconds | Float? | AudioFile.duration_seconds |
| format | String | AudioFile.format |

No new database queries — the route already fetches AudioFile per job.
