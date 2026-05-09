# SKILL — Resolve

## When to use
After every ingest — to update existing pages in light of new information.

## Steps

### 1. Find related pages
Read `Wikipedia/index.md` and find pages related to the topic just compiled.

### 2. For each related page — Check:
- Does the new info **contradict** existing info?
  - If yes — add a note to the page: `> ⚠️ Contradiction: [New source] claims X while [Old source] claims Y`
  - Update provenance to `ambiguous`
- Does the new info **strengthen** existing info?
  - If yes — update the page and add the new source to `wiki_sources`
- Does the new info **expand** on existing info?
  - If yes — add a new section to the page

### 3. Update last_compiled
In every page you touched — update `last_updated` to today's date.

### 4. Update log.md
`## [YYYY-MM-DD] resolve | [list of updated pages]`
