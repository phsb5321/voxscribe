# Research: UX Improvements for Voxscribe

**Branch**: `004-ux-improvements` | **Date**: 2026-03-31

## Executive Summary

Voxscribe has a solid technical foundation but lacks user guidance, polish, and key interaction patterns that modern transcription tools provide. This research synthesizes findings from:
- Full codebase UI/template audit (every line of HTML, CSS, JS)
- Complete API surface and domain model analysis
- Competitor analysis (Otter.ai, Descript, Rev.com, AssemblyAI, Happy Scribe, Whishper, OpenTranscribe)
- Web research on upload UX, transcription display, onboarding, accessibility, and mobile patterns
- Test coverage and bug analysis

---

## 1. Current State Assessment

### What Works Well
- Clean hexagonal architecture with real-time SSE progress
- Dark/light theme with localStorage persistence
- Drag-and-drop file upload with multi-file support
- Tab-based mode switching (File / URL) 
- Job history with search, filtering, and auto-refresh
- Toast notification system
- Responsive layout (600px breakpoint)
- Status badges with color + text (not color-only)

### Critical UX Gaps

#### No Onboarding or Guidance
- First-time users see a drop zone with no context on what Voxscribe does
- No explanation of processing stages (DOWNLOADING → CONVERTING → TRANSCRIBING)
- No indication of expected processing time
- No sample/demo transcription to learn the flow
- Language selector unexplained (why only 3 languages?)

#### Missing Audio Playback
- **No audio player on the result page** — this is the single biggest gap vs competitors
- Users can't verify transcription accuracy against the audio
- No waveform visualization
- No click-to-seek between text and audio
- Rev.com, Happy Scribe, and OpenTranscribe all offer synced playback as a core feature

#### Weak Error Communication
- Error messages are generic ("Service unavailable", "Job failed")
- Download failures (Instagram auth, rate limits) show opaque messages
- No distinction between "job not found" and "result not yet ready" (both return 404)
- Copy-to-clipboard silently fails if API unavailable
- No guidance on recovery actions

#### Accessibility Gaps (WCAG AA)
- Drop zone has no `role="button"`, no `tabindex`, no `aria-label`
- Search input has no `<label>` element
- Expand/collapse toggle missing `aria-expanded`
- SSE updates don't use `aria-live` regions
- Theme toggle missing `aria-pressed`
- No skip-to-content link
- File input not keyboard-accessible without clicking drop zone

#### Format Bug
- UI shows "MP3, WAV, FLAC, OGG, M4A" in drop zone
- JavaScript `ALLOWED` list only includes `['.mp3', '.wav', '.flac', '.ogg']`
- M4A accepted server-side but rejected client-side — confusing for users

---

## 2. Competitor Analysis Findings

### Key Patterns from Leading Tools

| Feature | Otter.ai | Descript | Rev.com | Happy Scribe | OpenTranscribe |
|---------|---------|---------|---------|-------------|----------------|
| Auto-transcribe on upload | Yes | Yes | Yes | Yes | Yes |
| Audio player with waveform | No | Yes | Yes | Yes | Yes (wavesurfer.js) |
| Synced text highlighting | No | Yes | Yes (blue cursor) | Yes | Yes (word-level) |
| Click word to seek audio | No | Yes | Yes | Yes | Yes |
| Speaker diarization UI | Yes | Yes | Yes | Yes | Yes |
| Inline text editing | No | Yes | Yes | Yes | No |
| Multiple export formats | Yes | Yes | Yes | Yes | Yes (TXT, SRT, VTT) |
| Playback speed control | No | Yes | Yes | Yes | Yes |
| Sample/demo audio | No | No | No | No | No |
| Progressive disclosure | No | No | Yes | Yes | No |

### Actionable Takeaways

1. **Audio player is table stakes** — every serious transcription tool has one
2. **Synced highlighting** is the gold standard (Rev.com's blue cursor, Happy Scribe's word highlighting)
3. **Progressive disclosure** reduces cognitive load — hide advanced options by default
4. **Multiple export formats** (TXT, SRT, VTT) serve different use cases (subtitles, documents)
5. **Simplicity wins** — Happy Scribe praised for "users know what to do from first use"

---

## 3. Upload UX Research

### Drop Zone Improvements

**Full-viewport drag overlay**: When user drags a file over the browser window (not just the drop zone), expand to a full-screen overlay. Prevents "missed drops."

**Format pills**: Replace text listing with scannable visual badges:
```
[MP3] [WAV] [FLAC] [OGG] [M4A]  ·  Max 500 MB
```

**Instant client-side validation**: Validate type and size in JavaScript before upload. Show inline errors: "Your file is 620 MB — max is 500 MB."

### URL Input Improvements

**Auto-detect platform**: When URL is pasted, show platform icon + confirmation: "Instagram Reel detected — we'll download the audio."

**Real-time URL validation**: Green checkmark for valid URLs, specific error for invalid: "Only Instagram reel URLs are supported."

### Progress Improvements

**Two-phase progress**: Separate upload progress (deterministic %) from processing progress (SSE stages).

**Cancel button**: Allow aborting during upload via XHR abort.

**ETA display**: "Uploading... 45% — about 12 seconds remaining."

---

## 4. Result Page Research

### Audio Player Integration (Priority 1)

**wavesurfer.js** (https://wavesurfer.xyz/) is the recommended library:
- Lightweight, no framework dependency
- Renders to HTML5 Canvas
- Click-to-seek on waveform
- Supports custom colors, bar style
- Pre-generate peaks server-side for large files

Basic integration (vanilla JS, CDN):
```html
<script src="https://unpkg.com/wavesurfer.js@7"></script>
<div id="waveform"></div>
<script>
const ws = WaveSurfer.create({
  container: '#waveform',
  url: '/api/jobs/{id}/audio',
  waveColor: '#94a3b8',
  progressColor: '#0f3460',
  height: 64,
  barWidth: 2,
  barGap: 1,
});
</script>
```

**Playback speed control**: 0.5x, 0.75x, 1x, 1.25x, 1.5x, 2x — essential for review.

### Synced Text Highlighting (Priority 2, requires word timestamps)

If faster-whisper provides word-level timestamps:
- Each word rendered as a `<span>` with `data-start` and `data-end`
- `timeupdate` event highlights current word
- **Critical**: Use direct DOM manipulation, not framework state — Metaview's research shows state-based approaches cause 400ms+ latency vs <1ms with direct DOM

### Result Display Improvements

**Paragraph segmentation**: Break continuous text into paragraphs based on silence gaps. Dramatically improves readability vs one long block.

**Multiple export formats**:
- `.txt` (current, plain text)
- `.srt` (subtitles with timestamps)
- `.vtt` (WebVTT for web video)
- `.json` (structured with timestamps)

**Copy options**:
- "Copy text" (current)
- "Copy with timestamps"
- "Copy as subtitles" (SRT format)

**Summary header**: Add estimated reading time: "342 words · ~1.5 min read"

---

## 5. Onboarding Research

### Empty State Design

Replace current "No transcriptions yet" with guided empty state:
```
[Waveform illustration]
No transcriptions yet

Drop an audio file above or paste an Instagram URL to get started.
Supports MP3, WAV, FLAC, OGG, M4A — up to 500 MB.

[Try with sample audio →]
```

### Sample Audio Demo

Offer a "Try with sample audio" button that transcribes a pre-loaded 15-second clip. First-time users see the full flow without providing their own file. NNGroup research confirms that pre-built/starter content helps users learn features.

### Feature Hints

On first visit (localStorage flag), show a dismissible banner:
```
💡 Tip: You can paste Instagram Reel URLs to transcribe video audio.  [Dismiss]
```

### Processing Stage Explanations

Add tooltips or inline text explaining each stage:
- **Downloading**: "Fetching audio from the URL..."
- **Converting**: "Optimizing audio for transcription (16kHz mono WAV)..."
- **Transcribing**: "AI is converting speech to text..."
- **Completed**: "Your transcription is ready!"

### Progressive Disclosure

Hide language selector and advanced options by default. Show "Options ▾" toggle. Most users want pt-BR with the default engine — power users click to expand.

---

## 6. Accessibility Findings (WCAG AA)

### Must-Fix Issues

| Issue | Fix | Priority |
|-------|-----|----------|
| Drop zone no keyboard access | Add `role="button"`, `tabindex="0"`, keydown handler | High |
| Search input no label | Add `aria-label="Search transcriptions by filename"` | High |
| SSE updates not announced | Add `aria-live="polite"` to progress region | High |
| Expand toggle no state | Add `aria-expanded="false/true"` | High |
| Theme toggle no state | Add `aria-pressed="false/true"`, `aria-label` | Medium |
| Copy feedback not announced | Add `aria-live="polite"` to feedback span | Medium |
| No skip-to-content link | Add skip link before header | Medium |
| Focus not managed on redirect | Focus job header after upload redirect | Low |

---

## 7. Mobile UX Research

### Touch-Specific Improvements

- On touch devices, change drop zone text to "Tap to select a file" (no drag-and-drop on mobile)
- Sticky submit button at bottom of viewport
- Native share API (`navigator.share()`) for sharing transcription text
- Safe area insets for notched devices
- Larger tap targets (minimum 44px)

---

## 8. Technical Issues Found

### Bug: M4A Format Mismatch
- **UI text**: Shows M4A as supported
- **JS validation**: `ALLOWED = ['.mp3', '.wav', '.flac', '.ogg']` — no `.m4a`
- **Server**: Accepts M4A via AudioFormat enum
- **Fix**: Add `.m4a` to the JavaScript ALLOWED array

### SSE Connection Resilience
- No reconnection logic if SSE drops
- HTMX SSE extension has limited error recovery
- Should implement heartbeat or reconnect with backoff

### Health Check Gaps
- `/api/health` doesn't check database or storage
- Returns 200 even when critical dependencies are broken
- Should validate SQLite connectivity and storage writability

### Progress Granularity
- During TRANSCRIBING phase (chunked files), progress stays at 50% for entire duration
- No per-chunk progress reporting
- Long files (30+ min) leave users uncertain

---

## 9. Prioritized Recommendations

### Quick Wins (1-2 days each, high impact)
1. **Fix M4A client-side validation** — add `.m4a` to ALLOWED list
2. **Add ARIA labels** — drop zone, search, expand toggle, theme toggle
3. **Improve empty state** — illustration + guided text + action link
4. **Add processing stage descriptions** — tooltips on job page explaining each state
5. **Add `aria-live` regions** — progress updates announced to screen readers

### Medium Effort (3-5 days each)
6. **Add basic audio player** — HTML5 `<audio>` with custom controls on job page
7. **Add wavesurfer.js waveform** — visual playback with click-to-seek
8. **Add playback speed control** — 0.5x to 2x
9. **Progressive disclosure** — hide language/options behind expandable section
10. **Multiple export formats** — TXT + SRT + VTT download options
11. **First-visit feature hint** — dismissible banner about URL support
12. **Improved error messages** — specific error types with recovery guidance

### Larger Features (1-2 weeks each)
13. **Sample audio demo** — "Try with sample" button for onboarding
14. **Synced text highlighting** — word-level timestamps + audio sync
15. **Paragraph segmentation** — break text by silence gaps
16. **SSE reconnection** — automatic reconnect with exponential backoff
17. **Per-chunk transcription progress** — granular progress for long files
18. **Inline text editing** — allow correcting transcription results

---

## Sources

- [Eleken - File Upload UI Tips](https://www.eleken.co/blog-posts/file-upload-ui)
- [Uploadcare - File Uploader UX Best Practices](https://uploadcare.com/blog/file-uploader-ux-best-practices/)
- [NNGroup - Drag-and-Drop UX](https://www.nngroup.com/articles/drag-drop/)
- [NNGroup - Empty States in Complex Applications](https://www.nngroup.com/articles/empty-state-interface-design/)
- [Rev.com - Transcript Editor Guide](https://www.rev.com/blog/rev-transcript-editor-guide)
- [Metaview - Syncing Transcript with Audio](https://www.metaview.ai/resources/blog/syncing-a-transcript-with-audio-in-react)
- [wavesurfer.js](https://wavesurfer.xyz/)
- [OpenTranscribe](https://github.com/davidamacey/OpenTranscribe)
- [Whishper](https://github.com/pluja/whishper)
- [AllAccessible - ARIA Labels Guide](https://www.allaccessible.org/blog/implementing-aria-labels-for-web-accessibility)
- [AssemblyAI - In-App Playground](https://www.assemblyai.com/blog/in-app-playground)
- [oTranscribe](https://otranscribe.com/)
- [Able Player - Accessible Media](https://ableplayer.github.io/ableplayer/)
