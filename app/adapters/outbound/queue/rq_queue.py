import logging
from uuid import UUID

from redis import Redis
from rq import Queue

from app.ports.job_queue import JobQueuePort

logger = logging.getLogger(__name__)


class RQJobQueue(JobQueuePort):
    def __init__(self, redis_url: str) -> None:
        self._redis = Redis.from_url(redis_url)
        self._queue = Queue(connection=self._redis)

    def enqueue(self, job_id: UUID) -> None:
        # Import the worker function path as a string to avoid circular imports
        self._queue.enqueue(
            "app.adapters.inbound.worker.process_job",
            str(job_id),
            job_timeout=1800,  # 30 minutes for model download + transcription
        )
        logger.info(f"Enqueued job {job_id} for processing")
