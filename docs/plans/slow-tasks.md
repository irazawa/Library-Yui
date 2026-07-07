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

- [ ] Add `GET /version` API endpoint returning app name, version, and current milestone.
- [ ] Add an API test for `/version`.
- [ ] Show API health status card in the status dashboard with a simple fetch to `http://127.0.0.1:8787/health`.
- [ ] Add a disabled URL input form shell to the main web app for future audio downloads.
- [ ] Add an empty library section component showing Audio, Video, Uploads counts as placeholders.
- [ ] Add `docs/API.md` documenting `/health` and `/version`.
- [ ] Add backend storage path constants for audio, video, uploads, and thumbnails.
- [ ] Add `GET /library/summary` returning placeholder counts from storage folders.
- [ ] Show library summary placeholders on the main web app.
- [ ] Add a progress dashboard card that links to the GitHub repository.
