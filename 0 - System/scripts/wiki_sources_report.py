#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wiki_sources_report.py — checks wiki_sources on every summary and prints the problems:
no source, a page listing itself, or a "source" that is really another wiki page.
Read-only: it prints and writes nothing.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikilib as V


def classify(page_path, entry, md_index):
    inner = str(entry).strip().removeprefix("[[").removesuffix("]]")
    inner = inner.split("|")[0].split("#")[0].strip()
    if inner.startswith(("http://", "https://")) or Path(inner).suffix.lower() not in ("", ".md"):
        return ("⚪ not checked", "External URL or non-Markdown source: not validated by this report.")
    status, target = V.resolve_link(inner, md_index)
    # Unresolved references can name excluded files. Never echo their names;
    # absence from the public index cannot distinguish protected from missing.
    if status != "ok" or target is None:
        return ("⚪ target unavailable", "The target is not available for checking in the public index (missing/ambiguous/out of scope).")
    target = Path(target)
    if V.is_forbidden(target):
        return ("⚪ target unavailable", "The target is not available for checking in the public index.")
    # ok — but it may point at itself or at another wiki page (not a real ingestion source)
    if V.nfc(str(target)) == V.nfc(str(page_path)):
        return ("🟣 self-reference", f"`{inner}` — the page lists itself as a source")
    if V.WIKI in Path(target).parents and V.RAW not in Path(target).parents:
        return ("🔵 source is a wiki page", f"`{inner}` — probably a cross-link, not a real source")
    return None  # fine (raw/ or a note)


def main():
    md_index = V.all_md_index()
    rows = []
    ok = 0
    for p, meta, _ in V.iter_wiki_pages():
        srcs = meta.get("wiki_sources", [])
        if isinstance(srcs, str):
            srcs = [srcs]
        if not srcs:
            rows.append((V.nfc(p.stem), "⚪ no source", "no wiki_sources field"))
            continue
        for entry in srcs:
            res = classify(p, entry, md_index)
            if res:
                rows.append((V.nfc(p.stem), res[0], res[1]))
            else:
                ok += 1

    print(f"✅ Valid entries: {ok}")
    print(f"⚠️  Problems found: {len(rows)}")
    for name, kind, detail in rows:
        print(f"   {kind}  {name}: {detail}")


if __name__ == "__main__":
    main()
