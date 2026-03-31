# Tasks: UX Improvements

**Input**: Design documents from `/specs/004-ux-improvements/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md, contracts/api.yaml

**Tests**: Included — the project has an established test structure and testing is part of the plan.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No new dependencies needed (wavesurfer.js is CDN-loaded). Create sample audio file.

- [x] T001 Create sample audio directory and add a 15-second pt-BR speech sample at app/static/sample/sample-pt-br.mp3. Generate using text-to-speech or record a short clip. Must be a valid MP3 file under 500 KB.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend endpoints and domain services that multiple user stories depend on.

**CRITICAL**: US1 (audio player) and US4 (export formats) need these endpoints before frontend work.

- [x] T002 Create subtitle generator service at app/domain/services/subtitle_generator.py. Implement `generate_srt(text: str, duration_seconds: float) -> str` and `generate_vtt(text: str, duration_seconds: float) -> str`. Split text into segments (by sentence or ~10-word chunks), distribute timestamps proportionally across the total duration, and format as valid SRT/VTT.
- [x] T003 [P] Add `GET /api/jobs/{job_id}/audio` endpoint to app/adapters/inbound/web/routes.py. Serve the audio file (prefer converted WAV if exists, otherwise original) using `FileResponse` with `stat_result` for Range request support. Set `Content-Type` based on file extension. Handle 404 if job or file not found.
- [x] T004 [P] Add `GET /api/jobs/{job_id}/result/download/{format}` endpoint to app/adapters/inbound/web/routes.py. Accept format path param: "txt", "srt", "vtt". For "txt", use existing download logic. For "srt"/"vtt", call subtitle_generator with result text and audio duration. Return with appropriate Content-Type and Content-Disposition headers.
- [x] T005 [P] Add `POST /api/sample` endpoint to app/adapters/inbound/web/routes.py. Read the sample audio from `app/static/sample/sample-pt-br.mp3`, submit it through the existing `SubmitTranscriptionUseCase.execute()` flow (same as a normal file upload), and return `UploadResponse` with redirect URL.
- [x] T006 Write unit tests for subtitle generator at tests/unit/domain/test_subtitle_generator.py. Test: SRT output has sequential numbering and valid timestamp format (HH:MM:SS,mmm), VTT output starts with "WEBVTT" header, empty text returns empty subtitle file, single-sentence text produces one cue, multi-paragraph text produces multiple cues with distributed timestamps.

**Checkpoint**: Backend ready — audio streaming, subtitle export, and sample demo endpoints all functional.

---

## Phase 3: User Story 1 — Audio Playback on Result Page (Priority: P1) MVP

**Goal**: Completed job pages show an audio player with waveform, speed control, and click-to-seek.

**Independent Test**: Open a completed job → see waveform player → play audio → change speed → click waveform to seek.

### Implementation for User Story 1

- [x] T007 [US1] Add wavesurfer.js integration to app/adapters/inbound/web/templates/job.html. In the result section (only when job is COMPLETED): (1) Load wavesurfer.js from CDN (`https://unpkg.com/wavesurfer.js@7`), (2) Add a `<div id="waveform">` container above the transcription text, (3) Initialize WaveSurfer with `url: '/api/jobs/{{ job.job_id }}/audio'`, colors matching the theme (waveColor: var(--slate-400), progressColor: var(--navy-800)), (4) Add play/pause button, (5) Add current time / duration display. Graceful fallback: if WaveSurfer fails to load, show a basic `<audio controls>` element instead.
- [x] T008 [US1] Add playback speed control to the audio player in app/adapters/inbound/web/templates/job.html. Render speed buttons or a dropdown with options: 0.5x, 0.75x, 1x, 1.25x, 1.5x, 2x. Default: 1x. On selection, call `wavesurfer.setPlaybackRate(speed)`. Style active speed with the navy accent color. Persist selected speed in sessionStorage for the current session.
- [x] T009 [US1] Add CSS styles for the audio player section in job.html. Style the waveform container, play/pause button, speed selector, and time display to match the existing dark/light theme system. Ensure responsive layout: on mobile (<600px), stack controls vertically. Add dark mode overrides for waveform colors.
- [x] T010 [US1] Write e2e test for audio streaming endpoint at tests/e2e/test_ux_improvements.py. Test: `GET /api/jobs/{id}/audio` returns 200 with audio content-type for completed jobs, returns 404 for non-existent jobs, supports Range header (returns 206 with Content-Range).

**Checkpoint**: Users can play audio with waveform visualization, seek by clicking, and adjust speed on completed job pages.

---

## Phase 4: User Story 2 — Guided Empty State and Onboarding (Priority: P2)

**Goal**: First-time users see clear guidance and can try a sample transcription.

**Independent Test**: Visit with no history → see guided empty state → click "Try with sample audio" → job created → redirected to job page.

### Implementation for User Story 2

- [x] T011 [US2] Redesign the empty state in app/adapters/inbound/web/templates/upload.html. Replace the current "No transcriptions yet" empty state with: (1) An SVG waveform illustration (inline, matches brand colors), (2) Heading: "No transcriptions yet", (3) Description: "Drop an audio file above or paste an Instagram URL to get started. Supports MP3, WAV, FLAC, OGG, M4A — up to 500 MB.", (4) Button: "Try with sample audio" that POSTs to `/api/sample` and redirects to the job page on success. Style to match the existing card design.
- [x] T012 [US2] Add first-visit hint banner in app/adapters/inbound/web/templates/upload.html. Above the mode tabs, show a dismissible banner on first visit: "You can also paste Instagram Reel URLs to transcribe video audio." with a dismiss [×] button. Use localStorage key `voxscribe-hint-dismissed` to persist dismissal. Add CSS for the hint banner (subtle background, border, dismiss button).
- [x] T013 [US2] Add processing stage explanations in app/adapters/inbound/web/templates/job.html. Update the progress stage text to include brief descriptions: "Waiting in queue..." → "Waiting in queue — your file is next", "Downloading reel audio..." → "Downloading reel audio from Instagram...", "Converting audio..." → "Optimizing audio for transcription (16kHz mono)...", "Transcribing..." → "AI is converting speech to text...", "Processing..." → "Processing your audio...". Update both the Jinja2 template and the SSE JavaScript handler.
- [x] T014 [US2] Write e2e test for sample demo at tests/e2e/test_ux_improvements.py. Test: `POST /api/sample` returns 201 with job_id, status "PENDING", and redirect_url. Test: `POST /api/sample` with custom language returns job with that language.

**Checkpoint**: New users see a welcoming empty state, can try the sample flow, and see contextual hints.

---

## Phase 5: User Story 3 — Accessibility and Keyboard Navigation (Priority: P3)

**Goal**: All interactive elements meet WCAG AA compliance.

**Independent Test**: Navigate upload → job flow with keyboard only. Verify screen reader announces status changes.

### Implementation for User Story 3

- [x] T015 [P] [US3] Add accessibility attributes to app/adapters/inbound/web/templates/upload.html. Changes: (1) Drop zone: add `role="button"`, `tabindex="0"`, `aria-label="Upload audio file. Drag and drop or click to select."`, add keydown handler for Enter/Space to trigger file input. (2) Search input: add `aria-label="Search transcriptions by filename"`. (3) Mode tabs: add `role="tablist"` on container, `role="tab"` and `aria-selected` on each tab. (4) File list: add `aria-live="polite"` for dynamic updates.
- [x] T016 [P] [US3] Add accessibility attributes to app/adapters/inbound/web/templates/job.html. Changes: (1) Progress section: add `aria-live="polite"` and `role="status"` on progress-stage element. (2) Status badge: add `role="status"` and `aria-live="assertive"`. (3) Expand toggle: add `aria-expanded="false"` (toggled via JS), `aria-controls="result-text"`. (4) Copy feedback: add `aria-live="polite"` on feedback span. (5) Result text: add `id="result-text"` for aria-controls reference.
- [x] T017 [P] [US3] Add skip-to-content link and theme toggle accessibility in app/adapters/inbound/web/templates/base.html. Changes: (1) Add visually-hidden skip link as first element in body: `<a href="#main-content" class="skip-link">Skip to content</a>`. (2) Add `id="main-content"` to the main content container. (3) Theme toggle: add `aria-label="Toggle dark mode"`, `aria-pressed="false"` (toggled in JS). (4) Add CSS for `.skip-link` (visually hidden, visible on focus).

**Checkpoint**: All interactive elements keyboard-navigable. Screen readers announce status changes and copy feedback.

---

## Phase 6: User Story 4 — Multiple Export Formats (Priority: P4)

**Goal**: Users can download transcriptions as TXT, SRT, or VTT.

**Independent Test**: Complete a transcription → see download format options → download SRT → valid subtitle file.

### Implementation for User Story 4

- [x] T018 [US4] Update the download section in app/adapters/inbound/web/templates/job.html. Replace the single "Download TXT" button with a dropdown or button group showing three options: "TXT", "SRT", "VTT". Each option links to `/api/jobs/{{ job.job_id }}/result/download/{format}`. Style to match existing button design. Add tooltip text explaining each format: "Plain text", "Subtitles (SubRip)", "Web subtitles (WebVTT)".
- [x] T019 [US4] Write e2e tests for export formats at tests/e2e/test_ux_improvements.py. Test: `GET /api/jobs/{id}/result/download/txt` returns plain text (existing behavior preserved). Test: `GET /api/jobs/{id}/result/download/srt` returns content with SRT structure. Test: `GET /api/jobs/{id}/result/download/vtt` returns content starting with "WEBVTT". Test: invalid format returns 400.

**Checkpoint**: Users can download in TXT, SRT, or VTT format.

---

## Phase 7: User Story 5 — Upload Polish and Bug Fixes (Priority: P5)

**Goal**: M4A bug fixed, cancel button added, progressive disclosure, better errors.

**Independent Test**: Upload M4A → accepted. Start upload → cancel. See collapsed options by default.

### Implementation for User Story 5

- [x] T020 [P] [US5] Fix M4A client-side validation in app/adapters/inbound/web/templates/upload.html. Add `.m4a` to the JavaScript `ALLOWED` array. Change: `var ALLOWED = ['.mp3', '.wav', '.flac', '.ogg'];` → `var ALLOWED = ['.mp3', '.wav', '.flac', '.ogg', '.m4a'];`.
- [x] T021 [P] [US5] Add upload cancel button in app/adapters/inbound/web/templates/upload.html. During file upload (when progress bar is visible), show a "Cancel" button next to the progress bar. On click, call `xhr.abort()` on the active XMLHttpRequest, hide progress bar, re-enable the submit button, and show a toast: "Upload cancelled". Add CSS for the cancel button (subtle red styling).
- [x] T022 [US5] Add progressive disclosure for language/options in app/adapters/inbound/web/templates/upload.html. Wrap the language selector in a collapsible "Options" section. Default collapsed, showing "Options ▸" toggle. On click, expand to show language dropdown (and future engine selector). Apply default language (pt-BR) without requiring user to see the selector. Store expansion state in sessionStorage.
- [x] T023 [US5] Improve error messages in app/adapters/inbound/web/templates/upload.html. Update the `showError()` function and XHR error handlers to show more specific messages: (1) Network errors: "Connection lost. Check your internet and try again." (2) 413 responses: "File too large. Maximum size is 500 MB." (3) 503 responses: "The transcription service is temporarily unavailable. Please try again in a few minutes." (4) Generic errors: Include the server's detail message when available.

**Checkpoint**: M4A accepted, uploads cancellable, options collapsed, errors descriptive.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and cleanup.

- [x] T024 [P] Run full test suite (`uv run pytest tests/ -v --cov=app`) and fix any regressions. Verify all existing tests still pass alongside new tests.
- [x] T025 [P] Run ruff lint and format checks (`uv run ruff check . && uv run ruff format --check .`) and fix any violations.
- [x] T026 Verify dark mode compatibility: ensure all new UI elements (waveform, speed controls, empty state, hint banner, export buttons, cancel button) render correctly in both light and dark themes.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — create sample audio
- **Foundational (Phase 2)**: No dependencies on setup — backend endpoints
- **US1 Audio Player (Phase 3)**: Depends on Phase 2 T003 (audio streaming endpoint)
- **US2 Onboarding (Phase 4)**: Depends on Phase 2 T005 (sample endpoint)
- **US3 Accessibility (Phase 5)**: No backend dependencies — can start after Phase 2
- **US4 Export Formats (Phase 6)**: Depends on Phase 2 T002 + T004 (subtitle generator + endpoint)
- **US5 Upload Polish (Phase 7)**: No dependencies — can start anytime after Phase 2
- **Polish (Phase 8)**: After all user stories complete

### User Story Dependencies

- **US1 (P1)**: Needs audio streaming endpoint (T003)
- **US2 (P2)**: Needs sample endpoint (T005)
- **US3 (P3)**: Independent — pure frontend ARIA changes
- **US4 (P4)**: Needs subtitle generator (T002) + download endpoint (T004)
- **US5 (P5)**: Independent — pure frontend fixes

### Parallel Opportunities

Phase 2: T003, T004, T005 can all run in parallel (different endpoints, same file but different functions).

Phase 5 (US3): T015, T016, T017 can all run in parallel (different template files).

Phase 7 (US5): T020, T021 can run in parallel (different parts of upload.html, no overlap).

US3 (Phase 5), US5 (Phase 7) can run in parallel with US1 (Phase 3) and US4 (Phase 6) since they touch different template sections.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: T002, T003, T004, T005, T006
3. Complete Phase 3: US1 Audio Player (T007-T010)
4. **STOP and VALIDATE**: Open a completed job page, verify waveform plays
5. Deploy — audio playback alone is a major UX win

### Incremental Delivery

1. Phase 2 (backend) → Foundation ready
2. US1 (audio player) → Users can verify transcriptions (MVP!)
3. US2 (onboarding) → First-time UX dramatically improved
4. US3 (accessibility) → WCAG AA compliance
5. US4 (export) → Content creators get subtitle formats
6. US5 (polish) → Bug fixes and refinements

---

## Notes

- wavesurfer.js v7 loaded from `https://unpkg.com/wavesurfer.js@7` — same CDN pattern as HTMX
- Sample audio must be a real speech clip (not silence) for the demo to be meaningful
- SRT/VTT timestamps are approximate without word-level data — distributed proportionally by text length
- The existing `/api/jobs/{id}/result/download` endpoint (TXT) remains unchanged for backward compatibility
- Dark mode CSS variables must be tested for all new UI elements
