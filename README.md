# LLM Wiki & YouTube Knowledge Ingestion System

An AI-driven pipeline that turns YouTube videos into structured, interconnected wiki pages inside an Obsidian vault — inspired by the Karpathy method for LLM-managed wikis. Great for YouTube addicts: watch, queue, and the knowledge lands in your second brain instead of evaporating.

## Overview

The system has two parts:

1. **YouTube Fetch (`0 - System/youtube-fetch.py`)** — a Python script that reads a queue of YouTube URLs, downloads their transcripts via the YouTube Transcript API, saves them as raw Markdown files with full frontmatter (video id, URL, tags, fetch date), and moves each entry from the queue's *Pending* table to its *Compiled* table.

2. **Agent skills (`0 - System/SKILL-ingest.md`, `SKILL-resolve.md`)** — instructions for an AI agent (Claude Code) to compile the raw transcripts into structured wiki pages, keep an index/manifest/log, cross-link the new pages with existing content, and update related pages.

## How It Works

```
YouTube URL ─► youtube_queue.md (Pending)
                    │  youtube-fetch.py
                    ▼
        7 - Wikipedia/raw/youtube-<id>-<date>.md      (raw transcript, immutable)
                    │  "compile the new sources"  (Claude Code + SKILL-ingest)
                    ▼
        7 - Wikipedia/<Concept Page>.md               (frontmatter, provenance, wikilinks)
                    │  automatic follow-ups
                    ▼
        index.md · .manifest.json · log.md updated ─► cross-link ─► resolve related pages
```

1. Add a YouTube URL to the *Pending* table in `7 - Wikipedia/raw/youtube_queue.md` (optionally with `#tags`)
2. Run the fetch script — transcripts are downloaded to `raw/` and the queue rows move to *Compiled* with a `[[⚠️ update page name]]` placeholder
3. Tell the agent: **"compile the new sources"**
4. The agent reads `SKILL-ingest.md`, extracts the key concepts, writes a wiki page, regenerates the index/manifest/log via scripts, cross-links, and replaces the queue placeholder with a link to the real page

## Prerequisites

- Python 3.8+
- [Claude Code](https://claude.com/claude-code) as the AI agent runtime
- An [Obsidian](https://obsidian.md) vault (any folder of Markdown files works)

```bash
pip install youtube-transcript-api
```

## Setup

1. Copy the repo's folders into your vault (or clone and point `VAULT_ROOT` at your vault):
   - `0 - System/` → the script + skills
   - `7 - Wikipedia/` → the wiki skeleton (index, log, cache, `raw/` inbox with the queue)
2. The script finds the vault automatically when it lives in `<vault>/0 - System/`; otherwise set the `VAULT_ROOT` env var.
3. Start Claude Code at the vault root: `claude`

## Usage

```bash
# 1. queue a video — add a row to the Pending table in 7 - Wikipedia/raw/youtube_queue.md
#    | https://youtu.be/XXXXXXXXXXX | #ai #learning |

# 2. fetch transcripts
python3 "0 - System/youtube-fetch.py"

# 3. compile (inside Claude Code)
> compile the new sources
```

Transcripts are saved as `raw/youtube-<video_id>-<YYYY-MM-DD>.md`. Hebrew and English captions are both supported.

## Part of a Bigger System

This pipeline is one organ of a full agentic vault — lazy-loading skills, a privacy-guard hook, a graphify knowledge graph, and bidirectional note↔wiki linking:

**[private-obsidian-agent](https://github.com/OferBlum/private-obsidian-agent)** — the complete digital-brain setup this repo plugs into.

## License

MIT — see [LICENSE](LICENSE).
