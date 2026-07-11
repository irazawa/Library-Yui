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
- [ ] Add a `POST /jobs/{id}/start` stub endpoint that transitions a job from `pending` to `downloading` (no real download yet).
- [ ] Add a `POST /jobs/{id}/complete` stub endpoint that transitions a job to `completed` (placeholder, no file yet).
- [ ] Add a job lifecycle test suite covering pending → downloading → completed transitions.
- [ ] Add a `GET /jobs` list endpoint returning all jobs (id, url, status) from the in-memory store.
- [ ] Add a status dashboard card that polls `GET /jobs` and shows a live count of active/recent jobs.
- [ ] Port the core MP3 download logic from `C:/games/music/Downloader.py` into a `app/downloader.py` module behind a feature flag (no wiring yet).
- [ ] Wire the real downloader into the `/jobs` flow so a created job actually downloads an MP3 into `library/audio/` (flag-gated).
