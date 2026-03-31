# Feature Specification: UX Improvements — Guided Onboarding, Audio Playback, and Polish

**Feature Branch**: `004-ux-improvements`
**Created**: 2026-03-31
**Status**: Draft
**Input**: User description: "Deep analysis on features and user flow for new users, written explanations on how to use the tools, research on UI best practices."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Audio Playback on Result Page (Priority: P1)

A user completes a transcription and wants to verify the result against the original audio. Currently, there is no audio player — the user must download the audio file and play it separately. With this change, the result page includes an inline audio player with waveform visualization, playback speed control, and click-to-seek.

**Why this priority**: Every major competitor (Rev.com, Happy Scribe, Descript, OpenTranscribe) provides audio playback alongside transcription results. This is the single biggest gap in Voxscribe's UX and the feature that would most improve the user's ability to verify and trust the transcription.

**Independent Test**: Open a completed job page → see audio player with waveform → click play → audio plays while progress moves through waveform → change speed to 1.5x → seek to a specific position by clicking the waveform.

**Acceptance Scenarios**:

1. **Given** a user views a completed transcription, **When** the result page loads, **Then** an audio player with waveform visualization is displayed above the transcription text.
2. **Given** the audio player is visible, **When** the user clicks play, **Then** the audio begins playing and the waveform progress indicator moves in sync.
3. **Given** audio is playing, **When** the user clicks a position on the waveform, **Then** playback seeks to that position.
4. **Given** audio is playing, **When** the user selects a different playback speed (0.5x, 0.75x, 1x, 1.25x, 1.5x, 2x), **Then** playback speed changes immediately without stopping.
5. **Given** a job is still processing (not completed), **When** the user views the job page, **Then** no audio player is shown (only progress indicators).

---

### User Story 2 — Guided Empty State and Onboarding (Priority: P2)

A first-time user visits Voxscribe and sees an upload form but has no context on what the tool does, what to expect, or how the process works. With this change, the empty state provides clear guidance, a sample audio demo, and contextual hints that help the user understand the full flow before committing their own file.

**Why this priority**: First impressions determine adoption. NNGroup research shows that guided empty states with starter content help users learn primary features. Currently, the empty state says "No transcriptions yet" with no further guidance.

**Independent Test**: Visit Voxscribe with no prior history → see illustrated empty state with description → click "Try with sample audio" → watch the full transcription flow complete with a 15-second sample → understand what the tool produces.

**Acceptance Scenarios**:

1. **Given** a first-time user visits the upload page with no job history, **When** the page loads, **Then** the empty state shows an illustration, a description of what Voxscribe does, and a "Try with sample audio" button.
2. **Given** the user clicks "Try with sample audio", **When** the system processes the sample, **Then** a short transcription job completes and the user is redirected to the result page to see the full output.
3. **Given** a first-time user visits the upload page, **When** the page loads, **Then** a dismissible hint banner appears: "You can also paste Instagram Reel URLs to transcribe video audio."
4. **Given** the user dismisses the hint, **When** they return to the page, **Then** the hint does not appear again (stored in localStorage).
5. **Given** a user is viewing a job in progress, **When** they see a processing stage (DOWNLOADING, CONVERTING, TRANSCRIBING), **Then** a brief explanation is displayed next to the stage name (e.g., "Optimizing audio for transcription...").

---

### User Story 3 — Accessibility and Keyboard Navigation (Priority: P3)

A user who relies on keyboard navigation or a screen reader cannot fully interact with Voxscribe. The drop zone is not keyboard-accessible, SSE progress updates are not announced, and interactive elements lack ARIA attributes. With this change, the interface meets WCAG AA standards.

**Why this priority**: Accessibility is a legal and ethical requirement. The current gaps prevent keyboard and screen reader users from using the core functionality (uploading files, monitoring progress, reading results).

**Independent Test**: Navigate the entire upload → transcription → result flow using only the keyboard (Tab, Enter, Space) with a screen reader. Verify all interactive elements are reachable, labeled, and status changes are announced.

**Acceptance Scenarios**:

1. **Given** a keyboard user is on the upload page, **When** they Tab to the drop zone and press Enter or Space, **Then** the file browser opens.
2. **Given** a screen reader user is monitoring a job, **When** the job status changes (e.g., CONVERTING → TRANSCRIBING), **Then** the screen reader announces the new status.
3. **Given** a user clicks "Copy to Clipboard", **When** the copy succeeds, **Then** a screen reader announces "Copied to clipboard".
4. **Given** a user expands the transcription text, **When** the toggle is activated, **Then** the `aria-expanded` attribute updates and the screen reader announces the state change.

---

### User Story 4 — Multiple Export Formats (Priority: P4)

A user has a completed transcription and needs it in subtitle format (SRT/VTT) for video editing, not just plain text. Currently, only TXT download is available. With this change, users can download in TXT, SRT, and VTT formats.

**Why this priority**: Subtitle formats (SRT, VTT) serve a distinct and common use case (adding captions to video). This differentiates Voxscribe from basic transcription tools and serves content creators who work with Instagram reels.

**Independent Test**: Complete a transcription → click the download dropdown → select SRT → file downloads with timestamped subtitle blocks.

**Acceptance Scenarios**:

1. **Given** a completed transcription, **When** the user clicks the download area, **Then** they see format options: TXT, SRT, VTT.
2. **Given** the user selects SRT format, **When** the download completes, **Then** the file contains properly formatted SRT blocks with sequential numbering and timestamps.
3. **Given** the user selects VTT format, **When** the download completes, **Then** the file contains valid WebVTT with "WEBVTT" header and timestamped cues.

---

### User Story 5 — Upload Polish and Bug Fixes (Priority: P5)

Small but impactful improvements to the upload experience: fix the M4A client-side validation bug, add progressive disclosure for advanced options, improve error messages, and add a cancel button during upload.

**Why this priority**: These are polish items that individually are small but collectively make the experience feel professional. The M4A bug specifically causes user confusion.

**Independent Test**: Upload an M4A file → it is accepted (bug fix). Upload a file → see cancel button during upload. See advanced options collapsed by default.

**Acceptance Scenarios**:

1. **Given** a user selects an M4A file, **When** client-side validation runs, **Then** the file is accepted (not rejected).
2. **Given** a file is uploading, **When** the user clicks Cancel, **Then** the upload is aborted and the form resets.
3. **Given** a user views the upload form, **When** the page loads, **Then** the language selector is hidden under an "Options" toggle (default: pt-BR applied automatically).
4. **Given** an upload fails due to a server error, **When** the error is displayed, **Then** the message includes specific guidance (e.g., "The transcription service is temporarily unavailable. Please try again in a few minutes.").

---

### Edge Cases

- What happens when the audio file has no speech (silence or music only)? The transcription completes with empty or minimal text — a message should inform the user: "No speech detected in this audio."
- What happens when wavesurfer.js fails to load (CDN down)? The result page should degrade gracefully — show a basic HTML5 `<audio>` element instead.
- What happens when the sample audio demo fails? Show an error message and still allow normal file upload.
- What happens on very long transcriptions (10,000+ words)? The result text should paginate or virtualize to avoid DOM performance issues.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display an audio player with waveform visualization on completed job pages.
- **FR-002**: System MUST support playback speed control (0.5x, 0.75x, 1x, 1.25x, 1.5x, 2x).
- **FR-003**: System MUST support click-to-seek on the waveform to jump to a specific audio position.
- **FR-004**: System MUST serve the original audio file via a new API endpoint for playback.
- **FR-005**: System MUST display a guided empty state with illustration and "Try with sample audio" button when no jobs exist.
- **FR-006**: System MUST provide a pre-loaded sample audio file for the demo flow.
- **FR-007**: System MUST show a dismissible first-visit hint banner about URL support.
- **FR-008**: System MUST display brief explanations next to each processing stage name.
- **FR-009**: System MUST meet WCAG AA for all interactive elements (drop zone, search, toggles, progress).
- **FR-010**: System MUST announce status changes to screen readers via aria-live regions.
- **FR-011**: System MUST offer download in TXT, SRT, and VTT formats.
- **FR-012**: System MUST generate valid SRT and VTT files with timestamps from the transcription.
- **FR-013**: System MUST accept M4A files in client-side validation (fix bug).
- **FR-014**: System MUST show a cancel button during file upload.
- **FR-015**: System MUST use progressive disclosure for language and engine options.

### Key Entities

- **Audio Playback Endpoint**: A new API endpoint that serves the original (or converted) audio file for in-browser playback. Must set appropriate Content-Type and support Range requests for seeking.
- **Sample Audio**: A short (15-second) pre-loaded audio file bundled with the application for the demo flow. Language: pt-BR.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can play audio and verify transcription accuracy without leaving the Voxscribe interface.
- **SC-002**: First-time users can complete a sample transcription within 60 seconds of landing on the page.
- **SC-003**: All interactive elements are keyboard-navigable and pass WCAG AA automated checks.
- **SC-004**: Users can download transcriptions in at least 3 formats (TXT, SRT, VTT).
- **SC-005**: The M4A upload bug is fixed — M4A files are accepted client-side and server-side consistently.
- **SC-006**: 90% of first-time users can complete a transcription without external help or documentation.

## Assumptions

- **wavesurfer.js via CDN**: The audio waveform will use wavesurfer.js loaded from a CDN (same pattern as HTMX). No build tooling required.
- **No word-level timestamps yet**: The initial audio player does not require synced text highlighting (future enhancement). Click-to-seek works on the waveform only.
- **Sample audio bundled**: A 15-second pt-BR audio clip is included in the app's static files. No external download required.
- **SRT/VTT generation is approximate**: Without word-level timestamps, subtitle files will use paragraph-level timestamps derived from chunking boundaries or estimated from text length.
- **Existing API patterns**: New endpoints follow the existing FastAPI + Pydantic schema pattern. No new frameworks introduced.
- **Mobile audio playback**: HTML5 audio and wavesurfer.js work on mobile browsers. No native app required.
