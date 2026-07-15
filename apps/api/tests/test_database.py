import sqlite3
from pathlib import Path

from app import database


def test_init_db_creates_database_file(tmp_path):
    db_path = tmp_path / "library.db"

    database.init_db(db_path=db_path)

    assert Path(db_path).is_file()


def test_init_db_creates_metadata_table(tmp_path):
    db_path = tmp_path / "library.db"

    database.init_db(db_path=db_path)

    connection = sqlite3.connect(str(db_path))
    try:
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='metadata'"
        )
        tables = cursor.fetchall()
    finally:
        connection.close()

    assert tables == [("metadata",)]


def test_init_db_has_expected_columns(tmp_path):
    db_path = tmp_path / "library.db"

    database.init_db(db_path=db_path)

    connection = sqlite3.connect(str(db_path))
    try:
        cursor = connection.execute("PRAGMA table_info(metadata)")
        columns = {row[1] for row in cursor.fetchall()}
    finally:
        connection.close()

    assert columns == {"id", "filename", "path", "size", "content_type", "uploaded_at"}


def test_init_db_is_idempotent(tmp_path):
    db_path = tmp_path / "library.db"

    database.init_db(db_path=db_path)
    # Calling again must not raise.
    database.init_db(db_path=db_path)

    connection = sqlite3.connect(str(db_path))
    try:
        cursor = connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='metadata'"
        )
        count = cursor.fetchone()[0]
    finally:
        connection.close()

    assert count == 1


def test_init_db_creates_parent_directory(tmp_path):
    db_path = tmp_path / "nested" / "deep" / "library.db"

    database.init_db(db_path=db_path)

    assert Path(db_path).is_file()
    assert db_path.parent.is_dir()


def test_insert_metadata_returns_row_id(tmp_path):
    db_path = tmp_path / "library.db"
    database.init_db(db_path=db_path)

    row_id = database.insert_metadata(
        filename="song.mp3",
        path="/library/audio/song.mp3",
        size=1024,
        content_type="audio/mpeg",
        db_path=db_path,
    )

    assert isinstance(row_id, int)
    assert row_id > 0


def test_insert_metadata_persists_fields(tmp_path):
    db_path = tmp_path / "library.db"
    database.init_db(db_path=db_path)

    database.insert_metadata(
        filename="clip.mp3",
        path="/library/audio/clip.mp3",
        size=2048,
        content_type="audio/mpeg",
        db_path=db_path,
    )

    rows = database.list_metadata(db_path=db_path)

    assert len(rows) == 1
    row = rows[0]
    assert row["filename"] == "clip.mp3"
    assert row["path"] == "/library/audio/clip.mp3"
    assert row["size"] == 2048
    assert row["content_type"] == "audio/mpeg"
    assert row["uploaded_at"]
    # uploaded_at should be an ISO-8601 string containing timezone info.
    assert "T" in row["uploaded_at"]


def test_list_metadata_returns_newest_first(tmp_path):
    db_path = tmp_path / "library.db"
    database.init_db(db_path=db_path)

    first = database.insert_metadata(
        filename="first.mp3", path="a", size=1, db_path=db_path
    )
    second = database.insert_metadata(
        filename="second.mp3", path="b", size=2, db_path=db_path
    )

    rows = database.list_metadata(db_path=db_path)

    assert len(rows) == 2
    assert rows[0]["id"] == second
    assert rows[1]["id"] == first


def test_list_metadata_empty_when_no_rows(tmp_path):
    db_path = tmp_path / "library.db"
    database.init_db(db_path=db_path)

    rows = database.list_metadata(db_path=db_path)

    assert rows == []


def test_insert_metadata_allows_null_content_type(tmp_path):
    db_path = tmp_path / "library.db"
    database.init_db(db_path=db_path)

    row_id = database.insert_metadata(
        filename="unknown.bin", path="x", size=10, content_type=None, db_path=db_path
    )

    rows = database.list_metadata(db_path=db_path)
    assert len(rows) == 1
    assert rows[0]["id"] == row_id
    assert rows[0]["content_type"] is None


def test_init_db_preserves_existing_data(tmp_path):
    """Re-running init_db on an existing populated database must not wipe rows."""
    db_path = tmp_path / "library.db"
    database.init_db(db_path=db_path)
    database.insert_metadata(
        filename="keep.mp3", path="a", size=1, db_path=db_path
    )

    # Reinitialize — simulates an app restart.
    database.init_db(db_path=db_path)

    rows = database.list_metadata(db_path=db_path)
    assert len(rows) == 1
    assert rows[0]["filename"] == "keep.mp3"


def test_list_metadata_returns_plain_dicts(tmp_path):
    """Rows returned by list_metadata should be plain dicts, not sqlite3.Row."""
    db_path = tmp_path / "library.db"
    database.init_db(db_path=db_path)
    database.insert_metadata(filename="a.mp3", path="a", size=1, db_path=db_path)

    rows = database.list_metadata(db_path=db_path)

    assert len(rows) == 1
    assert isinstance(rows[0], dict)
    assert not isinstance(rows[0], sqlite3.Row)


def test_insert_metadata_multiple_increasing_ids(tmp_path):
    """Sequential inserts produce strictly increasing row ids."""
    db_path = tmp_path / "library.db"
    database.init_db(db_path=db_path)

    ids = [
        database.insert_metadata(filename=f"f{i}.mp3", path=f"p{i}", size=i, db_path=db_path)
        for i in range(3)
    ]

    assert ids == sorted(ids)
    assert len(set(ids)) == 3


def test_insert_metadata_accepts_zero_size(tmp_path):
    """A zero-byte file should still be recordable (size is NOT NULL but 0 is valid)."""
    db_path = tmp_path / "library.db"
    database.init_db(db_path=db_path)

    row_id = database.insert_metadata(
        filename="empty.mp3", path="e", size=0, db_path=db_path
    )

    rows = database.list_metadata(db_path=db_path)
    assert rows[0]["id"] == row_id
    assert rows[0]["size"] == 0


def test_insert_metadata_handles_unicode_filename(tmp_path):
    """Non-ASCII filenames and paths are stored and retrieved faithfully."""
    db_path = tmp_path / "library.db"
    database.init_db(db_path=db_path)

    database.insert_metadata(
        filename="日本語タイトル.mp3", path="/library/audio/日本語タイトル.mp3",
        size=512, content_type="audio/mpeg", db_path=db_path,
    )

    rows = database.list_metadata(db_path=db_path)
    assert len(rows) == 1
    assert rows[0]["filename"] == "日本語タイトル.mp3"
    assert rows[0]["path"] == "/library/audio/日本語タイトル.mp3"


def test_get_connection_creates_parent_directory(tmp_path):
    """get_connection alone (without init_db) must create missing parent dirs."""
    db_path = tmp_path / "nested" / "deep" / "library.db"
    assert not db_path.parent.exists()

    connection = database.get_connection(db_path)
    try:
        assert db_path.parent.is_dir()
    finally:
        connection.close()


def _table_names(db_path):
    connection = sqlite3.connect(str(db_path))
    try:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    finally:
        connection.close()
    return {row[0] for row in rows}


def test_init_db_creates_tags_and_join_tables(tmp_path):
    db_path = tmp_path / "library.db"

    database.init_db(db_path=db_path)

    tables = _table_names(db_path)
    assert "tags" in tables
    assert "metadata_tags" in tables


def test_tags_table_has_expected_columns(tmp_path):
    db_path = tmp_path / "library.db"
    database.init_db(db_path=db_path)

    connection = sqlite3.connect(str(db_path))
    try:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(tags)")}
    finally:
        connection.close()

    assert columns == {"id", "name"}


def test_metadata_tags_table_has_expected_columns(tmp_path):
    db_path = tmp_path / "library.db"
    database.init_db(db_path=db_path)

    connection = sqlite3.connect(str(db_path))
    try:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(metadata_tags)")
        }
    finally:
        connection.close()

    assert columns == {"metadata_id", "tag_id"}


def test_tags_name_is_unique(tmp_path):
    db_path = tmp_path / "library.db"
    database.init_db(db_path=db_path)

    connection = sqlite3.connect(str(db_path))
    try:
        connection.execute("INSERT INTO tags (name) VALUES ('music')")
        connection.commit()
        try:
            connection.execute("INSERT INTO tags (name) VALUES ('music')")
            connection.commit()
            duplicated = True
        except sqlite3.IntegrityError:
            duplicated = False
    finally:
        connection.close()

    assert duplicated is False


def test_metadata_tags_pair_is_unique(tmp_path):
    db_path = tmp_path / "library.db"
    database.init_db(db_path=db_path)
    metadata_id = database.insert_metadata(
        filename="song.mp3", path="p", size=1, db_path=db_path
    )

    connection = sqlite3.connect(str(db_path))
    try:
        cursor = connection.execute("INSERT INTO tags (name) VALUES ('music')")
        tag_id = cursor.lastrowid
        connection.execute(
            "INSERT INTO metadata_tags (metadata_id, tag_id) VALUES (?, ?)",
            (metadata_id, tag_id),
        )
        connection.commit()
        try:
            connection.execute(
                "INSERT INTO metadata_tags (metadata_id, tag_id) VALUES (?, ?)",
                (metadata_id, tag_id),
            )
            connection.commit()
            duplicated = True
        except sqlite3.IntegrityError:
            duplicated = False
    finally:
        connection.close()

    assert duplicated is False


def _make_item(db_path, filename="song.mp3"):
    database.init_db(db_path=db_path)
    return database.insert_metadata(
        filename=filename, path=f"/library/audio/{filename}", size=1, db_path=db_path
    )


def test_add_tag_to_metadata_creates_tag_row(tmp_path):
    db_path = tmp_path / "library.db"
    metadata_id = _make_item(db_path)

    database.add_tag_to_metadata(metadata_id, "music", db_path=db_path)

    assert database.list_tags_for_metadata(metadata_id, db_path=db_path) == ["music"]


def test_add_tag_to_metadata_is_idempotent(tmp_path):
    db_path = tmp_path / "library.db"
    metadata_id = _make_item(db_path)

    database.add_tag_to_metadata(metadata_id, "music", db_path=db_path)
    database.add_tag_to_metadata(metadata_id, "music", db_path=db_path)

    assert database.list_tags_for_metadata(metadata_id, db_path=db_path) == ["music"]


def test_add_tag_reuses_existing_tag_row(tmp_path):
    db_path = tmp_path / "library.db"
    first = _make_item(db_path, "a.mp3")
    second = database.insert_metadata(
        filename="b.mp3", path="/library/audio/b.mp3", size=2, db_path=db_path
    )

    database.add_tag_to_metadata(first, "music", db_path=db_path)
    database.add_tag_to_metadata(second, "music", db_path=db_path)

    connection = sqlite3.connect(str(db_path))
    try:
        count = connection.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    finally:
        connection.close()
    assert count == 1


def test_add_tag_strips_whitespace(tmp_path):
    db_path = tmp_path / "library.db"
    metadata_id = _make_item(db_path)

    database.add_tag_to_metadata(metadata_id, "  music  ", db_path=db_path)

    assert database.list_tags_for_metadata(metadata_id, db_path=db_path) == ["music"]


def test_add_tag_rejects_empty_string(tmp_path):
    db_path = tmp_path / "library.db"
    metadata_id = _make_item(db_path)

    try:
        database.add_tag_to_metadata(metadata_id, "   ", db_path=db_path)
        raised = False
    except ValueError:
        raised = True

    assert raised is True


def test_remove_tag_from_metadata(tmp_path):
    db_path = tmp_path / "library.db"
    metadata_id = _make_item(db_path)
    database.add_tag_to_metadata(metadata_id, "music", db_path=db_path)
    database.add_tag_to_metadata(metadata_id, "chill", db_path=db_path)

    database.remove_tag_from_metadata(metadata_id, "music", db_path=db_path)

    assert database.list_tags_for_metadata(metadata_id, db_path=db_path) == ["chill"]


def test_remove_tag_is_idempotent_and_keeps_tag_row(tmp_path):
    db_path = tmp_path / "library.db"
    metadata_id = _make_item(db_path)
    database.add_tag_to_metadata(metadata_id, "music", db_path=db_path)

    database.remove_tag_from_metadata(metadata_id, "music", db_path=db_path)
    # Second removal (and removal of a never-existing tag) must not raise.
    database.remove_tag_from_metadata(metadata_id, "music", db_path=db_path)
    database.remove_tag_from_metadata(metadata_id, "ghost", db_path=db_path)

    assert database.list_tags_for_metadata(metadata_id, db_path=db_path) == []
    connection = sqlite3.connect(str(db_path))
    try:
        count = connection.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    finally:
        connection.close()
    assert count == 1  # tag row is preserved for reuse


def test_list_tags_for_metadata_sorted(tmp_path):
    db_path = tmp_path / "library.db"
    metadata_id = _make_item(db_path)
    for tag in ("zeta", "alpha", "mid"):
        database.add_tag_to_metadata(metadata_id, tag, db_path=db_path)

    tags = database.list_tags_for_metadata(metadata_id, db_path=db_path)

    assert tags == ["alpha", "mid", "zeta"]


def test_init_db_migrates_existing_metadata_only_database(tmp_path):
    """init_db on a pre-tags database adds the new tables without data loss."""
    db_path = tmp_path / "library.db"

    # Simulate an old database that only had the metadata table.
    connection = sqlite3.connect(str(db_path))
    try:
        connection.execute(
            """
            CREATE TABLE metadata (
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
            "INSERT INTO metadata (filename, path, size, uploaded_at) "
            "VALUES ('old.mp3', 'p', 1, '2026-01-01T00:00:00+00:00')"
        )
        connection.commit()
    finally:
        connection.close()

    database.init_db(db_path=db_path)

    tables = _table_names(db_path)
    assert {"metadata", "tags", "metadata_tags"} <= tables
    rows = database.list_metadata(db_path=db_path)
    assert len(rows) == 1
    assert rows[0]["filename"] == "old.mp3"
