# Research: UI/UX Redesign & Transcription History

**Date**: 2026-02-20
**Feature**: 001-ui-redesign

## R1: API Enhancement for Job List

**Decision**: Enrich `/api/jobs` response with `size_bytes`, `duration_seconds`, and `format` fields from the associated AudioFile.

**Rationale**: The `/api/jobs` endpoint already fetches `audio_file` for each job (to get `original_filename`). The additional fields are available on the AudioFile entity — just not currently serialized. Zero new queries needed.

**Alternatives considered**:
- Separate API call per job for details → rejected (N+1 problem, slow for 50 jobs)
- New dedicated `/api/jobs/enriched` endpoint → rejected (unnecessary; extend existing endpoint)

## R2: Static Files for Favicon

**Decision**: Create `app/static/` directory and mount via FastAPI `StaticFiles`. Serve inline SVG logo in templates, serve favicon as a static `.svg` file.

**Rationale**: `StaticFiles` is already imported in `app/main.py` but not mounted. Minimal change. SVG favicon is supported by all modern browsers and avoids needing an ICO conversion step.

**Alternatives considered**:
- Inline favicon as base64 data URI → rejected (messy, harder to maintain)
- External CDN for assets → rejected (unnecessary for a single favicon)

## R3: CSS Approach

**Decision**: Keep hand-rolled CSS in Jinja2 templates with refined design tokens. No CSS framework.

**Rationale**: The current codebase uses inline `<style>` blocks in `base.html` and `{% block extra_styles %}`. Adding Tailwind or Bootstrap would introduce build complexity (purging, CDN size). The app has only 3 pages — hand-rolled CSS is perfectly manageable and keeps the stack simple.

**Alternatives considered**:
- Tailwind CSS via CDN → rejected (adds 300KB+ download, overkill for 3 pages)
- CSS file in static directory → possible future move but inline keeps things simple for now

## R4: Client-Side Filtering

**Decision**: Implement status filter tabs and filename search as client-side JavaScript filtering on the already-fetched job list.

**Rationale**: The job list is capped at 50 items. Client-side filtering is instant, requires no API changes, and avoids server round-trips for filter changes.

**Alternatives considered**:
- Server-side filtering with query params → rejected (unnecessary for ≤50 items, adds API complexity)

## R5: Logo Design

**Decision**: Create an inline SVG logo representing audio waveform/speech-to-text concept. Use the existing navy color palette (#0f3460, #16213e). Logo will be embedded directly in `base.html` as an SVG element.

**Rationale**: Inline SVG avoids external file requests, is infinitely scalable, and can be styled with CSS. Keeps deployment simple (no image optimization pipeline).

**Alternatives considered**:
- PNG/WebP logo file → rejected (requires static file serving for header, doesn't scale cleanly)
- Icon font → rejected (overkill for one logo)
