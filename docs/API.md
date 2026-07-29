# Library-Yui API Reference

Base URL (local dev): `http://127.0.0.1:8787`

The API is built with FastAPI. All responses are JSON.

Every endpoint is grouped under one of the following OpenAPI tags, which surface
as sections in the interactive docs (`/docs`, `/redoc`):

| Tag           | Scope                                                                  |
| ------------- | ---------------------------------------------------------------------- |
| `System`      | Liveness probes, version, and runtime config (`/health`, `/version`, `/config`). |
| `Jobs`        | Download job lifecycle (`/jobs`, `/jobs/{id}`, `/jobs/{id}/start`, `DELETE /jobs/completed`, `DELETE /jobs/{id}`). |
| `Library`     | Library listing, streaming, audio/video deletion, uploads, thumbnails, storage usage, export, import, and summary. |
| `Collections` | Collections management and item membership (`POST/GET/DELETE /collections`, `POST /collections/{name}/rename`, `POST/GET/DELETE /collections/{name}/items`). |

## `GET /health`

Lightweight liveness probe. Always returns `200` if the service is running.

### Response — `200 OK`

```json
{
  "status": "ok",
  "service": "library-yui-api"
}
```

| Field     | Type   | Description                            |
| --------- | ------ | -------------------------------------- |
| `status`  | string | Liveness status, currently `ok`.       |
| `service` | string | Internal service identifier.           |

### Example

```bash
curl http://127.0.0.1:8787/health
```

## `GET /version`

Returns application metadata: app name, version, and the current milestone.

### Response — `200 OK`

```json
{
  "app_name": "Library-Yui API",
  "version": "0.1.0",
  "milestone": "MVP 1 — Audio Downloads"
}
```

| Field       | Type   | Description                                              |
| ----------- | ------ | -------------------------------------------------------- |
| `app_name`  | string | Human-readable application name.                         |
| `version`   | string | Semantic version of the API.                            |
| `milestone` | string | Active development milestone label.                      |

### Example

```bash
curl http://127.0.0.1:8787/version
```

## `GET /config`

Returns non-secret runtime configuration visible to clients: whether real
downloads are enabled, the upload size cap, and the resolved library storage
directories. Useful for frontends that need to adapt their UI to the backend's
operational mode (e.g. hide the download form when downloads are disabled).

### Response — `200 OK`

```json
{
  "downloads_enabled": false,
  "max_upload_bytes": 52428800,
  "library_dirs": {
    "library": "C:/games/Library-Yui/library",
    "audio": "C:/games/Library-Yui/library/audio",
    "video": "C:/games/Library-Yui/library/video",
    "uploads": "C:/games/Library-Yui/library/uploads",
    "thumbnails": "C:/games/Library-Yui/library/thumbnails"
  }
}
```

| Field               | Type           | Description                                                          |
| ------------------- | -------------- | -------------------------------------------------------------------- |
| `downloads_enabled` | boolean        | `true` when `LIBRARY_YUI_DOWNLOADS_ENABLED` is set (real downloads). |
| `max_upload_bytes`  | integer        | Upload size cap in bytes (`MAX_UPLOAD_BYTES`, default 50 MiB).       |
| `library_dirs`      | object         | Map of storage name → resolved absolute path.                        |
| `library_dirs.*`    | string         | Absolute path for `library`, `audio`, `video`, `uploads`, `thumbnails`. |

### Example

```bash
curl http://127.0.0.1:8787/config
```

## `GET /library/summary`

Returns file counts per storage category (audio, video, uploads, thumbnails).
Missing directories count as `0`, so this works before any downloads/uploads exist.

### Response — `200 OK`

```json
{
  "audio": 0,
  "video": 0,
  "uploads": 0,
  "thumbnails": 0
}
```

| Field        | Type | Description                                        |
| ------------ | ---- | -------------------------------------------------- |
| `audio`      | int  | Number of files in the audio library folder.       |
| `video`      | int  | Number of files in the video library folder.       |
| `uploads`    | int  | Number of files in the uploads folder.             |
| `thumbnails` | int  | Number of files in the thumbnails folder.          |

### Example

```bash
curl http://127.0.0.1:8787/library/summary
```

## `GET /library/storage`

Returns total bytes used per storage folder (`audio`, `video`, `uploads`, `thumbnails`).
Missing directories count as `0` bytes, so this works before any downloads/uploads exist.

### Response — `200 OK`

```json
{
  "audio": 0,
  "video": 0,
  "uploads": 0,
  "thumbnails": 0
}
```

| Field        | Type | Description                                         |
| ------------ | ---- | --------------------------------------------------- |
| `audio`      | int  | Total bytes used by files in the audio folder.      |
| `video`      | int  | Total bytes used by files in the video folder.      |
| `uploads`    | int  | Total bytes used by files in the uploads folder.    |
| `thumbnails` | int  | Total bytes used by files in the thumbnails folder. |

### Example

```bash
curl http://127.0.0.1:8787/library/storage
```

## `GET /library/export`

Returns a full JSON dump of all metadata records, tags, collections, and download jobs stored in the system.
Returns empty arrays for database-backed entities when the database file does not exist yet or is empty.

### Response — `200 OK`

```json
{
  "metadata": [
    {
      "id": 1,
      "filename": "track.mp3",
      "path": "library/uploads/track.mp3",
      "size": 10240,
      "content_type": "audio/mpeg",
      "uploaded_at": "2026-07-29T10:00:00Z"
    }
  ],
  "tags": ["rock"],
  "collections": [
    {
      "id": 1,
      "name": "Favorites"
    }
  ],
  "jobs": [
    {
      "id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "status": "completed",
      "mode": "audio"
    }
  ]
}
```

| Field                  | Type   | Description                                                               |
| ---------------------- | ------ | ------------------------------------------------------------------------- |
| `metadata`             | array  | List of uploaded item metadata objects (`id`, `filename`, `path`, etc.).  |
| `tags`                 | array  | Array of unique tag strings present across all items.                     |
| `collections`          | array  | List of collection objects (`id`, `name`).                                |
| `jobs`                 | array  | List of download job objects (`id`, `url`, `status`, `mode`).             |

### Example

```bash
curl http://127.0.0.1:8787/library/export
```

## `POST /library/import`

Restores metadata, tags, collections, and download jobs from an exported JSON dump (such as produced by `GET /library/export`).

### Request body

```json
{
  "metadata": [
    {
      "id": 1,
      "filename": "track.mp3",
      "path": "library/uploads/track.mp3",
      "size": 10240,
      "content_type": "audio/mpeg",
      "uploaded_at": "2026-07-29T10:00:00Z",
      "tags": ["rock"]
    }
  ],
  "tags": ["rock", "synth"],
  "collections": ["Favorites"],
  "jobs": [
    {
      "id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "status": "completed",
      "mode": "audio"
    }
  ]
}
```

| Field         | Type  | Description                                                           |
| ------------- | ----- | --------------------------------------------------------------------- |
| `metadata`    | array | Optional list of item metadata objects to restore.                    |
| `tags`        | array | Optional list of tag names to register in the tags table.             |
| `collections` | array | Optional list of collection names or collection objects to restore.   |
| `jobs`        | array | Optional list of download job objects to restore.                     |

### Response — `200 OK`

```json
{
  "imported_metadata": 1,
  "imported_tags": 2,
  "imported_collections": 1,
  "imported_jobs": 1
}
```

| Field                  | Type    | Description                                            |
| ---------------------- | ------- | ------------------------------------------------------ |
| `imported_metadata`    | integer | Total metadata records imported.                       |
| `imported_tags`        | integer | Total tags processed/inserted.                         |
| `imported_collections` | integer | Total collections processed/inserted.                  |
| `imported_jobs`        | integer | Total download jobs restored.                          |

### Example

```bash
curl -X POST http://127.0.0.1:8787/library/import \
  -H "Content-Type: application/json" \
  -d @library-export.json
```

## `GET /library/audio`

Returns the names of MP3 files in the audio library folder, sorted alphabetically.
Only `.mp3` files are included. A missing directory returns an empty list.
Supports an optional query parameter `q` for case-insensitive filename substring filtering.

Each item carries a best-effort `size` (bytes from the filesystem) and
`duration` (seconds, parsed from an MP4/MOV `moov`/`mvhd` container header
when present; `null` otherwise — never raises).

### Query parameters

| Parameter | Type   | Description                                                 |
| --------- | ------ | ----------------------------------------------------------- |
| `q`       | string | Optional case-insensitive substring filter against filename. |

### Response — `200 OK`

```json
{
  "items": [
    { "name": "song-a.mp3", "size": 4096000, "duration": null },
    { "name": "song-b.mp3", "size": 5120000, "duration": 197.5 }
  ]
}
```

| Field               | Type           | Description                                                            |
| ------------------- | -------------- | ---------------------------------------------------------------------- |
| `items`             | array          | List of audio items.                                                   |
| `items[].name`      | string         | File name of the MP3 (no path).                                        |
| `items[].size`      | integer        | File size in bytes (`0` on `stat` failure).                            |
| `items[].duration`  | number \| null | Best-effort duration in seconds (container-parsed), or `null`.         |

### Example

```bash
curl "http://127.0.0.1:8787/library/audio?q=song"
```

## `DELETE /library/audio/{name}`

Deletes a single `.mp3` file from the audio library folder (`library/audio/`).

The endpoint only deletes files directly inside `library/audio/`. Path-traversal
attempts (e.g. `../`, leading slashes, backslash separators, or nested
subdirectories) and non-`.mp3` names all resolve to a uniform `404` error.

### Path parameters

| Parameter | Type   | Description                             |
| --------- | ------ | --------------------------------------- |
| `name`    | string | The `.mp3` file name to delete (no path). |

### Response — `204 No Content`

Empty body. The file has been deleted.

### Response — `404 Not Found`

Returned when the file is missing, the name is not a `.mp3`, or the resolved
path escapes `library/audio`.

```json
{
  "detail": "Audio not found"
}
```

### Example

```bash
curl -X DELETE http://127.0.0.1:8787/library/audio/song.mp3
```

## `GET /library/video`

Returns the names of MP4 files in the video library folder, sorted alphabetically.
Only `.mp4` files are included. A missing directory returns an empty list.
Supports an optional query parameter `q` for case-insensitive filename substring filtering.

### Query parameters

| Parameter | Type   | Description                                                 |
| --------- | ------ | ----------------------------------------------------------- |
| `q`       | string | Optional case-insensitive substring filter against filename. |

### Response — `200 OK`

```json
{
  "items": [
    { "name": "clip-a.mp4", "size": 10485760, "duration": 45.0 }
  ]
}
```

| Field               | Type           | Description                                                            |
| ------------------- | -------------- | ---------------------------------------------------------------------- |
| `items`             | array          | List of video items.                                                   |
| `items[].name`      | string         | File name of the MP4 (no path).                                        |
| `items[].size`      | integer        | File size in bytes (`0` on `stat` failure).                            |
| `items[].duration`  | number \| null | Best-effort duration in seconds (container-parsed), or `null`.         |

### Example

```bash
curl "http://127.0.0.1:8787/library/video?q=clip"
```

## `GET /library/video/{name}`

Streams a single `.mp4` file from the video library folder. The response uses
the `video/mp4` media type and supports HTTP range requests, so browsers and
media players can seek within the file via an HTML5 `<video>` element.

The endpoint only serves files directly inside `library/video/`. Path-traversal
attempts (e.g. `../`, leading slashes, backslash separators, or nested
subdirectories) and non-`.mp4` names all resolve to a uniform `404` that does
not leak whether any file exists.

### Path parameters

| Parameter | Type   | Description                              |
| --------- | ------ | ---------------------------------------- |
| `name`    | string | The `.mp4` file name to stream (no path). |

### Response — `200 OK`

Binary MP4 content with `Content-Type: video/mp4`. Supports `Range` requests
for partial-content playback (HTTP 206).

### Response — `404 Not Found`

Returned when the file is missing, the name is not a `.mp4`, or the resolved
path escapes `library/video`.

```json
{
  "detail": "Video not found"
}
```

### Example

```bash
# Download the full file
curl -o clip.mp4 http://127.0.0.1:8787/library/video/clip.mp4

# Stream it into an HTML5 player
# <video src="http://127.0.0.1:8787/library/video/clip.mp4" controls></video>
```

## `DELETE /library/video/{name}`

Deletes a single `.mp4` file from the video library folder (`library/video/`) and
best-effort cleans up its associated `.jpg` thumbnail in `library/thumbnails/`.

The endpoint only deletes files directly inside `library/video/`. Path-traversal
attempts (e.g. `../`, leading slashes, backslash separators, or nested
subdirectories) and non-`.mp4` names all resolve to a uniform `404` error.

### Path parameters

| Parameter | Type   | Description                             |
| --------- | ------ | --------------------------------------- |
| `name`    | string | The `.mp4` file name to delete (no path). |

### Response — `204 No Content`

Empty body. The video file and its thumbnail (if present) have been deleted.

### Response — `404 Not Found`

Returned when the file is missing, the name is not a `.mp4`, or the resolved
path escapes `library/video`.

```json
{
  "detail": "Video not found"
}
```

### Example

```bash
curl -X DELETE http://127.0.0.1:8787/library/video/clip.mp4
```

## `POST /jobs`

Accepts a YouTube URL and initializes a pending download job. Returns the new
job's id, url, status, and mode. The job is stored in an in-memory store (jobs
are lost on server restart until durable persistence is added).

Non-YouTube URLs are rejected with HTTP 422 (`"Only YouTube URLs are accepted"`).

### Request body

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "mode": "audio"
}
```

| Field | Type   | Description                                                                                       |
| ----- | ------ | ------------------------------------------------------------------------------------------------- |
| `url` | string | A valid HTTP(S) URL of the media to download (must be a YouTube host).                            |
| `mode`| string | Optional download format: `"audio"` (default) extracts an MP3; `"video"` downloads an MP4. Unknown values are rejected with HTTP 422. |

### Response — `201 Created`

```json
{
  "id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "status": "pending",
  "mode": "audio"
}
```

| Field    | Type   | Description                                          |
| -------- | ------ | ---------------------------------------------------- |
| `id`     | string | Unique job identifier (UUID hex).                    |
| `url`    | string | The source URL submitted with the job.               |
| `status` | string | Current lifecycle status (see statuses below).       |
| `mode`   | string | Download format recorded on the job (`"audio"` or `"video"`). |

### Job statuses

| Status       | Description                                              |
| ------------ | -------------------------------------------------------- |
| `pending`    | Job created, waiting to be processed.                    |
| `downloading`| Download in progress.                                    |
| `completed`  | Download finished successfully.                          |
| `failed`     | Download failed.                                         |

### Example

```bash
curl -X POST http://127.0.0.1:8787/jobs \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

## `GET /jobs/{job_id}`

Returns the current status of a specific download job by its id.

### Path parameters

| Parameter | Type   | Description                       |
| --------- | ------ | --------------------------------- |
| `job_id`  | string | The UUID hex of the job to fetch. |

### Response — `200 OK`

```json
{
  "id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "status": "pending"
}
```

### Response — `404 Not Found`

Returned when no job exists for the given `job_id`.

```json
{
  "detail": "Job not found"
}
```

### Example

```bash
curl http://127.0.0.1:8787/jobs/a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4
```

## `POST /jobs/{job_id}/start`

Transitions a job from `pending` to `downloading`. This is currently a stub —
no real download is performed yet. The call is idempotent: re-invoking it on an
already-`downloading` or terminal-state job returns the current record unchanged.

### Path parameters

| Parameter | Type   | Description                       |
| --------- | ------ | --------------------------------- |
| `job_id`  | string | The UUID hex of the job to start. |

### Response — `200 OK`

```json
{
  "id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "status": "downloading"
}
```

### Response — `404 Not Found`

Returned when no job exists for the given `job_id`.

```json
{
  "detail": "Job not found"
}
```

### Example

```bash
curl -X POST http://127.0.0.1:8787/jobs/a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4/start
```

## `DELETE /jobs/{job_id}`

Removes a job from the in-memory store. If job persistence is wired, the
matching SQLite `jobs` row is also removed best-effort; any database failure is
swallowed so the in-memory removal always succeeds.

### Path parameters

| Parameter | Type   | Description                        |
| --------- | ------ | ---------------------------------- |
| `job_id`  | string | The UUID hex of the job to delete. |

### Response — `204 No Content`

Empty body. The job has been removed from the store.

### Response — `404 Not Found`

Returned when no job exists for the given `job_id`.

```json
{
  "detail": "Job not found"
}
```

### Example

```bash
curl -X DELETE http://127.0.0.1:8787/jobs/a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4
```

## `DELETE /jobs/completed`

Clears all finished (`completed`) or failed (`failed`) download jobs from the job store.
Active (`pending` or `downloading`) jobs are preserved.

### Response — `200 OK`

```json
{
  "count": 3
}
```

| Field   | Type    | Description                                             |
| ------- | ------- | ------------------------------------------------------- |
| `count` | integer | Total number of completed/failed jobs removed.          |

### Example

```bash
curl -X DELETE http://127.0.0.1:8787/jobs/completed
```

## `POST /library/upload`

Accepts a single multipart file upload (form field `file`) and saves it to the
`library/uploads/` directory. The file is streamed to disk in 64 KiB chunks
(never fully buffered in memory) and a metadata row is inserted into the SQLite
database recording the filename, on-disk path, size, content type, and an
ISO-8601 `uploaded_at` timestamp.

If the metadata insert fails after the file has been written, the partial file
is removed so no orphan is left on disk. Uploads larger than 50 MiB are rejected
and the partial file is cleaned up.

### Request

Multipart form data with a single file field:

| Field  | Type   | Description                                |
| ------ | ------ | ------------------------------------------ |
| `file` | file   | The file to upload (any filename/type).    |

### Response — `201 Created`

```json
{
  "id": 1,
  "filename": "song.mp3",
  "path": "library/uploads/song.mp3",
  "size": 8192,
  "content_type": "audio/mpeg",
  "uploaded_at": "2026-07-14T12:34:56.789012+00:00"
}
```

| Field          | Type        | Description                                              |
| -------------- | ----------- | -------------------------------------------------------- |
| `id`           | integer     | Auto-incrementing metadata row id.                       |
| `filename`     | string      | Original filename from the upload.                       |
| `path`         | string      | On-disk path where the file was stored.                  |
| `size`         | integer     | File size in bytes.                                      |
| `content_type` | string\|null| MIME content type, or `null` if the client omitted it.  |
| `uploaded_at`  | string      | Timezone-aware ISO-8601 timestamp of the upload.         |

### Response — `413 Payload Too Large`

Returned when the upload exceeds the 50 MiB cap (`MAX_UPLOAD_BYTES`). No file
is written and no metadata row is created.

```json
{
  "detail": "Upload exceeds the maximum allowed size of 52428800 bytes"
}
```

### Response — `422 Unprocessable Entity`

Returned by FastAPI when the required `file` field is missing from the request.

### Example

```bash
curl -X POST http://127.0.0.1:8787/library/upload \
  -F "file=@song.mp3;type=audio/mpeg"
```

## `GET /library/uploads`

Returns uploaded items recorded in the SQLite database, newest first (the
most recent upload appears at index 0). When the database file does not exist
yet, the endpoint returns an empty list rather than erroring, so it works before
any uploads have happened.

Results can be filtered and paginated via optional query parameters. The
response always includes a `total` field reporting the number of rows matching
the filters **before** pagination is applied, which lets clients render
"X of Y" counters and decide whether to fetch more pages.

### Query parameters

All parameters are optional. Filters combine with AND; pagination applies after
filtering.

| Parameter | Type    | Default | Description                                                        |
| --------- | ------- | ------- | ------------------------------------------------------------------ |
| `tag`     | string  | _none_  | Only items that have this tag name attached.                       |
| `q`       | string  | _none_  | Only items whose `filename` contains the substring (case-insensitive). |
| `limit`   | integer | _none_  | Maximum number of matching items to return (`>= 0`).               |
| `offset`  | integer | `0`     | Number of matching items to skip before returning results (`>= 0`). |

### Response — `200 OK`

```json
{
  "items": [
    {
      "id": 2,
      "filename": "second.mp3",
      "path": "library/uploads/second.mp3",
      "size": 4,
      "content_type": "audio/mpeg",
      "uploaded_at": "2026-07-14T12:35:10.000111+00:00"
    },
    {
      "id": 1,
      "filename": "first.mp3",
      "path": "library/uploads/first.mp3",
      "size": 4,
      "content_type": "audio/mpeg",
      "uploaded_at": "2026-07-14T12:34:56.789012+00:00"
    }
  ],
  "total": 2
}
```

| Field                   | Type        | Description                                          |
| ----------------------- | ----------- | ---------------------------------------------------- |
| `items`                 | array       | List of upload records, newest first.                |
| `items[].id`            | integer     | Metadata row id.                                     |
| `items[].filename`      | string      | Original filename.                                   |
| `items[].path`          | string      | On-disk path where the file is stored.               |
| `items[].size`          | integer     | File size in bytes.                                  |
| `items[].content_type`  | string\|null| MIME content type, or `null`.                        |
| `items[].uploaded_at`   | string      | Timezone-aware ISO-8601 timestamp of the upload.     |
| `total`                 | integer     | Number of rows matching the filters before pagination. |

### Example

```bash
# All uploads
curl http://127.0.0.1:8787/library/uploads

# First page of 10 uploads tagged "music"
curl "http://127.0.0.1:8787/library/uploads?tag=music&limit=10&offset=0"
```

## `DELETE /library/metadata/{metadata_id}`

Deletes a metadata row along with its tag assignments and the underlying
uploaded file. This is the inverse of `POST /library/upload`: it removes the
SQLite `metadata` row, its `metadata_tags` join rows, and best-effort deletes
the file from `library/uploads/` (only when the stored path resolves inside the
uploads directory, so arbitrary paths cannot be unlinked).

Filesystem cleanup is best-effort: a missing or unreadable file does not undo
the metadata deletion or fail the request. Tag rows themselves are preserved on
detach so they can be reused by other items.

### Path parameters

| Parameter      | Type    | Description                          |
| -------------- | ------- | ------------------------------------ |
| `metadata_id`  | integer | The metadata row id to delete.       |

### Response — `204 No Content`

Empty body. The metadata row, its tag joins, and (best-effort) the file have
been removed.

### Response — `404 Not Found`

Returned when the database file does not exist yet or no row matches the id.

```json
{
  "detail": "Metadata row not found"
}
```

### Example

```bash
curl -X DELETE http://127.0.0.1:8787/library/metadata/3
```

## `POST /collections`

Creates a named collection in the database.

### Request body

```json
{
  "name": "Favorites"
}
```

| Field  | Type   | Description                            |
| ------ | ------ | -------------------------------------- |
| `name` | string | The name of the collection to create.  |

### Response — `201 Created`

```json
{
  "id": 1,
  "name": "Favorites"
}
```

| Field  | Type    | Description                   |
| ------ | ------- | ----------------------------- |
| `id`   | integer | Unique collection row id.     |
| `name` | string  | Collection name.              |

### Response — `409 Conflict`

Returned when a collection with the given name already exists.

### Response — `422 Unprocessable Entity`

Returned when `name` is empty or missing.

### Example

```bash
curl -X POST http://127.0.0.1:8787/collections \
  -H "Content-Type: application/json" \
  -d '{"name": "Favorites"}'
```

## `GET /collections`

Returns all collections sorted alphabetically by name.

### Response — `200 OK`

```json
{
  "items": [
    {
      "id": 1,
      "name": "Favorites"
    }
  ]
}
```

| Field   | Type  | Description                                |
| ------- | ----- | ------------------------------------------ |
| `items` | array | List of collection objects (`id`, `name`). |

### Example

```bash
curl http://127.0.0.1:8787/collections
```

## `DELETE /collections/{name}`

Deletes a collection by name and removes all of its associated item memberships from the database.

### Path parameters

| Parameter | Type   | Description                       |
| --------- | ------ | --------------------------------- |
| `name`    | string | Name of the collection to delete. |

### Response — `204 No Content`

Empty body. The collection and its join rows have been removed.

### Response — `404 Not Found`

Returned when no collection matches the given name.

```json
{
  "detail": "Collection not found"
}
```

### Example

```bash
curl -X DELETE http://127.0.0.1:8787/collections/Favorites
```

## `POST /collections/{name}/rename`

Renames an existing collection from `name` to a new name specified in the request body.

### Path parameters

| Parameter | Type   | Description                               |
| --------- | ------ | ----------------------------------------- |
| `name`    | string | Current name of the collection to rename. |

### Request body

```json
{
  "new_name": "Best Songs"
}
```

| Field      | Type   | Description                                  |
| ---------- | ------ | -------------------------------------------- |
| `new_name` | string | The new name for the collection (non-empty). |

### Response — `200 OK`

```json
{
  "id": 1,
  "name": "Best Songs"
}
```

| Field  | Type    | Description                   |
| ------ | ------- | ----------------------------- |
| `id`   | integer | Unique collection row id.     |
| `name` | string  | Updated collection name.      |

### Response — `404 Not Found`

Returned when the target collection does not exist.

```json
{
  "detail": "Collection not found"
}
```

### Response — `409 Conflict`

Returned when `new_name` collides with an existing collection.

```json
{
  "detail": "A collection with that name already exists"
}
```

### Response — `422 Unprocessable Entity`

Returned when `new_name` is blank or omitted.

```json
{
  "detail": "collection name must be a non-empty string"
}
```

### Example

```bash
curl -X POST http://127.0.0.1:8787/collections/Favorites/rename \
  -H "Content-Type: application/json" \
  -d '{"new_name": "Best Songs"}'
```

## `POST /collections/{name}/items`

Adds an uploaded item (by `metadata_id`) to a collection. Idempotent: adding an item that is already in the collection is a no-op.

### Path parameters

| Parameter | Type   | Description                                |
| --------- | ------ | ------------------------------------------ |
| `name`    | string | Name of the collection to add the item to. |

### Request body

```json
{
  "metadata_id": 1
}
```

| Field         | Type    | Description                             |
| ------------- | ------- | --------------------------------------- |
| `metadata_id` | integer | The ID of the uploaded metadata record. |

### Response — `201 Created`

```json
{
  "collection": {
    "id": 1,
    "name": "Favorites"
  },
  "items": [
    {
      "id": 1,
      "filename": "track.mp3",
      "path": "library/uploads/track.mp3",
      "size": 10240,
      "content_type": "audio/mpeg",
      "uploaded_at": "2026-07-29T10:00:00Z"
    }
  ]
}
```

### Response — `404 Not Found`

Returned when the collection or metadata record is not found.

### Example

```bash
curl -X POST http://127.0.0.1:8787/collections/Favorites/items \
  -H "Content-Type: application/json" \
  -d '{"metadata_id": 1}'
```

## `GET /collections/{name}/items`

Lists all items in a collection, newest first.

### Path parameters

| Parameter | Type   | Description                        |
| --------- | ------ | ---------------------------------- |
| `name`    | string | Name of the collection to inspect. |

### Response — `200 OK`

```json
{
  "collection": {
    "id": 1,
    "name": "Favorites"
  },
  "items": [
    {
      "id": 1,
      "filename": "track.mp3",
      "path": "library/uploads/track.mp3",
      "size": 10240,
      "content_type": "audio/mpeg",
      "uploaded_at": "2026-07-29T10:00:00Z"
    }
  ]
}
```

### Response — `404 Not Found`

Returned when the collection does not exist.

### Example

```bash
curl http://127.0.0.1:8787/collections/Favorites/items
```

## `DELETE /collections/{name}/items/{metadata_id}`

Removes an item from a collection. Idempotent: removing an item that is not in the collection is a no-op.

### Path parameters

| Parameter     | Type    | Description                                     |
| ------------- | ------- | ----------------------------------------------- |
| `name`        | string  | Name of the collection.                         |
| `metadata_id` | integer | The ID of the uploaded metadata item to remove. |

### Response — `200 OK`

Returns the collection object and its remaining item list.

### Response — `404 Not Found`

Returned when the collection does not exist.

### Example

```bash
curl -X DELETE http://127.0.0.1:8787/collections/Favorites/items/1
```

## Notes

- Read-only endpoints (`GET`) require no authentication.
- `POST /jobs` currently stores jobs in memory only (cleared on restart).
- CORS is enabled for the configured local web frontends.
