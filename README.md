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

## Collections

Collections allow grouping media items into curated playlists or albums.

- **Endpoints:**
  - `POST /collections` — Create a named collection (`{"name": "Favorites"}`).
  - `GET /collections` — List all collections.
  - `POST /collections/{name}/items` — Add a media item (`{"metadata_id": 1}`) to a collection.
  - `GET /collections/{name}/items` — List items within a collection.
  - `DELETE /collections/{name}/items/{metadata_id}` — Remove an item from a collection.

- **Collections vs Tags:**
  - **Tags** are lightweight labels attached directly to individual media items (e.g. `ambient`, `synth`) used for quick filtering and search.
  - **Collections** are explicit, named groupings that collect multiple media items into custom lists.
