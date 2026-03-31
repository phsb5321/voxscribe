# Implementation Plan: UX Improvements

**Branch**: `004-ux-improvements` | **Date**: 2026-03-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-ux-improvements/spec.md`

## Summary

Improve Voxscribe's user experience with five incremental changes: (1) audio playback with waveform on the result page via wavesurfer.js, (2) guided onboarding with empty state redesign and sample audio demo, (3) WCAG AA accessibility compliance, (4) SRT/VTT export formats, and (5) upload polish including the M4A bug fix. All changes are frontend-heavy with minimal backend additions (audio streaming endpoint, subtitle generation service).

## Technical Context

**Language/Version**: Python 3.12 + vanilla JavaScript (no build tools)
**Primary Dependencies**: FastAPI, Jinja2, HTMX 2.0.4 (CDN), wavesurfer.js v7 (CDN, new)
**Storage**: SQLite (existing), local filesystem (existing)
**Testing**: pytest, httpx, pytest-asyncio
**Target Platform**: Linux server (Docker), modern browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (FastAPI + Jinja2 templates + vanilla JS)
**Performance Goals**: Audio player loads within 2s, waveform renders within 3s for files up to 30min
**Constraints**: No build tooling (webpack, vite). CDN-loaded libraries only. wavesurfer.js must degrade gracefully if CDN fails.
**Scale/Scope**: Single-user/small-team tool. Same 2-page architecture (upload + job).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Assessment |
|-----------|--------|------------|
| **I. Hexagonal Simplicity** | PASS | No new architectural layers. Audio streaming is a new route in the existing web adapter. Subtitle generation is a new domain service. Sample audio is a static file. All fit existing patterns. |
| **II. Reliability** | PASS | Audio streaming uses Range requests with proper error handling. wavesurfer.js has graceful fallback to HTML5 `<audio>`. Sample audio bundled locally (no external dependency). |
| **III. Containerized Deployment** | PASS | wavesurfer.js loaded from CDN (same as HTMX). Sample audio file added to `app/static/`. No Dockerfile changes needed. |
| **IV. Background Job Processing** | PASS | No changes to job processing pipeline. Audio playback is read-only access to existing stored files. |
| **V. Dependency Hygiene** | PASS | No new Python dependencies. wavesurfer.js is a CDN script tag (same pattern as HTMX). |
| **VI. Code Quality** | PASS | All changes will pass ruff lint/format. New e2e tests for audio endpoint and export formats. |
| **VII. Conventional Commits** | PASS | Feature branch from develop, conventional commit messages. |

**GATE RESULT: PASS** — No violations.

## Project Structure

### Documentation (this feature)

```text
specs/004-ux-improvements/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Competitor analysis, UX research, accessibility audit
├── quickstart.md        # Implementation overview and file map
├── checklists/
│   └── requirements.md  # Quality checklist
└── tasks.md             # Task breakdown (created by /speckit.tasks)
```

### Source Code (repository root)

```text
app/
├── domain/
│   └── services/
│       └── subtitle_generator.py    # CREATE: SRT/VTT generation from transcription text
├── adapters/
│   └── inbound/
│       └── web/
│           ├── routes.py            # MODIFY: add audio streaming + subtitle download endpoints
│           └── templates/
│               ├── upload.html      # MODIFY: empty state, onboarding hints, a11y, M4A fix, progressive disclosure
│               ├── job.html         # MODIFY: audio player, waveform, speed control, stage explanations, a11y
│               └── base.html        # MODIFY: skip-to-content link, theme toggle a11y
├── static/
│   └── sample/
│       └── sample-pt-br.mp3        # CREATE: 15-second sample audio for demo

tests/
├── unit/
│   └── domain/
│       └── test_subtitle_generator.py  # CREATE: SRT/VTT generation tests
└── e2e/
    └── test_ux_improvements.py         # CREATE: audio endpoint, export format, sample demo tests
```

**Structure Decision**: Follows the existing hexagonal architecture. The subtitle generator is a domain service (pure logic, no external deps). Audio streaming is a new route in the web adapter. All frontend changes are in existing Jinja2 templates.

## Complexity Tracking

> No constitution violations — this section is empty.
