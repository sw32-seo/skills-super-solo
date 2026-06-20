from __future__ import annotations

import posixpath
import re
from pathlib import Path
from urllib.parse import urlparse

SLUG_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.\-]*$")
RESERVED_FILENAMES = {"index.md", "log.md"}


class OkfError(Exception):
    pass


class HardFailure(OkfError):
    pass


def bundle_path(bundle: str | Path) -> Path:
    return Path(bundle).expanduser().resolve()


def split_id(concept_id: str) -> list[str]:
    cleaned = concept_id.strip().replace("\\", "/")
    if cleaned.endswith(".md"):
        cleaned = cleaned[:-3]
    if cleaned.startswith("/") or cleaned == "" or "//" in cleaned:
        raise HardFailure(f"Invalid concept id: {concept_id!r}")
    parts = cleaned.split("/")
    for part in parts:
        if part in {".", ".."} or not SLUG_RE.match(part):
            raise HardFailure(f"Invalid slug segment {part!r}; expected {SLUG_RE.pattern}")
    if parts[-1] + ".md" in RESERVED_FILENAMES:
        raise HardFailure(f"Reserved file is not a concept: {parts[-1]}.md")
    return parts


def validate_relative_md_path(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    parts = rel.split("/")
    if path.name in RESERVED_FILENAMES:
        return rel
    if not rel.endswith(".md"):
        raise HardFailure(f"Not a markdown file: {rel}")
    stem_parts = parts[:-1] + [parts[-1][:-3]]
    for part in stem_parts:
        if not SLUG_RE.match(part):
            raise HardFailure(f"Invalid slug segment {part!r} in {rel}")
    return rel


def id_to_path(root: Path, concept_id: str) -> Path:
    return root.joinpath(*split_id(concept_id)).with_suffix(".md")


def path_to_id(root: Path, path: Path) -> str:
    rel = path.relative_to(root).with_suffix("").as_posix()
    split_id(rel)
    return rel


def is_reserved(path: Path) -> bool:
    return path.name in RESERVED_FILENAMES


def is_external_link(target: str) -> bool:
    parsed = urlparse(target)
    return bool(parsed.scheme or parsed.netloc or target.startswith("mailto:"))


def strip_fragment(target: str) -> str:
    return target.split("#", 1)[0]


def normalize_link_target(base_file: Path, target: str, root: Path) -> str | None:
    bare = strip_fragment(target)
    if not bare or is_external_link(bare):
        return None
    if bare.startswith("/"):
        candidate = root / bare.lstrip("/")
    else:
        candidate = (base_file.parent / bare).resolve()
    try:
        rel = candidate.relative_to(root)
    except ValueError:
        return None
    return rel.as_posix()


def markdown_link(from_file: Path, to_file: Path, root: Path, style: str = "relative") -> str:
    if style == "absolute":
        return "/" + to_file.relative_to(root).as_posix()
    rel = posixpath.relpath(to_file.relative_to(root).as_posix(), from_file.parent.relative_to(root).as_posix() or ".")
    return rel
