---
name: wiki-librarian
description: "Librarian for the source-summary wiki (7 - Wikipedia) and for scoped file organization. Use to summarize/ingest a source (article, video, YouTube transcript), update or correct a summary, add related links, answer from the wiki, audit/status, or rename/move/merge requested notes. Triggers: librarian, compile, summarize this, what do I know about, check the wiki, wiki status, organize files."
license: MIT
compatibility: Python 3.9+ with PyYAML, on Linux or macOS (the scripts use POSIX no-follow file operations). Run from the vault root.
---

# Wiki Librarian

The single librarian workflow. It does not depend on a particular model, provider or runtime, and it does not schedule itself or grant filesystem access. This file holds the policy, boundaries and routing; each task's procedure is in `references/`. Load only the reference the task needs.

## Routing

| Request | Mode | Load |
|---|---|---|
| Summarize a new source ("compile", "summarize this video/article") | Wiki, write | `references/ingest.md` + `references/source-summaries.md` |
| Correct or extend an existing summary, handle a conflict | Wiki, write | `references/resolve.md` + `references/source-summaries.md` |
| Add or repair related links | Wiki, write | `references/crosslink.md` |
| Answer a question or find a source ("what do I know about…") | Read-only | `references/query.md` |
| Health check, status, pending sources, quality review | Read-only | `references/audit.md` (+ `source-summaries.md` for quality) |
| Rename, move, merge, archive or tidy requested files | Files, write | `references/files.md` |

Semantic search is a separate, optional `vault-search` skill. When it is installed, use it for candidate discovery from any procedure above; otherwise use a targeted filename or text search inside the allowed folders.

## Source-library policy

- The wiki is the owner's personal library of summaries of material they watched or read. It is not an auto-generated encyclopedia.
- One main summary per source by default. Split a long source only when there is a clear benefit and an approved scope.
- Different sources keep separate summaries and their own attribution. Topic similarity is not duplication. Cross-source synthesis is a separate output that has to be requested.
- Do not create automatic concept pages. Existing concept pages are legacy content: link to them, but do not migrate, rename or delete them unless asked.
- Summaries are written in the owner's language, whatever the language of the source. Do not invent facts, the owner's takeaways, personal applications or tasks.

## Hard boundaries

- **Private folder:** the private folder, including the journal, does not exist for this skill. Do not access, list, index, link or summarize it, and never create daily notes. Running a local model does not waive this rule.
- **Allowlist:** the skill works only in `7 - Wikipedia`, `2 - Notes`, `1 - Topics` and `0 - System`. A malformed header is read as empty metadata and reported, never skipped. Never disclose the names of excluded targets.
- **Search scope:** never scan the vault root and never follow symlinks. Search only explicit, task-specific allowed folders. A link target never expands permissions.
- **Read-only requests:** review, status and query make no writes at all: no log entry, manifest rebuild, report, cache edit or index refresh.
- **Write scope:** each change needs an explicit requested scope: rename, move, merge, archive, delete, schema change, mass edit or system configuration. A wiki request never authorizes editing notes. Finding or linking a target never authorizes changing it.
- **What stays untouched:** existing raw sources are immutable. Preserve human writing, completed tasks and task dates. Notes are never moved into the wiki automatically.
- **Read-only areas:** system files and templates are read-only unless their change is requested.
- **Outside the vault:** act only on exact paths the user names. No whole-computer scan.

## Running the tools

Run every command from the vault root with a Python that has PyYAML (`pip install -r "0 - System/scripts/requirements.txt"`).

```text
python3 ".claude/skills/wiki-librarian/scripts/audit.py" --vault "$PWD"
```

- **`scripts/audit.py`:** the read-only structural auditor, including link checking. It prints JSON and writes nothing.
- **`0 - System/scripts/`:** the bookkeeping writers (`build_index.py`, `build_manifest.py`, `append_log.py`), the read-only `wiki_sources_report.py`, and `youtube-fetch.py` for the YouTube queue.
- **`scripts/test_*.py`:** synthetic regression tests. Run them with `python3 -m unittest` from the `scripts/` folder.

## Before any write

1. Check frontmatter before reading a body. Orient from `7 - Wikipedia/index.md`, the relevant dates in `7 - Wikipedia/log.md`, and `0 - System/SCHEMA.md` when the vault has one.
2. State the exact files you will change. Back them up to `7 - Wikipedia/.backup/<timestamp>-<label>/` before replacing user-authored content or catalogs.
3. Run the audit before and after the change, and compare the issue sets, not just the exit code.

## Known limits

- **Structural only:** the auditor checks structure. It does not check how faithful or good a summary is, external URLs, or non-Markdown sources.
- **Manifest:** `.manifest.json` has no content hashes. It cannot prove that a source is unchanged or that a page still exists.
- **Search index:** if `vault-search` is installed, its index is refreshed only on request. An ordinary lookup never rebuilds it.
- **Hooks and schedulers:** they are separate from this skill. Inspect them per runtime before claiming they are active.

## Output

Report concisely in the owner's language:
- what was checked or changed, with exact paths;
- real counts from tool output;
- open problems;
- what was not tested, including whether the search index was refreshed.
