# Tasks: UI/UX Redesign & Transcription History

**Input**: Design documents from `/specs/001-ui-redesign/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-jobs-enhanced.yaml, quickstart.md
**Tests**: Not requested — no test tasks included.

**Organization**: Tasks are grouped by user story. US4 (Logo & Visual Identity) is merged into the Foundational phase since it modifies `base.html` which all other stories depend on.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- US4 tasks are in Foundational phase (base template prerequisite)

---

## Phase 1: Setup

**Purpose**: Mount static files directory and create favicon asset

- [x] T001 Mount static files directory at `/static` in app/main.py
- [x] T002 [P] Create SVG favicon (audio waveform icon, navy palette) in app/static/favicon.svg

**Details**:
- T001: `StaticFiles` is already imported in main.py. Add `app.mount("/static", StaticFiles(directory="app/static"), name="static")` after app creation. Create `app/static/` directory.
- T002: Small SVG icon representing audio/waveform concept. Use `#0f3460` navy color from existing palette. Keep under 2KB.

---

## Phase 2: Foundational (covers US4 - Logo & Visual Identity)

**Purpose**: Base template enhancements that ALL pages depend on. Completes User Story 4 (logo, favicon, visual identity) and enriches the API for User Story 2.

**CRITICAL**: No user story page work can begin until this phase is complete.

- [x] T003 Add inline SVG Voxscribe logo, favicon link tag, and refined global CSS (colors, typography, spacing, responsive base) in app/adapters/inbound/web/templates/base.html
- [x] T004 [P] Enrich /api/jobs response with size_bytes, duration_seconds, and format fields from AudioFile entity in app/adapters/inbound/web/routes.py

**Details**:
- T003: Create inline SVG logo (audio waveform + text concept, ~40x40px icon area). Add `<link rel="icon" href="/static/favicon.svg" type="image/svg+xml">`. Refine `<style>` block: update color palette (`#0f3460`, `#16213e` navy tones), improve typography (system font stack), add spacing/layout design tokens, ensure responsive base grid. Logo should appear in header on every page.
- T004: In the `/api/jobs` route handler, add three fields to each job dict: `"size_bytes": audio_file.size_bytes`, `"duration_seconds": audio_file.duration_seconds`, `"format": audio_file.format.value`. The route already fetches `audio_file` per job — no new queries needed. See `contracts/api-jobs-enhanced.yaml` for schema.

**Checkpoint**: Base template is polished, logo shows on all pages, favicon appears in browser tab, API returns enriched job data.

---

## Phase 3: User Story 1 - Polished Upload Experience (Priority: P1)

**Goal**: Transform the upload page into a modern, inviting interface with polished drop zone, clear form controls, and responsive layout.

**Independent Test**: Visit homepage → verify branded header with logo, polished upload area with drag feedback, responsive layout from 320px to 1920px.

### Implementation for User Story 1

- [x] T005 [US1] Redesign upload drop zone with modern styling, dashed border, upload icon, animated drag/hover feedback, and clear file type instructions in app/adapters/inbound/web/templates/upload.html
- [x] T006 [US1] Improve language selector styling, engine display, and upload button with cohesive form layout in app/adapters/inbound/web/templates/upload.html
- [x] T007 [US1] Add responsive styles for upload section ensuring usability from 320px to 1920px width in app/adapters/inbound/web/templates/upload.html

**Details**:
- T005: Replace current drop zone with larger, more inviting design. Add dashed border with rounded corners, upload cloud icon (inline SVG), "Drag & drop your audio file here" text, supported formats list. On dragover: border color change + slight scale animation. On drop: visual confirmation.
- T006: Style language `<select>` with custom appearance. Show engine name as subtle metadata. Make upload button prominent with hover/active states. Group form elements logically.
- T007: Use CSS media queries. On mobile (<768px): stack form elements vertically, full-width drop zone. On desktop: centered content with max-width constraint.

**Checkpoint**: Upload page looks professional, drag/drop works with visual feedback, responsive on all screen sizes.

---

## Phase 4: User Story 2 - Transcription History Dashboard (Priority: P1)

**Goal**: Rich, scannable history list with metadata columns, color-coded status badges, status filter tabs, and filename search.

**Independent Test**: Create several transcriptions with different statuses → verify history shows all metadata, filter tabs work, search filters by filename, empty state shows when no results match.

**Depends on**: Phase 2 (T004 — API must return size_bytes, duration_seconds, format)

### Implementation for User Story 2

- [x] T008 [US2] Build rich history list with metadata columns (filename, status badge, language, engine, file size, duration, timestamp) and color-coded status badges in app/adapters/inbound/web/templates/upload.html
- [x] T009 [US2] Implement client-side status filter tabs (All, Completed, In Progress, Failed) with active tab styling in app/adapters/inbound/web/templates/upload.html
- [x] T010 [US2] Implement client-side filename search input with instant filtering in app/adapters/inbound/web/templates/upload.html
- [x] T011 [US2] Add empty state display (friendly message + upload CTA) when no transcriptions exist or no results match filters in app/adapters/inbound/web/templates/upload.html

**Details**:
- T008: Replace current simple list with a table/card layout. Each row: truncated filename (link to job page), color-coded status badge (green=completed, blue=in-progress, red=failed, gray=pending), language tag, engine tag, human-readable file size (e.g., "2.4 MB"), duration (e.g., "3:25"), relative timestamp (e.g., "2 hours ago"). Format size_bytes with JS helper. Format duration_seconds as mm:ss.
- T009: Add filter tab bar above history list: "All", "Completed", "In Progress", "Failed". Active tab highlighted. JS filters rows by matching `data-status` attribute. Count shown per tab (e.g., "Completed (5)").
- T010: Add search input above/beside filter tabs. On keyup, filter visible rows by filename text match (case-insensitive). Combine with status filter (both must match).
- T011: When job list is empty OR all items filtered out, show centered message: icon + "No transcriptions yet" / "No matching transcriptions" + link to scroll to upload area.

**Checkpoint**: History section shows all metadata, status filters work instantly, search narrows results, empty state appears when appropriate.

---

## Phase 5: User Story 3 - Enhanced Job Detail Page (Priority: P2)

**Goal**: Polished result page with word count, improved typography, smooth progress display with stage labels, and clear error states.

**Independent Test**: Upload a file → watch progress page with stage labels → view completed result with word count, readable text, copy button → verify failed jobs show clear error with retry action.

### Implementation for User Story 3

- [x] T012 [US3] Add word count display and enhanced metadata section (duration, engine, language, processing time) for completed transcriptions in app/adapters/inbound/web/templates/job.html
- [x] T013 [US3] Enhance progress indicator with stage labels (Converting, Transcribing), smooth animation, and percentage display in app/adapters/inbound/web/templates/job.html
- [x] T014 [US3] Improve result text area with refined typography (line-height, font-size, max-width for readability), comfortable scrolling for long texts, and copy-to-clipboard visual confirmation in app/adapters/inbound/web/templates/job.html
- [x] T015 [US3] Improve failed job display with clear error message styling and "Upload Another File" action button in app/adapters/inbound/web/templates/job.html

**Details**:
- T012: Calculate word count client-side from transcription text (`text.split(/\s+/).length`). Display in metadata bar: "1,234 words | 3:25 duration | Groq whisper-large-v3 | Portuguese". Style as subtle info bar above or below transcription text.
- T013: During CONVERTING/TRANSCRIBING states, show labeled progress bar. Label changes with status: "Converting audio..." → "Transcribing...". Animate progress bar smoothly. Show percentage text.
- T014: Set result text `line-height: 1.8`, `font-size: 1.1rem`, `max-width: 72ch` for optimal reading. Add padding. For long texts, use `max-height` with `overflow-y: auto`. On copy button click, show brief "Copied!" tooltip/text feedback.
- T015: For FAILED status, show error message in a distinct error card (red/orange accent). Add prominent "Upload Another File" button linking back to homepage.

**Checkpoint**: Completed jobs show word count and metadata, progress page has smooth labeled progress, text is easy to read, failed jobs have clear error display.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency pass and validation

- [x] T016 [P] Cross-page responsive audit and visual consistency fixes across all templates in app/adapters/inbound/web/templates/
- [x] T017 [P] Run existing unit tests to verify no regressions (poetry run pytest tests/unit/ -v)
- [x] T018 Run quickstart.md end-to-end validation (start server, check API fields, visit all pages, verify mobile layout)

**Details**:
- T016: Check all three pages at 320px, 768px, 1024px, 1920px widths. Verify color palette consistency, font sizes, spacing. Fix any visual inconsistencies.
- T017: All existing tests must pass. The API change (T004) should not break existing test expectations since new fields are additive.
- T018: Follow quickstart.md verification steps: run tests, start dev server, curl /api/jobs to verify new fields, visit upload page and job page, confirm visual changes.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001 for static mount, T002 for favicon file)
- **US1 (Phase 3)**: Depends on Phase 2 (T003 — needs base template refinements)
- **US2 (Phase 4)**: Depends on Phase 2 (T003 for base template + T004 for enriched API)
- **US3 (Phase 5)**: Depends on Phase 2 (T003 — needs base template refinements)
- **Polish (Phase 6)**: Depends on all user story phases being complete

### Cross-Phase Parallel Opportunities

Once Phase 2 is complete:
- **US1 (Phase 3)** and **US3 (Phase 5)** modify different files (`upload.html` vs `job.html`) and CAN run in parallel
- **US2 (Phase 4)** modifies `upload.html` (same as US1) — must run after US1 or be carefully merged

### Within Each Phase

- Tasks within the same file must be executed sequentially (no [P] marker)
- Tasks marked [P] touch different files and can run in parallel

### Suggested Execution Flow (Single Developer)

```
Phase 1: T001 → T002 (parallel)
Phase 2: T003 → T004 (parallel with T003 since different files)
Phase 3: T005 → T006 → T007 (sequential, same file)
Phase 4: T008 → T009 → T010 → T011 (sequential, same file)
Phase 5: T012 → T013 → T014 → T015 (sequential, same file)
Phase 6: T016 + T017 (parallel) → T018
```

---

## Parallel Example: Foundational Phase

```bash
# These can run in parallel (different files):
Task: "Add inline SVG logo, favicon link, refined CSS in base.html"   # T003
Task: "Enrich /api/jobs with size_bytes, duration_seconds, format in routes.py"  # T004
```

## Parallel Example: After Foundational

```bash
# These can run in parallel (different template files):
Task: "Redesign upload drop zone in upload.html"  # T005 (US1)
Task: "Add word count display in job.html"         # T012 (US3)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 4)

1. Complete Phase 1: Setup (static files)
2. Complete Phase 2: Foundational (logo, base CSS, API enrichment) — delivers US4
3. Complete Phase 3: User Story 1 (polished upload)
4. **STOP and VALIDATE**: App has branded identity + polished upload experience
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Branded base template with logo/favicon (US4 complete)
2. Add US1 → Polished upload experience → Deploy
3. Add US2 → Rich history with filters/search → Deploy
4. Add US3 → Enhanced job detail page → Deploy
5. Polish → Final consistency pass → Deploy

### File Impact Summary

| File | Tasks | Stories |
|------|-------|---------|
| app/main.py | T001 | Setup |
| app/static/favicon.svg | T002 | Setup/US4 |
| app/adapters/inbound/web/templates/base.html | T003 | US4 (Foundational) |
| app/adapters/inbound/web/routes.py | T004 | US2 (Foundational) |
| app/adapters/inbound/web/templates/upload.html | T005-T011 | US1, US2 |
| app/adapters/inbound/web/templates/job.html | T012-T015 | US3 |

---

## Notes

- No new Python dependencies required
- No database migrations needed
- All CSS is inline in templates (no external CSS files)
- Client-side filtering uses vanilla JavaScript (no frameworks)
- SVG logo is inline in base.html (no external image files)
- Favicon is the only static file served
- Existing unit tests should continue to pass unchanged
