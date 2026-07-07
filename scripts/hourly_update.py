from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRESS = ROOT / "docs" / "PROGRESS.md"


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
    )


def main() -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_stamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    run(["git", "config", "user.name", "irazawa"])
    run(["git", "config", "user.email", "irazawa@users.noreply.github.com"])

    pull = run(["git", "pull", "--rebase", "--autostash", "origin", "main"], check=False)

    entry = f"""
## {stamp} — Hourly Slow Progress

- Current focus: continue Library-Yui with small real improvements.
- Status: repository skeleton is online; next implementation remains MVP 1 audio download queue.
- Next small step: add the smallest visible API or UI improvement before the next push.
"""
    with PROGRESS.open("a", encoding="utf-8") as file:
        file.write(entry)

    run(["git", "add", "docs/PROGRESS.md"])
    diff = run(["git", "diff", "--cached", "--quiet"], check=False)
    if diff.returncode == 0:
        print("## Library-Yui Hourly Update\n- No content changes to commit.")
        return

    commit_message = f"docs: update progress log {commit_stamp}"
    commit = run(["git", "commit", "-m", commit_message], check=False)
    if commit.returncode != 0:
        print("## Library-Yui Hourly Update\n- Commit failed.\n```\n" + commit.stdout[-1200:] + "\n```")
        return

    push = run(["git", "push", "origin", "main"], check=False)
    status = run(["git", "status", "--short", "--branch"], check=False).stdout.strip()
    last_commit = run(["git", "log", "-1", "--oneline"], check=False).stdout.strip()

    print("## Library-Yui Hourly Update")
    print(f"- **Time:** {stamp}")
    print(f"- **Commit:** `{last_commit}`")
    print(f"- **Push:** {'ok' if push.returncode == 0 else 'failed'}")
    print(f"- **Git:** `{status}`")
    print("- **Next small step:** add MVP 1 audio download queue skeleton.")
    if pull.returncode != 0:
        print("- **Pull note:** rebase/autostash had a warning; check repo before larger edits.")
    if push.returncode != 0:
        print("```")
        print(push.stdout[-1200:])
        print("```")


if __name__ == "__main__":
    main()
