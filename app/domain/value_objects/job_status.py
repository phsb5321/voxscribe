from enum import Enum


class JobStatus(str, Enum):
    PENDING = "PENDING"
    CONVERTING = "CONVERTING"
    TRANSCRIBING = "TRANSCRIBING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    def can_transition_to(self, target: "JobStatus") -> bool:
        return target in _VALID_TRANSITIONS.get(self, [])


_VALID_TRANSITIONS: dict[JobStatus, list[JobStatus]] = {
    JobStatus.PENDING: [JobStatus.CONVERTING, JobStatus.FAILED],
    JobStatus.CONVERTING: [JobStatus.TRANSCRIBING, JobStatus.FAILED],
    JobStatus.TRANSCRIBING: [JobStatus.COMPLETED, JobStatus.FAILED],
    JobStatus.FAILED: [JobStatus.PENDING],  # retry
    JobStatus.COMPLETED: [],
}
