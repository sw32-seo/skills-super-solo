# OKF v0.1 Draft Reference for okf-wiki

Source basis: GoogleCloudPlatform/knowledge-catalog OKF v0.1 draft (`okf/SPEC.md`), its reference enrichment agent, and the sample bundles `ga4`, `stackoverflow`, and `crypto_bitcoin`. OKF is versioned and draft status; preserve unknown versions and degrade gracefully using v0.1-compatible behavior.

## Bundle Model

An OKF LLM-wiki is a directory tree of UTF-8 Markdown files with YAML frontmatter. Files are cross-linked with normal Markdown links and made navigable by generated `index.md` files.

A concept is one `.md` file. Its concept ID is the bundle-relative path without `.md`, for example `tables/users.md` -> `tables/users`.

Reserved files are never concepts:

- `index.md`: generated listings
- `log.md`: update history

Every bundle-relative path segment for a concept must match:

```text
^[A-Za-z0-9_][A-Za-z0-9_.\-]*$
```

Invalid slugs are hard errors. Lowercase snake_case is recommended but not required.

## Frontmatter

Required on write:

- `type`
- `title`
- `description`: one sentence; used verbatim in indexes
- `timestamp`: current UTC if absent

Recommended when applicable:

- `resource`: an asset URI, not a docs URL
- `tags`: YAML list

Extra keys are allowed and preserved on round-trip. Canonical write order is:

```text
type, resource, title, description, tags, timestamp, <extras in existing order>
```

Serialization is block-style YAML, key order preserved, Unicode allowed. Concept files are serialized as:

```text
---
<frontmatter>
---

<body>
```

The file ends in exactly one trailing newline.

## Body

Body content is structural Markdown. Conventional top-level headings are:

- `# Schema`
- `# Examples`
- `# Citations`

Do not add preamble or narrative wrappers around concept bodies.

## Links

Binding decision for this skill: default links are file-relative, because leading `/` breaks GitHub rendering and the OKF samples use relative links. Root `index.md` stores `link_style: relative|absolute`; default is `relative`.

Rules for authoring:

- Use one link per mention per section.
- Do not link headings.
- Do not link code blocks.
- Do not link schema field listings.
- Do not self-link.
- Link only to existing concept IDs at authoring time.
- Broken links are tolerated on read and reported by `validate` as warnings, not failures.

## Reindex

`index.md` files have no frontmatter except root `index.md`. Root index frontmatter carries:

- `okf_version`
- `link_style`
- optional `name`

`reindex` preserves and re-emits this block, creating `okf_version: "0.1"` and `link_style: relative` if missing.

Algorithm:

1. Find all directories recursively containing Markdown, including root.
2. Process deepest directories first.
3. For each directory's immediate children:
   - Concept Markdown files except `index.md` and `log.md` become entries `(type, title|stem, bare filename, description)`.
   - Subdirectories with generated indexes become group `Subdirectories`, link `<dir>/index.md`, description from the child directory.
   - Empty directories are skipped.
4. Group by `type`, with subdirectories under `Subdirectories`.
5. Sort groups alphabetically and entries by title case-insensitively.
6. Render each entry as `* [<title>](<link>) - <description>`, dropping the description suffix when empty.

Directory description for parent indexes reuses the single child's description if exactly one entry has one; otherwise it uses `Contains N entries: a, b, ….`.

Default reindex is deterministic and idempotent. `--llm-descriptions` is reserved for optional fallback behavior; the default path must not require a model or network.

## Augment Rules

Augment existing concepts; do not rewrite them.

Frontmatter:

- The writer receives and replaces the full dict.
- Omitting a key drops it, so callers must copy keys intentionally.
- Copy `type`, `title`, and `resource` verbatim from the old concept.
- `tags` is the union of old and new tags.
- `description` may refine, otherwise preserve it verbatim.
- `timestamp` is the only key allowed to be dropped; it is refreshed automatically.

Body:

- Every existing `#` heading must reappear in the new body.
- Existing `#` headings must stay in the same order and wording.
- You may extend prose, add list items, add `##` subsections, and append new `#` sections after existing ones.
- Never shrink `# Schema`.
- Existing backtick field tokens inside `# Schema` must survive.
- Append citations to `# Citations`; do not invent URLs.

Escape hatch: if the heading-preservation rule cannot hold because the source material is a different topic, mint a new `references/<slug>.md` concept and cross-link it, or skip the update.

## Log

After every mutation, run `reindex`, then append a newest-first entry to `log.md` in the mutation scope, default root.

Format:

```markdown
# Directory Update Log

## 2026-06-20
* **Creation**: Established the [Orders table](tables/orders.md).
* **Update**: Added `# Metrics` to the [Events table](tables/events_.md).
```

Kind words are conventionally `Creation`, `Update`, `Deprecation`, and `Initialization`.

## Validate

Strict producer, permissive consumer.

Hard failures:

- Unparseable frontmatter.
- Empty `type`.
- Invalid slug.
- Missing required skill keys: `type`, `title`, `description`, `timestamp`.

Warnings/info only:

- Missing optional fields.
- Unknown `type`.
- Extra keys.
- Broken links.
- Missing `index.md`.

Validation reports broken links, orphan concepts, and cited-by counts. It exits non-zero only for hard failures.

## Citations

On write, use numbered citations:

```markdown
# Citations

[1] [Title](https://example.com)
```

Accept either numbered or unnumbered citations on read. `resource` is `[1]` when present. Never invent URLs.

## Binding Decisions

1. Links are file-relative by default, despite the draft spec recommending absolute `/` links.
2. This skill emits and requires `type`, `title`, `description`, and `timestamp`.
3. Citations are numbered `[n] [Title](url)` on write; read accepts either form.
4. `log.md` is implemented by this skill even though the reference agent omits it.
