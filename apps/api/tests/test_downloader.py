import sys
from pathlib import Path

import pytest

from app import downloader
from app.downloader import (
    AUDIO_DIR,
    DOWNLOADS_ENABLED_FLAG,
    THUMBNAILS_DIR,
    VIDEO_DIR,
    build_mp3_command,
    build_mp4_command,
    build_thumbnail_command,
    download_mp3,
    download_mp4,
    extract_thumbnail,
    is_downloads_enabled,
)


def _drop_self_from_argv() -> None:
    """Remove the current module path from sys.argv so subprocess calls (which
    we never actually execute here) wouldn't misinterpret pytest args."""
    sys.argv = sys.argv[:1]


def test_flag_disabled_by_default(monkeypatch):
    monkeypatch.delenv(DOWNLOADS_ENABLED_FLAG, raising=False)
    assert is_downloads_enabled() is False


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "Yes"])
def test_flag_enabled(monkeypatch, value):
    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, value)
    assert is_downloads_enabled() is True


@pytest.mark.parametrize("value", ["", "0", "false", "no", "random"])
def test_flag_disabled_other_values(monkeypatch, value):
    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, value)
    assert is_downloads_enabled() is False


def test_build_mp3_command_conventions(tmp_path):
    cmd = build_mp3_command("https://youtu.be/test", output_dir=tmp_path)
    # yt-dlp binary is the first element.
    assert cmd[0] in ("yt-dlp", "yt-dlp.exe") or "yt-dlp" in cmd[0]
    # Legacy conventions ported from Downloader.py.
    assert "--ignore-errors" in cmd
    assert "-N" in cmd and "8" in cmd
    assert "--no-playlist" in cmd
    assert "--audio-format" in cmd and "mp3" in cmd
    assert "--audio-quality" in cmd and "3" in cmd
    assert "-f" in cmd and "ba/b" in cmd
    # The URL is the last positional argument.
    assert cmd[-1] == "https://youtu.be/test"
    # Output template points into the provided dir.
    out_index = cmd.index("-o")
    assert str(tmp_path) in cmd[out_index + 1]
    assert "%(title)s.%(ext)s" in cmd[out_index + 1]


def test_build_mp3_command_defaults_to_audio_dir():
    cmd = build_mp3_command("https://youtu.be/test")
    out_index = cmd.index("-o")
    assert str(AUDIO_DIR) in cmd[out_index + 1]


def test_download_raises_when_disabled(monkeypatch, tmp_path):
    _drop_self_from_argv()
    monkeypatch.delenv(DOWNLOADS_ENABLED_FLAG, raising=False)
    with pytest.raises(RuntimeError, match="disabled"):
        download_mp3("https://youtu.be/test", output_dir=tmp_path)


def test_download_invokes_subprocess_when_enabled(monkeypatch, tmp_path):
    _drop_self_from_argv()
    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")

    captured = {}

    class FakeResult:
        returncode = 0

    def fake_run(command):
        captured["command"] = command
        return FakeResult()

    monkeypatch.setattr(downloader.subprocess, "run", fake_run)
    result = download_mp3("https://youtu.be/abc", output_dir=tmp_path)

    assert result["ok"] is True
    assert result["returncode"] == 0
    assert captured["command"][-1] == "https://youtu.be/abc"
    assert "--no-playlist" in captured["command"]
    # Output dir was created by download_mp3.
    assert tmp_path.is_dir()


def test_build_mp4_command_conventions(tmp_path):
    cmd = build_mp4_command("https://youtu.be/test", output_dir=tmp_path)
    # yt-dlp binary is the first element.
    assert cmd[0] in ("yt-dlp", "yt-dlp.exe") or "yt-dlp" in cmd[0]
    # Legacy video conventions ported from Downloader.py.
    assert "--ignore-errors" in cmd
    assert "-N" in cmd and "8" in cmd
    assert "--no-playlist" in cmd
    assert "-f" in cmd and "bv*+ba/b" in cmd
    assert "--merge-output-format" in cmd and "mp4" in cmd
    # No audio-extraction flags on the video path.
    assert "-x" not in cmd
    assert "--audio-format" not in cmd
    # The URL is the last positional argument.
    assert cmd[-1] == "https://youtu.be/test"
    # Output template points into the provided dir.
    out_index = cmd.index("-o")
    assert str(tmp_path) in cmd[out_index + 1]
    assert "%(title)s.%(ext)s" in cmd[out_index + 1]


def test_build_mp4_command_defaults_to_video_dir():
    cmd = build_mp4_command("https://youtu.be/test")
    out_index = cmd.index("-o")
    assert str(VIDEO_DIR) in cmd[out_index + 1]


def test_download_mp4_raises_when_disabled(monkeypatch, tmp_path):
    _drop_self_from_argv()
    monkeypatch.delenv(DOWNLOADS_ENABLED_FLAG, raising=False)
    with pytest.raises(RuntimeError, match="disabled"):
        download_mp4("https://youtu.be/test", output_dir=tmp_path)


def test_download_mp4_invokes_subprocess_when_enabled(monkeypatch, tmp_path):
    _drop_self_from_argv()
    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")

    captured = {}

    class FakeResult:
        returncode = 0

    def fake_run(command):
        captured["command"] = command
        return FakeResult()

    monkeypatch.setattr(downloader.subprocess, "run", fake_run)
    result = download_mp4("https://youtu.be/abc", output_dir=tmp_path)

    assert result["ok"] is True
    assert result["returncode"] == 0
    assert captured["command"][-1] == "https://youtu.be/abc"
    assert "--merge-output-format" in captured["command"]
    assert "mp4" in captured["command"]
    # Output dir was created by download_mp4.
    assert tmp_path.is_dir()


# --------------------------------------------------------------------------
# Thumbnail extraction (ffmpeg, flag-gated, best-effort)
# --------------------------------------------------------------------------


def test_build_thumbnail_command_conventions(tmp_path):
    video_path = tmp_path / "clip.mp4"
    output_path = tmp_path / "out" / "clip.jpg"
    cmd = build_thumbnail_command(video_path, output_path)

    # ffmpeg binary is the first element.
    assert cmd[0] == "ffmpeg"
    # Seek offset is the default 1.0s.
    ss_index = cmd.index("-ss")
    assert cmd[ss_index + 1] == "1.0"
    # Input path.
    i_index = cmd.index("-i")
    assert cmd[i_index + 1] == str(video_path)
    # Single frame, scale filter with default width.
    assert "-frames:v" in cmd and cmd[cmd.index("-frames:v") + 1] == "1"
    vf_index = cmd.index("-vf")
    assert cmd[vf_index + 1] == "scale=320:-1"
    # Output path is the last positional argument.
    assert cmd[-1] == str(output_path)
    # ``-update 1`` ensures a single JPEG file rather than a sequence.
    upd_index = cmd.index("-update")
    assert cmd[upd_index + 1] == "1"


def test_build_thumbnail_command_custom_args(tmp_path):
    video_path = tmp_path / "v.mp4"
    output_path = tmp_path / "v.jpg"
    cmd = build_thumbnail_command(
        video_path,
        output_path,
        offset=5.5,
        width=640,
        ffmpeg="/usr/local/bin/ffmpeg",
    )
    assert cmd[0] == "/usr/local/bin/ffmpeg"
    assert cmd[cmd.index("-ss") + 1] == "5.5"
    assert cmd[cmd.index("-vf") + 1] == "scale=640:-1"


def test_extract_thumbnail_skipped_when_flag_disabled(monkeypatch, tmp_path):
    _drop_self_from_argv()
    monkeypatch.delenv(DOWNLOADS_ENABLED_FLAG, raising=False)

    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")

    result = extract_thumbnail(video, output_dir=tmp_path / "thumbs")

    assert result["ok"] is False
    assert result["skipped"] is True
    assert result["path"] is None
    # No output produced and no subprocess call made.
    assert not (tmp_path / "thumbs").exists() or not list((tmp_path / "thumbs").iterdir())


def test_extract_thumbnail_skipped_when_ffmpeg_missing(monkeypatch, tmp_path):
    _drop_self_from_argv()
    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")
    # Simulate ffmpeg not installed.
    monkeypatch.setattr(downloader.shutil, "which", lambda name: None)

    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")

    result = extract_thumbnail(video, output_dir=tmp_path / "thumbs")

    assert result["ok"] is False
    assert result["skipped"] is True
    assert result["path"] is None


def test_extract_thumbnail_skipped_when_video_missing(monkeypatch, tmp_path):
    _drop_self_from_argv()
    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")
    # ffmpeg is "installed" for the resolution check.
    monkeypatch.setattr(downloader.shutil, "which", lambda name: "/fake/ffmpeg")

    result = extract_thumbnail(tmp_path / "does-not-exist.mp4", output_dir=tmp_path / "thumbs")

    assert result["ok"] is False
    assert result["skipped"] is True
    assert result["path"] is None


def test_extract_thumbnail_invokes_ffmpeg_when_enabled(monkeypatch, tmp_path):
    _drop_self_from_argv()
    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")
    monkeypatch.setattr(downloader.shutil, "which", lambda name: "/fake/ffmpeg")

    video = tmp_path / "clip.mp4"
    video.write_bytes(b"fake mp4 bytes")

    captured = {}

    class FakeCompleted:
        returncode = 0

    def fake_run(command):
        captured["command"] = command
        # Simulate ffmpeg producing the output file.
        # The output path is the last element of the command.
        Path(command[-1]).write_bytes(b"jpeg bytes")
        return FakeCompleted()

    monkeypatch.setattr(downloader.subprocess, "run", fake_run)

    result = extract_thumbnail(video, output_dir=tmp_path / "thumbs")

    assert result["ok"] is True
    assert result["skipped"] is False
    assert result["returncode"] == 0
    # Output filename is the video stem + .jpg.
    expected_path = (tmp_path / "thumbs" / "clip.jpg")
    assert result["path"] == str(expected_path)
    assert expected_path.is_file()
    # ffmpeg was invoked correctly.
    assert captured["command"][0] == "/fake/ffmpeg"
    assert captured["command"][cmd_index(captured["command"], "-i") + 1] == str(video)


def test_extract_thumbnail_cleans_up_partial_on_failure(monkeypatch, tmp_path):
    _drop_self_from_argv()
    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")
    monkeypatch.setattr(downloader.shutil, "which", lambda name: "/fake/ffmpeg")

    video = tmp_path / "clip.mp4"
    video.write_bytes(b"fake mp4 bytes")

    class FakeCompleted:
        returncode = 1  # ffmpeg failed

    def fake_run(command):
        # ffmpeg writes a partial file before failing.
        Path(command[-1]).write_bytes(b"partial")
        return FakeCompleted()

    monkeypatch.setattr(downloader.subprocess, "run", fake_run)

    result = extract_thumbnail(video, output_dir=tmp_path / "thumbs")

    assert result["ok"] is False
    assert result["skipped"] is True
    assert result["returncode"] == 1
    # Partial file removed.
    assert not (tmp_path / "thumbs" / "clip.jpg").exists()


def test_extract_thumbnail_defaults_to_thumbnails_dir(monkeypatch, tmp_path):
    _drop_self_from_argv()
    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")
    monkeypatch.setattr(downloader.shutil, "which", lambda name: "/fake/ffmpeg")

    video = tmp_path / "clip.mp4"
    video.write_bytes(b"fake mp4 bytes")

    captured = {}

    class FakeCompleted:
        returncode = 0

    def fake_run(command):
        captured["command"] = command
        Path(command[-1]).write_bytes(b"jpeg bytes")
        return FakeCompleted()

    monkeypatch.setattr(downloader.subprocess, "run", fake_run)

    result = extract_thumbnail(video)

    # Output path defaults to THUMBNAILS_DIR/<stem>.jpg.
    expected_path = THUMBNAILS_DIR / "clip.jpg"
    assert result["path"] == str(expected_path)
    # The command output path points at THUMBNAILS_DIR.
    out_path = Path(captured["command"][-1])
    assert out_path == expected_path


def cmd_index(command: list[str], token: str) -> int:
    """Helper: find the index of *token* in *command*; raises if missing."""
    return command.index(token)
