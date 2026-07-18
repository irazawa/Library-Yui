"""MP3 downloader module for Library-Yui.

Ports the core MP3 download approach from the legacy ``Downloader.py`` into
the Library-Yui backend. Downloads are gated behind a feature flag so the
behavior can be turned on or off without code changes.

This module is intentionally self-contained and is *not* wired into the job
flow yet; it only provides the building blocks (command builder + run helper)
for a future iteration. See ``docs/plans/slow-tasks.md``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from app.storage import AUDIO_DIR, THUMBNAILS_DIR, VIDEO_DIR

# Environment variable name used as the real-download feature flag.
DOWNLOADS_ENABLED_FLAG = "LIBRARY_YUI_DOWNLOADS_ENABLED"

# Default seek offset (seconds) at which the thumbnail frame is sampled.
DEFAULT_THUMBNAIL_OFFSET = 1.0
# Default max width for extracted thumbnails; height keeps aspect ratio.
DEFAULT_THUMBNAIL_WIDTH = 320


def is_downloads_enabled() -> bool:
    """Return whether the real-download feature flag is enabled.

    Disabled by default. Enable by setting the environment variable to one of
    ``1``, ``true``, or ``yes`` (case-insensitive). Keeping downloads off by
    default avoids unexpected subprocess calls during development and tests.
    """

    return os.environ.get(DOWNLOADS_ENABLED_FLAG, "").lower() in {"1", "true", "yes"}


def _audio_args(output_dir: Path) -> list[str]:
    """Build yt-dlp audio extraction args targeting MP3.

    Mirrors the legacy ``Downloader.py`` conventions: best-audio extraction
    (``ba/b``), forced MP3 format, audio quality ``3`` (VBR ~175 kbps), and
    ``--no-playlist`` for single-track downloads. The output filename uses the
    video title and is written directly into *output_dir*.
    """

    output_template = str(output_dir / "%(title)s.%(ext)s")
    return [
        "-o", output_template,
        "-f", "ba/b",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "3",
        "--no-playlist",
    ]


def _video_args(output_dir: Path) -> list[str]:
    """Build yt-dlp video download args targeting MP4.

    Mirrors the legacy ``Downloader.py`` conventions for video: best video +
    best audio (``bv*+ba/b``), merged into an MP4 container, and
    ``--no-playlist`` for single-item downloads. The output filename uses the
    video title and is written directly into *output_dir*.
    """

    output_template = str(output_dir / "%(title)s.%(ext)s")
    return [
        "-o", output_template,
        "-f", "bv*+ba/b",
        "--merge-output-format", "mp4",
        "--no-playlist",
    ]


def build_mp3_command(url: str, output_dir: Path = AUDIO_DIR) -> list[str]:
    """Build the full yt-dlp command to download a single URL as MP3.

    Uses a ``yt-dlp`` executable resolved from ``PATH`` (falling back to
    ``yt-dlp.exe`` on Windows when not found) and applies the same sensible
    defaults as the legacy downloader: ``--ignore-errors`` and ``-N 8``
    concurrent fragment downloads.
    """

    yt_dlp = shutil.which("yt-dlp") or "yt-dlp.exe"
    return [
        yt_dlp,
        "--ignore-errors",
        "-N", "8",
        *_audio_args(output_dir),
        url,
    ]


def download_mp3(url: str, output_dir: Path = AUDIO_DIR) -> dict:
    """Download a single YouTube URL as MP3 into *output_dir*.

    Returns a result dict with keys ``ok`` (bool), ``returncode`` (int), and
    ``command`` (the executed argv list). Raises :class:`RuntimeError` when the
    feature flag is not enabled, so callers never trigger a real download by
    accident.
    """

    if not is_downloads_enabled():
        raise RuntimeError(
            "Downloads are disabled. Set the "
            f"{DOWNLOADS_ENABLED_FLAG} environment variable to '1' to "
            "enable real downloads."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    command = build_mp3_command(url, output_dir)
    result = subprocess.run(command)
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "command": command,
    }


def build_mp4_command(url: str, output_dir: Path = VIDEO_DIR) -> list[str]:
    """Build the full yt-dlp command to download a single URL as MP4.

    Mirrors :func:`build_mp3_command` but with the legacy video conventions:
    ``-f "bv*+ba/b"`` and ``--merge-output-format mp4``, writing into
    *output_dir* (defaults to ``VIDEO_DIR``).
    """

    yt_dlp = shutil.which("yt-dlp") or "yt-dlp.exe"
    return [
        yt_dlp,
        "--ignore-errors",
        "-N", "8",
        *_video_args(output_dir),
        url,
    ]


def download_mp4(url: str, output_dir: Path = VIDEO_DIR) -> dict:
    """Download a single YouTube URL as MP4 into *output_dir*.

    Same contract as :func:`download_mp3`: returns a result dict with keys
    ``ok`` (bool), ``returncode`` (int), and ``command`` (the executed argv
    list). Raises :class:`RuntimeError` when the feature flag is not enabled,
    so callers never trigger a real download by accident.
    """

    if not is_downloads_enabled():
        raise RuntimeError(
            "Downloads are disabled. Set the "
            f"{DOWNLOADS_ENABLED_FLAG} environment variable to '1' to "
            "enable real downloads."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    command = build_mp4_command(url, output_dir)
    result = subprocess.run(command)
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "command": command,
    }


def _is_thumbnail_flag_enabled() -> bool:
    """Return whether thumbnail extraction is enabled.

    Thumbnails reuse the same ``LIBRARY_YUI_DOWNLOADS_ENABLED`` flag as
    downloads so they cannot run by accident during development or tests.
    """

    return is_downloads_enabled()


def _resolve_ffmpeg() -> str | None:
    """Resolve the ffmpeg executable, returning ``None`` if missing.

    Uses :func:`shutil.which` to find ``ffmpeg`` (or ``ffmpeg.exe`` on
    Windows as a fallback). Returns ``None`` when ffmpeg is not installed,
    which makes thumbnail extraction a best-effort, non-fatal operation.
    """

    return shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")


def build_thumbnail_command(
    video_path: Path,
    output_path: Path,
    *,
    offset: float = DEFAULT_THUMBNAIL_OFFSET,
    width: int = DEFAULT_THUMBNAIL_WIDTH,
    ffmpeg: str = "ffmpeg",
) -> list[str]:
    """Build the ffmpeg argv to extract a single thumbnail frame.

    Samples one frame at *offset* seconds, scales to *width* keeping aspect
    ratio (``-1`` for height), and writes a single JPEG to *output_path*.
    Mirrors ffmpeg conventions: input path, seek, frames, scale filter,
    ``-update`` so a single file is produced.
    """

    return [
        ffmpeg,
        "-ss", f"{offset}",
        "-i", str(video_path),
        "-frames:v", "1",
        "-vf", f"scale={width}:-1",
        "-q:v", "3",
        "-y",
        "-update", "1",
        str(output_path),
    ]


def extract_thumbnail(
    video_path: Path,
    *,
    output_dir: Path = THUMBNAILS_DIR,
    offset: float = DEFAULT_THUMBNAIL_OFFSET,
    width: int = DEFAULT_THUMBNAIL_WIDTH,
) -> dict:
    """Extract a single thumbnail JPEG from *video_path*.

    Writes ``<output_dir>/<video-stem>.jpg``. Best-effort: returns a result
    dict (``ok``, ``skipped``, ``path``, ``returncode``, ``command``) and
    never raises. Skips silently when:

    - The feature flag is off (``ok=False, skipped=True``).
    - ffmpeg is not on PATH (``ok=False, skipped=True``).
    - The input video file does not exist (``ok=False, skipped=True``).

    On ffmpeg failure the partial output file (if any) is removed so the
    thumbnails folder is not left with garbage.
    """

    result: dict = {
        "ok": False,
        "skipped": False,
        "path": None,
        "returncode": None,
        "command": None,
    }

    if not _is_thumbnail_flag_enabled():
        result["skipped"] = True
        result["ok"] = False
        return result

    ffmpeg = _resolve_ffmpeg()
    if ffmpeg is None:
        result["skipped"] = True
        result["ok"] = False
        return result

    if not Path(video_path).is_file():
        result["skipped"] = True
        result["ok"] = False
        return result

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / (Path(video_path).stem + ".jpg")

    command = build_thumbnail_command(
        Path(video_path),
        output_path,
        offset=offset,
        width=width,
        ffmpeg=ffmpeg,
    )
    completed = subprocess.run(command)
    result["returncode"] = completed.returncode
    result["command"] = command
    result["ok"] = completed.returncode == 0 and output_path.is_file()

    # Clean up partial output on failure so we never leak garbage.
    if not result["ok"] and output_path.exists():
        try:
            output_path.unlink()
        except OSError:
            pass

    if result["ok"]:
        result["path"] = str(output_path)
    else:
        result["skipped"] = True

    return result
