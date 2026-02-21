# Implementation Plan: UI/UX Redesign & Transcription History

**Branch**: `001-ui-redesign` | **Date**: 2026-02-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-ui-redesign/spec.md`

## Summary

Transform Voxscribe from a prototype UI into a polished, branded application. Add a custom SVG logo and favicon, redesign all three pages (upload, job detail, base layout) with refined visual identity, enrich the transcription history list with metadata/filtering/search, and enhance the job result page with word count and improved typography. One minor API change (3 new fields on `/api/jobs`). No new dependencies, no schema changes.

## Technical Context

**Language/Version**: Python 3.12, Jinja2 templates, vanilla JavaScript
**Primary Dependencies**: FastAPI, Jinja2, HTMX 2.0.4 (already loaded via CDN)
**Storage**: SQLite (no changes)
**Testing**: pytest (unit tests only — no frontend test framework)
**Target Platform**: Linux server (Dokku), served via Cloudflare tunnel
**Project Type**: Web application (server-rendered with progressive enhancement)
**Performance Goals**: Pages render in <1s, history list filters instantly (client-side)
**Constraints**: No new Python dependencies, no CSS framework, inline styles in templates
**Scale/Scope**: 3 pages, 1 API endpoint change, ~5 files modified/created

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity | PASS | No new architectural layers. Extends existing templates and one route. |
| II. Reliability | PASS | No new external calls. Client-side filtering has no failure modes. |
| III. Containerized Deployment | PASS | Static files directory will be created inside `/app/` in the Docker image. No new system deps. |
| IV. Concurrent Processing | N/A | No processing changes. |
| V. Dependency Hygiene | PASS | No new dependencies. Uses existing FastAPI StaticFiles (already imported). |

**Post-Phase 1 Re-check**: All gates still pass. No violations introduced.

## Project Structure

### Documentation (this feature)

```text
specs/001-ui-redesign/
├── plan.md              # This file
├── research.md          # Phase 0: decisions on API, CSS, logo approach
├── data-model.md        # Phase 1: existing entities, API response changes
├── quickstart.md        # Phase 1: implementation guide
├── contracts/           # Phase 1: enhanced API contract
│   └── api-jobs-enhanced.yaml
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (files to modify)

```text
app/
├── main.py                                    # Mount static files
├── static/                                    # NEW directory
│   └── favicon.svg                            # NEW: browser tab icon
└── adapters/inbound/web/
    ├── routes.py                              # Add 3 fields to /api/jobs
    └── templates/
        ├── base.html                          # Logo SVG, favicon, refined global CSS
        ├── upload.html                        # Redesigned upload + rich history
        └── job.html                           # Enhanced result page + word count

tests/
└── unit/                                      # Existing tests (no changes needed)
```

**Structure Decision**: Single project with server-rendered templates. No frontend/backend split — the existing hexagonal architecture with Jinja2 templates is maintained. Static files directory added for favicon only.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
