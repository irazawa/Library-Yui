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

## Notes

- Read-only endpoints (`GET`) require no authentication.
- `POST /jobs` currently stores jobs in memory only (cleared on restart).
- CORS is enabled for the configured local web frontends.
