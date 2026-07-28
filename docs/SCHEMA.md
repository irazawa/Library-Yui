# Library-Yui Database Schema

This document details the SQLite database schema used by Library-Yui. The database file lives at `apps/api/data/library.db` and is initialized and managed by `apps/api/app/database.py` via `init_db()`.

## Tables Summary

| Table | Purpose | Primary Key |
| --- | --- | --- |
| `metadata` | Media item file metadata (uploads & downloads) | `id` (AUTOINCREMENT) |
| `tags` | Unique tag names | `id` (AUTOINCREMENT) |
| `metadata_tags` | Many-to-many join table connecting `metadata` and `tags` | `(metadata_id, tag_id)` |
| `collections` | Named collections for grouping media items | `id` (AUTOINCREMENT) |
| `collection_items` | Many-to-many join table connecting `collections` and `metadata` | `(collection_id, metadata_id)` |
| `jobs` | Async download job lifecycle records | `id` (UUID string) |

---

## Detailed Table Definitions

### 1. `metadata`

Stores metadata for files uploaded by users or produced by download jobs.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique row identifier |
| `filename` | TEXT | NOT NULL | Display filename (e.g. `track.mp3`) |
| `path` | TEXT | NOT NULL | Stored filesystem path |
| `size` | INTEGER | NOT NULL | File size in bytes |
| `content_type` | TEXT | NULLABLE | MIME type (e.g. `audio/mpeg`, `video/mp4`) |
| `uploaded_at` | TEXT | NOT NULL | ISO-8601 UTC timestamp of record creation |

### 2. `tags`

Stores distinct tag names used to categorize media metadata rows.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique tag identifier |
| `name` | TEXT | NOT NULL UNIQUE | Case-preserved tag string |

### 3. `metadata_tags`

Junction table mapping tags to media metadata entries.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `metadata_id` | INTEGER | NOT NULL REFERENCES `metadata(id)` ON DELETE CASCADE | Target metadata row id |
| `tag_id` | INTEGER | NOT NULL REFERENCES `tags(id)` ON DELETE CASCADE | Target tag id |

- **Primary Key:** `(metadata_id, tag_id)`

### 4. `collections`

Stores named groupings for organizing media items into custom collections.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique collection identifier |
| `name` | TEXT | NOT NULL UNIQUE | Unique collection name |

### 5. `collection_items`

Junction table mapping media metadata entries into collections.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `collection_id` | INTEGER | NOT NULL REFERENCES `collections(id)` ON DELETE CASCADE | Target collection id |
| `metadata_id` | INTEGER | NOT NULL REFERENCES `metadata(id)` ON DELETE CASCADE | Target metadata row id |

- **Primary Key:** `(collection_id, metadata_id)`
- **Indexes:** `idx_collection_items_unique` (UNIQUE INDEX on `(collection_id, metadata_id)`)

### 6. `jobs`

Persists download job status and parameters across process restarts.

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | TEXT | PRIMARY KEY | Unique job UUID string |
| `url` | TEXT | NOT NULL | Target YouTube video URL |
| `mode` | TEXT | NOT NULL | Download format (`audio` \| `video`) |
| `status` | TEXT | NOT NULL | Job state (`pending` \| `downloading` \| `completed` \| `failed`) |
| `created_at` | TEXT | NOT NULL | ISO-8601 UTC timestamp of job creation |
| `updated_at` | TEXT | NOT NULL | ISO-8601 UTC timestamp of last status update |

---

## Entity Relationships

```
[metadata] 1 ───< [metadata_tags] >─── 1 [tags]
[collections] 1 ───< [collection_items] >─── 1 [metadata]

[jobs] (Standalone entity for download queue state)
```
