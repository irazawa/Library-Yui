from datetime import datetime
from pathlib import Path

root = Path(__file__).resolve().parents[1]
progress = root / "docs" / "PROGRESS.md"
stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
entry = f"
## {stamp} — Slow Progress Tick

- Current focus: keep Library-Yui moving with small real improvements.
- Status: inspect roadmap, choose one tiny implementation/doc task, then commit it.
- Next small step: make the next visible UI/API improvement.
"

with progress.open("a", encoding="utf-8") as file:
    file.write(entry)

print(f"Updated {progress}")
