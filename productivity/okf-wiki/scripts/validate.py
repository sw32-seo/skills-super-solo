from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

from document import parse_markdown, require_concept_fm
from paths import HardFailure, is_reserved, normalize_link_target, validate_relative_md_path

MD_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def _without_code_fences(text: str) -> str:
    out = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def validate(root: Path) -> tuple[int, list[str]]:
    messages: list[str] = []
    failures = 0
    if not root.exists():
        return 1, [f"FAIL: bundle does not exist: {root}"]

    concept_paths: list[Path] = []
    all_md = sorted(root.rglob("*.md"))
    for path in all_md:
        rel = path.relative_to(root).as_posix()
        try:
            validate_relative_md_path(path, root)
            fm, body, has_fm = parse_markdown(path)
            if is_reserved(path):
                if path.name == "index.md" and path.parent != root and has_fm:
                    messages.append(f"WARN: non-root index has frontmatter: {rel}")
                continue
            concept_paths.append(path)
            if not has_fm:
                raise HardFailure(f"Missing frontmatter in {rel}")
            require_concept_fm(fm, path)
            if "resource" not in fm:
                messages.append(f"INFO: optional resource missing: {rel}")
            if "tags" not in fm:
                messages.append(f"INFO: optional tags missing: {rel}")
            extras = sorted(set(fm) - {"type", "resource", "title", "description", "tags", "timestamp"})
            if extras:
                messages.append(f"INFO: extra frontmatter keys in {rel}: {', '.join(extras)}")
        except HardFailure as exc:
            failures += 1
            messages.append(f"FAIL: {exc}")

    if not (root / "index.md").exists():
        messages.append("WARN: missing index.md at root")
    for dirpath in sorted({p.parent for p in concept_paths}):
        if not (dirpath / "index.md").exists():
            messages.append(f"WARN: missing index.md: {dirpath.relative_to(root).as_posix()}/index.md")

    existing = {p.relative_to(root).as_posix() for p in all_md}
    inbound: Counter[str] = Counter()
    outbound: defaultdict[str, list[str]] = defaultdict(list)
    for path in all_md:
        rel = path.relative_to(root).as_posix()
        try:
            _fm, body, _has = parse_markdown(path)
        except HardFailure:
            continue
        for target in MD_LINK_RE.findall(_without_code_fences(body)):
            norm = normalize_link_target(path, target, root)
            if norm is None:
                continue
            outbound[rel].append(norm)
            if norm in existing:
                inbound[norm] += 1
            else:
                messages.append(f"WARN: broken link in {rel}: {target}")

    for path in concept_paths:
        rel = path.relative_to(root).as_posix()
        messages.append(f"INFO: cited-by {rel}: {inbound[rel]}")
        if inbound[rel] == 0:
            messages.append(f"INFO: orphan concept: {rel}")

    if failures:
        messages.insert(0, f"FAIL: {failures} hard validation failure(s)")
        return 1, messages
    messages.insert(0, "OK: no hard validation failures")
    return 0, messages
