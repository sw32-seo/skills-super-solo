from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from paths import markdown_link

HEADER = "# Directory Update Log"


def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def append_log(root: Path, kind: str, message: str, target: Path | None = None, scope: Path | None = None) -> None:
    scope_dir = scope or root
    scope_dir.mkdir(parents=True, exist_ok=True)
    path = scope_dir / "log.md"
    date = today()
    if target is not None and "[" not in message:
        title = target.stem.replace("_", " ").title()
        link = markdown_link(path, target, root, "relative")
        message = f"{message} [{title}]({link})."
    bullet = f"* **{kind}**: {message}".rstrip()
    if not bullet.endswith("."):
        bullet += "."

    if path.exists():
        text = path.read_text(encoding="utf-8").rstrip() + "\n"
    else:
        text = f"{HEADER}\n"
    lines = text.splitlines()
    if not lines or lines[0].strip() != HEADER:
        lines.insert(0, HEADER)
    date_heading = f"## {date}"
    out: list[str] = []
    inserted = False
    i = 0
    while i < len(lines):
        out.append(lines[i])
        if lines[i].strip() == HEADER and not inserted:
            if i + 1 >= len(lines) or lines[i + 1].strip() != "":
                out.append("")
            if date_heading in [l.strip() for l in lines]:
                pass
            else:
                out.extend([date_heading, bullet, ""])
                inserted = True
        if lines[i].strip() == date_heading and not inserted:
            out.append(bullet)
            inserted = True
        i += 1
    if not inserted:
        out.extend(["", date_heading, bullet])
    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
