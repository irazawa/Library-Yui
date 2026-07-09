# Library-Yui Progress

## 2026-07-08 — MVP 0 Start

- Created the first implementation plan for the repository scaffold.
- Focus: make a visible, runnable shell before adding downloader logic.
- Current target: API on `8787`, main web on `5174`, status dashboard on `5175`.

## Current Status

- Phase: MVP 0 scaffold
- Active plan: `docs/plans/0001-mvp0-scaffold.md`
- Next small step: verify all three services can start locally.

## 2026-07-08 01:54 — Hourly Slow Progress

- Current focus: continue Library-Yui with small real improvements.
- Status: repository skeleton is online; next implementation remains MVP 1 audio download queue.
- Next small step: add the smallest visible API or UI improvement before the next push.

## 2026-07-08 01:55 — Hourly Slow Progress

- Current focus: continue Library-Yui with small real improvements.
- Status: repository skeleton is online; next implementation remains MVP 1 audio download queue.
- Next small step: add the smallest visible API or UI improvement before the next push.

## 2026-07-08 02:07 SEAST — Slow Builder

- Task: added `GET /version` returning app name, version, and current milestone.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py -q` passed.
- Next small step: add an API test for `/version`.

## 2026-07-08 — Slow Builder

- Task: added `tests/test_version.py` covering the `/version` endpoint response.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_version.py -q` — 2 passed.
- Next small step: show API health status card in the status dashboard.

## 2026-07-08 — Slow Builder

- Task: added API health status card in the status dashboard (`apps/status/src/main.tsx` + `styles.css`) that fetches `http://127.0.0.1:8787/health` and shows Online/Offline/Checking states.
- Verification: `cd apps/status && npm run build` — built successfully (tsc + vite), 15 modules transformed.
- Next small step: add a disabled URL input form shell to the main web app for future audio downloads.

## 2026-07-08 SEAST — Slow Builder

- Task: added an empty library section component showing Audio, Video, Uploads counts as placeholders (`apps/web/src/main.tsx` + `styles.css`) — three `count-card` placeholders set to 0, displayed above the existing cards section.
- Verification: `cd apps/web && npm run build` — built successfully (tsc + vite), 15 modules transformed.
- Next small step: add `docs/API.md` documenting `/health` and `/version`.

## 2026-07-09 — Slow Builder

- Task: added `docs/API.md` documenting `GET /health` and `GET /version` (fields, examples, base URL).
- Verification: `git diff --check` (docs-only task) — clean, no whitespace errors.
- Next small step: add backend storage path constants for audio, video, uploads, and thumbnails.

## 2026-07-09 SEAST — Slow Builder

- Task: added backend storage path constants module `apps/api/app/storage.py` (REPO_ROOT, LIBRARY_DIR, AUDIO_DIR, VIDEO_DIR, UPLOADS_DIR, THUMBNAILS_DIR, STORAGE_DIRS map, `ensure_storage_dirs()` helper) plus `tests/test_storage.py`.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_storage.py -q` — 4 passed.
- Next small step: add `GET /library/summary` returning placeholder counts from storage folders.

## 2026-07-09 SEAST — Slow Builder (library summary)

- Task: added `GET /library/summary` endpoint (`apps/api/app/routes/library.py`) returning per-type file counts (audio, video, uploads, thumbnails) from `STORAGE_DIRS`; missing folders count as 0. Registered router in `main.py` and added `tests/test_library.py`.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_library.py -q` — 2 passed.
- Next small step: show library summary placeholders on the main web app.

## 2026-07-09 SEAST — Slow Builder (web library summary wired)

- Task: wired the main web app library section to `GET /library/summary` (`apps/web/src/main.tsx`) — added a `useLibrarySummary` hook that fetches live counts and shows loading (`…`) / error (`—`) fallbacks with a status-aware subtitle.
- Verification: `cd apps/web && npm run build` — built successfully (tsc + vite), 15 modules transformed.
- Next small step: add a progress dashboard card that links to the GitHub repository.
