# AGENTS.md

Instructions for AI coding agents working in this repository.

## Build & Run Commands

```bash
# Install dependencies (uses uv, not pip)
uv sync

# Run web server
uv run uvicorn app.main:create_app --factory --host 0.0.0.0 --port 5000

# Run background worker (requires Redis)
uv run rq worker --url redis://localhost:6379

# Docker (web + worker + redis)
docker compose up
```

System dependencies: `ffmpeg` and `libsndfile1` must be installed at runtime.

## Test Commands

```bash
# Run all tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/unit/domain/test_transcription_job.py -v

# Run a single test class
uv run pytest tests/unit/domain/test_transcription_job.py::TestTranscriptionJobTransitions -v

# Run a single test method
uv run pytest tests/unit/domain/test_transcription_job.py::TestTranscriptionJobTransitions::test_pending_to_converting -v

# Run by test layer
uv run pytest tests/unit/ -v          # Unit tests (no I/O)
uv run pytest tests/integration/ -v   # Integration tests (real SQLite, filesystem, pydub)
uv run pytest tests/e2e/ -v           # End-to-end API tests (no Redis needed)
```

There is no linter or formatter configured. No ruff, flake8, mypy, or pylint config exists.
Async tests use `pytest-asyncio` with `asyncio_mode = "auto"` (pyproject.toml).

## Architecture Rules

Hexagonal architecture with strict dependency direction: adapters -> application -> domain.

- **Domain** (`app/domain/`) -- Zero external dependencies. Never import from `app.ports`, `app.application`, or `app.adapters`.
- **Ports** (`app/ports/`) -- ABC interfaces only. Depend on domain types.
- **Application** (`app/application/`) -- Use cases. Depend on ports and domain. Never import adapters.
- **Adapters** (`app/adapters/`) -- Implementations. May import from any layer.
- **Bootstrap** (`app/bootstrap.py`) -- Composition root. Wires adapters to ports. Singleton container.

## Code Style

### Imports

- **Absolute imports only.** Always `from app.domain.entities.audio_file import AudioFile`, never relative `from .audio_file import AudioFile`.
- **Three groups** separated by blank lines: (1) stdlib, (2) third-party, (3) local `app.*`. Alphabetical within each group.
- **`from X import Y` preferred** over bare `import X`, except for top-level stdlib modules used by namespace (`import os`, `import logging`, `import uuid`, `import json`, `import time`, `import sqlite3`).
- **Lazy imports for heavy deps.** Import `faster_whisper`, `openai`, and `redis` inside the method that uses them, not at module top level.

### Type Annotations

- **Annotate all function signatures** including `-> None` for void methods and `-> X | None` for optional returns.
- **Use `X | None`**, not `Optional[X]`. Do not import `Optional` from typing.
- **Annotate all dataclass fields.** Use `field(default_factory=...)` for mutable defaults.
- No `# type: ignore` comments exist in the codebase; avoid adding them.

### Naming

| Element              | Convention                  | Example                           |
|----------------------|-----------------------------|-----------------------------------|
| Files/modules        | `snake_case`                | `transcription_job.py`            |
| Classes              | `PascalCase`                | `TranscriptionJob`                |
| Port interfaces      | Suffix `Port`               | `AudioStoragePort`                |
| Adapter classes      | Descriptive, no suffix      | `SQLiteJobRepository`             |
| Use cases            | Suffix `UseCase`            | `SubmitTranscriptionUseCase`      |
| DTOs                 | Suffix `Request`/`Response` | `SubmitTranscriptionRequest`      |
| Pydantic schemas     | Suffix `Schema`/`Response`  | `AudioFileSchema`                 |
| Functions/methods    | `snake_case`                | `validate_audio_file`             |
| Private members      | Single underscore prefix    | `_validate()`, `self._storage`    |
| Constants            | `UPPER_SNAKE_CASE`          | `MAX_FILE_SIZE_BYTES`             |
| Private module-level | Underscore prefix           | `_VALID_TRANSITIONS`              |
| Test files           | `test_` prefix              | `test_audio_file.py`              |

### Error Handling

- All domain exceptions inherit from `DomainError` (defined in `app/domain/exceptions.py`).
- Raise domain exceptions from domain logic; catch and wrap infrastructure exceptions in adapters using `raise DomainError(...) from exc`.
- In engine adapters, re-raise `TranscriptionError` directly; catch all other `Exception` and wrap into `TranscriptionError`.
- Map domain exceptions to HTTP status codes in route handlers (e.g., `InvalidAudioFormatError` -> 400, `FileTooLargeError` -> 413).

### String Formatting

- **f-strings** for all string interpolation.
- **%-formatting** only in `logging` calls (deferred evaluation): `logger.error("Failed %s: %s", path, e)`.
- Never use `str.format()`.
- Use underscore separators for large numbers: `524_288_000`.

### Async

- All FastAPI route handlers are `async def`.
- Domain layer, use cases, ports, and adapter implementations are synchronous.
- Background processing (RQ worker) is synchronous.

### Classes & Patterns

- **Entities**: Mutable `@dataclass`. UUIDs default to `uuid4()`, timestamps to `datetime.now(timezone.utc)`.
- **DTOs**: `@dataclass(frozen=True)`. Pure data, no methods.
- **Ports**: Inherit `ABC`, every method is `@abstractmethod` with a docstring.
- **Use cases**: Class with `__init__` accepting ports, `execute()` method taking request DTO, returning response DTO.
- **`__init__.py` files**: Present in every package but always empty. No re-exports, no `__all__`.
- **No DI framework.** Dependency wiring happens only in `bootstrap.py`.

### Logging

- `logger = logging.getLogger(__name__)` at module level.
- Used in application and adapter layers only, never in domain.

### Docstrings

- Required on: port interface methods, domain entity methods with non-obvious behavior, domain service functions, module-level in adapter files.
- Not required on: private helpers, tests, constructors with obvious signatures.
- Format: plain prose, no structured tags (no `:param:`, no Google/NumPy style).

## Test Conventions

- Tests grouped into classes by behavior: `TestTranscriptionJobCreation`, `TestUploadEndpoint`, etc.
- Test class docstrings: brief one-line description.
- Method names: `test_<specific_behavior>` -- be descriptive.
- Fixtures defined locally in each test file (no shared `conftest.py`).
- Use `unittest.mock.MagicMock` for mocking ports.
- Use `pytest.raises(ExceptionType, match="...")` for exception assertions.
- Factory helpers prefixed `_make_` for test entity construction.
- E2E tests use `httpx.AsyncClient` with `ASGITransport`, `NoOpQueue` replaces RQ.
- Autouse fixtures for setup/teardown are prefixed with underscore: `_clean_container`.

### None and Boolean Checks

- Always `is None` / `is not None`, never `== None`.
- `if not X:` for emptiness; `if X is None:` for explicit None checks.
- In test assertions: `assert job.is_terminal is True`.
