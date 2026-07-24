# Library-Yui API Reference

Base URL (local dev): `http://127.0.0.1:8787`

The API is built with FastAPI. All responses are JSON.

Every endpoint is grouped under one of the following OpenAPI tags, which surface
as sections in the interactive docs (`/docs`, `/redoc`):

| Tag           | Scope                                                                  |
| ------------- | ---------------------------------------------------------------------- |
| `System`      | Liveness probes, version, and runtime config (`/health`, `/version`, `/config`). |
| `Jobs`        | Download job lifecycle (`/jobs`, `/jobs/{id}`, `/jobs/{id}/start`, `/jobs/{id}/complete`, `DELETE /jobs/{id}`). |
| `Library`     | Library listing, streaming, uploads, thumbnails, and summary.          |
| `Collections` | Tags, per-item metadata, and metadata deletion (tag assignment, search filters, metadata detail, `DELETE /library/metadata/{id}`). |

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

## `GET /library/audio`

Returns the names of MP3 files in the audio library folder, sorted alphabetically.
Only `.mp3` files are included. A missing directory returns an empty list.

Each item carries a best-effort `size` (bytes from the filesystem) and
`duration` (seconds, parsed from an MP4/MOV `moov`/`mvhd` container header
when present; `null` otherwise — never raises).

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
curl http://127.0.0.1:8787/library/audio
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

## Notes

- Read-only endpoints (`GET`) require no authentication.
- `POST /jobs` currently stores jobs in memory only (cleared on restart).
- CORS is enabled for the configured local web frontends.
