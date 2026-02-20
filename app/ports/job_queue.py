from abc import ABC, abstractmethod
from uuid import UUID


class JobQueuePort(ABC):
    @abstractmethod
    def enqueue(self, job_id: UUID) -> None:
        """Submit job for background processing."""
