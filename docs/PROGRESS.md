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

## 2026-07-09 SEAST — Slow Builder (status GitHub card)

- Task: added a GitHub repository card to the status dashboard (`apps/status/src/main.tsx` + `styles.css`) linking to `https://github.com/irazawa/Library-Yui`, with hover state styling; updated the dashboard footer note to the next milestone focus.
- Verification: `cd apps/status && npm run build` — built successfully (tsc + vite), 15 modules transformed.
- Next small step: all slow-tasks queue items checked — generate next tiny task batch.

## 2026-07-09 SEAST — Slow Builder (plan refresh)

- Task: all original slow-tasks were complete; generated the next batch of 8 tiny tasks for MVP 1 (Audio Downloads) via Gemini 3.5 Flash and merged into `docs/plans/slow-tasks.md`.
- Verification: docs-only plan update — `git diff --check` (clean).
- Next small step: `POST /jobs` endpoint to accept a YouTube URL and initialize a pending download job.

## 2026-07-10 — Slow Builder (POST /jobs endpoint + tests)

- Task: added `POST /jobs` API endpoint (`apps/api/app/routes/jobs.py`) accepting a YouTube URL via `JobCreateRequest`, initializing a pending download job with a UUID, and returning 201 with `{id, url, status}`. Backed by an in-memory job store (`apps/api/app/jobs.py`). Registered router in `main.py`. Added `tests/test_jobs.py` covering 201 response, job ID generation, pending status, and stored state isolation.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest -q` — 8 passed (full suite).
- Next small step: implement `GET /jobs/{id}` returning the status of a specific job.

## 2026-07-10 SEAST — Slow Builder

- Task: implemented `GET /jobs/{id}` in `apps/api/app/routes/jobs.py` returning job status (404 with "Job not found" for unknown ids) plus two new tests in `tests/test_jobs.py`.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_jobs.py -q` — 5 passed.
- Next small step: enable and wire the URL input form in the main web app (port 5174) to call `POST /jobs` on submit and show the resulting job ID.

## 2026-07-10 15:08 SEAST — Slow Builder

- Task: enabled and wired the URL input form in the main web app (`apps/web/src/main.tsx`) to call `POST /jobs` on submit; shows the created job ID (pending) or an error note, with submitting state and new `.job-note` styles.
- Verification: `cd apps/web && npm run build` — built successfully (tsc + vite), 15 modules transformed.
- Next small step: add a polling hook in the main web app that periodically calls `GET /jobs/{id}` and shows active job status.

## 2026-07-10 SEAST — Slow Builder (web job polling hook)

- Task: added a `useJobStatus` polling hook in the main web app (`apps/web/src/main.tsx`) that calls `GET /jobs/{id}` every 2 seconds once a job id exists, auto-stops on terminal statuses (completed/failed), and renders the live status in the job note with error handling; added matching `.job-status` / `.job-status-error` styles.
- Verification: `cd apps/web && npm run build` — built successfully (tsc + vite), 15 modules transformed.
- Next small step: add `GET /library/audio` returning a JSON list of MP3 files in `library/audio`.

## 2026-07-11 SEAST — Slow Builder (library audio list endpoint)

- Task: added `GET /library/audio` endpoint (`apps/api/app/routes/library.py`) returning a JSON list of MP3 file names in `library/audio` via `AudioListResponse`/`AudioItem`; filters to `.mp3` only, sorted, and returns `{"items": []}` when the directory is missing. Added two tests in `tests/test_library.py` (mp3 filtering + empty/missing dir).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_library.py -q` — 4 passed.
- Next small step: wire the main web app library audio card to `GET /library/audio` so it lists actual audio items.

## 2026-07-11 SEAST — Slow Builder (web audio list wired)

- Task: wired the main web app Audio card to `GET /library/audio` (`apps/web/src/main.tsx` + `styles.css`) — added a `useLibraryAudio` hook that fetches MP3 items once on mount and renders them as a styled list inside the Audio card, with loading and empty fallback states.
- Verification: `cd apps/web && npm run build` — built successfully (tsc + vite), 15 modules transformed.
- Next small step: update `docs/API.md` documenting `/jobs` and `/jobs/{id}` endpoints.

## 2026-07-11 SEAST — Slow Builder (API docs + plan refresh)

- Task: updated `docs/API.md` documenting `GET /library/summary`, `GET /library/audio`, `POST /jobs` (request body, 201 response, job statuses table), and `GET /jobs/{id}` (200/404 responses, path params). All four new endpoint sections include field tables and curl examples. Also generated the next batch of 8 tiny tasks (fallback — `agy`/Gemini auth failed) targeting MVP 1 completion and the downloader port.
- Verification: docs-only task — `git diff --check` clean (exit 0).
- Next small step: add YouTube URL validation in `POST /jobs` rejecting non-YouTube URLs.

## 2026-07-11 SEAST — Slow Builder (YouTube URL validation)

- Task: added YouTube URL validation in `POST /jobs` (`apps/api/app/routes/jobs.py`) via `_is_youtube_url()` helper — accepts `youtube.com`, `www.youtube.com`, `m.youtube.com`, `music.youtube.com`, and `youtu.be` hosts; rejects all other URLs with HTTP 422 ("Only YouTube URLs are accepted"). Added 3 new tests in `tests/test_jobs.py` (reject non-YouTube example.com, accept youtu.be short URL, accept music.youtube.com).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_jobs.py -q` — 8 passed.
- Next small step: add `POST /jobs/{id}/start` stub endpoint that transitions a job from `pending` to `downloading`.

## 2026-07-11 SEAST — Slow Builder (jobs/{id}/start stub)

- Task: added `POST /jobs/{id}/start` stub endpoint (`apps/api/app/routes/jobs.py`) that transitions a job from `pending` to `downloading` (no real download yet). Idempotent — re-calling on an already-downloading job leaves it untouched. Unknown ids return 404. Added `update_job_status()` helper to `app/jobs.py`. Added 3 tests in `tests/test_jobs.py` (transition pending→downloading, idempotency, unknown id 404).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_jobs.py -q` — 11 passed.
- Next small step: add `POST /jobs/{id}/complete` stub endpoint that transitions a job to `completed`.

## 2026-07-12 SEAST — Slow Builder (jobs/{id}/complete stub)

- Task: added `POST /jobs/{id}/complete` stub endpoint (`apps/api/app/routes/jobs.py`) that transitions a job from `pending`/`downloading` to `completed` (no file produced yet). Idempotent — re-calling on an already-completed job leaves it untouched; a `failed` job is also left untouched. Unknown ids return 404. Added 3 tests in `tests/test_jobs.py` (transition downloading→completed, idempotency, unknown id 404).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_jobs.py -q` — 14 passed.
- Next small step: add a job lifecycle test suite covering pending → downloading → completed transitions.

## 2026-07-12 09:56 SEAST — Slow Builder (job lifecycle test suite)

- Task: added `test_job_lifecycle_pending_to_downloading_to_completed` to `apps/api/tests/test_jobs.py` — a single happy-path sequence covering the full lifecycle of one job: `pending` (create) → `downloading` (POST `/jobs/{id}/start`) → `completed` (POST `/jobs/{id}/complete`), with GET status assertions between transitions to document the lifecycle contract in one place.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_jobs.py -q` — 15 passed.
- Next small step: add a `GET /jobs` list endpoint returning all jobs (id, url, status) from the in-memory store.

## 2026-07-12 SEAST — Slow Builder (GET /jobs list endpoint)

- Task: added `GET /jobs` list endpoint (`apps/api/app/routes/jobs.py`) returning all jobs (id, url, status) from the in-memory store as `{"items": [...]}` in creation order. Added `list_jobs()` helper to `app/jobs.py` and a `JobListResponse` model. Registered the collection route before `/jobs/{job_id}` to avoid path ambiguity. Added 2 tests in `tests/test_jobs.py` (empty list returns `{"items": []}`; multiple created jobs returned in insertion order).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_jobs.py -q` — 17 passed.
- Next small step: add a status dashboard card that polls `GET /jobs` and shows a live count of active/recent jobs.

## 2026-07-12 SEAST — Slow Builder (status dashboard jobs card)

- Task: added a Jobs card to the status dashboard (`apps/status/src/main.tsx` + `styles.css`) that polls `GET /jobs` every 5 seconds via a `useJobs` hook, and renders a live count breakdown (pending / downloading / completed / failed) plus a total + active summary. Includes error handling when the API is unreachable and color-coded status dots. Also updated the dashboard footer to reflect the next milestone step.
- Verification: `cd apps/status && npm run build` — built successfully (tsc + vite), 15 modules transformed.
- Next small step: port the core MP3 download logic from `C:/games/music/Downloader.py` into a `app/downloader.py` module behind a feature flag (no wiring yet).

## 2026-07-13 SEAST — Slow Builder (downloader module + feature flag)

- Task: created `apps/api/app/downloader.py` porting the core MP3 download logic from `C:/games/music/Downloader.py` — `build_mp3_command()` builds the yt-dlp argv using the legacy conventions (best-audio `ba/b`, `-x`, `--audio-format mp3`, `--audio-quality 3`, `--no-playlist`, `--ignore-errors`, `-N 8`, output template `<dir>/%(title)s.%(ext)s`). Real downloads are gated behind the `LIBRARY_YUI_DOWNLOADS_ENABLED` env flag (disabled by default); `download_mp3()` raises `RuntimeError` unless the flag is set. Module is self-contained and not wired into the job flow yet. Added `tests/test_downloader.py` (14 tests covering flag on/off, command conventions, default output dir, disabled-raises, and enabled-invokes-subprocess via monkeypatched `subprocess.run`).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_downloader.py -q` — 16 passed.
- Next small step: wire the real downloader into the `/jobs` flow so a created job actually downloads an MP3 into `library/audio/` (flag-gated).

## 2026-07-13 SEAST — Slow Builder (downloader wired to jobs)

- Task: wired the real downloader module into the `/jobs` flow so that a started job actually downloads an MP3 into `library/audio/` (when `LIBRARY_YUI_DOWNLOADS_ENABLED` is set to `1`). When disabled, `/jobs/{job_id}/start` falls back to stub behavior.
- Verification: added 4 new unit and integration tests in `tests/test_jobs.py` covering successful download completion, download failures, exception/error handling, and disabled flag check; ran `$env:PYTHONPATH=""; $env:PYTHONNOUSERSITE="1"; .venv\Scripts\python -m pytest` with 43/43 tests passing.
- Next small step: commit the completed MVP 1 audio downloader, then generate the plan for MVP 2 (Uploads) and add the first task to the slow-tasks queue.

## 2026-07-13 SEAST — Slow Builder (SQLite database init + metadata table)

- Task: created `apps/api/app/database.py` setting up SQLite database initialization for `apps/api/data/library.db` (first MVP 2 / Uploads task). `init_db()` lazily creates the `metadata` table (id, filename, path, size, content_type, uploaded_at) if missing and is idempotent. Also added `get_connection()`, `insert_metadata()`, and `list_metadata()` helpers plus `DEFAULT_DB_PATH`/`DATA_DIR` constants, all overridable per-call so tests can target a tmp dir. Added `tests/test_database.py` (11 tests: file creation, table/columns, idempotency, parent dir creation, insert returns id, field persistence, newest-first ordering, empty list, nullable content_type).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest -q` — 53 passed (full suite, 10 new tests). No `.db` files staged (gitignore covers `apps/api/data/*.db`; tests use tmp_path).
- Next small step: add unit/integration tests for SQLite database initialization and basic CRUD operations on metadata (largely covered, but can be expanded for edge cases).

## 2026-07-13 SEAST — Slow Builder (database CRUD edge-case tests)

- Task: expanded `apps/api/tests/test_database.py` with 6 new edge-case tests covering re-init data preservation (app restart simulation), plain-dict return type guarantee, strictly-increasing row ids, zero-size files, unicode filenames/paths, and `get_connection` parent-dir creation without `init_db`.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest -q` — 59 passed (6 new). `tests/test_health.py` — 1 passed.
- Next small step: add `POST /library/upload` API endpoint accepting multipart file uploads and saving to `library/uploads/`.

## 2026-07-13 SEAST — Slow Builder (POST /library/upload endpoint)

- Task: added `POST /library/upload` API endpoint (`apps/api/app/routes/library.py`) accepting a multipart file upload (`UploadFile`), streaming it to `library/uploads/` in 64 KiB chunks, and recording a metadata row in the SQLite database (filename, path, size, content_type, uploaded_at). Enforces a 50 MiB size cap (HTTP 413) with partial-file cleanup on any error. Added `python-multipart==0.0.20` to `requirements.txt` (FastAPI dependency for multipart parsing). Added `tests/test_upload.py` (6 integration tests: successful upload + 201 + filesystem write + db row, metadata persistence, missing file field 422, filename with dots, empty file allowed, multiple uploads unique ids).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest -q` — 65 passed (full suite, 6 new). `tests/test_health.py` — 1 passed.
- Next small step: record upload metadata (filename, path, size, content type, uploaded_at) in the SQLite database upon upload (already partially done — next task can refine/extend).

## 2026-07-13 SEAST — Slow Builder (upload metadata reliability)

- Task: hardened the "record upload metadata" path in `POST /library/upload` (`apps/api/app/routes/library.py`). The metadata insert is now wrapped so that if `insert_metadata` raises, the just-written upload file is removed (no orphan on disk) and the error is logged + re-raised. Added 2 tests in `tests/test_upload.py`: (1) `uploaded_at` is persisted as a parseable, timezone-aware ISO-8601 timestamp in the DB; (2) orphan-cleanup on simulated metadata-insert failure (file removed, no row recorded).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_upload.py -q` — 9 passed. Full suite `pytest -q` — 67 passed (2 new).
- Next small step: add integration tests for `POST /library/upload` verifying filesystem write and database insert (can expand on size-cap/rejection paths).
