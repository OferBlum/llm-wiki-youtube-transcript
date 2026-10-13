#!/usr/bin/env python3
"""
youtube-fetch.py — saves the transcript of every pending video in youtube_queue.md to raw/.

Fetch only: it reads the queue and never edits it. The librarian moves a row from
Pending to Compiled once the summary page exists. Videos that already have a transcript
in raw/ are skipped, so running it twice is safe.
"""
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    sys.exit("❌ Missing dependency: pip install youtube-transcript-api")

# ── Config ──────────────────────────────────────────────
# Vault root: VAULT_ROOT, or two levels above this script (<vault>/0 - System/scripts/).
VAULT = Path(os.environ.get("VAULT_ROOT") or Path(__file__).resolve().parents[2])
RAW = VAULT / "7 - Wikipedia" / "raw"
QUEUE = RAW / "youtube_queue.md"

# Caption languages, in order of preference.
LANGUAGES = ["en", "he", "iw"]

PENDING_HEADING = "## Pending"
COMPILED_HEADING = "## Compiled"


# ── Helpers ─────────────────────────────────────────────
def has_symlink(path):
    p = Path(os.path.abspath(path))
    return any(item.is_symlink() for item in (p, *p.parents))


def extract_video_id(url):
    for pattern in (r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
                    r"youtu\.be/([a-zA-Z0-9_-]{11})",
                    r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
                    r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})"):
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_transcript(video_id):
    try:
        fetched = YouTubeTranscriptApi().fetch(video_id, languages=LANGUAGES)
        return " ".join(t.text for t in fetched)
    except Exception as e:
        print(f"  ⚠️ No transcript found: {e}")
        return None


def parse_queue(text):
    """[{url, tags}] for every row under the `## Pending` heading."""
    pending, in_pending = [], False
    for line in text.split("\n"):
        if line.startswith("## "):
            in_pending = line.strip() == PENDING_HEADING
            continue
        if in_pending:
            urls = re.findall(r"https?://[^\s)\]|]+", line)
            if urls:
                tags = [t.lstrip("#") for t in re.findall(r"#\w[\w-]*", line)]
                pending.append({"url": urls[0], "tags": tags})
    return pending


def already_fetched(video_id):
    return any(RAW.glob(f"youtube-{video_id}-*.md"))


def raw_page(video_id, url, tags, transcript, date):
    tag_lines = "".join(f'\n  - "{t}"' for t in tags)
    return f"""---
subject:
tags:{tag_lines if tags else " []"}
type: youtube
youtube_id: "{video_id}"
youtube_url: "{url}"
fetched: {date}
---

# Transcript — {video_id}

{transcript}
"""


# ── Main ────────────────────────────────────────────────
def main():
    if has_symlink(QUEUE) or not QUEUE.is_file():
        sys.exit(f"❌ Queue not found: {QUEUE}")

    pending = parse_queue(QUEUE.read_text(encoding="utf-8"))
    if not pending:
        print("✅ No pending videos in the queue")
        return

    print(f"📺 {len(pending)} pending videos")
    saved = 0
    for video in pending:
        video_id = extract_video_id(video["url"])
        if not video_id:
            print(f"  ❌ Could not extract a video ID from: {video['url']}")
            continue
        if already_fetched(video_id):
            print(f"  ⏭️  Already in raw/: {video_id}")
            continue

        print(f"  ⬇️ Downloading transcript: {video_id}...")
        transcript = get_transcript(video_id)
        if not transcript:
            continue

        date = datetime.now().strftime("%Y-%m-%d")
        path = RAW / f"youtube-{video_id}-{date}.md"
        path.write_text(raw_page(video_id, video["url"], video["tags"], transcript, date),
                        encoding="utf-8")
        saved += 1
        print(f"  ✅ Saved: {path.name}")

    print(f"\n✅ {saved} new transcripts in raw/. Next: ask the librarian to summarize them.")


if __name__ == "__main__":
    main()
