# Research: Instagram Reel URL Transcription

**Branch**: `002-instagram-reel-support` | **Date**: 2026-03-30

## R-001: Instagram Reel Audio Download Tool

**Decision**: Use `yt-dlp` as the media download library.

**Rationale**: yt-dlp is the de facto standard for downloading media from social platforms. It has built-in Instagram extractors (`InstagramIE`) that handle reel URLs, audio extraction via ffmpeg post-processing, and a clean Python API (`yt_dlp.YoutubeDL`). It already supports the URL patterns we need (`/reel/`, `/reels/`, user-scoped reel URLs). The project already requires ffmpeg as a system dependency, so the post-processing requirement is already met.

**Alternatives considered**:
- **instaloader**: Instagram-specific tool, but primarily focused on photos/stories and lacks audio extraction. Would require manual ffmpeg integration.
- **gallery-dl**: Focused on image galleries, limited video/audio support.
- **Custom HTTP scraping**: Fragile, requires reverse-engineering Instagram's API, no community maintenance.

---

## R-002: Authentication Requirements

**Decision**: Support optional cookie-based authentication via a server-side cookie file, configured through an environment variable (`INSTAGRAM_COOKIES_FILE`).

**Rationale**: Research confirms that Instagram effectively requires authentication even for public reels. The platform locks content behind login walls, blocks datacenter IPs, and returns "login required" errors for unauthenticated requests. yt-dlp's recommended approach is `--cookies` with a Netscape-format cookie file. The `--cookies-from-browser` option is impractical for server deployments (no browser installed). Making cookies optional allows the system to attempt unauthenticated downloads (which may work for some content/IPs) while providing a reliable path for authenticated access.

**Alternatives considered**:
- **Username/password login**: Less reliable, triggers 2FA, risks account lockout.
- **Cookies from browser**: Requires browser on server — not viable in Docker.
- **No authentication**: Would result in high failure rates for most deployments.
- **Instagram Graph API (official)**: Requires Facebook developer account, app review, and does not provide audio download for reels.

---

## R-003: Job State Machine Extension

**Decision**: Add a `DOWNLOADING` state to the `JobStatus` enum, inserted between `PENDING` and `CONVERTING`.

**Rationale**: Instagram reel downloads are network-bound and may take several seconds. Users need visibility into whether the system is downloading the media vs. converting or transcribing it. The existing state machine pattern (with `can_transition_to` validation) cleanly supports a new state. The download should happen in the background worker (not synchronously at submit time) to avoid blocking the HTTP response.

**State transitions**:
```
PENDING → DOWNLOADING → CONVERTING → TRANSCRIBING → COMPLETED
    ↓         ↓            ↓             ↓
  FAILED    FAILED       FAILED        FAILED
```

For file uploads, the flow skips `DOWNLOADING` (PENDING → CONVERTING as today).

**Alternatives considered**:
- **Download synchronously at submit time**: Blocks the HTTP request, bad UX for slow downloads.
- **Reuse CONVERTING state for download**: Obscures what the system is actually doing; poor observability.
- **No new state**: Would leave users uninformed during the download phase.

---

## R-004: Architectural Integration Pattern

**Decision**: Create a new port (`MediaDownloaderPort`) with a yt-dlp adapter, following the existing hexagonal pattern. The download step is added to `ProcessTranscriptionUseCase` for URL-sourced jobs.

**Rationale**: The project uses hexagonal architecture with 5 existing ports. Adding a 6th port for media downloading follows the same pattern without introducing new architectural layers (satisfying Constitution Principle I). The download is a new outbound adapter concern — exactly what ports are for. The `ProcessTranscriptionUseCase` already orchestrates the PENDING → CONVERTING → TRANSCRIBING → COMPLETED flow; inserting a DOWNLOADING step for URL-sourced jobs is a natural extension.

**Alternatives considered**:
- **Separate "SubmitFromURL" use case**: Over-engineers the solution; the only difference is an initial download step.
- **Download in the web route handler**: Violates hexagonal architecture (business logic in adapter layer).
- **Inline yt-dlp calls without a port**: Violates dependency inversion and makes testing harder.

---

## R-005: URL Validation Pattern

**Decision**: Validate Instagram reel URLs using a regex pattern matching yt-dlp's `InstagramIE._VALID_URL`, applied at submit time (before enqueueing the job).

**Rationale**: yt-dlp recognizes these Instagram reel URL patterns:
- `https://www.instagram.com/reel/{CODE}/`
- `https://www.instagram.com/reels/{CODE}/`
- `https://www.instagram.com/{USERNAME}/reel/{CODE}/`
- With or without `www.`, with or without trailing slash

Validating before enqueueing provides immediate user feedback and avoids wasting worker resources on obviously invalid URLs.

**Regex pattern**:
```
^https?://(?:www\.)?instagram\.com(?:/[^/?#]+)?/reels?/[A-Za-z0-9_-]+/?(?:\?.*)?$
```

---

## R-006: Audio Format and Storage

**Decision**: Download audio as MP3 format via yt-dlp's ffmpeg post-processor. Store the downloaded file using the existing `AudioStoragePort` with a generated filename based on the reel's title/ID.

**Rationale**: MP3 is already a supported `AudioFormat` in the system. yt-dlp can extract audio and convert to MP3 in one step using ffmpeg (already a system dependency). The existing storage adapter (LocalFileStorage) handles file storage with UUID prefixing, so the downloaded file integrates seamlessly.

**Alternatives considered**:
- **Download as WAV**: Larger file size, no benefit since the converter already converts to WAV.
- **Download as M4A/AAC**: Supported format but less universally compatible.
- **Keep original video format**: Wastes storage on video data that will be discarded.

---

## R-007: Risk Assessment and Mitigations

**Key risks identified**:

| Risk | Severity | Mitigation |
|------|----------|------------|
| Instagram blocks server IP | High | Cookie auth support, clear error messages, retry mechanism |
| Instagram API changes break yt-dlp | Medium | Pin yt-dlp version, document update procedure, graceful failure |
| Rate limiting from Instagram | Medium | Sequential downloads only (no parallelism), user-initiated only |
| Cookie expiration | Medium | Log clear warning when auth fails, document cookie refresh process |
| Large video files consume disk during download | Low | yt-dlp downloads to temp dir, cleanup on completion/failure |

---

## R-008: Docker and Dependency Impact

**Decision**: Add `yt-dlp` as a Python dependency via `uv add yt-dlp`. No new system-level dependencies needed (ffmpeg is already required).

**Rationale**: yt-dlp is a pure Python package with no compiled extensions. ffmpeg (already in Dockerfile) handles the audio extraction post-processing. The cookie file mount (if used) is a Docker volume concern, not a Dockerfile change.

**Docker considerations**:
- Cookie file: Mount via `-v /path/to/cookies.txt:/app/cookies.txt` and set `INSTAGRAM_COOKIES_FILE=/app/cookies.txt`
- No Dockerfile changes required for yt-dlp itself
- `START.SH` and `docker-compose.yml` may need environment variable documentation
