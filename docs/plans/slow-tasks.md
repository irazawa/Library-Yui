# Library-Yui Slow Build Task Queue

This queue is for scheduled slow-progress runs. Each run should implement at most one small task, verify it, commit, and push.

## Rules

- Do exactly one unchecked task per scheduled run.
- Keep changes small and reviewable.
- Do not delete features or rewrite architecture.
- Run the relevant verification before committing.
- Mark the completed task checked in this file in the same commit.
- If all tasks are checked, generate the next small plan before implementing anything else.

## Queue

- [x] Add `GET /version` API endpoint returning app name, version, and current milestone.
- [x] Add an API test for `/version`.
- [x] Show API health status card in the status dashboard with a simple fetch to `http://127.0.0.1:8787/health`.
- [x] Add a disabled URL input form shell to the main web app for future audio downloads.
- [x] Add an empty library section component showing Audio, Video, Uploads counts as placeholders.
- [x] Add `docs/API.md` documenting `/health` and `/version`.
- [x] Add backend storage path constants for audio, video, uploads, and thumbnails.
- [x] Add `GET /library/summary` returning placeholder counts from storage folders.
- [x] Show library summary placeholders on the main web app.
- [x] Add a progress dashboard card that links to the GitHub repository.

## Next batch (generated 2026-07-09 via Gemini 3.5 Flash)

- [x] Add `POST /jobs` API endpoint accepting a YouTube URL, initializing a pending download job and returning a job ID.
- [x] Add an integration test verifying `POST /jobs` returns 201, generates a job ID, and stores job state.
- [x] Implement `GET /jobs/{id}` returning the status (pending/downloading/completed/failed) of a specific job.
- [x] Enable and wire the URL input form in the main web app (port 5174) to call `POST /jobs` on submit and show the resulting job ID.
- [x] Add a polling hook in the main web app that periodically calls `GET /jobs/{id}` and shows active job status.
- [x] Add `GET /library/audio` returning a JSON list of MP3 files in `library/audio`.
- [x] Wire the main web app library audio card to `GET /library/audio` so it lists actual audio items.
- [x] Update `docs/API.md` documenting the `/jobs` and `/jobs/{id}` endpoints (method, fields, example responses).

## Next batch (generated 2026-07-11 via fallback — Gemini auth failed)

- [x] Add a `DOWNLOADABLE` validation in `POST /jobs` that rejects non-YouTube URLs with a 422/400 error.
- [x] Add a `POST /jobs/{id}/start` stub endpoint that transitions a job from `pending` to `downloading` (no real download yet).
- [x] Add a `POST /jobs/{id}/complete` stub endpoint that transitions a job to `completed` (placeholder, no file yet).
- [x] Add a job lifecycle test suite covering pending → downloading → completed transitions.
- [x] Add a `GET /jobs` list endpoint returning all jobs (id, url, status) from the in-memory store.
- [x] Add a status dashboard card that polls `GET /jobs` and shows a live count of active/recent jobs.
- [x] Port the core MP3 download logic from `C:/games/music/Downloader.py` into a `app/downloader.py` module behind a feature flag (no wiring yet).
- [x] Wire the real downloader into the `/jobs` flow so a created job actually downloads an MP3 into `library/audio/` (flag-gated).

## Next batch (generated 2026-07-13 via Gemini 3.5 Flash)

- [x] Set up SQLite database initialization logic for `apps/api/data/library.db` and create a `metadata` table.
- [x] Add unit/integration tests for SQLite database initialization and basic CRUD operations on metadata.
- [x] Add `POST /library/upload` API endpoint accepting multipart file uploads and saving to `library/uploads/`.
- [x] Record upload metadata (filename, path, size, content type, uploaded_at) in the SQLite database upon upload.
- [x] Add integration tests for `POST /library/upload` verifying filesystem write and database insert.
- [x] Add `GET /library/uploads` API endpoint returning a list of all uploaded items from the SQLite database.
- [x] Add a file upload UI component (drag-and-drop or file selector) in the main web app to upload files.
- [x] Wire the main web app Uploads list to display uploaded files fetched from `GET /library/uploads`.
- [x] Update `docs/API.md` with descriptions and examples for `POST /library/upload` and `GET /library/uploads`.

## Next batch (generated 2026-07-15 via Gemini 3.5 Flash)

Begins MVP 3 (Collections) plus one MVP 4 (Video) starter. Each task is small,
self-contained, and verifiable with a single `pytest` run (backend) or
`npm run build` (frontend).

- [x] Add a `tags` table (id, name UNIQUE) and a `metadata_tags` join table (metadata_id, tag_id) to the SQLite schema in `apps/api/app/database.py` `init_db()`, created alongside the existing `metadata` table; add schema/migration tests in `tests/test_database.py`.
- [x] Add `add_tag_to_metadata(metadata_id, tag, db_path)` and `remove_tag_from_metadata(metadata_id, tag, db_path)` helpers to `apps/api/app/database.py` (auto-creating tag rows, idempotent) plus unit tests in `tests/test_database.py`.
- [x] Add a `GET /library/tags` endpoint returning all tag names in `apps/api/app/routes/library.py` (backed by the `tags` table) plus integration tests.
- [x] Add `POST /library/metadata/{id}/tags` (body `{tag}`) and `DELETE /library/metadata/{id}/tags/{tag}` endpoints to `apps/api/app/routes/library.py` for tagging/untagging an uploaded item; add integration tests.
- [x] Extend `GET /library/uploads` to accept optional `?tag=` and `?q=` query params filtering by tag name and substring of filename respectively; add tests for both filters.
- [x] Add a `GET /library/metadata/{id}` endpoint returning a single metadata row plus its tag list; add tests.
- [x] Add a simple search/filter input to the main web app Uploads card (`apps/web/src/main.tsx`) that filters the displayed uploads list by filename substring.
- [x] Add a `GET /library/video` endpoint returning a JSON list of `.mp4` files in `library/video` (mirroring `GET /library/audio`) plus tests — MVP 4 starter.

## Next batch (generated 2026-07-17 via Gemini 3.5 Flash)

MVP 4 (Video Library) expansion. Each task is small, self-contained, and
verifiable with a single `pytest` run (backend) or `npm run build` (frontend).
Adapted to Library-Yui conventions (filesystem-based `/library/video`,
`app/downloader.py` MP3 module, flag-gated downloads).

- [x] Add `build_mp4_command()` / `download_mp4()` to `apps/api/app/downloader.py` mirroring the MP3 path (`-f "bv*+ba/b"`, `--merge-output-format mp4`, output into `VIDEO_DIR`, same flag gate) plus tests in `tests/test_downloader.py`.
- [x] Add an optional `mode` field (`audio` | `video`, default `audio`) to the `POST /jobs` request body and persist it on the job; reject unknown modes with 422; add tests in `tests/test_jobs.py`.
- [x] Wire `/jobs/{id}/start` (when flag-enabled) to call `download_mp4` for `mode == "video"` and `download_mp3` otherwise; add tests in `tests/test_jobs.py`.
- [x] Add a `GET /library/video/{name}` endpoint streaming a single `.mp4` file from `library/video` with HTTP 404 for missing/unknown files and path-traversal protection; add tests in `tests/test_library.py`.
- [x] Add an HTML5 `<video>` preview modal/inline player in the main web app (`apps/web/src/main.tsx`) wired to `GET /library/video/{name}`; verify with `npm run build` in `apps/web`.
- [x] Extend `GET /library/video` to also return file size and duration (parsed via the container headers, best-effort) alongside the name; add tests in `tests/test_library.py`.
- [x] Add a backend thumbnail extraction helper using ffmpeg (flag-gated, best-effort, skipped if ffmpeg missing) writing `library/thumbnails/<name>.jpg`; add tests in `tests/test_downloader.py` using a monkeypatched ffmpeg call.
- [x] Update `docs/API.md` documenting `GET /library/video/{name}` (streaming) and the `mode` field on `POST /jobs`; verify with `git diff --check`.

## Next batch (generated 2026-07-19 via Gemini 3.5 Flash)

MVP 4 polish (thumbnails) plus MVP 2/3 consistency and MVP 5 (Persistence)
starters. Each task is small, self-contained, and verifiable with a single
`pytest` run (backend) or `npm run build` (frontend). Adapted to
Library-Yui conventions (filesystem-based library, `app/downloader.py`,
SQLite `metadata` store, in-memory job store).

- [x] Add an audio streaming endpoint `GET /library/audio/{name}` mirroring `GET /library/video/{name}` (FileResponse `audio/mpeg`, HTTP range support, 404 + path-traversal protection) plus tests in `tests/test_library.py`.
- [x] Extend `GET /library/audio` to also return file `size` and `duration` (best-effort, reusing the existing `_probe_mp4_duration` container parser from `library.py`) alongside the name; add tests in `tests/test_library.py`.
- [x] Wire the ffmpeg thumbnail extraction helper (`extract_thumbnail` from `app/downloader.py`) into the `/jobs/{id}/start` flag-gated path so that a successful `mode == "video"` download also produces `library/thumbnails/<stem>.jpg` (best-effort, never fails the job); add tests in `tests/test_jobs.py`.
- [x] Add a `GET /library/thumbnails/{name}` endpoint serving a single `.jpg` thumbnail from `library/thumbnails` with 404 + path-traversal protection (mirroring `_resolve_video_file`); add tests in `tests/test_library.py`.
- [x] Show generated thumbnails next to video items in the main web app Video card (best-effort `<img src="/api/library/thumbnails/{name}.jpg">` with `onError` fallback to a placeholder); verify with `npm run build` in `apps/web`.
- [x] Add a `jobs` table (id TEXT PRIMARY KEY, url, mode, status, created_at, updated_at) to `init_db()` in `apps/api/app/database.py` without migrating the in-memory store yet (schema-only, with migration tests for pre-existing databases); add tests in `tests/test_database.py`.
- [x] Refactor FastAPI route decorators across `apps/api/app/routes/*.py` to use structured OpenAPI `tags=[...]` (`Jobs`, `Library`, `Collections`, `System`) and document the grouping in `docs/API.md`; verify with `pytest tests/test_health.py -q` and `git diff --check`.
- [x] Add a global error notification banner component to the main web app (`apps/web/src/main.tsx` + `styles.css`) that captures upload/download failures already caught locally and surfaces them as a dismissible top-of-page banner; verify with `npm run build` in `apps/web`.

## Next batch (generated 2026-07-21 via fallback — Gemini `agy` drifted off-task)

MVP 5 (Persistence) wiring plus small robustness/management tasks. Each task
is small, self-contained, and verifiable with a single `pytest` run
(backend) or `npm run build` (frontend) or `git diff --check` (docs).
Adapted to Library-Yui conventions (SQLite `metadata`/`tags`/`metadata_tags`/
`jobs` schema in `apps/api/app/database.py`, in-memory job store in
`app/jobs.py`, filesystem-based `library/` storage, `app/downloader.py`
flag-gated downloads).

- [x] Dual-write job persistence: extend `create_job()` and `update_job_status()` in `apps/api/app/jobs.py` to also insert/update a row in the SQLite `jobs` table (best-effort, wrapped so a DB error never breaks the in-memory store); add tests in `tests/test_jobs.py` verifying a created/transitioned job is reflected in the DB.
- [x] Add a `DELETE /library/metadata/{id}` endpoint (`apps/api/app/routes/library.py`) that removes the metadata row, its `metadata_tags` rows, and deletes the underlying file from `library/uploads/` (best-effort file removal); return 404 for unknown ids; add tests in `tests/test_library.py`.
- [x] Add a `DELETE /jobs/{id}` endpoint (`apps/api/app/routes/jobs.py`) that removes a job from the in-memory store (and its SQLite row if persistence is wired); return 404 for unknown ids and 204 on success; add tests in `tests/test_jobs.py`.
- [x] Extend `GET /library/uploads` to accept optional `?limit=` and `?offset=` query params (defaulting to no pagination) and include a `total` count field in the response; add tests in `tests/test_upload.py` covering limit, offset, and total.
- [ ] Add a `GET /config` endpoint (`apps/api/app/routes/system.py` or `health.py`) returning runtime config: download-flag state (`LIBRARY_YUI_DOWNLOADS_ENABLED`), `MAX_UPLOAD_BYTES`, and the resolved library dirs; tag it `System`; add tests in a new `tests/test_config.py`.
- [ ] Add a per-upload tag-editing UI in the main web app Uploads card (`apps/web/src/main.tsx` + `styles.css`): a small input + "Add tag" button per item calling `POST /library/metadata/{id}/tags` and rendering removable tag chips via `DELETE /library/metadata/{id}/tags/{tag}`; verify with `npm run build` in `apps/web`.
- [ ] Add a "Load more" pagination control to the main web app Uploads list (`apps/web/src/main.tsx`) that fetches the next page via `?limit=&offset=` on `GET /library/uploads` when more items are available; verify with `npm run build` in `apps/web`.
- [ ] Update `docs/API.md` documenting the new `DELETE /library/metadata/{id}`, `DELETE /jobs/{id}`, `GET /config` endpoints and the `?limit=`/`?offset=`/`total` pagination fields on `GET /library/uploads`; verify with `git diff --check`.
