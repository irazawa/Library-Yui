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

## Notes

- Endpoints are read-only and require no authentication.
- CORS is enabled for the configured local web frontends.
