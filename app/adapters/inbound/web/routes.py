"""FastAPI routes for the web UI and API."""

import asyncio
import json
import logging
import os
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.adapters.inbound.web.schemas import (
    AudioFileSchema,
    HealthResponse,
    JobStatusResponse,
    TranscriptionResultResponse,
    UploadResponse,
)
from app.application.dto import SubmitTranscriptionRequest
from app.bootstrap import get_container
from app.domain.exceptions import (
    FileTooLargeError,
    InvalidAudioFormatError,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=_templates_dir)


# ── HTML Pages ──────────────────────────────────────────────


@router.get("/")
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@router.get("/jobs/{job_id}")
async def job_page(request: Request, job_id: UUID):
    container = get_container()
    job = container.get_job_status.execute(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    result = container.get_job_status.get_result(job_id)

    return templates.TemplateResponse(
        "job.html",
        {"request": request, "job": job, "result": result},
    )


# ── API Endpoints ───────────────────────────────────────────


@router.post("/api/upload", status_code=201, response_model=UploadResponse)
async def upload_file(file: UploadFile, language: str = "pt-BR"):
    container = get_container()

    file_data = await file.read()

    try:
        request = SubmitTranscriptionRequest(
            filename=file.filename or "unknown",
            file_data=file_data,
            language=language,
        )
        response = container.submit_transcription.execute(request)
    except InvalidAudioFormatError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

    return UploadResponse(
        job_id=response.job_id,
        status=response.status,
        redirect_url=response.redirect_url,
    )


@router.get("/api/jobs")
async def list_jobs():
    container = get_container()
    jobs = container.repository.get_all_jobs(limit=50)
    result = []
    for job in jobs:
        audio = container.repository.get_audio_file(job.audio_file_id)
        result.append({
            "job_id": str(job.id),
            "status": job.status.value,
            "progress_percent": job.progress_percent,
            "language": job.language,
            "engine_name": job.engine_name,
            "original_filename": audio.original_filename if audio else "unknown",
            "created_at": job.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "error_message": job.error_message,
        })
    return result


@router.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: UUID):
    container = get_container()
    job = container.get_job_status.execute(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    audio_file_schema = None
    if job.audio_file:
        audio_file_schema = AudioFileSchema(
            original_filename=job.audio_file.original_filename,
            format=job.audio_file.format,
            size_bytes=job.audio_file.size_bytes,
            duration_seconds=job.audio_file.duration_seconds,
        )

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress_percent=job.progress_percent,
        language=job.language,
        engine_name=job.engine_name,
        audio_file=audio_file_schema,
        created_at=job.created_at,
        updated_at=job.updated_at,
        error_message=job.error_message,
    )


@router.get("/api/jobs/{job_id}/result", response_model=TranscriptionResultResponse)
async def get_result(job_id: UUID):
    container = get_container()
    result = container.get_job_status.get_result(job_id)
    if result is None:
        raise HTTPException(
            status_code=404, detail="Job not found or not yet completed"
        )

    return TranscriptionResultResponse(
        job_id=result.job_id,
        full_text=result.full_text,
        language=result.language,
        engine_name=result.engine_name,
        processing_duration_seconds=result.processing_duration_seconds,
    )


@router.get("/api/jobs/{job_id}/result/download")
async def download_result(job_id: UUID):
    container = get_container()
    result = container.get_job_status.get_result(job_id)
    if result is None:
        raise HTTPException(
            status_code=404, detail="Job not found or not yet completed"
        )

    job = container.get_job_status.execute(job_id)
    filename = "transcription.txt"
    if job and job.audio_file:
        base = os.path.splitext(job.audio_file.original_filename)[0]
        filename = f"{base}.txt"

    return PlainTextResponse(
        content=result.full_text,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/jobs/{job_id}/progress")
async def job_progress_sse(job_id: UUID):
    container = get_container()

    async def event_stream():
        last_status = None
        last_progress = -1

        while True:
            job = container.get_job_status.execute(job_id)
            if job is None:
                yield f"event: error\ndata: {{\"error\": \"Job not found\"}}\n\n"
                return

            if job.status != last_status or job.progress_percent != last_progress:
                last_status = job.status
                last_progress = job.progress_percent
                data = json.dumps(
                    {"status": job.status, "progress_percent": job.progress_percent}
                )
                yield f"event: status\ndata: {data}\n\n"

            if job.status in ("COMPLETED", "FAILED"):
                done_data = json.dumps({"redirect_url": f"/jobs/{job_id}"})
                yield f"event: done\ndata: {done_data}\n\n"
                return

            await asyncio.sleep(1)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    container = get_container()

    redis_status = "disconnected"
    try:
        from redis import Redis

        r = Redis.from_url(container.settings.redis_url)
        r.ping()
        redis_status = "connected"
    except Exception:
        pass

    return HealthResponse(
        status="healthy",
        engine=container.settings.transcription_engine,
        redis=redis_status,
    )
