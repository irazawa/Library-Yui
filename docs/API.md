# Library-Yui API Reference

Base URL (local dev): `http://127.0.0.1:8787`

The API is built with FastAPI. All responses are JSON.

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

### Response — `200 OK`

```json
{
  "items": [
    { "name": "song-a.mp3" },
    { "name": "song-b.mp3" }
  ]
}
```

| Field               | Type   | Description                                         |
| ------------------- | ------ | --------------------------------------------------- |
| `items`             | array  | List of audio items.                                |
| `items[].name`      | string | File name of the MP3 (no path).                     |

### Example

```bash
curl http://127.0.0.1:8787/library/audio
```

## `POST /jobs`

Accepts a YouTube URL and initializes a pending download job. Returns the new
job's id, url, and status. The job is stored in an in-memory store (jobs are
lost on server restart until durable persistence is added).

### Request body

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

| Field | Type   | Description                                      |
| ----- | ------ | ------------------------------------------------ |
| `url` | string | A valid HTTP(S) URL of the media to download.    |

### Response — `201 Created`

```json
{
  "id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "status": "pending"
}
```

| Field    | Type   | Description                                          |
| -------- | ------ | ---------------------------------------------------- |
| `id`     | string | Unique job identifier (UUID hex).                    |
| `url`    | string | The source URL submitted with the job.               |
| `status` | string | Current lifecycle status (see statuses below).       |

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

Returns all uploaded items recorded in the SQLite database, newest first (the
most recent upload appears at index 0). When the database file does not exist
yet, the endpoint returns an empty list rather than erroring, so it works before
any uploads have happened.

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
  ]
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

### Example

```bash
curl http://127.0.0.1:8787/library/uploads
```

## Notes

- Read-only endpoints (`GET`) require no authentication.
- `POST /jobs` currently stores jobs in memory only (cleared on restart).
- CORS is enabled for the configured local web frontends.
