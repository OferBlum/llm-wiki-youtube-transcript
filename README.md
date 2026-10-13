# LLM Wiki: a librarian for everything you watch and read

**An agent keeps a wiki of summaries of your videos, articles and books: one page per source,
indexed, logged and audited. YouTube transcripts, in English or Hebrew, are one way in.**

Watching and reading without notes means the ideas evaporate. Asking an agent to "add it to my
notes" works once, then drifts: duplicate pages, invented takeaways, broken links, no record of
what came from where. This repo is the librarian half of
[Karpathy's LLM-wiki idea](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f),
with the rules that stop that drift.

Part of [Digital Brain](https://github.com/OferBlum/personal-digital-brain-with-ai).

## The idea

- **A library of sources, not an encyclopedia.** One summary per source, with its creator and
  link. Two videos on the same topic stay two pages. No automatic concept pages, no invented
  "what I learned". A synthesis across sources is a separate thing you ask for.
- **Written in your language.** A summary is written in the owner's language whatever the
  source's language. An English talk can become a Hebrew page, and the other way round.
- **The agent writes prose, scripts do bookkeeping.** The index, the source manifest and the log
  are maintained by small scripts, so they stay consistent. The log is append-only.
- **Read-only means read-only.** "Check the wiki" or "what's pending?" changes nothing: no log
  line, no rebuild. The auditor prints JSON and writes nothing.
- **An allowlist boundary.** The scripts list and read only `7 - Wikipedia`, `2 - Notes`,
  `1 - Topics` and `0 - System`, refuse symlinks, and never name an excluded file in their output,
  so the private folder stays invisible.

## How it works

```text
youtube_queue.md (Pending) ──youtube-fetch.py──► raw/youtube-<id>-<date>.md   (immutable)
article / URL / book / your text ─────────────►       │
                                                      ▼  "summarize this"  (wiki-librarian skill)
                                     7 - Wikipedia/<Source title>.md   (frontmatter + wiki_sources)
                                                      │
              build_index.py ─► index.md · build_manifest.py ─► .manifest.json · append_log.py ─► log.md
                                                      │
                                    audit.py ─► JSON: missing fields, unindexed pages, broken links
```

The `wiki-librarian` skill routes each request to one procedure: **ingest**, **resolve** (fix or
extend a summary), **crosslink**, **query**, **audit**, or **files** (rename/move/merge). The
agent loads only the procedure it needs. If the
[vault-semantic-search](https://github.com/OferBlum/vault-semantic-search) skill is installed, the
librarian uses it to find duplicates and link candidates.

## Files

```text
.claude/
  agents/wiki-librarian.md          # subagent: a pointer to the skill
  skills/wiki-librarian/
    SKILL.md                        # policy, boundaries, routing
    references/                     # ingest · resolve · crosslink · query · audit · files · source-summaries
    scripts/audit.py                # read-only structural audit + link check (self-contained)
    scripts/test_*.py
0 - System/scripts/
  youtube-fetch.py                  # queue → raw transcripts (fetch only, never edits the queue)
  build_index.py · build_manifest.py · append_log.py    # bookkeeping writers, back up first
  wiki_sources_report.py            # read-only check of every page's sources
  wikilib.py                        # the allowlist boundary, no-follow reads, frontmatter, links
  test_*.py · requirements.txt
7 - Wikipedia/
  index.md · log.md · raw/youtube_queue.md
```

## Quickstart

1. Copy `.claude/`, `0 - System/` and `7 - Wikipedia/` into your vault, then
   `pip install -r "0 - System/scripts/requirements.txt"`.
2. Add a video under Pending in `7 - Wikipedia/raw/youtube_queue.md`, then run
   `python3 "0 - System/scripts/youtube-fetch.py"`.
3. In Claude Code at the vault root: **"summarize the new transcripts"**. Later: **"check the
   wiki"** or **"what do I know about …?"**.

Tests: `python3 -m unittest discover -s "0 - System/scripts" -p "test_*.py"` and the same for
`.claude/skills/wiki-librarian/scripts`.

**Upgrading from the old version:** `SKILL-ingest.md` and `SKILL-resolve.md` are replaced by the
skill folder, and `youtube-fetch.py` moved to `0 - System/scripts/`. It no longer moves queue
rows. The librarian does that once the summary exists.

## License

MIT, see [LICENSE](LICENSE).
