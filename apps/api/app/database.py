"""SQLite database initialization and connection helpers for Library-Yui.

This module sets up the metadata database that will store information about
uploaded and downloaded media. The database lives at
``apps/api/data/library.db`` and is created lazily by :func:`init_db`.

Keeping the database logic in one place makes it easy to reuse across routes
and to override the database path during tests.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Repository root: apps/api/app/database.py -> up three levels.
REPO_ROOT = Path(__file__).resolve().parents[3]

# Directory that holds the SQLite database file. Matches the existing
# ``apps/api/data/`` folder (already present with a .gitkeep).
DATA_DIR = REPO_ROOT / "apps" / "api" / "data"

# Default database file path. Tests may override this via the ``db_path``
# argument of :func:`init_db` / :func:`get_connection`.
DEFAULT_DB_PATH = DATA_DIR / "library.db"


def get_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open and return a SQLite connection to *db_path*.

    ``check_same_thread`` is disabled so the connection can be shared across
    the FastAPI request thread pool. Row access is configured to behave like a
    mapping (``row["column"]``) for convenience.
    """

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Create the database file and core tables if missing.

    Safe to call repeatedly; existing tables are left untouched. The
    ``metadata`` table stores one row per uploaded or downloaded media item.

    ``metadata`` columns:
        - ``id``: auto-increment primary key.
        - ``filename``: original file name (e.g. ``song.mp3``).
        - ``path``: filesystem path of the stored file.
        - ``size``: file size in bytes.
        - ``content_type``: MIME type (e.g. ``audio/mpeg``), nullable.
        - ``uploaded_at``: ISO-8601 UTC timestamp of insertion.

    ``tags`` columns (collections / MVP 3):
        - ``id``: auto-increment primary key.
        - ``name``: unique tag name.

    ``metadata_tags`` join table:
        - ``metadata_id``: references ``metadata.id``.
        - ``tag_id``: references ``tags.id``.
        - Primary key on ``(metadata_id, tag_id)`` keeps assignments unique.
    """

    connection = get_connection(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                size INTEGER NOT NULL,
                content_type TEXT,
                uploaded_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata_tags (
                metadata_id INTEGER NOT NULL REFERENCES metadata(id) ON DELETE CASCADE,
                tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
                PRIMARY KEY (metadata_id, tag_id)
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""

    return datetime.now(timezone.utc).isoformat()


def insert_metadata(
    *,
    filename: str,
    path: str,
    size: int,
    content_type: str | None = None,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> int:
    """Insert a metadata row and return the new row id.

    This is a small convenience helper used by the upload flow. The
    ``uploaded_at`` timestamp is filled in automatically.
    """

    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO metadata (filename, path, size, content_type, uploaded_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (filename, path, size, content_type, _now_iso()),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def list_metadata(db_path: Path | str = DEFAULT_DB_PATH) -> list[dict]:
    """Return all metadata rows as a list of dicts, newest first."""

    connection = get_connection(db_path)
    try:
        rows = connection.execute(
            "SELECT id, filename, path, size, content_type, uploaded_at "
            "FROM metadata ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
