import sys

import pytest

from app import downloader
from app.downloader import (
    AUDIO_DIR,
    DOWNLOADS_ENABLED_FLAG,
    build_mp3_command,
    download_mp3,
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
