"""Storage path constants for Library-Yui library content.

All paths are relative to the repository root. The constants describe where
the API should look for (or persist) downloaded and uploaded media.

Keeping them in one place avoids scattering magic strings across the routes and
makes future configuration easier.
"""

from pathlib import Path

# Repository root: apps/api/app/storage.py -> up three levels.
REPO_ROOT = Path(__file__).resolve().parents[3]

# Base library directory that holds all media content.
LIBRARY_DIR = REPO_ROOT / "library"

# Per-content-type storage folders.
AUDIO_DIR = LIBRARY_DIR / "audio"
VIDEO_DIR = LIBRARY_DIR / "video"
UPLOADS_DIR = LIBRARY_DIR / "uploads"
THUMBNAILS_DIR = LIBRARY_DIR / "thumbnails"

# Ordered mapping useful for summary/iteration tasks.
STORAGE_DIRS = {
    "audio": AUDIO_DIR,
    "video": VIDEO_DIR,
    "uploads": UPLOADS_DIR,
    "thumbnails": THUMBNAILS_DIR,
}


def ensure_storage_dirs() -> None:
    """Create the library storage directories if they do not exist yet.

    Safe to call repeatedly; existing directories are left untouched.
    """

    for directory in STORAGE_DIRS.values():
        directory.mkdir(parents=True, exist_ok=True)
