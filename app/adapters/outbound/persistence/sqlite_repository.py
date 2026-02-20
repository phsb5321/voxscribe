import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from app.domain.entities.audio_file import AudioFile
from app.domain.entities.transcription_job import TranscriptionJob
from app.domain.entities.transcription_result import TranscriptionResult
from app.domain.value_objects.audio_format import AudioFormat
from app.domain.value_objects.job_status import JobStatus
from app.ports.job_repository import JobRepositoryPort

_CREATE_AUDIO_FILES = """
CREATE TABLE IF NOT EXISTS audio_files (
    id TEXT PRIMARY KEY,
    original_filename TEXT NOT NULL,
    format TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    duration_seconds REAL,
    storage_path TEXT NOT NULL,
    upload_timestamp TEXT NOT NULL,
    converted_path TEXT
);
"""

_CREATE_TRANSCRIPTION_JOBS = """
CREATE TABLE IF NOT EXISTS transcription_jobs (
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
"""

_CREATE_TRANSCRIPTION_RESULTS = """
CREATE TABLE IF NOT EXISTS transcription_results (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL UNIQUE REFERENCES transcription_jobs(id),
    full_text TEXT NOT NULL,
    language TEXT NOT NULL,
    engine_name TEXT NOT NULL,
    processing_duration_seconds REAL NOT NULL,
    created_at TEXT NOT NULL
);
"""


class SQLiteJobRepository(JobRepositoryPort):
    """SQLite-backed implementation of JobRepositoryPort."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._create_tables()

    def _create_tables(self) -> None:
        with self._conn:
            self._conn.execute(_CREATE_AUDIO_FILES)
            self._conn.execute(_CREATE_TRANSCRIPTION_JOBS)
            self._conn.execute(_CREATE_TRANSCRIPTION_RESULTS)

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def save_job(self, job: TranscriptionJob) -> None:
        """Save or update a transcription job (upsert)."""
        sql = """
            INSERT OR REPLACE INTO transcription_jobs
                (id, audio_file_id, status, progress_percent, language,
                 engine_name, created_at, updated_at, error_message, retry_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._conn:
            self._conn.execute(sql, (
                str(job.id),
                str(job.audio_file_id),
                job.status.value,
                job.progress_percent,
                job.language,
                job.engine_name or None,
                job.created_at.isoformat(),
                job.updated_at.isoformat(),
                job.error_message,
                job.retry_count,
            ))

    def create_audio_file(self, audio_file: AudioFile) -> None:
        """Persist or update an audio file record."""
        sql = """
            INSERT OR REPLACE INTO audio_files
                (id, original_filename, format, size_bytes, duration_seconds,
                 storage_path, upload_timestamp, converted_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._conn:
            self._conn.execute(sql, (
                str(audio_file.id),
                audio_file.original_filename,
                audio_file.format.value,
                audio_file.size_bytes,
                audio_file.duration_seconds,
                audio_file.storage_path,
                audio_file.upload_timestamp.isoformat(),
                audio_file.converted_path,
            ))

    def save_result(self, result: TranscriptionResult) -> None:
        """Save a transcription result."""
        sql = """
            INSERT INTO transcription_results
                (id, job_id, full_text, language, engine_name,
                 processing_duration_seconds, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        with self._conn:
            self._conn.execute(sql, (
                str(result.id),
                str(result.job_id),
                result.full_text,
                result.language,
                result.engine_name,
                result.processing_duration_seconds,
                result.created_at.isoformat(),
            ))

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_job(self, job_id: UUID) -> TranscriptionJob | None:
        """Get a job by ID, or None if not found."""
        sql = "SELECT * FROM transcription_jobs WHERE id = ?"
        row = self._conn.execute(sql, (str(job_id),)).fetchone()
        if row is None:
            return None
        return self._row_to_job(row)

    def get_jobs_by_status(self, status: JobStatus) -> list[TranscriptionJob]:
        """Get all jobs with the given status."""
        sql = "SELECT * FROM transcription_jobs WHERE status = ?"
        rows = self._conn.execute(sql, (status.value,)).fetchall()
        return [self._row_to_job(row) for row in rows]

    def get_result_for_job(self, job_id: UUID) -> TranscriptionResult | None:
        """Get the result for a completed job, or None."""
        sql = "SELECT * FROM transcription_results WHERE job_id = ?"
        row = self._conn.execute(sql, (str(job_id),)).fetchone()
        if row is None:
            return None
        return self._row_to_result(row)

    def get_audio_file(self, audio_file_id: UUID) -> AudioFile | None:
        """Get an audio file by ID, or None if not found."""
        sql = "SELECT * FROM audio_files WHERE id = ?"
        row = self._conn.execute(sql, (str(audio_file_id),)).fetchone()
        if row is None:
            return None
        return self._row_to_audio_file(row)

    # ------------------------------------------------------------------
    # Row-to-domain mappers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> TranscriptionJob:
        return TranscriptionJob(
            id=UUID(row["id"]),
            audio_file_id=UUID(row["audio_file_id"]),
            status=JobStatus(row["status"]),
            progress_percent=row["progress_percent"],
            language=row["language"],
            engine_name=row["engine_name"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            error_message=row["error_message"],
            retry_count=row["retry_count"],
        )

    @staticmethod
    def _row_to_audio_file(row: sqlite3.Row) -> AudioFile:
        return AudioFile(
            id=UUID(row["id"]),
            original_filename=row["original_filename"],
            format=AudioFormat(row["format"]),
            size_bytes=row["size_bytes"],
            duration_seconds=row["duration_seconds"],
            storage_path=row["storage_path"],
            upload_timestamp=datetime.fromisoformat(row["upload_timestamp"]),
            converted_path=row["converted_path"],
        )

    @staticmethod
    def _row_to_result(row: sqlite3.Row) -> TranscriptionResult:
        return TranscriptionResult(
            id=UUID(row["id"]),
            job_id=UUID(row["job_id"]),
            full_text=row["full_text"],
            language=row["language"],
            engine_name=row["engine_name"],
            processing_duration_seconds=row["processing_duration_seconds"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
