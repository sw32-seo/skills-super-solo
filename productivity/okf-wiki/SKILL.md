---
name: okf-wiki
description: "Create and manage an OKF 'LLM-wiki': a version-controllable knowledge base of Markdown files with YAML frontmatter, cross-linked and indexed for humans and LLMs. Use whenever the user wants to build, scaffold, populate, document, curate, reindex, validate, or maintain a knowledge base / knowledge bundle / agent memory store / internal wiki / data catalog / context corpus as files — even if they don't say 'OKF'."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [okf, wiki, knowledge-base, markdown, data-catalog, llm-context]
    related_skills: [llm-wiki, obsidian, ocr-and-documents]
---

# OKF Wiki

## Overview

Use this skill to create and maintain an OKF v0.1 draft-compatible LLM-wiki: a directory tree of Markdown concept files with YAML frontmatter, Markdown cross-links, generated `index.md` navigation, and `log.md` history.

The skill is domain-agnostic. Never hard-code a type taxonomy. Concepts can be tables, datasets, APIs, metrics, people, policies, references, or any other domain type the user needs.

The deterministic CLI is at:

```bash
python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py <verb> --bundle <bundle>
```

Hard guardrail for CLI examples: never place `--body-file` or `--frontmatter-file` scratch Markdown anywhere under `--bundle`. `validate` scans every `.md` under the bundle and will treat scratch Markdown as concepts. Use `/tmp/okf-body-*.md`, `/tmp/okf-frontmatter-*.yaml`, or a sibling `.scratch/` directory outside the bundle.

Full local rules are in `references/okf-spec-v0.1.md`. OKF is a versioned draft; preserve unknown `okf_version` values and degrade gracefully with v0.1-compatible behavior.

## Scratch File Hygiene

When using `--body-file` or `--frontmatter-file`, keep scratch/input files **outside** the bundle tree. `validate` recursively scans every `.md` under `--bundle`; if you stage temporary bodies such as `users.md`, `orders.md`, or `*-aug.md` inside the bundle, validation will treat them as concepts and may hard-fail for missing frontmatter.

Safe patterns:

```bash
mkdir -p /tmp/okf-bodies
cat > /tmp/okf-bodies/users.md <<'EOF'
# Schema

- `user_id`: Stable user identifier.

# Examples

# Citations
EOF

python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py new \
  --bundle /path/to/wiki \
  --id tables/users \
  --type table \
  --title "Users" \
  --description "Stores application users." \
  --body-file /tmp/okf-bodies/users.md
```

If `validate` reports missing frontmatter for unexpected files like `users.md`, `orders.md`, `*-aug.md`, or `*-delete.md`, first check whether scratch Markdown was accidentally written inside the bundle. Move or remove those scratch files from the bundle, then run `reindex` and `validate` again.

## Augment Guardrails First

When editing an existing concept, augment rather than rewrite.

Before calling `augment`, inspect the existing concept and ensure the proposed body obeys these non-negotiable rules:

- Every existing top-level `#` heading reappears with the same wording.
- Existing top-level `#` headings stay in the same order.
- Existing backtick field tokens inside `# Schema` survive.
- `type`, `title`, and `resource` stay verbatim.
- `tags` becomes the union of old and new tags.
- `description` may refine; otherwise preserve it.
- `timestamp` refreshes automatically.

If the new material is really a different topic, do not force it into the old concept. Mint a `references/<slug>.md` concept and cross-link it, or skip the update.

## When to Use

- User wants to scaffold a knowledge base, internal wiki, context corpus, memory store, data catalog, documentation bundle, or file-based agent knowledge pack.
- User asks to populate, curate, move, deprecate, validate, reindex, or visualize Markdown knowledge files.
- User mentions OKF, LLM-wiki, concept files, YAML frontmatter, generated indexes, or cross-linked Markdown bundles.
- User has source documents and wants a navigable set of concepts for humans and LLMs.

Do not use this for one-off prose documents that are not meant to become a linked concept bundle.

## Operation Menu

All operations are deterministic and use stdlib plus PyYAML only. Default paths do not call models or the network.

### Initialize

Create a bundle and root `index.md` with `okf_version: "0.1"` and `link_style: relative`.

```bash
python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py init \
  --bundle /path/to/wiki \
  --name "Knowledge Catalog"
```

Post-step is automatic: reindex, then append an `Initialization` log entry.

### New Concept

Mint a concept. Concept ID is bundle-relative path without `.md`.

```bash
python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py new \
  --bundle /path/to/wiki \
  --id tables/users \
  --type table \
  --title "Users" \
  --description "Stores application users." \
  --tags pii,core \
  --body-file /tmp/users.md
```

The script rejects invalid slug segments and reserved concept names (`index.md`, `log.md`). It writes canonical frontmatter, auto-fills UTC `timestamp`, enforces exactly one trailing newline, runs `reindex`, then appends a `Creation` log entry.

### Augment Concept

Edit a concept under strict preservation rules.

```bash
python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py augment \
  --bundle /path/to/wiki \
  --id tables/users \
  --description "Stores application user accounts." \
  --tags warehouse \
  --body-file /tmp/users-augmented.md
```

The script rejects heading-dropping, heading-renaming, heading-reordering, and `# Schema` field-token loss. It unions tags, refreshes timestamp, reindexes, then appends an `Update` log entry.

### Reindex

Regenerate all `index.md` files deterministically.

```bash
python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py reindex \
  --bundle /path/to/wiki
```

Root `index.md` preserves frontmatter. Non-root indexes have no frontmatter. Two runs should produce no diff.

Optional flag:

```bash
--llm-descriptions
```

This flag is reserved for future fallback behavior. The default path remains model-free.

### Log

Append a manual newest-first log entry.

```bash
python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py log \
  --bundle /path/to/wiki \
  --kind Update \
  --message "Added metric relationships to the events reference."
```

Use conventional kinds: `Creation`, `Update`, `Deprecation`, `Initialization`.

### Validate

Run strict-producer/permissive-consumer validation.

```bash
python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py validate \
  --bundle /path/to/wiki
```

Hard failures exit non-zero:

- Unparseable frontmatter.
- Invalid slug.
- Empty `type`.
- Missing `type`, `title`, `description`, or `timestamp` on concepts.

Warnings/info do not fail:

- Broken links.
- Missing optional fields.
- Unknown types.
- Extra keys.
- Missing `index.md`.
- Orphans and cited-by counts.

### Move

Move a concept without hard-deleting it.

```bash
python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py move \
  --bundle /path/to/wiki \
  --id tables/users \
  --new-id entities/users
```

The script moves the file, reindexes, then appends an `Update` log entry. It does not rewrite all inbound links; run `validate` afterward to report broken links for repair.

### Deprecate

Mark a concept as deprecated rather than deleting it.

```bash
python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py deprecate \
  --bundle /path/to/wiki \
  --id tables/old_users \
  --replaced-by entities/users \
  --message "Replaced by the normalized users concept."
```

The script adds deprecation metadata and a `# Deprecation` body section, reindexes, then appends a `Deprecation` log entry.

### Visualize

Emit a minimal Graphviz DOT node list.

```bash
python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py visualize \
  --bundle /path/to/wiki
```

This is optional and intentionally conservative.

## Clean Happy Path

Use this compact path for straightforward bundle creation. It keeps scratch files in `/tmp`, creates two linked concepts, validates, and runs `reindex` twice to prove idempotence.

```bash
BUNDLE=/tmp/okf-demo-wiki
rm -rf "$BUNDLE"

cat > /tmp/okf-body-users.md <<'EOF'
# Schema

- `user_id`: Stable user identifier.
- `email`: Contact email.

# Examples

Users are referenced by [Orders](orders.md).

# Citations
EOF

cat > /tmp/okf-body-orders.md <<'EOF'
# Schema

- `order_id`: Stable order identifier.
- `user_id`: User who placed the order.

# Examples

Each order links back to [Users](users.md).

# Citations
EOF

python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py init \
  --bundle "$BUNDLE" \
  --name "Demo Knowledge Catalog"

python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py new \
  --bundle "$BUNDLE" \
  --id tables/users \
  --type table \
  --title "Users" \
  --description "Stores application users." \
  --tags core \
  --body-file /tmp/okf-body-users.md

python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py new \
  --bundle "$BUNDLE" \
  --id tables/orders \
  --type table \
  --title "Orders" \
  --description "Stores customer orders." \
  --tags core \
  --body-file /tmp/okf-body-orders.md

python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py validate --bundle "$BUNDLE"
python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py reindex --bundle "$BUNDLE"
python3 /root/.hermes/skills/productivity/okf-wiki/scripts/okf.py reindex --bundle "$BUNDLE"
```

## Authoring Rules

- Default to file-relative links; never emit leading `/` unless root `index.md` explicitly sets `link_style: absolute`.
- Do not link headings, code blocks, schema field listings, or self-references.
- Link only to existing IDs when authoring; tolerate future broken links when reading.
- Keep descriptions one sentence because indexes reuse them verbatim.
- Use `resource` for an asset URI, not a docs URL.
- Put docs URLs in `# Citations`; never invent URLs.
- Preserve unknown frontmatter keys and extras.
- Never treat `index.md` or `log.md` as concepts.
- Never hard-delete concepts; move or deprecate so git can recover history.

## Recommended Workflow

1. Run `init` for a new bundle.
2. Draft concept bodies with structural Markdown and conventional `# Schema`, `# Examples`, and `# Citations` sections when applicable.
3. Keep all `--body-file` and `--frontmatter-file` scratch inputs outside the bundle tree.
4. Use `new` for each concept; let the script reindex and log.
5. Use `augment` for edits; do not hand-edit concept files unless the user explicitly asks.
6. Run `validate` after batches and repair hard failures.
7. Run `reindex` before handoff if any files were edited outside the CLI.
8. For an existing bundle where the user asks to validate or reindex without semantic changes, run `validate`, `reindex`, then `validate` again; do not run `new`, `augment`, `move`, or `deprecate` unless the user requested semantic edits. Treat regenerated navigation as a file change but not a concept-semantic change.
9. Preserve unknown or newer `okf_version` values and unknown frontmatter keys when validating or reindexing existing bundles; never downgrade, normalize, or remove them just because this skill implements v0.1-compatible behavior.
10. If `validate` flags unexpected Markdown files with missing frontmatter, check whether scratch `--body-file` or `--frontmatter-file` inputs were stored inside the bundle; move them outside the bundle, then rerun `reindex` and `validate`.
11. Under deletion or rewrite pressure, do not hard-delete. Use `augment` only when preservation rules hold; if the concept is obsolete, run `deprecate`; if it was renamed or relocated, run `move`; then run `validate` and report hard failures separately from warnings.

## Common Pitfalls

1. Treating `type` as a fixed taxonomy. OKF is domain-agnostic; accept user/domain types.
2. Rewriting a concept during augmentation. Preserve headings and schema field tokens.
3. Putting docs URLs in `resource`. Use `# Citations` for documentation links.
4. Using absolute links by default. Use relative links for GitHub-compatible bundles.
5. Forgetting post-mutation order. Always reindex first, then append the log entry.
6. Failing validation for broken links. Broken links are warnings because future knowledge may arrive later.
7. Indexing `log.md`. It is reserved history, never a concept.

## Verification Checklist

- [ ] `init` then `validate` exits zero.
- [ ] Root `index.md` has `okf_version` and `link_style` frontmatter.
- [ ] Bad slugs are rejected.
- [ ] Concept frontmatter is canonical-ordered and includes a UTC `timestamp`.
- [ ] Reindex is idempotent across two runs.
- [ ] Augment rejects dropped headings or schema field tokens.
- [ ] `log.md` is newest-first and is not indexed as a concept.
- [ ] `validate` fails only on hard producer errors and warns on broken links.
