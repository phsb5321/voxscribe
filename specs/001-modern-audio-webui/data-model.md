# Data Model: Modern Audio Transcription Web UI

**Feature Branch**: `001-modern-audio-webui`
**Date**: 2026-02-20

## Domain Entities

### AudioFile

Represents an uploaded audio file.

| Field | Type | Constraints |
|-------|------|------------|
| id | UUID | Primary key, generated on creation |
| original_filename | string | Max 255 chars, non-empty |
| format | AudioFormat enum | One of: MP3, WAV, FLAC, OGG |
| size_bytes | integer | > 0, <= 524_288_000 (500 MB) |
| duration_seconds | float | Nullable (calculated after conversion) |
| storage_path | string | Relative path within persistent storage |
| upload_timestamp | datetime | UTC, set on creation |
| converted_path | string | Nullable (path to 16kHz mono WAV after conversion) |

**Validation Rules**:
- `format` MUST be one of the supported AudioFormat values.
- `size_bytes` MUST NOT exceed 500 MB (524,288,000 bytes).
- `original_filename` MUST NOT contain path separators or null bytes.

### TranscriptionJob

Represents a unit of work to transcribe an audio file.

| Field | Type | Constraints |
|-------|------|------------|
| id | UUID | Primary key, generated on creation |
| audio_file_id | UUID | Foreign key → AudioFile.id |
| status | JobStatus enum | See state machine below |
| progress_percent | integer | 0-100, default 0 |
| language | string | BCP-47 tag, default "pt-BR" |
| engine_name | string | Identifier of the engine used |
| created_at | datetime | UTC, set on creation |
| updated_at | datetime | UTC, updated on every status change |
| error_message | string | Nullable, populated on failure |
| retry_count | integer | 0-3, default 0 |

**State Machine** (JobStatus):

```
PENDING → CONVERTING → TRANSCRIBING → COMPLETED
   │          │              │
   └──────────┴──────────────┴──→ FAILED
                                    │
                                    └──→ PENDING (retry, if retry_count < 3)
```

- `PENDING`: Job created, waiting for worker pickup.
- `CONVERTING`: Audio being converted to 16 kHz mono WAV.
- `TRANSCRIBING`: Audio being transcribed by engine.
- `COMPLETED`: Transcription finished successfully.
- `FAILED`: An error occurred. If `retry_count < 3`, may transition back to PENDING.

**Business Rules**:
- Status transitions MUST follow the state machine. Invalid transitions raise a domain error.
- `retry_count` MUST NOT exceed 3 (MAX_RETRIES).
- `updated_at` MUST be refreshed on every state transition.
- A job in COMPLETED or FAILED (with max retries) is terminal.

### TranscriptionResult

The output of a completed transcription job.

| Field | Type | Constraints |
|-------|------|------------|
| id | UUID | Primary key, generated on creation |
| job_id | UUID | Foreign key → TranscriptionJob.id, unique |
| full_text | string | Non-empty for successful transcriptions |
| language | string | BCP-47 tag, matches job language |
| engine_name | string | Engine that produced this result |
| processing_duration_seconds | float | Wall-clock time for transcription |
| created_at | datetime | UTC, set on creation |

**Validation Rules**:
- Exactly one result per completed job (1:1 relationship).
- `full_text` may be empty if the audio contained only silence (not an error).

## Value Objects

### AudioFormat (Enum)
```
MP3, WAV, FLAC, OGG
```

### JobStatus (Enum)
```
PENDING, CONVERTING, TRANSCRIBING, COMPLETED, FAILED
```

## Relationships

```
AudioFile 1 ──── * TranscriptionJob
TranscriptionJob 1 ──── 0..1 TranscriptionResult
```

- An AudioFile can have multiple TranscriptionJobs (re-transcription with different
  engines or languages).
- A TranscriptionJob has at most one TranscriptionResult (created on completion).

## Ports (Abstract Interfaces)

### TranscriptionEnginePort (Outbound)

```
transcribe(audio_path: str, language: str) → str
    Transcribe audio file at given path in given language.
    Returns full transcription text.
    Raises TranscriptionError on failure.
```

### AudioStoragePort (Outbound)

```
store(filename: str, data: bytes) → str
    Store audio file, return storage path.

retrieve(storage_path: str) → bytes
    Retrieve audio file by storage path.

delete(storage_path: str) → None
    Delete audio file from storage.
```

### JobRepositoryPort (Outbound)

```
save_job(job: TranscriptionJob) → None
create_audio_file(audio_file: AudioFile) → None
save_result(result: TranscriptionResult) → None
get_job(job_id: UUID) → TranscriptionJob | None
get_jobs_by_status(status: JobStatus) → list[TranscriptionJob]
get_result_for_job(job_id: UUID) → TranscriptionResult | None
get_audio_file(audio_file_id: UUID) → AudioFile | None
```

### JobQueuePort (Outbound)

```
enqueue(job_id: UUID) → None
    Submit job for background processing.
```

### AudioConverterPort (Outbound)

```
convert_to_wav(input_path: str, output_path: str, sample_rate: int = 16000, channels: int = 1) → bool
    Convert audio file to WAV format. Returns success status.

detect_silence_boundaries(audio_path: str, min_silence_ms: int = 500) → list[tuple[int, int]]
    Detect non-silent segments. Returns list of (start_ms, end_ms) tuples.

split_at_boundaries(audio_path: str, boundaries: list[tuple[int, int]]) → list[str]
    Split audio at given boundaries. Returns list of chunk file paths.
```

## SQLite Schema (Adapter-Level)

This is the persistence adapter's implementation detail — not part of the domain.

```sql
CREATE TABLE audio_files (
    id TEXT PRIMARY KEY,
    original_filename TEXT NOT NULL,
    format TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    duration_seconds REAL,
    storage_path TEXT NOT NULL,
    upload_timestamp TEXT NOT NULL,
    converted_path TEXT
);

CREATE TABLE transcription_jobs (
    id TEXT PRIMARY KEY,
    audio_file_id TEXT NOT NULL REFERENCES audio_files(id),
    status TEXT NOT NULL DEFAULT 'PENDING',
    progress_percent INTEGER NOT NULL DEFAULT 0,
    language TEXT NOT NULL DEFAULT 'pt-BR',
    engine_name TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE transcription_results (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL UNIQUE REFERENCES transcription_jobs(id),
    full_text TEXT NOT NULL,
    language TEXT NOT NULL,
    engine_name TEXT NOT NULL,
    processing_duration_seconds REAL NOT NULL,
    created_at TEXT NOT NULL
);
```
