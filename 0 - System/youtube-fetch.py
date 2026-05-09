#!/usr/bin/env python3
"""
YouTube Fetch — Downloads transcripts from youtube_queue.md
Downloads transcripts from YouTube to the raw/ directory
"""

import os
import sys
import re
import glob
from datetime import datetime

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("❌ Missing: pip install youtube-transcript-api")
    sys.exit(1)

# ── Config ──────────────────────────────────────────────
VAULT_PATH = os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents"
)
# Make sure to update QUEUE_PATH to your Vault's exact path
QUEUE_PATH = "Wikipedia/raw/youtube_queue.md"
RAW_FOLDER = "Wikipedia/raw"

# ── Helpers ─────────────────────────────────────────────
def find_vault() -> str:
    for v in glob.glob(os.path.join(VAULT_PATH, "*")):
        if os.path.isdir(v) and os.path.exists(os.path.join(v, QUEUE_PATH)):
            return v
    return None

def extract_video_id(url: str) -> str:
    patterns = [
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(video_id: str) -> str:
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=["en", "iw", "he"])
        return " ".join([t.text for t in fetched])
    except Exception as e:
        print(f"  ⚠️ Transcript not found: {e}")
        return None

def parse_queue(queue_path: str):
    with open(queue_path, "r", encoding="utf-8") as f:
        content = f.read()
    pending = []
    in_pending = False
    for line in content.split("\n"):
        # Supports both English and Hebrew section headers
        if "Pending" in line or "ממתינים" in line:
            in_pending = True
            continue
        if "Compiled" in line or "קומפלו" in line:
            in_pending = False
            continue
        if in_pending and "|" in line and "http" in line:
            urls = re.findall(r'https?://[^\s\)\]|]+', line)
            tags = re.findall(r'#\w+', line)
            if urls:
                pending.append({
                    "url": urls[0],
                    "tags": tags,
                    "line": line
                })
    return pending, content

def mark_as_compiled(content: str, original_line: str, page_name: str) -> str:
    new_line = original_line.rstrip() + f" | [[{page_name}]]"
    content = content.replace(original_line, "")
    compiled_marker = "## Compiled"
    if compiled_marker not in content and "## קומפלו" in content:
        compiled_marker = "## קומפלו"
        
    if compiled_marker in content:
        insert_pos = content.find(compiled_marker) + len(compiled_marker)
        next_line = content.find("\n", insert_pos) + 1
        content = content[:next_line] + new_line + "\n" + content[next_line:]
    return content

# ── Main ────────────────────────────────────────────────
def main():
    vault_dir = find_vault()
    if not vault_dir:
        print("❌ Vault not found")
        sys.exit(1)

    queue_full_path = os.path.join(vault_dir, QUEUE_PATH)
    raw_full_path = os.path.join(vault_dir, RAW_FOLDER)

    if not os.path.exists(queue_full_path):
        print(f"❌ Not found: {queue_full_path}")
        sys.exit(1)

    pending, queue_content = parse_queue(queue_full_path)

    if not pending:
        print("✅ No pending videos in the queue")
        sys.exit(0)

    print(f"📺 Found {len(pending)} pending videos...")

    for video in pending:
        url = video["url"]
        tags = video["tags"]
        video_id = extract_video_id(url)

        if not video_id:
            print(f"  ❌ Could not extract video ID from: {url}")
            continue

        print(f"  ⬇️ Downloading transcript: {video_id}...")
        transcript = get_transcript(video_id)

        if not transcript:
            continue

        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"youtube-{video_id}-{date_str}.md"
        filepath = os.path.join(raw_full_path, filename)

        tags_str = "\n  - ".join(tags) if tags else ""
        file_content = f"""---
topic:
tags:
  - wiki
  - {tags_str}
private: false
type: youtube
youtube_id: {video_id}
youtube_url: {url}
fetched: {date_str}
---

# Transcript — {video_id}

{transcript}
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(file_content)

        print(f"  ✅ Saved: {filename}")

        queue_content = mark_as_compiled(queue_content, video["line"], f"youtube-{video_id}-{date_str}")

    with open(queue_full_path, "w", encoding="utf-8") as f:
        f.write(queue_content)

    print("\n✅ Done — Claude Code can now compile the new files in raw/")

if __name__ == "__main__":
    main()
