from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from document import parse_markdown
from paths import HardFailure, is_reserved, markdown_link, validate_relative_md_path


def root_settings(root: Path) -> dict[str, Any]:
    index = root / "index.md"
    if index.exists():
        fm, _body, has = parse_markdown(index)
        if has:
            settings = dict(fm)
        else:
            settings = {}
    else:
        settings = {}
    settings.setdefault("okf_version", "0.1")
    settings.setdefault("link_style", "relative")
    return settings


def dump_root_settings(settings: dict[str, Any]) -> str:
    ordered = {}
    for key in ("okf_version", "link_style", "name"):
        if key in settings:
            ordered[key] = settings[key]
    for key, val in settings.items():
        if key not in ordered:
            ordered[key] = val
    return yaml.dump(ordered, allow_unicode=True, default_flow_style=False, sort_keys=False).rstrip()


def concept_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    files = []
    for path in root.rglob("*.md"):
        validate_relative_md_path(path, root)
        if not is_reserved(path):
            files.append(path)
    return sorted(files)


def dirs_with_markdown(root: Path) -> list[Path]:
    dirs = {root}
    for path in root.rglob("*.md"):
        validate_relative_md_path(path, root)
        dirs.add(path.parent)
    return sorted(dirs, key=lambda p: (len(p.relative_to(root).parts), p.as_posix()), reverse=True)


def fallback_description(entries: list[dict[str, str]]) -> str:
    descs = [e.get("description", "") for e in entries if e.get("description")]
    if len(descs) == 1:
        return descs[0]
    names = [e.get("title") or e.get("name") or e.get("link", "") for e in entries]
    preview = ", ".join(names[:5])
    if len(names) > 5:
        preview += ", …"
    return f"Contains {len(entries)} entries: {preview}." if entries else ""


def _concept_entry(path: Path) -> dict[str, str]:
    fm, _body, has = parse_markdown(path)
    if not has:
        fm = {}
    return {
        "type": str(fm.get("type") or "Unknown"),
        "title": str(fm.get("title") or path.stem),
        "description": str(fm.get("description") or ""),
        "path": path.as_posix(),
        "file": path.name,
    }


def render_index(root: Path, dirpath: Path, entries: list[dict[str, str]], settings: dict[str, Any], is_root: bool) -> str:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for entry in entries:
        groups[entry["type"]].append(entry)
    lines: list[str] = []
    if is_root:
        lines.extend(["---", dump_root_settings(settings), "---", ""])
    title = settings.get("name") if is_root and settings.get("name") else ("Index" if is_root else dirpath.name)
    lines.append(f"# {title}")
    lines.append("")
    for group in sorted(groups.keys(), key=str.lower):
        lines.append(f"## {group}")
        lines.append("")
        for entry in sorted(groups[group], key=lambda e: e["title"].lower()):
            desc = entry.get("description", "")
            suffix = f" - {desc}" if desc else ""
            lines.append(f"* [{entry['title']}]({entry['link']}){suffix}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def reindex(root: Path, llm_descriptions: bool = False) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    settings = root_settings(root)
    if settings.get("okf_version") not in ("0.1", 0.1):
        print(f"INFO: unknown okf_version {settings.get('okf_version')!r}; preserving settings and using v0.1-compatible index rules")
    link_style = str(settings.get("link_style") or "relative")
    if link_style not in {"relative", "absolute"}:
        print(f"INFO: unknown link_style {link_style!r}; falling back to relative")
        link_style = "relative"
        settings["link_style"] = link_style

    descriptions: dict[Path, str] = {}
    written: dict[str, str] = {}
    for dirpath in dirs_with_markdown(root):
        entries: list[dict[str, str]] = []
        for child in sorted(dirpath.iterdir(), key=lambda p: p.name.lower()):
            if child.is_file() and child.suffix == ".md" and child.name not in {"index.md", "log.md"}:
                validate_relative_md_path(child, root)
                entry = _concept_entry(child)
                entry["link"] = markdown_link(dirpath / "index.md", child, root, link_style)
                entries.append(entry)
            elif child.is_dir():
                idx = child / "index.md"
                if idx.exists() and child in descriptions:
                    entries.append({
                        "type": "Subdirectories",
                        "title": child.name,
                        "description": descriptions.get(child, ""),
                        "link": markdown_link(dirpath / "index.md", idx, root, link_style),
                    })
        if not entries and dirpath != root:
            continue
        content = render_index(root, dirpath, entries, settings, dirpath == root)
        (dirpath / "index.md").write_text(content, encoding="utf-8")
        descriptions[dirpath] = fallback_description(entries)
        written[(dirpath / "index.md").relative_to(root).as_posix()] = descriptions[dirpath]
    return written
