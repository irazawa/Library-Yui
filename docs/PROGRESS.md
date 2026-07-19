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

## 2026-07-14 SEAST — Slow Builder (upload size-cap + multichunk tests)

- Task: expanded `tests/test_upload.py` with 2 new integration tests covering previously-untested paths of `POST /library/upload`: (1) `test_upload_rejects_file_exceeding_size_cap` — a payload over `MAX_UPLOAD_BYTES` (50 MiB + 1 KiB) is rejected with HTTP 413 and leaves no partial file on disk and no metadata row; (2) `test_upload_writes_multichunk_file` — a payload larger than a single 64 KiB chunk is streamed across multiple writes and reconstructed byte-for-byte on disk (>160 KiB distinct-pattern payload). This completes the "verify filesystem write and database insert" task by exercising the size-cap rejection and multichunk streaming paths.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_upload.py -q` — 11 passed. Full suite `pytest -q` — 69 passed (2 new).
- Next small step: add `GET /library/uploads` API endpoint returning a list of all uploaded items from the SQLite database.

## 2026-07-14 SEAST — Slow Builder (GET /library/uploads endpoint)

- Task: added `GET /library/uploads` API endpoint (`apps/api/app/routes/library.py`) returning all uploaded items recorded in the SQLite database, newest-first, via a new `UploadListResponse` model. Returns `{"items": []}` when the database file does not exist yet (works before any uploads). Wraps `list_metadata` in a `sqlite3.Error` guard so a corrupt/unreadable db returns an empty list rather than 500-ing. Added 3 integration tests in `tests/test_upload.py` (empty when no db; two uploads returned newest-first with full metadata contract; a subsequent GET reflects a newly uploaded file).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_upload.py -q` — 14 passed. Full suite `pytest -q` — 72 passed (3 new).
- Next small step: add a file upload UI component (drag-and-drop or file selector) in the main web app to upload files.

## 2026-07-14 13:14 SEAST — Slow Builder (upload UI in main web app)

- Task: added a file-selector upload UI to the main web app (`apps/web/src/main.tsx`). The old placeholder "Upload coming soon" button is now a working "Upload a file" button backed by a hidden `<input type="file">`; selecting a file POSTs it as multipart form data to `POST /library/upload` and shows an "Uploaded: <filename>" status note (or an error note if the API is unreachable/rejects the upload). Button disables while uploading; input value is reset after each attempt so the same file can be re-selected.
- Verification: `cd apps/web && npm run build` — built successfully (tsc + vite), 15 modules transformed.
- Next small step: wire the main web app Uploads list to display uploaded files fetched from `GET /library/uploads`.

## 2026-07-14 SEAST — Slow Builder (web uploads list wired)

- Task: wired the main web app Uploads card to `GET /library/uploads` (`apps/web/src/main.tsx` + `styles.css`). Added a `useLibraryUploads(refreshKey)` hook that fetches all uploaded items once on mount and re-fetches whenever `refreshKey` changes; the hook is re-triggered automatically after each successful upload so newly uploaded files appear immediately. The new Uploads card (in the `.cards` grid) renders filename, human-readable size, content type, and a localized `uploaded_at` timestamp, with loading and empty fallback states. Added matching `.upload-item` / `.upload-name` / `.upload-meta` styles.
- Verification: `cd apps/web && npm run build` — built successfully (tsc + vite), 15 modules transformed.
- Next small step: update `docs/API.md` with descriptions and examples for `POST /library/upload` and `GET /library/uploads`.

## 2026-07-14 SEAST — Slow Builder (API docs: upload endpoints)

- Task: updated `docs/API.md` with full documentation for `POST /library/upload` (multipart `file` field, streaming write, 201 response with metadata fields, 413 size-cap with `MAX_UPLOAD_BYTES` detail, 422 missing-field, curl example) and `GET /library/uploads` (200 newest-first list, full per-item field table, empty list before any db, curl example). Both sections verified against the actual `apps/api/app/routes/library.py` implementation and `tests/test_upload.py` contracts.
- Verification: docs-only task — `git diff --check` clean (exit 0).
- Next small step: all current slow-tasks queue items are checked — generate the next tiny task batch (MVP 3 Collections or MVP 1/2 polish).

## 2026-07-15 SEAST — Slow Builder (plan refresh)

- Task: all previous slow-tasks were complete; generated the next batch of 8 tiny tasks via Gemini 3.5 Flash (`agy --model "Gemini 3.5 Flash (High)"`), targeting MVP 3 (Collections: tags/search/metadata detail) plus one MVP 4 (Video) starter. Tasks were aligned to the actual Library-Yui schema (`metadata` table in `apps/api/app/database.py`) and existing route conventions before merging into `docs/plans/slow-tasks.md`. No implementation done this run per cron rule (plan update only).
- Verification: docs-only plan update — `git diff --check` clean.
- Next small step: add a `tags` table (id, name UNIQUE) and `metadata_tags` join table to the SQLite schema in `init_db()`, plus schema tests.
## 2026-07-15 SEAST — Slow Builder (tags schema)

- Task: added `tags` (id, name UNIQUE) and `metadata_tags` (metadata_id, tag_id, composite PK, FK cascade) tables to `init_db()` in `apps/api/app/database.py`; added 6 schema/migration tests in `tests/test_database.py` including a migration test for pre-tags databases.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_database.py -q` — 23 passed.
- Next small step: add `add_tag_to_metadata`/`remove_tag_from_metadata` helpers plus unit tests.

## 2026-07-15 14:48 SEAST — Slow Builder (tag helpers)

- Task: added `add_tag_to_metadata` / `remove_tag_from_metadata` / `list_tags_for_metadata` helpers to `apps/api/app/database.py` (auto-create tag rows via INSERT OR IGNORE, idempotent add/remove, whitespace-stripped names, empty-tag ValueError, tag rows preserved on detach) plus 8 unit tests in `tests/test_database.py`.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_database.py -q` — 31 passed.
- Next small step: add `GET /library/tags` endpoint returning all tag names, plus integration tests.

## 2026-07-15 SEAST — Slow Builder (GET /library/tags endpoint)

- Task: added `GET /library/tags` endpoint (`apps/api/app/routes/library.py`) returning all tag names from the `tags` table in alphabetical order via a new `TagListResponse` model and a `list_all_tags(db_path)` helper in `apps/api/app/database.py`. Returns `{"items": []}` when the database file does not exist yet (works before any tags have been created); a corrupt/unreadable db is guarded with an empty-list fallback. Added 2 integration tests in `tests/test_library.py` (empty when no db; all tags returned sorted after seeding two metadata rows + two distinct tags).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_library.py -q` — 6 passed. Full suite `pytest -q` — 88 passed (2 new).
- Next small step: add `POST /library/metadata/{id}/tags` and `DELETE /library/metadata/{id}/tags/{tag}` endpoints for tagging/untagging an uploaded item.

## 2026-07-16 SEAST — Slow Builder (tag assign/remove endpoints)

- Task: added `POST /library/metadata/{id}/tags` (body `{tag}`, 200 with `{metadata_id, tags[]}`) and `DELETE /library/metadata/{id}/tags/{tag}` (200 with `{metadata_id, tags[]}`) endpoints to `apps/api/app/routes/library.py`. Both endpoints return 404 when the metadata row does not exist (backed by a new `metadata_exists()` helper in `app/database.py`), are idempotent, and return the full sorted tag list now attached to the row. POST rejects blank/whitespace-only tags with 422. Added 7 integration tests in `tests/test_library.py` (attach + sorted list, idempotent attach, unknown metadata 404, empty tag 422, detach + remaining, idempotent detach when not attached, unknown metadata 404 on DELETE).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_library.py -q` — 13 passed. Full suite `pytest -q` — 95 passed (7 new).
- Next small step: extend `GET /library/uploads` to accept optional `?tag=` and `?q=` query params filtering by tag name and filename substring.

## 2026-07-16 SEAST — Slow Builder (uploads list tag/q filters)

- Task: extended `GET /library/uploads` (`apps/api/app/routes/library.py`) to accept optional `?tag=` and `?q=` query params (combined with AND). Added a `list_metadata_filtered(tag, q, db_path)` helper to `apps/api/app/database.py` (tag filter via subquery on `metadata_tags`/`tags`; `q` is a case-insensitive `LOWER(filename) LIKE` substring match; blank/None params skip each filter). Added 3 integration tests in `tests/test_upload.py` (filter by q substring + no-match + blank-no-filter; filter by tag + multiple tags + blank-no-filter; combined tag AND q).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_upload.py -q` — 17 passed. Full suite `pytest -q` — 98 passed (3 new).
- Next small step: add a `GET /library/metadata/{id}` endpoint returning a single metadata row plus its tag list.

## 2026-07-16 13:10 SEAST — Slow Builder (metadata detail endpoint)

- Task: added `GET /library/metadata/{id}` endpoint to `apps/api/app/routes/library.py` returning a single metadata row (id, filename, path, size, content_type, uploaded_at) plus its sorted `tags` list via a new `MetadataDetailResponse` model. Returns 404 when the database file does not exist yet or the row is missing. Added a `get_metadata(metadata_id, db_path)` helper to `apps/api/app/database.py`. Added 4 integration tests in `tests/test_library.py` (row + sorted tags, row without tags → empty list, unknown id 404, missing db 404).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_library.py tests/test_database.py -q` — 47 passed. Full suite `pytest -q` — 102 passed (4 new).
- Next small step: add a search/filter input to the main web app Uploads card filtering by filename substring.

## 2026-07-16 SEAST — Slow Builder (uploads search/filter input)

- Task: added a search/filter input to the main web app Uploads card (`apps/web/src/main.tsx` + `styles.css`). A `uploadsFilter` state drives a case-insensitive substring filter over `filename`; the list renders only matching items, with a "No uploads match …" empty state when the filter excludes everything. The input is hidden until there is at least one upload, and the filter only affects client-side display (no API change).
- Verification: `cd apps/web && npm run build` — built successfully (tsc + vite), 15 modules transformed.
- Next small step: add a `GET /library/video` endpoint returning a JSON list of `.mp4` files in `library/video` (MVP 4 starter).

## 2026-07-16 23:19 SEAST — Slow Builder (GET /library/video endpoint)

- Task: added `GET /library/video` endpoint (`apps/api/app/routes/library.py`) returning a JSON list of `.mp4` files in `library/video`, mirroring `GET /library/audio` exactly. Uses new `VideoItem`/`VideoListResponse` models, imports `VIDEO_DIR` from `app.storage`, filters to `.mp4` only, sorted, and returns `{"items": []}` when the directory is missing. Added 2 integration tests in `tests/test_library.py` (mp4 filtering + empty/missing dir). This is the MVP 4 (Video Library) starter task.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_library.py -q` — 19 passed. Full suite `pytest -q` — 104 passed (2 new).
- Next small step: all current slow-tasks queue items are checked — generate the next tiny task batch (MVP 4 Video Library expansion).

## 2026-07-17 SEAST — Slow Builder (plan refresh)

- Task: all previous slow-tasks were complete; generated the next batch of 8 tiny tasks via Gemini 3.5 Flash (`agy --model "Gemini 3.5 Flash (High)" --print ...`), targeting MVP 4 (Video Library: MP4 download, streaming, preview, thumbnails). Tasks were adapted to Library-Yui's actual conventions (filesystem-based `/library/video`, `app/downloader.py` MP3 module with flag gate, `/jobs` flow) before merging into `docs/plans/slow-tasks.md`. No implementation done this run per cron rule (plan update only).
- Verification: docs-only plan update — `git diff --check` clean.
- Next small step: add `build_mp4_command()` / `download_mp4()` to `apps/api/app/downloader.py` mirroring the MP3 path.

## 2026-07-17 09:32 SEAST — Slow Builder (MP4 downloader module)

- Task: added `build_mp4_command()` / `download_mp4()` to `apps/api/app/downloader.py`, porting the legacy video conventions from `Downloader.py` (`-f "bv*+ba/b"`, `--merge-output-format mp4`, `--no-playlist`, `-N 8`, `--ignore-errors`) with output into `VIDEO_DIR` and the same `LIBRARY_YUI_DOWNLOADS_ENABLED` flag gate as the MP3 path. Added 4 new tests in `tests/test_downloader.py` (command conventions, default `VIDEO_DIR`, flag-disabled raise, mocked subprocess run).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_downloader.py -q` — 20 passed.
- Next small step: add an optional `mode` field (`audio` | `video`) to `POST /jobs` with 422 on unknown modes.

## 2026-07-17 SEAST — Slow Builder (POST /jobs mode field)

- Task: added an optional `mode` field (`audio` | `video`, default `audio`) to the `POST /jobs` request body (`apps/api/app/routes/jobs.py`) and persisted it on the job. `JobCreateRequest.mode` is a `Literal["audio", "video"]` so Pydantic rejects unknown values with HTTP 422 (validation error body mentions the `mode` field). `JobRecord` (`app/jobs.py`) gained a `mode: str` key and `create_job()` accepts an optional `mode` argument (defaults to `"audio"`). `JobResponse` now exposes `mode` in all job endpoints. Added 4 new tests in `tests/test_jobs.py` (default audio when omitted + persisted; explicit video persisted; explicit audio; unknown mode → 422 with `mode` in error locs) and updated the existing `test_list_jobs_returns_all_created_jobs` to assert the new key set `{id, url, status, mode}`.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_jobs.py -q` — 25 passed. Full suite `pytest -q` — 112 passed (4 new).
- Next small step: wire `/jobs/{id}/start` (when flag-enabled) to call `download_mp4` for `mode == "video"` and `download_mp3` otherwise.

## 2026-07-17 SEAST — Slow Builder (video-mode download dispatch)

- Task: wired `/jobs/{id}/start` (`apps/api/app/routes/jobs.py`) so that, when `LIBRARY_YUI_DOWNLOADS_ENABLED` is set, the download function is chosen by job `mode`: `download_mp4` for `mode == "video"` (MP4 into `library/video`) and `download_mp3` for any other value (default `audio`, MP3 into `library/audio`). The new dispatch lives in `_maybe_run_download`; flag-disabled behavior is unchanged (stub `downloading` transition). Added 2 new tests in `tests/test_jobs.py`: (1) `mode == "video"` calls `download_mp4` exactly once and never `download_mp3` and completes the job; (2) explicit `mode == "audio"` calls `download_mp3` exactly once and never `download_mp4`.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_jobs.py -q` — 27 passed (2 new).
- Next small step: add a `GET /library/video/{name}` endpoint streaming a single `.mp4` file from `library/video` with 404 + path-traversal protection.

## 2026-07-18 SEAST — Slow Builder (GET /library/video/{name} streaming)

- Task: added `GET /library/video/{name}` endpoint (`apps/api/app/routes/library.py`) streaming a single `.mp4` file from `library/video` via `FileResponse` (media type `video/mp4`, supports HTTP range requests for playback). Added a `_resolve_video_file(name)` helper that enforces path-traversal protection: rejects empty names, any `/` or `\\` separators, non-`.mp4` suffixes, and any resolved target whose parent is not the resolved `VIDEO_DIR`. Returns a uniform 404 ("Video not found") for missing files, non-mp4 names, and escaping paths. Added 4 new integration tests in `tests/test_library.py` (stream existing mp4 body + content-type, 404 missing, 404 non-mp4, path-traversal block covering `../`, `..\\`, leading-slash, and subdirectory names — all return 404 and never leak the secret file).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_library.py -q` — 23 passed (4 new).
- Next small step: add an HTML5 `<video>` preview modal/inline player in the main web app wired to `GET /library/video/{name}`.

## 2026-07-18 SEAST — Slow Builder (web video preview modal)

- Task: added an HTML5 `<video>` preview modal to the main web app (`apps/web/src/main.tsx` + `styles.css`) wired to `GET /library/video/{name}`. Added a `useLibraryVideo()` hook that fetches MP4 items from `GET /library/video` on mount; the Video card (replacing the old placeholder) now lists actual items with a ▶ button each. Clicking an item opens a centered modal containing a native `<video controls autoplay playsInline>` element pointed at the per-file streaming URL (`encodeURIComponent`-encoded). Closing: backdrop click, ✕ button, or any navigation away. Added matching `.video-item` / `.video-play` / `.video-modal-*` styles.
- Verification: `cd apps/web && npm run build` — built successfully (tsc + vite), 15 modules transformed, dist sizes unchanged (CSS 4.33 kB, JS 200.08 kB).
- Next small step: extend `GET /library/video` to also return file size and duration (parsed via container headers, best-effort) alongside the name.

## 2026-07-18 11:07 SEAST — Slow Builder (video size + duration probe)

- Task: extended `GET /library/video` (`apps/api/app/routes/library.py`) so each `VideoItem` now also carries `size` (bytes from `stat().st_size`) and `duration` (seconds, best-effort). Added a self-contained MP4 container parser (`_probe_mp4_duration` / `_read_mp4_duration` / `_find_top_level_box` / `_decode_mvhd_duration`) that walks the top-level ISO/IEC 14496-12 boxes, finds the first `moov` box, then the first `mvhd` inside it, and decodes version 0 (32-bit) and version 1 (64-bit) movie headers — no new dependencies. The probe never raises; any unreadable/truncated/garbage `.mp4` simply returns `duration: null` while still reporting size. Updated the existing `test_library_video_returns_list_of_mp4_files` test to assert the new `size` and `duration` fields, and added 2 new tests: (1) a synthetic minimal MP4 (ftyp + moov + mvhd) verifies `duration ≈ 2.5s` parsed from a 1000 Hz timescale; (2) a `.mp4` containing garbage bytes still returns name + size with `duration: null`.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_library.py -q` — 25 passed (2 new). Full suite `pytest -q` — 120 passed.
- Next small step: add a backend thumbnail extraction helper using ffmpeg (flag-gated, best-effort).

## 2026-07-18 SEAST — Slow Builder (ffmpeg thumbnail helper)

- Task: added a backend thumbnail extraction helper to `apps/api/app/downloader.py` writing `library/thumbnails/<video-stem>.jpg` using ffmpeg. `build_thumbnail_command()` builds the argv (seek at default 1.0s, scale to 320px width keeping aspect ratio, single JPEG frame via `-frames:v 1` / `-update 1`, `-q:v 3`). `extract_thumbnail()` is best-effort and never raises: it returns a result dict (`ok`, `skipped`, `path`, `returncode`, `command`) and silently skips when (1) the `LIBRARY_YUI_DOWNLOADS_ENABLED` flag is off, (2) ffmpeg is not on PATH (`_resolve_ffmpeg()` returns None), or (3) the input video file is missing; on ffmpeg failure any partial output file is cleaned up so the thumbnails folder never leaks garbage. Reuses the existing feature flag for consistency with the MP3/MP4 downloaders. Added 7 new tests in `tests/test_downloader.py` (command conventions, custom args, skip-when-flag-disabled, skip-when-ffmpeg-missing, skip-when-video-missing, successful invocation via monkeypatched subprocess.run, partial-cleanup-on-failure, default-THUMBNAILS_DIR output).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_downloader.py -q` — 28 passed (7 new). Full suite `pytest -q` — 128 passed.
- Next small step: update `docs/API.md` documenting `GET /library/video/{name}` (streaming) and the `mode` field on `POST /jobs`.

## 2026-07-18 21:17 SEAST — Slow Builder (API docs: video streaming + jobs mode)

- Task: updated `docs/API.md` with two new pieces of documentation. (1) Added a `GET /library/video/{name}` section covering path parameters, the `video/mp4` `FileResponse` with HTTP range support, the uniform 404 for missing/non-mp4/path-traversal names (no existence leak), and curl + `<video>` examples. (2) Extended the `POST /jobs` section: documented the optional `mode` field (`"audio"` default → MP3, `"video"` → MP4, unknown values → 422), added `mode` to the request body table and example, and added `mode` to the 201 response example and field table. All content verified against the actual `apps/api/app/routes/library.py` (`stream_video`, `_resolve_video_file`) and `apps/api/app/routes/jobs.py` (`JobCreateRequest`, `JobResponse`) implementations.
- Verification: docs-only task — `git diff --check` clean (exit 0; only line-ending notices, no whitespace errors).
- Next small step: all current slow-tasks queue items are checked — generate the next tiny task batch for MVP 4 polish / MVP 5 starters.

## 2026-07-19 SEAST — Slow Builder (plan refresh)

- Task: all previous slow-tasks were complete; generated the next batch of 8 tiny tasks via Gemini 3.5 Flash (`agy --model "Gemini 3.5 Flash (High)" --print ...`), targeting MVP 4 polish (audio streaming, audio probe, thumbnail wiring + serving + UI) plus MVP 5 (Persistence) starters (`jobs` SQLite table) and OpenAPI tagging. Tasks were adapted to Library-Yui's actual conventions (filesystem-based `/library/audio` and `/library/video`, `app/downloader.py` ffmpeg helper, SQLite `metadata` store, in-memory job store) before merging into `docs/plans/slow-tasks.md`. No implementation done this run per cron rule (plan update only).
- Verification: docs-only plan update — `git diff --check` clean.
- Next small step: add an audio streaming endpoint `GET /library/audio/{name}` mirroring the video streaming endpoint.

## 2026-07-19 SEAST — Slow Builder (GET /library/audio/{name} streaming)

- Task: added `GET /library/audio/{name}` endpoint (`apps/api/app/routes/library.py`) streaming a single `.mp3` file from `library/audio` via `FileResponse` (media type `audio/mpeg`, supports HTTP range requests for playback). Added a `_resolve_audio_file(name)` helper mirroring `_resolve_video_file`: rejects empty names, any `/` or `\\` separators, non-`.mp3` suffixes, and any resolved target whose parent is not the resolved `AUDIO_DIR`. Returns a uniform 404 ("Audio not found") for missing files, non-mp3 names, and escaping paths — no existence leak. Added 4 new integration tests in `tests/test_library.py` (stream existing mp3 body + content-type, 404 missing, 404 non-mp3, path-traversal block covering `../`, `..\\`, leading-slash, and subdirectory names — all return 404 and never leak the secret file).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_library.py -q` — 29 passed (4 new). Full suite `pytest -q` — 132 passed.
- Next small step: extend `GET /library/audio` to also return file `size` and `duration` (best-effort, reusing the existing `_probe_mp4_duration` container parser) alongside the name.

## 2026-07-19 SEAST — Slow Builder (audio size + duration probe)

- Task: extended `GET /library/audio` (`apps/api/app/routes/library.py`) so each `AudioItem` now also carries `size` (bytes from `stat().st_size`) and `duration` (seconds, best-effort). The existing `_probe_mp4_duration` container parser (originally built for the video list) is reused unchanged — it walks the top-level ISO/IEC 14496-12 boxes, finds the first `moov`/`mvhd`, and decodes version 0/1 movie headers. The probe never raises; any plain (non-MP4-container) `.mp3` simply returns `duration: null` while still reporting size. Updated the existing `test_library_audio_returns_list_of_mp3_files` test to assert the new `size`/`duration` fields, and added 2 new tests: (1) a `.mp3` containing a synthetic MP4 container reports `duration ≈ 3.0s`; (2) a plain ID3-headed `.mp3` returns name + size with `duration: null`. Updated `docs/API.md` with the new `size` / `duration` columns and example.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_library.py -q` — 31 passed (2 new). Full suite `pytest -q` — 134 passed (was 132). `git diff --check` — clean (exit 0; only LF/CRLF notices, no whitespace errors).
- Next small step: wire the ffmpeg thumbnail extraction helper (`extract_thumbnail` from `app/downloader.py`) into the `/jobs/{id}/start` flag-gated path so a successful `mode == "video"` download also produces `library/thumbnails/<stem>.jpg` (best-effort, never fails the job).

## 2026-07-19 17:36 SEAST — Slow Builder (thumbnail extraction wiring)

- Task: wired the ffmpeg thumbnail extraction helper (`extract_thumbnail` from `app/downloader.py`) into the `/jobs/{id}/start` flag-gated path so that a successful `mode == "video"` download also produces `library/thumbnails/<stem>.jpg`. Added `_maybe_extract_thumbnails()` in `apps/api/app/routes/jobs.py`: after a successful video download completes, it scans `VIDEO_DIR` for `*.mp4` files and feeds each one to `extract_thumbnail` (which is non-raising, flag-gated, and skips silently when ffmpeg is missing or the input is unreadable). The whole step is wrapped in a try/except so any thumbnail/ffmpeg problem is logged and swallowed — it can never turn a completed download into a failed job. Note: the yt-dlp result dict does not surface the produced file path, so the helper scans the directory (best-effort, acceptable for a single-user library). Added 4 new tests in `tests/test_jobs.py`: (1) successful `mode == "video"` triggers `extract_thumbnail` exactly once and the job completes; (2) `mode == "audio"` never calls `extract_thumbnail`; (3) when `extract_thumbnail` raises, the job still reports `completed`; (4) when `VIDEO_DIR` does not exist on disk, `extract_thumbnail` is never called and the job still completes.
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py -q` — 1 passed. `pytest tests/test_jobs.py -q` — 30 passed (4 new). Full suite `pytest -q` — 138 passed (was 134). `git diff --check` — clean (only LF/CRLF notices, no whitespace errors).
- Next small step: add a `GET /library/thumbnails/{name}` endpoint serving a single `.jpg` thumbnail from `library/thumbnails` with 404 + path-traversal protection.

## 2026-07-19 18:30 SEAST — Slow Builder (GET /library/thumbnails/{name} serving)

- Task: added `GET /library/thumbnails/{name}` endpoint (`apps/api/app/routes/library.py`) serving a single `.jpg` thumbnail from `library/thumbnails` via `FileResponse` (media type `image/jpeg`). Added a `_resolve_thumbnail_file(name)` helper mirroring the existing `_resolve_video_file`/`_resolve_audio_file`: rejects empty names, any `/` or `\` separators, non-`.jpg` suffixes, and any resolved target whose parent is not the resolved `THUMBNAILS_DIR`. Returns a uniform 404 ("Thumbnail not found") for missing files, non-jpg names, and escaping paths — no existence leak. Imported `THUMBNAILS_DIR` from `app.storage`. Added 4 new integration tests in `tests/test_library.py`: serve existing jpg body + content-type, 404 missing, 404 non-jpg, path-traversal block (covers `../`, `..\`, leading-slash, and subdirectory names — all return 404 and never leak the secret file).
- Verification: `cd apps/api && PYTHONPATH= PYTHONNOUSERSITE=1 .venv/Scripts/python -m pytest tests/test_health.py tests/test_library.py -q` — 35 passed (4 new).
- Next small step: show generated thumbnails next to video items in the main web app Video card (best-effort `<img src="/api/library/thumbnails/{name}.jpg">` with `onError` fallback to a placeholder).
