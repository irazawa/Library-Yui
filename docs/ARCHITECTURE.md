# Library-Yui Architecture

## Overview

Library-Yui is a small monorepo with one Python backend and two frontend apps.

```text
FastAPI API (8787)
  ├─ health endpoints
  ├─ library metadata endpoints
  ├─ download job endpoints
  └─ upload endpoints

Main Web (5174)
  ├─ download form
  ├─ library list
  └─ collection/tag views

Status Dashboard (5175)
  ├─ roadmap/progress view
  ├─ server status view
  └─ next task summary
```

## Storage

- SQLite database: `apps/api/data/library.db`
- Audio files: `library/audio/`
- Video files: `library/video/`
- User uploads: `library/uploads/`
- Thumbnails: `library/thumbnails/`

## Development Rule

Prefer small, real improvements over fake activity. Every commit should leave a visible artifact: code, docs, config, or working UI progress.
