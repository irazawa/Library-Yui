# Library-Yui

Personal media library and downloader web app, built slowly with real progress commits.

## Services

| Service | Port | Purpose |
|---|---:|---|
| API | 8787 | FastAPI backend for health, library, downloads, uploads |
| Web | 5174 | Main library UI |
| Status | 5175 | Progress dashboard |

## MVP 0

- Repository scaffold
- FastAPI health endpoint
- React/Vite main web shell
- React/Vite status dashboard shell
- Roadmap/progress docs

## Development

```bash
bash scripts/dev.sh
```

Or run services separately:

```bash
cd apps/api && python -m uvicorn main:app --reload --port 8787
cd apps/web && npm run dev -- --host 127.0.0.1 --port 5174
cd apps/status && npm run dev -- --host 127.0.0.1 --port 5175
```
