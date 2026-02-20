"""RQ worker task handler."""

import logging
from uuid import UUID

logger = logging.getLogger(__name__)


def process_job(job_id_str: str) -> None:
    """Process a transcription job. Called by the RQ worker."""
    from app.bootstrap import bootstrap

    job_id = UUID(job_id_str)
    logger.info(f"Worker picking up job {job_id}")

    container = bootstrap()
    container.process_transcription.execute(job_id)

    logger.info(f"Worker completed job {job_id}")
