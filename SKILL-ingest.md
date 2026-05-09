# SKILL — Ingest

## When to use
When asked to compile new files from `Wikipedia/raw/`

## Steps

### 1. Check manifest
Read `Wikipedia/.manifest.json`
Skip files that have already been compiled and haven't changed.
Process only new files or files that changed since the last compile.

### 2. Read the source
Read the raw/ file in its entirety.

### 3. Extract information
Extract from the source:
- Core concepts
- Entities (people, companies, tools)
- Key claims and facts
- Open questions
Leave out the noise — do not include every minor detail.

### 4. Write a concept page
Create or update a page in `Wikipedia/` with frontmatter:
```
---
topic: [[]]
tags: [wiki]
private: false
wiki_sources: [[raw/filename]]
provenance: extracted
last_updated: YYYY-MM-DD
---
```

### 5. Mark provenance
- `extracted` — Direct information from the source
- `inferred` — Your own synthesis
- `ambiguous` — Contradictory sources, note the contradiction

### 6. Update index.md
Add a row to the table in `Wikipedia/index.md`

### 7. Update manifest
Add to `Wikipedia/.manifest.json`:
```json
{
  "path": "Wikipedia/raw/filename",
  "ingested": "YYYY-MM-DD",
  "pages_produced": ["page-name"]
}
```

### 8. Update log.md
Add a line to `Wikipedia/log.md`:
`## [YYYY-MM-DD] ingest | [Source Title]`

### 9. Run cross-link
After compiling — read SKILL-crosslink.md and connect the new page to the rest of the wiki.

### 10. Run resolve
Read SKILL-resolve.md and update existing pages related to the new information.

## YouTube Queue
When the user asks to compile videos (e.g., "compile videos", "compile the queue"):
1. Run: `python3 "System/youtube-fetch.py"` — downloads transcripts to raw/
2. Wait for the script to finish
3. Compile the new transcript files from raw/ using the standard ingest steps above
4. The script already moves videos from "Pending" to "Compiled" in youtube_queue.md automatically