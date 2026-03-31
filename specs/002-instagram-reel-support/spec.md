# Feature Specification: Instagram Reel URL Transcription

**Feature Branch**: `002-instagram-reel-support`
**Created**: 2026-03-30
**Status**: Draft
**Input**: User description: "I need you to extend the features in order to support Instagram reels transcriptions from URLs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Transcribe an Instagram Reel by Pasting a URL (Priority: P1)

A user has an Instagram reel they want transcribed. Instead of manually downloading the video, extracting the audio, and uploading it, they simply paste the reel's URL into Voxscribe. The system downloads the reel's audio, processes it through the existing transcription pipeline, and delivers the text result — just like a regular file upload.

**Why this priority**: This is the core value proposition of the feature. Without this, nothing else matters. It removes the manual friction of downloading and converting Instagram content before uploading.

**Independent Test**: Can be fully tested by pasting a valid Instagram reel URL and receiving an accurate transcription. Delivers immediate value as a standalone capability.

**Acceptance Scenarios**:

1. **Given** a user is on the upload page, **When** they paste a valid Instagram reel URL (e.g., `https://www.instagram.com/reel/ABC123/`) and select a language, **Then** the system accepts the URL, begins downloading the audio, and creates a transcription job visible in the job history.
2. **Given** a user submits a valid Instagram reel URL, **When** the download and transcription complete successfully, **Then** the user can view and download the transcription result, identical in format to a file-upload transcription.
3. **Given** a user submits an Instagram reel URL, **When** the job is processing, **Then** the user sees real-time progress updates (download status, conversion, transcription) via the existing progress mechanism.
4. **Given** a user submits a URL that is not a valid Instagram reel link, **When** the system validates the input, **Then** the user receives a clear error message indicating the URL is not a recognized Instagram reel format.

---

### User Story 2 - Seamless Upload Experience for Both Files and URLs (Priority: P2)

A user visits the upload page and can choose between uploading a local audio file (existing behavior) or pasting an Instagram reel URL. The interface makes both options intuitive and does not disrupt the existing drag-and-drop file upload workflow.

**Why this priority**: A confusing or cluttered interface would hurt adoption. The URL input must feel like a natural extension of the existing upload experience, not a bolted-on afterthought.

**Independent Test**: Can be tested by verifying that both upload methods (file and URL) are accessible, clearly labeled, and work without interfering with each other.

**Acceptance Scenarios**:

1. **Given** a user is on the upload page, **When** they look at the interface, **Then** they see a clear option to paste a URL alongside the existing file upload area.
2. **Given** a user has pasted a URL into the URL input, **When** they click the submit button, **Then** the system processes the URL (not a file upload) and the file upload area remains unaffected for future use.
3. **Given** a user has selected a local file for upload, **When** they also paste a URL, **Then** the system prioritizes one input method and clearly communicates which will be used (file upload takes precedence, or the URL field is disabled while files are selected — and vice versa).

---

### User Story 3 - Graceful Handling of Download Failures (Priority: P3)

A user pastes an Instagram reel URL, but the download fails — the reel may be private, deleted, geo-restricted, or the URL may be malformed. The system communicates the failure clearly and allows the user to try again or upload a file instead.

**Why this priority**: Users will inevitably encounter URLs that cannot be processed. Clear error handling prevents confusion and builds trust in the system.

**Independent Test**: Can be tested by submitting various invalid or inaccessible URLs and verifying appropriate error messages appear without crashing the application.

**Acceptance Scenarios**:

1. **Given** a user submits a URL to a private Instagram reel, **When** the system attempts to download it, **Then** the user receives a message indicating the content is not publicly accessible.
2. **Given** a user submits a URL to a deleted or non-existent reel, **When** the system attempts to download it, **Then** the user receives a message indicating the content could not be found.
3. **Given** a user submits a URL that is a valid Instagram link but not a reel (e.g., a profile page or a photo post), **When** the system validates the URL, **Then** the user receives a message indicating only reel URLs are supported.
4. **Given** a download fails mid-way due to a network issue, **When** the failure is detected, **Then** the job is marked as failed with a descriptive error and the user can retry using the existing retry mechanism.

---

### Edge Cases

- What happens when the Instagram reel audio exceeds the maximum file size (500 MB)? The system rejects the job with a clear size error after downloading, before entering the transcription pipeline.
- What happens when the reel contains no spoken audio (e.g., music-only)? The transcription completes but returns empty or minimal text — consistent with existing behavior for silent/music-only audio files.
- What happens when the reel URL uses a shortened format (e.g., `instagram.com/reel/ABC123` without `www`)? The system accepts common URL variations.
- What happens when a user submits the same Instagram reel URL twice? The system creates a new independent transcription job each time (no deduplication), consistent with how duplicate file uploads are handled.
- What happens if Instagram changes their URL structure or blocks automated downloads? The system fails gracefully with a descriptive error rather than crashing or hanging.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept Instagram reel URLs as an alternative input method alongside file uploads.
- **FR-002**: System MUST validate that a submitted URL matches recognized Instagram reel URL patterns before attempting a download.
- **FR-003**: System MUST download the audio content from a valid, publicly accessible Instagram reel URL.
- **FR-004**: System MUST feed the downloaded audio into the existing transcription pipeline (conversion, chunking, transcription) without requiring changes to the core processing logic.
- **FR-005**: System MUST display a transcription job in the user's job history for URL-based submissions, showing the source URL or reel identifier as the job name.
- **FR-006**: System MUST enforce the same file size limit (500 MB) on downloaded audio as on uploaded files.
- **FR-007**: System MUST provide clear, user-friendly error messages for: invalid URLs, private/deleted reels, download failures, and unsupported content types.
- **FR-008**: System MUST support the same language selection options for URL-based transcriptions as for file uploads.
- **FR-009**: System MUST allow users to retry failed URL-based transcription jobs using the existing retry mechanism.
- **FR-010**: System MUST track the source URL as metadata on the transcription job for user reference.

### Key Entities

- **URL Submission**: Represents a user's request to transcribe from a URL. Contains the source URL, selected language, and maps to an AudioFile entity once the download completes. The downloaded audio becomes a standard AudioFile flowing through the existing pipeline.
- **Source Metadata**: An extension of the existing AudioFile or TranscriptionJob concept that records the origin of the audio (file upload vs. URL) and the original URL for display and troubleshooting purposes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can submit an Instagram reel URL and receive a completed transcription within the same timeframe as an equivalent-length file upload (plus download time).
- **SC-002**: 95% of valid, publicly accessible Instagram reel URLs submitted by users result in a successful transcription.
- **SC-003**: Users receive a clear, actionable error message within 30 seconds when a URL cannot be processed (invalid, private, deleted, or network failure).
- **SC-004**: The URL input workflow requires no more than 3 user actions (paste URL, select language, click submit) to initiate a transcription.
- **SC-005**: Existing file upload functionality remains fully operational with no regressions after the URL feature is added.

## Assumptions

- **Instagram reel audio is publicly downloadable**: The system targets publicly accessible reels only. Private or login-required content is out of scope.
- **Audio extraction is feasible**: Instagram reels contain an audio track that can be extracted and converted to a supported format for transcription.
- **No authentication required**: The system does not require Instagram login credentials or API keys to download public reel audio. If Instagram's structure requires authentication in the future, this would be a separate enhancement.
- **Single URL per submission**: Users submit one URL at a time. Batch URL submission is out of scope for this feature.
- **No video processing**: Only the audio track is extracted from the reel. Video content is discarded.
- **URL format stability**: Instagram's reel URL patterns (e.g., `instagram.com/reel/{id}/`, `instagram.com/reels/{id}/`) are assumed to be stable. Changes to URL structure would require a maintenance update.
