from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.domain.exceptions import InvalidStateTransitionError, MaxRetriesExceededError
from app.domain.value_objects.job_status import JobStatus

MAX_RETRIES = 3


@dataclass
class TranscriptionJob:
    audio_file_id: UUID
    language: str = "pt-BR"
    engine_name: str = ""
    id: UUID = field(default_factory=uuid4)
    status: JobStatus = field(default=JobStatus.PENDING)
    progress_percent: int = 0
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    error_message: str | None = None
    retry_count: int = 0

    def transition_to(self, new_status: JobStatus) -> None:
        """Transition job to a new status following the state machine rules."""
        if not self.status.can_transition_to(new_status):
            raise InvalidStateTransitionError(self.status.value, new_status.value)
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

    def update_progress(self, percent: int) -> None:
        self.progress_percent = max(0, min(100, percent))
        self.updated_at = datetime.now(timezone.utc)

    def fail(self, error_message: str) -> None:
        """Transition to FAILED with an error message."""
        self.transition_to(JobStatus.FAILED)
        self.error_message = error_message

    def retry(self) -> None:
        """Retry a failed job by transitioning back to PENDING."""
        if self.retry_count >= MAX_RETRIES:
            raise MaxRetriesExceededError(
                f"Job {self.id} has exceeded maximum retries ({MAX_RETRIES})"
            )
        self.transition_to(JobStatus.PENDING)
        self.retry_count += 1
        self.error_message = None
        self.progress_percent = 0

    @property
    def is_terminal(self) -> bool:
        if self.status == JobStatus.COMPLETED:
            return True
        if self.status == JobStatus.FAILED and self.retry_count >= MAX_RETRIES:
            return True
        return False
