from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class TranscriptionResult:
    job_id: UUID
    full_text: str
    language: str
    engine_name: str
    processing_duration_seconds: float
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
