<!--
Sync Impact Report
- Version change: N/A → 1.0.0 (initial ratification)
- Added principles:
  - I. Simplicity
  - II. Reliability
  - III. Containerized Deployment
  - IV. Concurrent Processing
  - V. Dependency Hygiene
- Added sections:
  - Runtime Constraints
  - Development Workflow
  - Governance
- Removed sections: none
- Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ no changes needed (Constitution Check section is generic)
  - .specify/templates/spec-template.md — ✅ no changes needed
  - .specify/templates/tasks-template.md — ✅ no changes needed
- Follow-up TODOs: none
-->

# Audio Transcriber Constitution

## Core Principles

### I. Simplicity

All features MUST be implementable without introducing new architectural layers.
The application is a single-entrypoint CLI tool (`main.py`). New functionality
MUST extend the existing `AudioTranscriber` class or add peer-level functions
rather than introduce frameworks, plugin systems, or service abstractions.
Rationale: the project solves a focused problem (batch audio-to-text); complexity
beyond that scope degrades maintainability.

### II. Reliability

Every external call (network API, DNS resolution, file I/O) MUST include
retry logic or explicit error handling that produces a human-readable
diagnostic. Silent failures are prohibited — all error paths MUST log at
WARNING or ERROR level before returning a fallback value. Rationale: audio
transcription depends on external services (Google Speech API) and
heterogeneous input files; graceful degradation is non-negotiable.

### III. Containerized Deployment

The Docker image MUST remain the canonical deployment target. Changes to
system-level dependencies (e.g., ffmpeg, libportaudio2) MUST be reflected
in the Dockerfile. The `START.SH` script MUST continue to work as the
single-command entry point for end users. Local Poetry-based development
is supported but MUST NOT diverge from what the container executes.
Rationale: reproducibility across environments is essential when handling
binary audio dependencies.

### IV. Concurrent Processing

Batch file processing MUST use `concurrent.futures.ThreadPoolExecutor` for
parallelism. New processing stages MUST be compatible with concurrent
execution (no shared mutable state between file-processing tasks). Each
file MUST be processable independently. Rationale: audio transcription is
I/O-bound; concurrency provides significant throughput gains with minimal
complexity.

### V. Dependency Hygiene

All runtime imports MUST have corresponding entries in `pyproject.toml`
(Poetry) AND `requirements.txt` (Docker). Adding a new dependency requires
updating both files. System-level dependencies (apt packages) MUST be
documented in the Dockerfile. Rationale: the project currently has a
known violation (`dnspython` is imported but not declared); this principle
prevents recurrence.

## Runtime Constraints

- **Target language**: Brazilian Portuguese (pt-BR) via Google Speech API.
  Language configuration is controlled by the `LANGUAGE` constant in `main.py`.
- **Supported formats**: mp3, wav, flac, ogg. Format conversion to WAV is
  handled by pydub/ffmpeg before transcription.
- **Audio input directory**: `./DATA` (relative to working directory).
- **Python version**: 3.12+ as specified in `pyproject.toml`.

## Development Workflow

- **Package manager**: Poetry (local dev), pip via `requirements.txt`
  (Docker builds).
- **Run locally**: `poetry install && python main.py`
- **Run via Docker**: `bash START.SH`
- **No test suite exists yet**. When tests are added, they MUST be
  runnable via `pytest` and MUST NOT require network access for unit-level
  tests (mock the Google Speech API).

## Governance

This constitution governs all changes to the Audio Transcriber project.
Amendments require:

1. A description of the change and its rationale.
2. An update to `CONSTITUTION_VERSION` following semantic versioning:
   - MAJOR: principle removal or redefinition.
   - MINOR: new principle or materially expanded guidance.
   - PATCH: clarifications, wording, typo fixes.
3. `LAST_AMENDED_DATE` MUST be updated to the date of the change.
4. A review of dependent templates (plan, spec, tasks) for consistency.

All feature work SHOULD be checked against these principles during the
plan phase (see "Constitution Check" in `.specify/templates/plan-template.md`).

**Version**: 1.0.0 | **Ratified**: 2026-02-20 | **Last Amended**: 2026-02-20
