# Quickstart: UX Improvements

**Branch**: `004-ux-improvements` | **Date**: 2026-03-31

## What This Feature Does

Five incremental UX improvements that bring Voxscribe from a functional tool to a polished product:
1. Audio playback with waveform visualization on the result page
2. Guided onboarding with sample demo for first-time users
3. WCAG AA accessibility compliance
4. SRT/VTT subtitle export formats
5. Upload polish (M4A bug fix, cancel button, progressive disclosure)

## Key Design Decisions

1. **wavesurfer.js via CDN** — lightweight waveform library, same CDN pattern as HTMX
2. **Graceful degradation** — if wavesurfer fails to load, fall back to HTML5 `<audio>` element
3. **Audio streaming with Range requests** — enables seeking without downloading entire file
4. **Subtitle generation in domain layer** — pure function, no external deps, testable
5. **Sample audio bundled** — 15-second pt-BR clip in `app/static/sample/`, no external fetch
6. **No new Python dependencies** — all frontend improvements use vanilla JS + CDN libraries

## Files to Create

| File | Purpose |
|------|---------|
| `app/domain/services/subtitle_generator.py` | Generate SRT/VTT from transcription text + duration |
| `app/static/sample/sample-pt-br.mp3` | 15-second sample audio for onboarding demo |
| `tests/unit/domain/test_subtitle_generator.py` | SRT/VTT output validation tests |
| `tests/e2e/test_ux_improvements.py` | Audio endpoint, export, sample demo e2e tests |

## Files to Modify

| File | Change |
|------|--------|
| `app/adapters/inbound/web/routes.py` | Add `GET /api/jobs/{id}/audio` (Range-request audio stream), `GET /api/jobs/{id}/result/download/{format}` (SRT/VTT), `POST /api/sample` (demo) |
| `app/adapters/inbound/web/templates/job.html` | Add wavesurfer.js player, speed control, stage explanations, ARIA labels |
| `app/adapters/inbound/web/templates/upload.html` | Redesigned empty state, hint banner, M4A fix, cancel button, progressive disclosure, ARIA labels |
| `app/adapters/inbound/web/templates/base.html` | Skip-to-content link, theme toggle aria-pressed |

## New API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/jobs/{id}/audio` | Stream original audio with Range support for seeking |
| GET | `/api/jobs/{id}/result/download/srt` | Download SRT subtitle file |
| GET | `/api/jobs/{id}/result/download/vtt` | Download VTT subtitle file |
| POST | `/api/sample` | Submit bundled sample audio for demo transcription |
