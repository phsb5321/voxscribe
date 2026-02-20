"""RQ worker task handler."""

import logging
from uuid import UUID

from app.domain.value_objects.job_status import JobStatus

logger = logging.getLogger(__name__)


def process_job(job_id_str: str) -> None:
    """Process a transcription job. Called by the RQ worker."""
    from app.bootstrap import bootstrap

    job_id = UUID(job_id_str)
    logger.info(f"Worker picking up job {job_id}")

    container = bootstrap()
    container.process_transcription.execute(job_id)

    # Check if the job needs a retry (was reset to PENDING after failure)
    job = container.process_transcription._repository.get_job(job_id)
    if job and job.status == JobStatus.PENDING and job.retry_count > 0:
        logger.info(f"Job {job_id}: Re-enqueuing for retry {job.retry_count}/3")
        container.queue.enqueue(job_id)
    else:
        logger.info(f"Worker completed job {job_id}")
