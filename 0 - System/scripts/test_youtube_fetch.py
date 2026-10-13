"""youtube-fetch.py against a throwaway vault, with the transcript API stubbed out."""
import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

SCRIPT = Path(__file__).with_name("youtube-fetch.py")

QUEUE = """---
tags: [wiki]
---

# YouTube Queue

Add a row under Pending: `| https://youtu.be/AAAAAAAAAAA | #tag |`. The librarian moves it to Compiled.

## Pending

| Video | Tags |
| ----- | ---- |
| https://youtu.be/BBBBBBBBBBB | #ai #למידה |
| https://www.youtube.com/watch?v=CCCCCCCCCCC | |

## Compiled

| Video | Page created/updated | Date |
| ----- | -------------------- | ---- |
| https://youtu.be/DDDDDDDDDDD | [[Done]] | 2026-10-01 |
"""


class Snippet:
    def __init__(self, text):
        self.text = text


class FetchTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.raw = self.root / "7 - Wikipedia" / "raw"
        self.raw.mkdir(parents=True)
        (self.raw / "youtube_queue.md").write_text(QUEUE, encoding="utf-8")
        self.fetched = []
        api = types.ModuleType("youtube_transcript_api")
        test = self

        class YouTubeTranscriptApi:
            def fetch(self, video_id, languages):
                test.fetched.append(video_id)
                return [Snippet("hello"), Snippet("world")]

        api.YouTubeTranscriptApi = YouTubeTranscriptApi
        with patch.dict(sys.modules, {"youtube_transcript_api": api}), \
             patch.dict(os.environ, {"VAULT_ROOT": str(self.root)}):
            spec = importlib.util.spec_from_file_location("youtube_fetch", SCRIPT)
            self.m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.m)

    def test_only_rows_under_the_pending_heading_are_read(self):
        rows = self.m.parse_queue(QUEUE)
        self.assertEqual([r["url"] for r in rows],
                         ["https://youtu.be/BBBBBBBBBBB", "https://www.youtube.com/watch?v=CCCCCCCCCCC"])
        self.assertEqual(rows[0]["tags"], ["ai", "למידה"])

    def test_fetch_writes_valid_frontmatter_and_never_touches_the_queue(self):
        self.m.main()
        self.assertEqual(sorted(self.fetched), ["BBBBBBBBBBB", "CCCCCCCCCCC"])
        self.assertEqual((self.raw / "youtube_queue.md").read_text(encoding="utf-8"), QUEUE)
        page = next(self.raw.glob("youtube-BBBBBBBBBBB-*.md")).read_text(encoding="utf-8")
        meta = yaml.safe_load(page.split("---")[1])
        self.assertEqual(meta["tags"], ["ai", "למידה"])
        self.assertEqual(meta["youtube_id"], "BBBBBBBBBBB")
        self.assertIn("hello world", page)

    def test_second_run_skips_videos_already_in_raw(self):
        self.m.main()
        self.fetched.clear()
        self.m.main()
        self.assertEqual(self.fetched, [])
        self.assertEqual(len(list(self.raw.glob("youtube-*.md"))), 2)


if __name__ == "__main__":
    unittest.main()
