from __future__ import annotations

import re
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from paths import HardFailure

REQUIRED_KEYS = ["type", "title", "description", "timestamp"]
CANONICAL_PREFIX = ["type", "resource", "title", "description", "tags", "timestamp"]
TOP_HEADING_RE = re.compile(r"^# (.+?)\s*$", re.MULTILINE)
SCHEMA_FIELD_RE = re.compile(r"`([^`]+)`")


class OrderedDumper(yaml.SafeDumper):
    pass


def _dict_representer(dumper: yaml.Dumper, data: dict):
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())

OrderedDumper.add_representer(dict, _dict_representer)
OrderedDumper.add_representer(OrderedDict, _dict_representer)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_markdown(path: Path) -> tuple[dict[str, Any], str, bool]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text, False
    end = text.find("\n---\n", 4)
    if end == -1:
        raise HardFailure(f"Unparseable frontmatter in {path}")
    raw = text[4:end]
    try:
        fm = yaml.safe_load(raw) if raw.strip() else {}
    except Exception as exc:
        raise HardFailure(f"Unparseable frontmatter in {path}: {exc}") from exc
    if fm is None:
        fm = {}
    if not isinstance(fm, dict):
        raise HardFailure(f"Frontmatter is not a mapping in {path}")
    body = text[end + 5:]
    return dict(fm), body, True


def require_concept_fm(fm: dict[str, Any], path: Path) -> None:
    missing = [k for k in REQUIRED_KEYS if k not in fm or fm.get(k) in (None, "")]
    if missing:
        raise HardFailure(f"Missing required frontmatter keys in {path}: {', '.join(missing)}")
    if not str(fm.get("type", "")).strip():
        raise HardFailure(f"Empty type in {path}")
    desc = str(fm.get("description", ""))
    if "\n" in desc:
        raise HardFailure(f"description must be one sentence/scalar in {path}")


def canonicalize_fm(fm: dict[str, Any], old_fm: dict[str, Any] | None = None, refresh_timestamp: bool = False) -> dict[str, Any]:
    data = dict(fm)
    if not data.get("timestamp") or refresh_timestamp:
        data["timestamp"] = utc_now()
    ordered: dict[str, Any] = {}
    for key in CANONICAL_PREFIX:
        if key in data:
            ordered[key] = data.pop(key)
    old_order = list(old_fm.keys()) if old_fm else []
    for key in old_order:
        if key in data and key not in ordered:
            ordered[key] = data.pop(key)
    for key, val in data.items():
        if key not in ordered:
            ordered[key] = val
    return ordered


def dump_fm(fm: dict[str, Any]) -> str:
    return yaml.dump(
        fm,
        Dumper=OrderedDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=10_000,
    ).rstrip()


def serialize(fm: dict[str, Any], body: str) -> str:
    body = body.strip("\n")
    return f"---\n{dump_fm(fm)}\n---\n\n{body}\n"


def write_concept(path: Path, fm: dict[str, Any], body: str, old_fm: dict[str, Any] | None = None, refresh_timestamp: bool = False) -> None:
    ordered = canonicalize_fm(fm, old_fm=old_fm, refresh_timestamp=refresh_timestamp)
    require_concept_fm(ordered, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize(ordered, body), encoding="utf-8")


def top_headings(body: str) -> list[str]:
    return TOP_HEADING_RE.findall(body or "")


def schema_fields(body: str) -> set[str]:
    in_schema = False
    lines = []
    for line in (body or "").splitlines():
        if line.startswith("# "):
            in_schema = line.strip() == "# Schema"
            continue
        if in_schema:
            lines.append(line)
    return set(SCHEMA_FIELD_RE.findall("\n".join(lines)))


def check_augment_body(old_body: str, new_body: str) -> None:
    old = top_headings(old_body)
    new = top_headings(new_body)
    pos = 0
    for heading in old:
        try:
            idx = new.index(heading, pos)
        except ValueError as exc:
            raise HardFailure(f"Augment rejected: missing/renamed top-level heading {heading!r}") from exc
        pos = idx + 1
    old_fields = schema_fields(old_body)
    new_fields = schema_fields(new_body)
    missing = sorted(old_fields - new_fields)
    if missing:
        raise HardFailure(f"Augment rejected: # Schema lost field tokens: {', '.join(missing)}")


def merge_tags(old_tags: Any, new_tags: Any) -> list[Any] | None:
    vals = []
    for source in (old_tags, new_tags):
        if source is None:
            continue
        if isinstance(source, str):
            iterable = [t.strip() for t in source.split(",") if t.strip()]
        elif isinstance(source, list):
            iterable = source
        else:
            iterable = [source]
        for item in iterable:
            if item not in vals:
                vals.append(item)
    return vals or None


def augment_frontmatter(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    merged = dict(old)
    for key in ("type", "title", "resource"):
        if key in old:
            merged[key] = old[key]
    for key, val in new.items():
        if key in ("type", "title", "resource", "timestamp"):
            continue
        if key == "tags":
            continue
        merged[key] = val
    tags = merge_tags(old.get("tags"), new.get("tags"))
    if tags is not None:
        merged["tags"] = tags
    merged.pop("timestamp", None)
    return merged


def load_body_file(path: str | None) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8")
