# Quickstart: UI/UX Redesign & Transcription History

**Feature**: 001-ui-redesign

## What This Feature Does

Transforms the Voxscribe app from a basic prototype UI into a polished, branded experience with:
- Custom Voxscribe logo and favicon
- Rich transcription history with metadata, filtering, and search
- Enhanced job detail page with word count and improved typography
- Cohesive visual identity across all pages

## Files to Modify

### Backend (1 file)
- `app/adapters/inbound/web/routes.py` — Add `size_bytes`, `duration_seconds`, `format` to `/api/jobs` response

### Frontend Templates (3 files)
- `app/adapters/inbound/web/templates/base.html` — New logo SVG, favicon link, refined global styles
- `app/adapters/inbound/web/templates/upload.html` — Redesigned upload area, rich history list with filters/search
- `app/adapters/inbound/web/templates/job.html` — Enhanced result display, word count, improved progress view

### Static Assets (1 new file)
- `app/static/favicon.svg` — SVG favicon for browser tab

### App Setup (1 file)
- `app/main.py` — Mount static files directory

## Implementation Order

1. **Static files setup** — Mount `app/static/` in `main.py`, create favicon
2. **Logo & base template** — SVG logo in header, favicon link, refined global CSS
3. **API enrichment** — Add 3 fields to `/api/jobs` response in routes.py
4. **Upload page redesign** — New layout, rich history table, status filters, filename search
5. **Job page redesign** — Word count, improved typography, better progress display

## How to Verify

```bash
# Run tests
poetry run pytest tests/unit/ -v

# Start dev server
poetry run uvicorn app.main:create_app --factory --host 0.0.0.0 --port 5000

# Check API response has new fields
curl http://localhost:5000/api/jobs | python -m json.tool

# Visit pages
open http://localhost:5000/        # Upload page with history
open http://localhost:5000/jobs/{id}  # Job detail page
```

## Dependencies

- No new Python packages required
- No new system dependencies
- No database migrations
