# Feature Specification: Modern Audio Transcription Web UI

**Feature Branch**: `001-modern-audio-webui`
**Created**: 2026-02-20
**Status**: Draft
**Input**: User description: "Modernize audio transcription with web UI, hexagonal architecture, and Dokku deployment"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload and Transcribe Audio via Web Browser (Priority: P1)

A user visits the web interface, uploads an audio file (MP3, WAV, FLAC, or OGG), and receives a Brazilian Portuguese (pt-BR) transcription. The user sees real-time progress as the audio is converted and transcribed. When complete, the transcribed text is displayed on screen and can be copied to clipboard or downloaded as a text file.

**Why this priority**: This is the core value proposition. Without upload-and-transcribe, there is no product. It replaces the current CLI-only workflow with an accessible web interface.

**Independent Test**: Upload a 2-minute MP3 file in pt-BR via the browser, observe progress updates, and verify the transcription appears and can be downloaded as TXT.

**Acceptance Scenarios**:

1. **Given** the user is on the upload page, **When** they drag-and-drop a 5MB MP3 file onto the upload zone, **Then** the file uploads with a visible progress indicator and a transcription job starts automatically.
2. **Given** a transcription job is processing, **When** the user views the processing page, **Then** they see status updates (e.g., "Converting audio...", "Transcribing...") and a progress indicator.
3. **Given** the transcription is complete, **When** the user views the results page, **Then** the transcribed text is displayed, and "Copy to clipboard" and "Download as TXT" buttons are available and functional.
4. **Given** the user uploads a file in an unsupported format (e.g., .exe), **When** they attempt to submit, **Then** the system rejects the file immediately with a clear error message listing accepted formats.

---

### User Story 2 - Swap Transcription Engine Without Code Changes (Priority: P2)

An administrator or developer can switch between transcription engines (e.g., a local self-hosted engine vs. a cloud-based API) by changing configuration, without modifying application code. The system architecture uses ports and adapters (hexagonal) so that the transcription engine is an interchangeable adapter behind a defined interface.

**Why this priority**: The current system is tightly coupled to a single transcription provider (Google's free, rate-limited, undocumented API). Decoupling the engine via a port/adapter interface is essential for reliability, accuracy improvements, and cost management. It also enables offline operation.

**Independent Test**: Deploy the application with one transcription engine configured, transcribe a file, then switch to a different engine via configuration and transcribe the same file -- both produce valid transcriptions without code changes.

**Acceptance Scenarios**:

1. **Given** the system is configured to use a cloud transcription provider, **When** a file is transcribed, **Then** the transcription is produced by the cloud provider and the result includes provider metadata.
2. **Given** the system is configured to use a local/self-hosted transcription engine, **When** a file is transcribed, **Then** the transcription runs entirely offline without any external API calls.
3. **Given** the administrator changes the transcription engine setting, **When** the system processes the next file, **Then** it uses the newly configured engine with no application restart required beyond a configuration reload.

---

### User Story 3 - Deploy to Dokku Server via Git Push (Priority: P3)

A developer deploys the full application (web UI and background transcription worker) to the Dokku server on ProxMox.Dokku via SSH and git push. The deployment includes SSL, persistent storage for uploaded audio files, and a background worker for processing transcription jobs. Uploaded files and transcription results survive container redeployments.

**Why this priority**: Deployment is necessary for the application to be usable beyond the developer's local machine, but the application must work locally first (P1 and P2). Dokku deployment enables production access with minimal infrastructure overhead.

**Independent Test**: Push the application to Dokku via `git push dokku main`, verify the web UI is accessible over HTTPS, upload a file, and confirm the transcription completes. Redeploy and verify previously uploaded files and results are still accessible.

**Acceptance Scenarios**:

1. **Given** the application code is committed, **When** the developer runs `git push dokku main`, **Then** the application builds and deploys successfully on the Dokku server.
2. **Given** the application is deployed, **When** a user accesses the configured domain over HTTPS, **Then** the web UI loads with a valid SSL certificate.
3. **Given** audio files were uploaded before a redeployment, **When** the application is redeployed, **Then** previously uploaded files and their transcription results are preserved.
4. **Given** the background worker is running, **When** a transcription job is submitted via the web UI, **Then** the worker picks up the job and processes it asynchronously.

---

### User Story 4 - Process Multiple Files Concurrently (Priority: P4)

A user uploads multiple audio files (or a single large file). The system processes them concurrently, showing individual progress for each job. Long audio files are automatically split into segments for efficient processing, and results are stitched together seamlessly.

**Why this priority**: Builds on P1 to handle real-world workloads (meetings, lectures, podcast batches). The current system already supports concurrent processing via ThreadPoolExecutor; this story extends it to the web interface.

**Independent Test**: Upload three audio files simultaneously, observe that all three show independent progress, and verify all three produce complete transcriptions.

**Acceptance Scenarios**:

1. **Given** a user uploads 3 audio files, **When** they view the processing page, **Then** each file shows its own progress indicator and status.
2. **Given** a user uploads a 60-minute audio file, **When** the system processes it, **Then** the file is split into segments, processed concurrently, and the final transcript is a seamless continuous text.

---

### Edge Cases

- What happens when an upload is interrupted mid-transfer? The system discards the partial upload and displays an error prompting the user to retry.
- What happens when the transcription engine is unreachable (cloud) or crashes (local)? The job is marked as failed with a descriptive error, and the user can retry the job.
- What happens when the uploaded file is empty or contains silence only? The system returns a result indicating no speech was detected, rather than an error.
- What happens when available disk space for uploads is exhausted? The system rejects new uploads with a clear "storage full" message.
- What happens when a file exceeds the maximum allowed size (500MB)? The system rejects the upload before transfer completes, with guidance on the size limit.
- What happens when the audio contains multiple languages? The system transcribes using the configured language (pt-BR by default); mixed-language accuracy depends on the engine but the system does not crash.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a web interface for uploading audio files in MP3, WAV, FLAC, and OGG formats.
- **FR-002**: System MUST convert uploaded audio to an optimal format for transcription (16 kHz mono WAV) before processing.
- **FR-003**: System MUST transcribe audio to text targeting Brazilian Portuguese (pt-BR) by default, with the language configurable per request.
- **FR-004**: System MUST display real-time progress updates to the user during transcription (upload progress, conversion status, transcription status).
- **FR-005**: System MUST allow users to copy transcription results to clipboard and download as plain text (TXT).
- **FR-006**: System MUST process transcription jobs asynchronously in a background worker, not blocking the web server.
- **FR-007**: System MUST support at least two interchangeable transcription engine adapters behind a common interface (port): one cloud-based API and one local/self-hosted engine.
- **FR-008**: System MUST validate uploaded files client-side (format and size) before transfer begins, and server-side before processing.
- **FR-009**: System MUST persist uploaded audio files and transcription results across application redeployments using persistent storage.
- **FR-010**: System MUST be deployable to a Dokku server via `git push` using a Dockerfile-based build.
- **FR-011**: System MUST support HTTPS with automated SSL certificate management in production.
- **FR-012**: System MUST enforce a maximum upload size of 500MB per file.
- **FR-013**: System MUST implement retry logic (up to 3 attempts with backoff) for transient transcription engine failures.
- **FR-014**: System MUST split audio files longer than 10 minutes into segments at silence boundaries for parallel processing, then stitch results together.
- **FR-015**: System MUST use a hexagonal (ports and adapters) architecture where domain logic has zero dependencies on web framework, transcription engine, or storage implementation.
- **FR-016**: System MUST provide a CLI entry point (in addition to the web UI) that preserves the current batch-processing workflow for backward compatibility.

### Key Entities

- **AudioFile**: Represents an uploaded audio file. Key attributes: original filename, format, size, duration, upload timestamp, storage location.
- **TranscriptionJob**: Represents a unit of work to transcribe an audio file. Key attributes: status (pending, converting, transcribing, completed, failed), progress percentage, associated AudioFile, created/updated timestamps, error message (if failed).
- **TranscriptionResult**: The output of a completed transcription. Key attributes: full text, language, engine used, processing duration, associated TranscriptionJob.
- **TranscriptionEngine (Port)**: Abstract interface for any transcription provider. Operations: transcribe audio data in a given language, return text result.

## Assumptions

- The Dokku server at ProxMox.Dokku is already set up with Dokku installed and SSH access configured. The server runs in a full VM (not LXC) for Docker compatibility.
- DNS for the application domain is already configured to point to the Dokku server.
- For the cloud transcription engine, the user will provide their own API key via environment variable configuration on Dokku.
- The system does not require user authentication for the MVP. Any visitor can upload and transcribe files. Authentication can be added in a future iteration.
- Audio files are stored on the server's local filesystem via Dokku persistent storage mounts, not on cloud object storage.
- The background job queue will use Redis, provisioned via the Dokku Redis plugin.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can upload an audio file and receive a complete transcription within 2x the audio duration (e.g., a 5-minute file transcribes in under 10 minutes).
- **SC-002**: Transcription accuracy for clear pt-BR speech reaches at least 90% word accuracy (under 10% word error rate), measured against a reference transcript.
- **SC-003**: The complete upload-to-result workflow (upload, convert, transcribe, display) is completable in under 5 clicks from the home page.
- **SC-004**: The system handles at least 3 concurrent transcription jobs without degradation or failure.
- **SC-005**: Switching transcription engines requires changing only configuration (environment variables), with zero code modifications and no redeployment beyond a configuration reload.
- **SC-006**: A fresh deployment from `git push` to a working HTTPS application takes under 10 minutes (excluding initial server setup).
- **SC-007**: Uploaded files and completed transcriptions persist across at least 3 consecutive redeployments with zero data loss.
- **SC-008**: The web interface loads and is usable on both desktop and mobile browsers without horizontal scrolling.
