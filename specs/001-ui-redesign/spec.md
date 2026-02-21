# Feature Specification: UI/UX Redesign & Transcription History

**Feature Branch**: `001-ui-redesign`
**Created**: 2026-02-20
**Status**: Draft
**Input**: User description: "Improve UX/UI, improve the history of transcriptions, improve the interface, generate a small logo and so on"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Polished Upload Experience (Priority: P1)

A user visits the app and sees a modern, branded interface with a distinctive logo and clear visual identity — not a generic-looking tool. The upload area is inviting, the language selector is clear, and the overall layout feels professional and trustworthy.

**Why this priority**: First impressions determine whether users trust the tool enough to upload their files. The upload page is the entry point for 100% of users.

**Independent Test**: Can be fully tested by visiting the homepage and verifying the visual design, logo presence, responsive layout, and upload flow work end-to-end.

**Acceptance Scenarios**:

1. **Given** a user visits the homepage, **When** the page loads, **Then** they see a branded header with a logo/icon, the app name "Voxscribe", and a visually polished upload area
2. **Given** a user is on mobile, **When** viewing the upload page, **Then** all elements are properly sized and accessible without horizontal scrolling
3. **Given** a user drags a file into the drop zone, **When** hovering, **Then** the drop zone shows clear visual feedback (color change, icon animation)
4. **Given** a user uploads a file, **When** the upload completes, **Then** they see smooth progress feedback and are redirected to the job page

---

### User Story 2 - Transcription History Dashboard (Priority: P1)

A user wants to see all their past transcriptions in a rich, scannable list — not just filename and status. They need to see duration, file size, engine used, and be able to quickly identify completed vs in-progress vs failed jobs. They can filter through their history.

**Why this priority**: Users frequently return to find previous transcriptions. A usable history is essential for repeat usage and is currently minimal (just filename + badge + date).

**Independent Test**: Can be fully tested by creating several transcriptions and verifying the history list displays all metadata, supports filtering, and links to individual results.

**Acceptance Scenarios**:

1. **Given** a user has multiple transcriptions, **When** they view the history section, **Then** each entry shows: filename, status badge, language, engine, file size, duration, and timestamp
2. **Given** a user has many transcriptions, **When** they want to find a specific one, **Then** they can filter by status (all, completed, failed, in-progress) and search by filename
3. **Given** a user clicks on a completed transcription in the history, **When** the job page loads, **Then** they see the full transcription text with copy/download options
4. **Given** there are no transcriptions yet, **When** viewing the history section, **Then** a friendly empty state with a call-to-action to upload is shown

---

### User Story 3 - Enhanced Job Detail Page (Priority: P2)

A user viewing a transcription result wants a polished experience: readable text formatting, clear metadata display, word count, and easy actions (copy, download). The progress view during transcription should feel smooth and informative.

**Why this priority**: The result page is where users get their actual value. A better reading experience and clear metadata increases satisfaction and trust in the tool.

**Independent Test**: Can be fully tested by uploading a file, watching the progress page, and then reviewing the completed result page for layout, actions, and metadata display.

**Acceptance Scenarios**:

1. **Given** a transcription is complete, **When** viewing the result, **Then** the text is displayed in a clean, readable format with word count shown
2. **Given** a transcription is in progress, **When** viewing the job page, **Then** the user sees a smooth progress bar with status updates and stage labels (Converting, Transcribing)
3. **Given** a completed transcription, **When** the user clicks "Copy to Clipboard", **Then** the full text is copied and a visual confirmation is shown
4. **Given** a failed transcription, **When** viewing the job page, **Then** the error is displayed clearly with an "Upload Again" action

---

### User Story 4 - App Logo & Visual Identity (Priority: P2)

The app displays a custom SVG logo/icon that represents audio transcription. The logo appears in the header, browser tab (favicon), and reinforces the "Voxscribe" brand identity.

**Why this priority**: A logo transforms the app from a prototype feel to a finished product. It builds brand recognition and trust.

**Independent Test**: Can be tested by verifying the logo renders in the header, the favicon shows in the browser tab, and the logo scales correctly on different screen sizes.

**Acceptance Scenarios**:

1. **Given** a user visits any page, **When** the page loads, **Then** a Voxscribe logo/icon is visible in the header area
2. **Given** a user has the tab open, **When** looking at the browser tab, **Then** a recognizable favicon is displayed
3. **Given** different screen sizes, **When** the logo renders, **Then** it scales appropriately without distortion

---

### Edge Cases

- What happens when the transcription text is very long (10,000+ words)? The result area should support comfortable scrolling and the copy button should still work
- What happens when a file has no recognizable speech? The result should show the output as-is rather than empty text
- What happens when the job list is empty? A friendly empty state should guide users to upload their first file
- What happens on very slow connections? The upload progress should remain informative and not appear frozen

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST display a custom SVG logo/icon in the header of every page
- **FR-002**: The app MUST display a favicon in the browser tab
- **FR-003**: The upload page MUST show a visually polished drop zone with clear instructions and animated hover/drag feedback
- **FR-004**: The transcription history section MUST display: filename, status badge (color-coded), language, engine name, file size, audio duration, and timestamp for each job
- **FR-005**: The history section MUST support filtering by status (All, Completed, In Progress, Failed)
- **FR-006**: The history section MUST support filtering by filename text
- **FR-007**: The job detail page MUST display word count for completed transcriptions
- **FR-008**: The job detail page MUST show a progress indicator during transcription with stage labels (Converting, Transcribing)
- **FR-009**: The result text area MUST support comfortable reading with proper typography and scrolling for long texts
- **FR-010**: All pages MUST be responsive and usable on screens from 320px to 1920px width
- **FR-011**: The app MUST use a cohesive color scheme and typography across all pages
- **FR-012**: The history section MUST load data from the existing API without requiring full page refresh

### Key Entities

- **TranscriptionJob**: Existing entity — now displayed with richer metadata in the history list (filename, status, language, engine, size, duration, timestamp, error message)
- **AudioFile**: Existing entity — size and duration now prominently displayed in history rows

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify the status of any transcription within 2 seconds of viewing the history list (clear visual hierarchy with color-coded badges)
- **SC-002**: Users can find a specific past transcription within 5 seconds using search or status filter
- **SC-003**: The app is visually branded — logo, favicon, and consistent visual identity present on all pages
- **SC-004**: All pages render correctly on mobile devices (320px width) without horizontal scrolling or broken layouts
- **SC-005**: The transcription result page displays word count and processing metadata clearly
- **SC-006**: Users can copy or download transcription results in one click from the result page

## Assumptions

- The app name is "Voxscribe" and the logo should represent audio/sound/transcription concepts
- The SVG logo will be inline (no external image files) to keep deployment simple
- The existing API endpoints (`/api/jobs`, `/api/jobs/{id}`, `/api/jobs/{id}/result`) provide all data needed — the `/api/jobs` endpoint may need minor enrichment (adding duration, size fields)
- Status filter and filename search will be client-side since the job list is limited to 50 items
- The current Jinja2 + vanilla JS approach will be maintained (no frontend framework)
- Color scheme will evolve from the current navy/slate palette into a more polished version
