#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from document import augment_frontmatter, check_augment_body, load_body_file, parse_markdown, write_concept
from logbook import append_log
from paths import HardFailure, bundle_path, id_to_path, path_to_id
from reindex import reindex
from validate import validate


def parse_tags(tags: str | None) -> list[str] | None:
    if not tags:
        return None
    return [t.strip() for t in tags.split(",") if t.strip()]


def fm_from_args(args: argparse.Namespace) -> dict[str, Any]:
    fm: dict[str, Any] = {}
    for key in ("type", "title", "description", "resource"):
        val = getattr(args, key, None)
        if val is not None:
            fm[key] = val
    tags = parse_tags(getattr(args, "tags", None))
    if tags is not None:
        fm["tags"] = tags
    if getattr(args, "timestamp", None):
        fm["timestamp"] = args.timestamp
    if getattr(args, "frontmatter_file", None):
        loaded = yaml.safe_load(Path(args.frontmatter_file).read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise HardFailure("--frontmatter-file must contain a YAML mapping")
        fm.update(loaded)
    return fm


def post_mutation(root: Path, kind: str, message: str, target: Path | None = None, llm_descriptions: bool = False) -> None:
    reindex(root, llm_descriptions=llm_descriptions)
    append_log(root, kind, message, target=target)


def cmd_init(args: argparse.Namespace) -> int:
    root = bundle_path(args.bundle)
    root.mkdir(parents=True, exist_ok=True)
    index = root / "index.md"
    if not index.exists():
        name_line = f"name: {args.name}\n" if args.name else ""
        index.write_text(f"---\nokf_version: \"0.1\"\nlink_style: relative\n{name_line}---\n\n# {args.name or 'Index'}\n", encoding="utf-8")
    post_mutation(root, "Initialization", f"Initialized OKF bundle at `{root}`", llm_descriptions=args.llm_descriptions)
    print(f"Initialized {root}")
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    root = bundle_path(args.bundle)
    path = id_to_path(root, args.id)
    if path.exists() and not args.force:
        raise HardFailure(f"Concept already exists: {path.relative_to(root).as_posix()}")
    fm = fm_from_args(args)
    body = load_body_file(args.body_file)
    if not body:
        body = "# Schema\n\n# Examples\n\n# Citations\n"
    write_concept(path, fm, body)
    post_mutation(root, "Creation", f"Established the [{fm.get('title', args.id)}]({path.relative_to(root).as_posix()}).", target=None, llm_descriptions=args.llm_descriptions)
    print(path.relative_to(root).as_posix())
    return 0


def cmd_augment(args: argparse.Namespace) -> int:
    root = bundle_path(args.bundle)
    path = id_to_path(root, args.id)
    if not path.exists():
        raise HardFailure(f"Concept does not exist: {args.id}")
    old_fm, old_body, _has = parse_markdown(path)
    new_fm_input = fm_from_args(args)
    new_body = load_body_file(args.body_file) if args.body_file else old_body
    check_augment_body(old_body, new_body)
    merged = augment_frontmatter(old_fm, new_fm_input)
    write_concept(path, merged, new_body, old_fm=old_fm, refresh_timestamp=True)
    post_mutation(root, "Update", f"Augmented the [{merged.get('title', args.id)}]({path.relative_to(root).as_posix()}).", llm_descriptions=args.llm_descriptions)
    print(path.relative_to(root).as_posix())
    return 0


def cmd_reindex(args: argparse.Namespace) -> int:
    root = bundle_path(args.bundle)
    written = reindex(root, llm_descriptions=args.llm_descriptions)
    for rel in sorted(written):
        print(rel)
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    root = bundle_path(args.bundle)
    target = id_to_path(root, args.id) if args.id else None
    append_log(root, args.kind, args.message, target=target)
    print((root / "log.md").as_posix())
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    root = bundle_path(args.bundle)
    code, messages = validate(root)
    print("\n".join(messages))
    return code


def cmd_move(args: argparse.Namespace) -> int:
    root = bundle_path(args.bundle)
    old = id_to_path(root, args.id)
    new = id_to_path(root, args.new_id)
    if not old.exists():
        raise HardFailure(f"Concept does not exist: {args.id}")
    if new.exists() and not args.force:
        raise HardFailure(f"Destination exists: {args.new_id}")
    new.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(old), str(new))
    post_mutation(root, "Update", f"Moved `{args.id}` to `{args.new_id}`", llm_descriptions=args.llm_descriptions)
    print(f"{args.id} -> {args.new_id}")
    return 0


def cmd_deprecate(args: argparse.Namespace) -> int:
    root = bundle_path(args.bundle)
    path = id_to_path(root, args.id)
    if not path.exists():
        raise HardFailure(f"Concept does not exist: {args.id}")
    fm, body, _has = parse_markdown(path)
    fm["deprecated"] = True
    if args.replaced_by:
        fm["replaced_by"] = args.replaced_by
    note = args.message or "Deprecated."
    body = body.rstrip() + f"\n\n# Deprecation\n\n{note}\n"
    write_concept(path, fm, body, old_fm=fm, refresh_timestamp=True)
    post_mutation(root, "Deprecation", f"Deprecated the [{fm.get('title', args.id)}]({path.relative_to(root).as_posix()}).", llm_descriptions=args.llm_descriptions)
    print(path.relative_to(root).as_posix())
    return 0


def cmd_visualize(args: argparse.Namespace) -> int:
    root = bundle_path(args.bundle)
    print("digraph okf {")
    for md in sorted(root.rglob("*.md")):
        if md.name in {"index.md", "log.md"}:
            continue
        print(f'  "{path_to_id(root, md)}";')
    print("}")
    return 0


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--llm-descriptions", action="store_true", help="Reserved: default path remains deterministic and model-free")


def add_fm_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--type")
    parser.add_argument("--title")
    parser.add_argument("--description")
    parser.add_argument("--resource")
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--timestamp")
    parser.add_argument("--frontmatter-file")
    parser.add_argument("--body-file")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create and manage OKF LLM-wiki bundles")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init"); add_common(p); p.add_argument("--name"); p.set_defaults(func=cmd_init)
    p = sub.add_parser("new"); add_common(p); p.add_argument("--id", required=True); add_fm_args(p); p.add_argument("--force", action="store_true"); p.set_defaults(func=cmd_new)
    p = sub.add_parser("augment"); add_common(p); p.add_argument("--id", required=True); add_fm_args(p); p.set_defaults(func=cmd_augment)
    p = sub.add_parser("reindex"); add_common(p); p.set_defaults(func=cmd_reindex)
    p = sub.add_parser("log"); add_common(p); p.add_argument("--kind", required=True); p.add_argument("--message", required=True); p.add_argument("--id"); p.set_defaults(func=cmd_log)
    p = sub.add_parser("validate"); add_common(p); p.set_defaults(func=cmd_validate)
    p = sub.add_parser("move"); add_common(p); p.add_argument("--id", required=True); p.add_argument("--new-id", required=True); p.add_argument("--force", action="store_true"); p.set_defaults(func=cmd_move)
    p = sub.add_parser("deprecate"); add_common(p); p.add_argument("--id", required=True); p.add_argument("--message"); p.add_argument("--replaced-by"); p.set_defaults(func=cmd_deprecate)
    p = sub.add_parser("visualize"); add_common(p); p.set_defaults(func=cmd_visualize)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except HardFailure as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
