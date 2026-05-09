# LLM Wiki & YouTube Knowledge Ingestion System

An AI-driven knowledge base that automatically ingests YouTube videos and turns them into structured, interconnected wiki pages inside an Obsidian Vault — inspired by the Karpathy method for LLM-managed wikis.

## Overview

The system has two parts:

1. **YouTube Fetch (`youtube-fetch.py`)** — A Python script that reads a queue of YouTube URLs, downloads their transcripts via the YouTube Transcript API, and saves them as raw Markdown files ready for ingestion.

2. **Agent Skills (`SKILL-ingest.md`, `SKILL-resolve.md`)** — Instructions for an AI agent (Claude Code) to compile the raw transcripts into structured wiki pages, cross-link them with existing content, and maintain an append-only operation log.

## How It Works

```
YouTube URL → youtube_queue.md → youtube-fetch.py → raw/ → Agent (SKILL-ingest) → Wikipedia/
```

1. Add a YouTube URL to `7 - Wikipedia/raw/youtube_queue.md`
2. Run the fetch script — transcripts are downloaded to `raw/`
3. Tell the agent: `"Compile the new sources"`
4. The agent reads `SKILL-ingest.md`, extracts key concepts, writes a structured wiki page, and updates the index, manifest, and log

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.com/) or [Claude Code](https://claude.ai/code) as the AI agent runtime
- An [Obsidian](https://obsidian.md) Vault with iCloud sync (or adjust `VAULT_PATH` in the script)

```bash
pip install youtube-transcript-api
```

## Setup

1. Clone this repository into your Obsidian Vault (e.g., under `0 - System/`)
2. Open `0 - System/youtube-fetch.py` and confirm `VAULT_PATH` matches your iCloud Obsidian path
3. Initialize Claude Code at the Vault root: `claude`

## Usage

**Fetch transcripts from the queue:**
```bash
python3 "0 - System/youtube-fetch.py"
```

**Then ask the agent:**
```
Compile the new sources
```

The agent reads `SKILL-ingest.md`, creates wiki pages in `7 - Wikipedia/`, and updates `index.md`, `log.md`, and `.manifest.json`.

## File Structure

```
├── 0 - System/
│   ├── youtube-fetch.py       # Downloads transcripts from the YouTube queue
│   ├── SKILL-ingest.md        # Agent instructions for compiling raw sources
│   └── SKILL-resolve.md       # Agent instructions for updating existing pages
└── 7 - Wikipedia/
    ├── index.md               # Master catalog of all wiki pages
    ├── log.md                 # Append-only operation history
    ├── .manifest.json         # Tracks every ingested source
    └── raw/
        └── youtube_queue.md   # Queue of YouTube URLs to fetch
```

## Tech Stack

| Tool | Role |
|---|---|
| [Claude Code](https://claude.ai/code) | AI agent for compiling and maintaining the wiki |
| [Obsidian](https://obsidian.md) | Vault and Markdown note management |
| [YouTube Transcript API](https://pypi.org/project/youtube-transcript-api/) | Transcript extraction |
| Python 3 | Fetch script runtime |

## License

MIT License — see [LICENSE](LICENSE)
